import re
import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import os
import sys
import requests
import time
from tqdm import tqdm

# Add backend/utils to path for importing the cache decorator
backend_path = Path(__file__).resolve().parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Import configuration and disk cache decorator
from utils.config_loader import get_cache_dir
from utils.disk_cache_decorator import disk_cache_skip_none

# Mutalyzer API endpoint for cDNA to genomic HGVS conversion
MUTALYZER_NORMALIZE_URL = "https://mutalyzer.nl/api/normalize"


@disk_cache_skip_none(str(get_cache_dir('mutalyzer_cache')))
def convert_cdna_to_genomic_hgvs_mutalyzer(transcript_accession, cdna_hgvs_string, genomic_accession):
    """
    Converts a cDNA HGVS string to a genomic HGVS (GRCh38) string using Mutalyzer API.
    Results are cached to disk for fast retrieval on subsequent runs.
    Only successful conversions are cached - failures will be retried.
    
    This function handles two cases:
    1. Complete c notation: convert_cdna_to_genomic_hgvs_mutalyzer("NM_000051.4:c.4415T>A")
       - Only transcript_accession is needed (contains the full notation)
    2. Incomplete c notation: convert_cdna_to_genomic_hgvs_mutalyzer("NM_000051.4", "c.4415T>A", "NC_000011.10")
       - All three parameters are needed
    
    Parameters:
    - transcript_accession: Either the complete notation (NM_...:c....) or just NM_ accession
    - cdna_hgvs_string: The c. HGVS notation (e.g., "c.3247_3248insT") - optional if complete notation provided
    - genomic_accession: The NC_ accession (e.g., "NC_000016.10") - optional if complete notation provided
    
    Returns:
    - Genomic HGVS g. notation, or None if conversion fails
    """
    # Build combined genomic+transcript description for API call
    combined_desc = f"{genomic_accession}({transcript_accession}):{cdna_hgvs_string}"
    encoded_variant = requests.utils.quote(combined_desc, safe='()/:*+')
    url = f"{MUTALYZER_NORMALIZE_URL}/{encoded_variant}"

    response = requests.get(url, timeout=30)
    if response.status_code == 429:
        # Rate limited
        time.sleep(5)
        return None
    if response.status_code != 200:
        # API error
        return None

    data = response.json()

    # Prefer exact genomic equivalent when present
    eq = data.get("equivalent_descriptions", {})
    g_list = eq.get("g") or []
    if isinstance(g_list, list) and len(g_list) > 0:
        first_g = g_list[0]
        if isinstance(first_g, dict):
            g_desc = first_g.get("description")
            if g_desc and ":g." in g_desc:
                return g_desc
        elif isinstance(first_g, str) and ":g." in first_g:
            return first_g

    # Fallback to genomic_description if available
    g_desc = data.get("genomic_description")
    if g_desc and ":g." in g_desc:
        return g_desc
    
    # Conversion failed - decorator will not cache None
    return None

def main():

    def normalize_cdna_hgvs(cdna_hgvs_string):
        """
        Normalize cDNA HGVS string by extracting value from parentheses if present.
        
        If the value contains parentheses like "c.IVS24+1G>T (c.3082+1G>T)",
        extract and return the value inside the parentheses.
        
        Parameters:
        - cdna_hgvs_string: The cDNA HGVS notation (e.g., "c.IVS24+1G>T (c.3082+1G>T)")
        
        Returns:
        - Normalized cDNA HGVS string (e.g., "c.3082+1G>T")
        """
        if not cdna_hgvs_string or pd.isna(cdna_hgvs_string):
            return cdna_hgvs_string
        
        cdna_hgvs_string = str(cdna_hgvs_string).strip()
        
        # Check if there's a pattern like "c.XXX (c.YYY)" and extract the value in parentheses
        # Pattern: something like "c.IVS24+1G>T (c.3082+1G>T)" -> extract "c.3082+1G>T"
        match = re.search(r'\(c\.[^)]+\)', cdna_hgvs_string)
        if match:
            # Extract the value inside parentheses (remove the parentheses)
            normalized = match.group(0).strip('()')
            return normalized
        
        # If no parentheses pattern found, return original value
        return cdna_hgvs_string

    GENE_SYMBOL = 'FBN1' # The gene name for all variants in this specific file
    TRANSCRIPT_ACCESSION = 'NM_000138.5' # The RefSeq transcript accession for FBN1
    GENOMIC_ACCESSION = 'NC_000015.10' # The GenBank genomic accession for FBN1
    cdna_column_name = 'cDNA Nomenclature'

    # Load the CSV file
    csv_file_path = f"data_local_raw/FBN1_phenotypes_v2/Aortic Dilation.csv"
    df = pd.read_csv(csv_file_path)

    # Enable tqdm progress bar for pandas apply
    tqdm.pandas(desc="Converting cDNA to genomic HGVS")
    
    # Use progress_apply() to convert each cDNA HGVS to genomic HGVS with progress bar
    df[cdna_column_name] = df[cdna_column_name].progress_apply(
        lambda x: convert_cdna_to_genomic_hgvs_mutalyzer(TRANSCRIPT_ACCESSION, x, GENOMIC_ACCESSION)
    )

    # Save the DataFrame to a new CSV file
    # result_df.to_csv(f"data_local_raw/FBN1_phenotypes_v2/Aortic Dilation_genomic38.csv", index=False)

if __name__ == "__main__":
    main()
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

# Add the parent directory to the Python path to enable package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# Mutalyzer API endpoint for cDNA to genomic HGVS conversion
MUTALYZER_NORMALIZE_URL = "https://mutalyzer.nl/api/normalize"

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

def convert_cdna_to_genomic_hgvs_mutalyzer(transcript_accession, cdna_hgvs_string, genomic_accession):
    """
    Converts a cDNA HGVS string to a genomic HGVS (GRCh38) string using Mutalyzer API.
    Used as fallback when SPDI parsing fails.
    
    Parameters:
    - transcript_accession: The NM_ accession (e.g., "NM_024675.4")
    - cdna_hgvs_string: The c. HGVS notation (e.g., "c.3247_3248insT")
    - genomic_accession: The NC_ accession (e.g., "NC_000016.10")
    
    Returns:
    - Genomic HGVS g. notation, or None if conversion fails
    """
    try:
        # Normalize the cDNA HGVS string before API call
        normalized_cdna = normalize_cdna_hgvs(cdna_hgvs_string)
        
        # Build combined genomic+transcript description: NC_...(NM_...):c....
        combined_desc = f"{genomic_accession}({transcript_accession}):{normalized_cdna}"
        encoded_variant = requests.utils.quote(combined_desc, safe='()/:*+')
        url = f"{MUTALYZER_NORMALIZE_URL}/{encoded_variant}"

        response = requests.get(url, timeout=30)
        if response.status_code == 429:
            # Rate limited
            time.sleep(5)
            return None
        if response.status_code != 200:
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
            
        return None

    except (requests.exceptions.Timeout, requests.exceptions.RequestException, Exception):
        return None

def convert_single_variant(c_hgvs, transcript_accession, genomic_accession):
    """
    Helper function to convert a single cDNA HGVS to genomic HGVS.
    Used with pandas apply().
    
    Parameters:
    - c_hgvs: The cDNA HGVS notation (may contain parentheses like "c.IVS24+1G>T (c.3082+1G>T)")
    - transcript_accession: The transcript accession
    - genomic_accession: The genomic accession
    
    Returns:
    - pandas Series with hgvs_coding (normalized) and hgvs_genomic_38
    """
    # Normalize the cDNA HGVS before conversion
    normalized_c_hgvs = normalize_cdna_hgvs(c_hgvs)
    genomic_hgvs = convert_cdna_to_genomic_hgvs_mutalyzer(transcript_accession, normalized_c_hgvs, genomic_accession)
    return pd.Series({
        'hgvs_coding': normalized_c_hgvs,  # Store normalized value
        'hgvs_genomic_38': genomic_hgvs
    })

def main():
    GENE_NAME = 'FBN1' # The gene name for all variants in this specific file
    TRANSCRIPT_ACCESSION = 'NM_000138.5' # The RefSeq transcript accession for FBN1
    GENOMIC_ACCESSION = 'NC_000015.10' # The GenBank genomic accession for FBN1

    # Load the CSV file
    csv_file_path = f"data_local_raw/FBN1_phenotypes_v2/Aortic Dilation.csv"
    df = pd.read_csv(csv_file_path)

    # Enable tqdm progress bar for pandas apply
    tqdm.pandas(desc="Converting cDNA to genomic HGVS")
    
    # Use progress_apply() to convert each cDNA HGVS to genomic HGVS with progress bar
    result_df = df['cDNA Nomenclature'].progress_apply(
        lambda x: convert_single_variant(x, TRANSCRIPT_ACCESSION, GENOMIC_ACCESSION)
    )

    # Save the DataFrame to a new CSV file
    result_df.to_csv(f"data_local_raw/FBN1_phenotypes_v2/Aortic Dilation_genomic38.csv", index=False)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import requests
import pandas as pd
import os
import sys
import logging
from typing import List, Optional, Tuple, Dict, Any

# Add the parent directory to the Python path to enable package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Constants
API_BASE = "https://brcaexchange.org/backend/data"

requested_fields = [
    "Chr",
    "Pos",
    "Ref",
    "Alt",
    "Gene_Symbol",
    "Genomic_HGVS_38",
    "HGVS_cDNA",
    "Pathogenicity_expert", 

]

def convert_brca_pathogenicity_to_standard(original_value: str) -> str:
    """
    Convert BRCA Exchange pathogenicity values to standard pattern names.
    This function handles the specific pathogenicity terms used in BRCA Exchange data.
    
    Args:
        original_value: Raw pathogenicity value from BRCA Exchange
        
    Returns:
        Standardized pathogenicity value
    """
    if pd.isna(original_value) or not original_value:
        return "unknown"
    
    original_lower = str(original_value).lower().strip()
    
    # Map BRCA Exchange specific pathogenicity terms to standard patterns
    if original_lower == 'pathogenic':
        return "pathogenic"
    elif original_lower == 'likely pathogenic':
        return "likely_pathogenic"
    elif original_lower == 'benign / little clinical significance':
        return "benign"
    elif original_lower == 'likely benign':
        return "likely_benign"
    elif original_lower == 'uncertain significance':
        return "uncertain_significance"
    elif original_lower == 'not yet reviewed':
        return "not_yet_reviewed"
    else:
        return "unknown"

class BRCAProcessor:
    """
    BRCA Exchange processor for creating variant DataFrames following the same pattern as ClinVarProcessor.
    """
    
    def __init__(self, gene_symbol: str, logger=None):
        """Initialize the BRCAProcessor."""
        self.gene_symbol = gene_symbol
        self.logger = logger or self._setup_logger()
        self.df_brca = self._fetch_brca_data()
    
    def _setup_logger(self):
        """Set up default logger for the processor."""
        logger = logging.getLogger(f"{__name__}.BRCAProcessor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _fetch_brca_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch BRCA Exchange data from API.
        
        Returns:
            pandas.DataFrame: DataFrame containing the BRCA data, or None if error
        """
        self.logger.info(f"Fetching BRCA Exchange data for gene: {self.gene_symbol}")
        
        try:
            # Fetch data from API
            params = {
                "format": "json",
                "filter": "Gene_Symbol", 
                "filterValue": self.gene_symbol,
                "page_size": 0,
                "include": "all"
            }
            
            response = requests.get(API_BASE, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process variants into DataFrame
            variants = []
            for variant in data.get("data", []):
                variant_dict = {field: variant.get(field, "") for field in requested_fields}
                variants.append(variant_dict)
            
            df = pd.DataFrame(variants)
            self.logger.info(f"Successfully loaded {len(df)} variants from BRCA Exchange")
            return df
            
        except Exception as e:
            self.logger.error(f"An error occurred while fetching BRCA data: {e}")
            return None
    
    
    def _create_variants_dataframe(self) -> pd.DataFrame:
        """
        Create a simplified variants DataFrame following the VariantModel schema.
        
        Returns:
            DataFrame with variant data following VariantModel schema
        """
        if self.df_brca is None or self.df_brca.empty:
            self.logger.warning("Empty DataFrame provided for variant processing")
            return pd.DataFrame()
        
        self.logger.info(f"Creating variants DataFrame for {len(self.df_brca)} BRCA variants for gene {self.gene_symbol}")
        
        variants_data = []
        
        for idx, row in self.df_brca.iterrows():
            try:
                # Extract basic variant information
                chromosome = str(row.get('Chr', '')).replace('chr', '')
                position = row.get('Pos')
                ref_allele = str(row.get('Ref', ''))
                alt_allele = str(row.get('Alt', ''))
                
                # Skip if essential fields are missing
                if not all([chromosome, position, ref_allele, alt_allele]):
                    self.logger.debug(f"Skipping variant at index {idx}: missing essential fields")
                    continue
                
                # Convert position to int
                try:
                    position = int(position)
                except (ValueError, TypeError):
                    self.logger.debug(f"Skipping variant at index {idx}: invalid position")
                    continue
                
                # Extract HGVS information
                hgvs_genomic_38 = row.get('Genomic_HGVS_38', '')
                hgvs_coding = row.get('HGVS_cDNA', '')
                pathogenicity_original = convert_brca_pathogenicity_to_standard(row.get('Pathogenicity_expert', ''))

                # Create variant record
                variant_record = {
                    'chromosome': chromosome,
                    'position': position,
                    'ref_allele': ref_allele,
                    'alt_allele': alt_allele,
                    
                    'hgvs_genomic_38': hgvs_genomic_38,
                    'hgvs_coding': hgvs_coding,

                    'pathogenicity_original': pathogenicity_original,
                }
                
                variants_data.append(variant_record)
                
            except Exception as e:
                self.logger.error(f"Error processing variant at index {idx}: {e}")
                continue
        
        if variants_data:
            result_df = pd.DataFrame(variants_data)
            self.logger.info(f"Successfully created DataFrame with {len(result_df)} variants")
            return result_df
        else:
            self.logger.warning("No variants could be processed")
            return pd.DataFrame()
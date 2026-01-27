#!/usr/bin/env python3
"""
Load JSON file and extract missense variants, saving as a DataFrame.

This script:
1. Loads the metadata JSON file
2. Filters variants where most_severe_consequence == "missense_variant"
3. Converts the filtered variants to a pandas DataFrame
4. Saves the result as a CSV file
"""

import json
import pandas as pd
from pathlib import Path


def load_json_and_get_missense_variants(json_path: str) -> pd.DataFrame:
    """
    Load JSON file and extract missense variants.
    
    Args:
        json_path: Path to the JSON metadata file
        
    Returns:
        DataFrame containing missense variants with specified columns
    """
    # Define required columns
    required_columns = [
        'hgvs_genomic_38',
        'hgvs_coding',
        'hgvs_protein',
        'chromosome',
        'position',
        'ref_allele',
        'alt_allele',
        'gene_symbol',
        'most_severe_consequence',
        'pathogenicity_original'
    ]
    
    # Load JSON file
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract variants list
    variants = data.get('variants', [])
    
    # Filter for missense variants
    missense_variants = [
        variant for variant in variants
        if variant.get('most_severe_consequence') == 'missense_variant'
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(missense_variants)
    
    # Select only the required columns (if they exist)
    available_columns = [col for col in required_columns if col in df.columns]
    df = df[available_columns]
    
    return df


def main():
    """Main function to load JSON and extract missense variants."""
    # Path to JSON file
    json_path = 'data_user/training_embedding_results/metadata/FBN1/metadata.json'
    
    # Load and filter missense variants
    print(f"Loading JSON file: {json_path}")
    df = load_json_and_get_missense_variants(json_path)
    
    print(f"Found {len(df)} missense variants")
    print(f"DataFrame shape: {df.shape}")
    print(f"\nDataFrame columns: {list(df.columns)}")
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Save to CSV
    output_path = 'data_user/training_embedding_results/metadata/FBN1/missense_variants.csv'
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"\nSaved missense variants to: {output_path}")
    
    return df


if __name__ == '__main__':
    df = main()


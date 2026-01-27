import os
import pandas as pd
import sys
from pathlib import Path
from tqdm import tqdm

# Add the parent directory to the Python path to enable package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.variant_processor.hgvsg_to_vcf import hgvs_g_to_vcf

def process_single_variant_genomic(hgvs_g):
    """
    Process a single variant: convert genomic HGVS to VCF format.
    
    Parameters:
    - hgvs_g: The genomic HGVS notation
    
    Returns:
    - pandas Series with VCF fields (chrom, pos, ref, alt)
    """
    # Convert genomic HGVS to VCF format
    vcf_data = None
    if hgvs_g and pd.notna(hgvs_g):
        vcf_data = hgvs_g_to_vcf(hgvs_g)
    
    # Build result dictionary
    if vcf_data:
        result = {
            'chromosome': vcf_data.get('chrom'),
            'position': vcf_data.get('pos'),
            'ref_allele': vcf_data.get('ref'),
            'alt_allele': vcf_data.get('alt')
        }
    else:
        result = {
            'chromosome': None,
            'position': None,
            'ref_allele': None,
            'alt_allele': None
        }
    
    return pd.Series(result)

def process_dataframe_genomic(df, hgvs_column_name='hgvs_genomic_38'):
    """
    Process a DataFrame: convert genomic HGVS to VCF format.
    
    Parameters:
    - df: Input DataFrame with genomic HGVS column
    - hgvs_column_name: Name of the column containing genomic HGVS
    
    Returns:
    - DataFrame with added VCF fields (chromosome, position, ref_allele, alt_allele)
    """
    # Enable tqdm progress bar for pandas apply
    tqdm.pandas(desc="Processing variants")
    
    # Process each variant: genomic HGVS -> VCF
    result_df = df[hgvs_column_name].progress_apply(
        lambda x: process_single_variant_genomic(x)
    )
    
    # Merge with original dataframe (keep other columns)
    output_df = df.copy()
    output_df = pd.concat([output_df, result_df], axis=1)
    
    # Convert chromosome and position to nullable integer type to avoid decimal points in CSV
    # Use Int64 (nullable integer) to handle NaN values while keeping integer format
    if 'chromosome' in output_df.columns:
        output_df['chromosome'] = output_df['chromosome'].astype('Int64')
    if 'position' in output_df.columns:
        output_df['position'] = output_df['position'].astype('Int64')
    
    return output_df

def main():
    """Main function to process BRCA variants."""
    genes = ["BRCA1", "BRCA2"]
    num_variants = 3000
    seed = 42
    query_index = 0
    hgvs_column_name = "hgvs_genomic_38"
    
    for gene in genes:
        print(f"\nProcessing {gene}...")
        
        # Read input CSV
        input_file = f"data_local_raw/{gene}/not_yet_reviewed.csv"
        if not os.path.exists(input_file):
            print(f"Warning: {input_file} not found, skipping {gene}")
            continue
        
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} variants from {input_file}")
        
        # Sample variants
        if len(df) < num_variants:
            print(f"Warning: Only {len(df)} variants available, using all of them")
            selected_df = df.copy()
        else:
            selected_df = df.sample(n=num_variants, random_state=seed).reset_index(drop=True)
        
        print(f"Selected {len(selected_df)} variants for processing")
        
        # Process variants: genomic HGVS -> VCF
        processed_df = process_dataframe_genomic(selected_df, hgvs_column_name)
        
        # Create output directory
        output_dir = f"data_user/user_query/inputs/{gene}/query_{query_index}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the result
        output_file = os.path.join(output_dir, f"{gene}_test.csv")
        processed_df.to_csv(output_file, index=False)
        print(f"Saved processed file: {output_file}")
        print(f"Processed {len(processed_df)} variants for {gene}")
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()

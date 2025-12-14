import pandas as pd
import os
import sys
from pathlib import Path
from tqdm import tqdm

# Add the parent directory to the Python path to enable package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import conversion functions
from tools.variant_processor.hgvs_c_to_g import convert_cdna_to_genomic_hgvs_mutalyzer, normalize_cdna_hgvs
from tools.variant_processor.hgvsg_to_vcf import hgvs_g_to_vcf

# FBN1 gene configuration
GENE_NAME = 'FBN1'
TRANSCRIPT_ACCESSION = 'NM_000138.5'  # The RefSeq transcript accession for FBN1
GENOMIC_ACCESSION = 'NC_000015.10'    # The GenBank genomic accession for FBN1

def process_single_variant(c_hgvs, transcript_accession, genomic_accession):
    """
    Process a single variant: convert cDNA HGVS to genomic HGVS, then to VCF format.
    
    Parameters:
    - c_hgvs: The cDNA HGVS notation
    - transcript_accession: The transcript accession
    - genomic_accession: The genomic accession
    
    Returns:
    - pandas Series with hgvs_coding, hgvs_genomic_38, and VCF fields (chrom, pos, ref, alt)
    """
    # Normalize the cDNA HGVS
    normalized_c_hgvs = normalize_cdna_hgvs(c_hgvs)
    
    # Convert cDNA to genomic HGVS
    genomic_hgvs = convert_cdna_to_genomic_hgvs_mutalyzer(
        transcript_accession, 
        normalized_c_hgvs, 
        genomic_accession
    )
    
    # Convert genomic HGVS to VCF format
    vcf_data = None
    if genomic_hgvs:
        vcf_data = hgvs_g_to_vcf(genomic_hgvs)
    
    # Build result dictionary
    result = {
        'hgvs_coding': normalized_c_hgvs,
        'hgvs_genomic_38': genomic_hgvs
    }
    
    # Add VCF fields if conversion was successful
    if vcf_data:
        result.update({
            'chromosome': vcf_data.get('chrom'),
            'position': vcf_data.get('pos'),
            'ref_allele': vcf_data.get('ref'),
            'alt_allele': vcf_data.get('alt')
        })
    else:
        result.update({
            'chromosome': None,
            'position': None,
            'ref_allele': None,
            'alt_allele': None
        })
    
    return pd.Series(result)

def process_csv_file(csv_file_path, transcript_accession, genomic_accession, output_dir):
    """
    Process a single CSV file: convert cDNA HGVS to genomic HGVS and VCF format.
    
    Parameters:
    - csv_file_path: Path to the input CSV file
    - transcript_accession: The transcript accession
    - genomic_accession: The genomic accession
    - output_dir: Directory to save output files
    """
    # Load the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Check if 'cDNA Nomenclature' column exists
    if 'cDNA Nomenclature' not in df.columns:
        print(f"Warning: 'cDNA Nomenclature' column not found in {csv_file_path}. Skipping.")
        return
    
    # Get the base filename without extension
    base_name = Path(csv_file_path).stem
    
    # Enable tqdm progress bar for pandas apply
    tqdm.pandas(desc=f"Processing {base_name}")
    
    # Process each variant: cDNA -> genomic HGVS -> VCF
    result_df = df['cDNA Nomenclature'].progress_apply(
        lambda x: process_single_variant(x, transcript_accession, genomic_accession)
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
    
    # Save the result
    output_file_path = os.path.join(output_dir, f"{base_name}_processed.csv")
    output_df.to_csv(output_file_path, index=False)
    print(f"Saved processed file: {output_file_path}")
    
    return output_df

def main():
    """Main function to process all CSV files in the directory."""
    # Directory containing CSV files
    input_dir = "data_local_raw/FBN1_phenotypes_v2"
    output_dir = "data_user/user_query/inputs/FBN1/query_1"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all CSV files in the directory
    # csv_files = list(Path(input_dir).glob("*.csv"))
    csv_files = ["data_local_raw/FBN1_phenotypes_v2/Both Aortic Dilation and Mitral Valve Prolapse.csv"]
    
    if not csv_files:
        print(f"No CSV files found in {input_dir}")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to process:")
    for csv_file in csv_files:
        csv_path = Path(csv_file)
        print(f"  - {csv_path.name}")
    
    # Process each CSV file
    for csv_file in tqdm(csv_files, desc="Processing files"):
        csv_path = Path(csv_file)
        print(f"\nProcessing: {csv_path.name}")
        try:
            process_csv_file(
                str(csv_path),
                TRANSCRIPT_ACCESSION,
                GENOMIC_ACCESSION,
                output_dir
            )
        except Exception as e:
            print(f"Error processing {csv_path.name}: {e}")
            continue
    
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()

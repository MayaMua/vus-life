import os
import sys
import pandas as pd
import re
from tqdm import tqdm

# Add the backend directory to the Python path to enable package imports
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from tools.variant_processor.hgvs_g_to_vcf import hgvs_g_to_vcf
from tools.variant_processor.hgvs_c_to_g import convert_cdna_to_genomic_hgvs_mutalyzer


def normalize_cdna_notation(name_str):
    """
    Normalize cDNA notation by removing gene name in parentheses.
    
    Examples:
    - "NM_000051.4(ATM):c.-174A>G" -> "NM_000051.4:c.-174A>G"
    - "NM_000051.4:c.4415T>A" -> "NM_000051.4:c.4415T>A" (no change)
    - "NC_000011.10:g.108222768C>T" -> "NC_000011.10:g.108222768C>T" (genomic, no change)
    
    Parameters:
    - name_str: The Name column value from ClinVar
    
    Returns:
    - Normalized notation string
    """
    if not name_str or pd.isna(name_str):
        return None
    
    name_str = str(name_str).strip()
    
    # Check if it contains gene name in parentheses: NM_...(GENE):c....
    # Pattern: capture NM_accession, skip (gene), keep :c.variant
    match = re.match(r'(NM_[^(]+)\([^)]+\)(:.+)', name_str)
    if match:
        # Remove the gene name part
        return match.group(1) + match.group(2)
    
    # If no gene name pattern, return as is
    return name_str


def clean_protein_annotation(hgvs_str):
    """
    Remove protein annotation from HGVS notation.
    
    Many ClinVar entries include protein-level changes like (p.Met1Leu) which
    interfere with cDNA to genomic conversion. This function removes them.
    
    Examples:
    - "NM_000051.4:c.1A>T (p.Met1Leu)" -> "NM_000051.4:c.1A>T"
    - "NM_000051.4:c.-174A>G" -> "NM_000051.4:c.-174A>G" (no change)
    
    Parameters:
    - hgvs_str: HGVS notation string (possibly with protein annotation)
    
    Returns:
    - Cleaned HGVS notation string
    """
    if not hgvs_str or pd.isna(hgvs_str):
        return hgvs_str
    
    hgvs_str = str(hgvs_str).strip()
    
    # Remove protein annotation: (p.xxx) or ( p.xxx ) with optional spaces
    hgvs_str = re.sub(r'\s*\(p\.[^)]+\)\s*', '', hgvs_str)
    
    return hgvs_str.strip()


def classify_pathogenicity(pathogenicity_str):
    """
    Classify pathogenicity into clear categories.
    Returns 'pathogenic', 'benign', or None for mixed/unclear cases.
    
    Parameters:
    - pathogenicity_str: The Germline classification value
    
    Returns:
    - 'pathogenic', 'benign', or None
    """
    if not pathogenicity_str or pd.isna(pathogenicity_str):
        return None
    
    path_lower = str(pathogenicity_str).lower()
    
    # Check for clear pathogenic cases (no benign, no VUS, no conflicting)
    if "pathogenic" in path_lower and "benign" not in path_lower and "uncertain" not in path_lower and "conflicting" not in path_lower:
        return "pathogenic"
    
    # Check for clear benign cases (no pathogenic, no VUS, no conflicting)
    if "benign" in path_lower and "pathogenic" not in path_lower and "uncertain" not in path_lower and "conflicting" not in path_lower:
        return "benign"
    
    # Mixed or unclear cases
    return None


def process_clinvar(input_file, output_file, 
                    gene_symbol, 
                    genomic_accession, 
                    test_rows=0,
                    batch_size=100,
                    save_checkpoints=False):
    """
    Process ClinVar data in simplified format with batch processing.
    
    Parameters:
    - input_file: Path to ClinVar txt file
    - output_file: Path to output CSV file
    - gene_symbol: Gene symbol to add to results
    - genomic_accession: Genomic accession for the gene (e.g., "NC_000011.10" for ATM)
    - test_rows: Number of rows to process for testing (0 for all)
    - batch_size: Number of variants to process per batch (default: 100)
    - save_checkpoints: If True, save intermediate results after each batch
    """
    print(f"Reading ClinVar data from: {input_file}")
    
    # Read the tab-separated file
    df = pd.read_csv(input_file, sep='\t', low_memory=False)
    
    print(f"Total rows in file: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Select only Name and Germline classification columns
    columns_required = ['Name', 'Germline classification']
    df = df[columns_required].copy()
    
    # For testing, take first N rows
    if test_rows:
        df = df.head(test_rows).copy()
        print(f"\nProcessing first {test_rows} rows for testing")
    
    print(f"\nSample data:")
    print(df.head())
    
    # Filter by pathogenicity
    print("\nFiltering by pathogenicity...")
    df['pathogenicity_original'] = df['Germline classification'].apply(classify_pathogenicity)
    df_filtered = df[df['pathogenicity_original'].notna()].copy()
    
    print(f"Rows after pathogenicity filter: {len(df_filtered)}")
    if len(df_filtered) == 0:
        print("Warning: No rows passed pathogenicity filter!")
        return
    
    print(f"\nPathogenicity distribution:")
    print(df_filtered['pathogenicity_original'].value_counts())
    
    # Normalize cDNA notation and filter out genomic notations
    print("\nNormalizing cDNA notation...")
    df_filtered['hgvs_coding'] = df_filtered['Name'].apply(normalize_cdna_notation)
    
    # Clean protein annotations that interfere with conversion
    print("Cleaning protein annotations...")
    before_clean_sample = df_filtered['hgvs_coding'].head(10).tolist()
    df_filtered['hgvs_coding'] = df_filtered['hgvs_coding'].apply(clean_protein_annotation)
    after_clean_sample = df_filtered['hgvs_coding'].head(10).tolist()
    
    # Show cleaning examples
    cleaned_count = sum(1 for before, after in zip(before_clean_sample, after_clean_sample) if before != after)
    if cleaned_count > 0:
        print(f"  Cleaned {cleaned_count} protein annotations from sample")
        for i, (before, after) in enumerate(zip(before_clean_sample, after_clean_sample)):
            if before != after:
                print(f"    Before: {before}")
                print(f"    After:  {after}")
    
    # Filter out rows with genomic notation (g.) - only keep cDNA notation (c.)
    print("\nFiltering to keep only cDNA notations (c.)...")
    initial_count = len(df_filtered)
    df_filtered = df_filtered[df_filtered['hgvs_coding'].str.contains(':c.', na=False)].copy()
    print(f"Rows with cDNA notation: {len(df_filtered)}/{initial_count}")
    
    if len(df_filtered) == 0:
        print("Warning: No cDNA notations found after filtering!")
        return
    
    print("\nSample cDNA notations:")
    print(df_filtered[['Name', 'hgvs_coding']].head())
    
    # Convert cDNA to genomic HGVS in batches
    print("\nConverting cDNA to genomic HGVS (GRCh38)...")
    print(f"Using genomic accession: {genomic_accession}")
    
    total_variants = len(df_filtered)
    num_batches = (total_variants + batch_size - 1) // batch_size
    
    print(f"Processing {total_variants} variants in {num_batches} batches of {batch_size}")
    if save_checkpoints:
        print(f"Checkpoint mode: Intermediate results will be saved after each batch")
    
    hgvs_genomic_list = []
    failed_examples = []
    
    # Process in batches
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_variants)
        current_batch_size = end_idx - start_idx
        
        print(f"\nBatch {batch_num + 1}/{num_batches}: Processing variants {start_idx + 1}-{end_idx}")
        
        # Get batch of variants
        batch_variants = df_filtered['hgvs_coding'].iloc[start_idx:end_idx]
        
        # Process batch with progress bar
        batch_results = []
        for hgvs_c in tqdm(batch_variants, desc=f"Batch {batch_num + 1}", total=current_batch_size):
            # All rows should have cDNA notation at this point
            if hgvs_c and ':c.' in hgvs_c:
                # Parse the cDNA notation to extract transcript and variant
                # Format: NM_000051.4:c.-174A>G
                parts = hgvs_c.split(':', 1)
                if len(parts) == 2:
                    transcript_acc = parts[0]  # NM_000051.4
                    cdna_variant = parts[1]    # c.-174A>G
                    
                    # Call with three parameters: transcript, cdna, genomic
                    # Results are automatically cached by @disk_cache.memoize()
                    hgvs_g = convert_cdna_to_genomic_hgvs_mutalyzer(
                        transcript_acc, 
                        cdna_variant, 
                        genomic_accession
                    )
                else:
                    hgvs_g = None
                
                if hgvs_g is None and len(failed_examples) < 3:
                    failed_examples.append(hgvs_c)
            else:
                # Should not happen after filtering, but handle it
                hgvs_g = None
            
            batch_results.append(hgvs_g)
        
        # Add batch results to overall list
        hgvs_genomic_list.extend(batch_results)
        
        # Show batch statistics
        batch_success = sum(1 for x in batch_results if x is not None)
        batch_failed = current_batch_size - batch_success
        print(f"  Batch {batch_num + 1} complete: {batch_success} success, {batch_failed} failed")
        
        # Save checkpoint if requested
        if save_checkpoints:
            # Add genomic HGVS results processed so far
            df_filtered_copy = df_filtered.iloc[:end_idx].copy()
            df_filtered_copy['hgvs_genomic_38'] = hgvs_genomic_list
            
            # Create checkpoint filename
            checkpoint_file = output_file.replace('.csv', f'_checkpoint_batch{batch_num + 1}.csv')
            
            # Save checkpoint with partial results
            checkpoint_df = df_filtered_copy[df_filtered_copy['hgvs_genomic_38'].notna()].copy()
            
            if len(checkpoint_df) > 0:
                # Parse VCF for checkpoint
                vcf_results_checkpoint = []
                for hgvs_g in checkpoint_df['hgvs_genomic_38']:
                    vcf = hgvs_g_to_vcf(hgvs_g)
                    vcf_results_checkpoint.append(vcf)
                
                vcf_df_checkpoint = pd.DataFrame([
                    {
                        'chromosome': vcf.get('chrom') if vcf else None,
                        'position': vcf.get('pos') if vcf else None,
                        'ref_allele': vcf.get('ref') if vcf else None,
                        'alt_allele': vcf.get('alt') if vcf else None
                    }
                    for vcf in vcf_results_checkpoint
                ], index=checkpoint_df.index)
                
                checkpoint_df[['chromosome', 'position', 'ref_allele', 'alt_allele']] = vcf_df_checkpoint
                checkpoint_df['gene_symbol'] = gene_symbol
                
                output_columns = [
                    'hgvs_genomic_38',
                    'hgvs_coding',
                    'chromosome',
                    'position',
                    'ref_allele',
                    'alt_allele',
                    'gene_symbol',
                    'pathogenicity_original'
                ]
                
                checkpoint_output = checkpoint_df[output_columns].copy()
                checkpoint_output = checkpoint_output[checkpoint_output['chromosome'].notna()].copy()
                
                os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
                checkpoint_output.to_csv(checkpoint_file, index=False)
                print(f"  Checkpoint saved: {checkpoint_file} ({len(checkpoint_output)} variants)")
    
    df_filtered['hgvs_genomic_38'] = hgvs_genomic_list
    
    # Debug: Check conversion results
    print(f"\nGenomic HGVS conversion results:")
    print(f"  Success: {df_filtered['hgvs_genomic_38'].notna().sum()}/{len(df_filtered)}")
    print(f"  Failed: {df_filtered['hgvs_genomic_38'].isna().sum()}/{len(df_filtered)}")
    
    if failed_examples:
        print(f"\nSample failed conversions:")
        for example in failed_examples:
            print(f"  {example}")
    
    # Filter out failed conversions
    df_filtered = df_filtered[df_filtered['hgvs_genomic_38'].notna()].copy()
    
    if len(df_filtered) == 0:
        print("Warning: No successful genomic HGVS conversions!")
        return
    
    print(f"\nSample genomic HGVS:")
    print(df_filtered[['hgvs_coding', 'hgvs_genomic_38']].head())
    
    # Convert HGVS genomic to VCF format
    print("\nConverting HGVS genomic to VCF format...")
    vcf_results = []
    for hgvs_g in tqdm(df_filtered['hgvs_genomic_38'], desc="HGVS to VCF"):
        vcf = hgvs_g_to_vcf(hgvs_g)
        vcf_results.append(vcf)
    
    # Parse VCF dictionary into separate columns in a single pass
    vcf_df = pd.DataFrame([
        {
            'chromosome': vcf.get('chrom') if vcf else None,
            'position': vcf.get('pos') if vcf else None,
            'ref_allele': vcf.get('ref') if vcf else None,
            'alt_allele': vcf.get('alt') if vcf else None
        }
        for vcf in vcf_results
    ], index=df_filtered.index)
    
    # Assign all columns at once
    df_filtered[['chromosome', 'position', 'ref_allele', 'alt_allele']] = vcf_df
    
    # Add gene symbol
    df_filtered['gene_symbol'] = gene_symbol
    
    # Reorder columns to match required format
    output_columns = [
        'hgvs_genomic_38',
        'hgvs_coding',
        'chromosome',
        'position',
        'ref_allele',
        'alt_allele',
        'gene_symbol',
        'pathogenicity_original'
    ]
    
    df_output = df_filtered[output_columns].copy()
    
    # Remove rows where VCF conversion failed
    df_output = df_output[df_output['chromosome'].notna()].copy()
    
    print(f"\nFinal output rows (after VCF conversion): {len(df_output)}")
    print(f"\nSample output data:")
    print(df_output.head(10))
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_output.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")
    
    return df_output


if __name__ == "__main__":
    gene_symbol = "ATM"
    genomic_accession = "NC_000011.10"
    test_rows = 200  # Set to 0 to process all rows
    input_file_path = f"../data_local/raw/clinvar/{gene_symbol}_clinvar_result.txt"
    output_file_path = f"../data_local/processed/clinvar/{gene_symbol}_variants.csv"
    
    # Batch processing settings
    batch_size = 100  # Process 100 variants per batch
    save_checkpoints = False  # Set to True to save intermediate results after each batch
    
    process_clinvar(
        input_file=input_file_path, 
        output_file=output_file_path, 
        gene_symbol=gene_symbol, 
        genomic_accession=genomic_accession, 
        test_rows=test_rows,
        batch_size=batch_size,
        save_checkpoints=save_checkpoints
    )

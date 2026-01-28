import os
import sys
import pandas as pd

# Add the backend directory to the Python path to enable package imports
# This file is at: backend/tools/training_data_processors/lovd_process.py
# We need to add: backend/ (3 levels up)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from tools.variant_processor.hgvs_g_to_vcf import hgvs_g_to_vcf
from tools.variant_processor.hgvs_c_to_g import convert_cdna_to_genomic_hgvs_mutalyzer


if __name__ == "__main__":
    gene_symbol = "USH2A"
    genomic_accession = "NC_000001.11"
    transcript_accession = "NM_206933.4"
    input_file_path = f"../data_local/raw/lovd/{gene_symbol}_LOVD.csv"
    df = pd.read_csv(input_file_path, encoding='utf-8')
    columns_required = ['DNA change (cDNA)     ', 'Clinical classification     ', 'DNA change (hg38)     ']
    df = df[columns_required]

    # df = df.rename(columns={columns_required[0]: 'hgvs_coding', columns_required[1]: 'pathogenicity_original'})
    df['gene_symbol'] = gene_symbol
    
    # Filter and classify pathogenicity
    def classify_pathogenicity(x):
        """
        Classify pathogenicity into clear categories.
        Returns 'pathogenic', 'benign', or None for mixed/unclear cases.
        """
        if pd.isna(x):
            return None
        
        x_lower = str(x).lower()
        
        # Check for clear pathogenic cases (no benign, no VUS)
        if "pathogenic" in x_lower and "benign" not in x_lower and "vus" not in x_lower:
            return "pathogenic"
        
        # Check for clear benign cases (no pathogenic, no VUS)
        if "benign" in x_lower and "pathogenic" not in x_lower and "vus" not in x_lower:
            return "benign"
        
        # Mixed or unclear cases
        return None
    
    df['pathogenicity_original'] = df[columns_required[1]].apply(classify_pathogenicity)
    
    # Filter to keep only rows with clear classification
    df_filtered = df[df['pathogenicity_original'].notna()].copy()
    
    print(f"Original rows: {len(df)}")
    print(f"Filtered rows: {len(df_filtered)}")
    print(f"\nPathogenicity distribution:")
    print(df_filtered['pathogenicity_original'].value_counts())
    print(f"\nSample filtered data:")
    print(df_filtered[columns_required + ['pathogenicity_original']].head(10))
    
    # Import tqdm for progress tracking
    from tqdm import tqdm
    
    # Process variants: convert cDNA to genomic HGVS, then to VCF
    print("\nBuilding hgvs_coding...")
    df_filtered['hgvs_coding'] = df_filtered[columns_required[0]].apply(lambda x: transcript_accession + ":" + x)
    # Select first 10 rows to test
    # df_filtered = df_filtered[:10].copy()

    print("\nBuilding hgvs_genomic_38 from existing DNA change (hg38) column...")
    hgvs_genomic_list = []
    hg38_col = columns_required[2]  # 'DNA change (hg38)'
    cdna_col = columns_required[0]  # 'DNA change (cDNA)'
    from_existing = 0
    from_conversion = 0
    
    for idx, row in tqdm(df_filtered.iterrows(), total=len(df_filtered), desc="Building genomic HGVS"):
        hg38_value = row[hg38_col]
        
        # Use existing hg38 value if available and not empty
        if pd.notna(hg38_value) and str(hg38_value).strip():
            # Add NC_000001.11: prefix if not already present
            hg38_str = str(hg38_value).strip()
            if hg38_str.startswith('NC_'):
                hgvs_genomic_list.append(hg38_str)
            elif hg38_str.startswith('g.'):
                hgvs_genomic_list.append(genomic_accession + ':' + hg38_str)
            else:
                # Assume it's a g. notation without prefix
                hgvs_genomic_list.append(genomic_accession + ':g.' + hg38_str)
            from_existing += 1
        else:
            # If empty, try to convert from cDNA using Mutalyzer
            cdna = row[cdna_col]
            hgvs_g = convert_cdna_to_genomic_hgvs_mutalyzer(transcript_accession, cdna, genomic_accession)
            hgvs_genomic_list.append(hgvs_g)
            from_conversion += 1
    
    df_filtered['hgvs_genomic_38'] = hgvs_genomic_list
    print(f"\nGenomic HGVS sources: {from_existing} from existing column, {from_conversion} from cDNA conversion")
    
    # Debug: Check what genomic HGVS values we got
    print("\nSample genomic HGVS values:")
    print(df_filtered[['hgvs_coding', 'hgvs_genomic_38']].head())
    print(f"\nNone values in hgvs_genomic_38: {df_filtered['hgvs_genomic_38'].isna().sum()}")
    
    # Convert HGVS genomic to VCF format
    print("\nConverting HGVS genomic to VCF format...")
    vcf_results = []
    for hgvs_g in tqdm(df_filtered['hgvs_genomic_38'], desc="HGVS to VCF"):
        vcf = hgvs_g_to_vcf(hgvs_g)
        vcf_results.append(vcf)
    
    # Debug: Check how many VCF conversions succeeded
    vcf_success = sum(1 for vcf in vcf_results if vcf is not None)
    print(f"\nVCF conversion success: {vcf_success}/{len(vcf_results)}")
    if vcf_success < len(vcf_results):
        print("Sample failed conversions:")
        for i, (hgvs_g, vcf) in enumerate(zip(df_filtered['hgvs_genomic_38'], vcf_results)):
            if vcf is None:
                print(f"  {i}: {hgvs_g} -> None")
                if i >= 2:  # Show max 3 examples
                    break
    
    # Parse VCF dictionary into separate columns in a single pass (more efficient)
    vcf_df = pd.DataFrame([
        {
            'chromosome': vcf.get('chrom') if vcf else None,
            'position': vcf.get('pos') if vcf else None,
            'ref_allele': vcf.get('ref') if vcf else None,
            'alt_allele': vcf.get('alt') if vcf else None
        }
        for vcf in vcf_results
    ], index=df_filtered.index)
    
    # Convert integer columns to nullable integer type (Int64) to preserve integer format
    # This prevents pandas from converting to float when None values are present
    vcf_df['chromosome'] = vcf_df['chromosome'].astype('Int64')
    vcf_df['position'] = vcf_df['position'].astype('Int64')
    
    # Assign all columns at once
    df_filtered[['chromosome', 'position', 'ref_allele', 'alt_allele']] = vcf_df
    
    # Reorder columns to match clinvar_process.py structure
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
    
    output_file_path = f"../data_local/processed/lovd/{gene_symbol}_variants.csv"
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    df_output.to_csv(output_file_path, index=False, encoding='utf-8')
    print(f"\nSaved to: {output_file_path}")
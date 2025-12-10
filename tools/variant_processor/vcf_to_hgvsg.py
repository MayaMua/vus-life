import hgvs.dataproviders.uta
import hgvs.parser
from hgvs.extras.babelfish import Babelfish
from hgvs.assemblymapper import AssemblyMapper
import pandas as pd
import os
from tqdm import tqdm
import socket

# Set socket timeout to 30 seconds
socket.setdefaulttimeout(30)

# Initialize data provider (connect to UTA database)
# The connection automatically caches data locally
hdp = hgvs.dataproviders.uta.connect()

# 1. Initialize Babelfish (for VCF <-> genomic HGVS conversion, specify GRCh38 assembly)
babelfish38 = Babelfish(hdp, assembly_name="GRCh38")

# Cache for conversion results to avoid redundant lookups
conversion_cache = {}

# Function to convert VCF to HGVS genomic format
def vcf_to_hgvs_genomic(chrom, position, ref, alt):
    """
    Convert VCF format variant to HGVS genomic format with caching.
    
    Parameters:
    - chrom: Chromosome (without "chr" prefix)
    - position: VCF position (1-based)
    - ref: Reference allele
    - alt: Alternate allele
    
    Returns:
    - HGVS genomic format string
    """
    # Create cache key
    cache_key = f"{chrom}:{position}:{ref}:{alt}"
    
    # Check cache first
    if cache_key in conversion_cache:
        return conversion_cache[cache_key]
    
    try:
        var_g = babelfish38.vcf_to_g_hgvs(chrom, position, ref, alt)
        result = str(var_g)
        # Store in cache
        conversion_cache[cache_key] = result
        return result
    except socket.timeout:
        print(f"Timeout converting {chrom}:{position} {ref}>{alt}: Network timeout")
        return "TIMEOUT_ERROR"
    except Exception as e:
        error_msg = str(e)[:100]  # Truncate long error messages
        print(f"Error converting {chrom}:{position} {ref}>{alt}: {error_msg}")
        return f"ERROR: {error_msg}"

# Process all CSV files in the directory
input_dir = "data/output/NORMAL_TUMOR"
files_to_process = [
    "ATM_multiple_files.csv",
    "BRCA1_multiple_files.csv",
    "BRCA2_multiple_files.csv",
    "PALB2_multiple_files.csv"
]

for file_name in files_to_process:
    file_path = os.path.join(input_dir, file_name)
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
    
    print(f"\n{'='*60}")
    print(f"Processing: {file_name}")
    print(f"{'='*60}")
    
    # Load the CSV file
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} variants")
    
    # Convert each variant to HGVS genomic format with progress bar
    hgvs_results = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"Converting {file_name}"):
        result = vcf_to_hgvs_genomic(
            str(row['chromosome']),
            int(row['position']),
            row['ref_allele'],
            row['alt_allele']
        )
        hgvs_results.append(result)
    
    df['hgvs_genomic_38'] = hgvs_results
    
    # Save the modified CSV file
    df.to_csv(file_path, index=False)
    print(f"\nSaved: {file_path}")
    print(f"Cache statistics: {len(conversion_cache)} unique variants cached")
    print(f"Sample results:\n{df[['chromosome', 'position', 'ref_allele', 'alt_allele', 'hgvs_genomic_38']].head()}")

print(f"\n{'='*60}")
print("All files processed successfully!")
print(f"{'='*60}")
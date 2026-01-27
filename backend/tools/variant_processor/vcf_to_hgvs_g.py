import hgvs.dataproviders.uta
import hgvs.parser
from hgvs.extras.babelfish import Babelfish
from hgvs.assemblymapper import AssemblyMapper
import pandas as pd
import os
from tqdm import tqdm
import socket
import sys
from pathlib import Path

# Add backend/utils to path for importing the cache decorator
backend_path = Path(__file__).resolve().parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from utils.disk_cache_decorator import disk_cache_skip_none

# Set socket timeout to 30 seconds
socket.setdefaulttimeout(30)

# Initialize data provider (connect to UTA database)
# The connection automatically caches data locally
hdp = hgvs.dataproviders.uta.connect()

# 1. Initialize Babelfish (for VCF <-> genomic HGVS conversion, specify GRCh38 assembly)
babelfish38 = Babelfish(hdp, assembly_name="GRCh38")

# Function to convert VCF to HGVS genomic format with disk caching
@disk_cache_skip_none("data_local/.cache/vcf_to_hgvs_g")
def vcf_to_hgvs_genomic(chrom, position, ref, alt):
    """
    Convert VCF format variant to HGVS genomic format with persistent disk caching.
    
    Parameters:
    - chrom: Chromosome (without "chr" prefix)
    - position: VCF position (1-based)
    - ref: Reference allele
    - alt: Alternate allele
    
    Returns:
    - HGVS genomic format string or error message
    - Returns None for timeout errors (will retry on next call)
    """
    try:
        var_g = babelfish38.vcf_to_g_hgvs(chrom, position, ref, alt)
        result = str(var_g)
        return result
    except socket.timeout:
        print(f"Timeout converting {chrom}:{position} {ref}>{alt}: Network timeout")
        return None  # Don't cache timeouts - retry next time
    except Exception as e:
        error_msg = str(e)[:100]  # Truncate long error messages
        print(f"Error converting {chrom}:{position} {ref}>{alt}: {error_msg}")
        return f"ERROR: {error_msg}"  # Cache other errors


import hgvs.parser
from bioutils.seqfetcher import fetch_seq
import pandas as pd
import hgvs.dataproviders.uta
from hgvs.extras.babelfish import Babelfish
import socket
from functools import lru_cache
from diskcache import Cache
from pathlib import Path

# Initialize the HGVS parser (no database connection required for parsing)
parser = hgvs.parser.Parser()

# Set socket timeout to 30 seconds
socket.setdefaulttimeout(30)

# Initialize simple disk cache
cache_dir = Path.home() / ".cache" / "hgvs_vcf"
disk_cache = Cache(str(cache_dir))

# Initialize data provider (connect to UTA database)
hdp = hgvs.dataproviders.uta.connect()

# Initialize Babelfish (for VCF <-> genomic HGVS conversion, specify GRCh38 assembly)
babelfish38 = Babelfish(hdp, assembly_name="GRCh38")

# Cache sequence fetching to avoid repeated network calls
@lru_cache(maxsize=10000)
def get_reference_base_cached(ac, pos):
    """Cached wrapper for reference base fetching."""
    return fetch_seq(ac, start_i=pos - 1, end_i=pos)


def get_reference_base(ac, pos):
    """
    Retrieve the reference base at the given position (1-based index) from the reference sequence.

    Args:
        ac (str): Accession (e.g., 'NC_000001.11')
        pos (int): 1-based position

    Returns:
        str: Reference base as a string
    """
    return get_reference_base_cached(ac, pos)

def build_anchored_variant(ac, start, end, alt_seq):
    """
    Build VCF representation for variants requiring an anchor base.
    Used for deletions, delins, and inversions.

    Args:
        ac (str): Accession (e.g., 'NC_000001.11')
        start (int): Start position (1-based)
        end (int): End position (1-based)
        alt_seq (str): Alternative sequence (empty for pure deletions)

    Returns:
        tuple: (pos_vcf, ref, alt)
    """
    pos_vcf = start - 1
    anchor_base = get_reference_base(ac, pos_vcf)
    original_seq = fetch_seq(ac, start_i=start-1, end_i=end)
    ref = anchor_base + original_seq
    alt = anchor_base + alt_seq
    return pos_vcf, ref, alt

def reverse_complement(seq):
    """
    Compute the reverse complement of a DNA sequence.

    Args:
        seq (str): DNA sequence

    Returns:
        str: Reverse complement of the DNA sequence
    """
    complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 
                  'N': 'N', 'a': 't', 't': 'a', 'g': 'c', 'c': 'g',
                  'n': 'n'}
    return ''.join(complement.get(base, base) for base in reversed(seq))

@disk_cache.memoize()
def hgvs_g_to_vcf(hgvs_g_str):
    """
    Convert an HGVS g. variant string to its equivalent VCF representation.
    Results are cached to disk for fast retrieval on subsequent runs.

    Args:
        hgvs_g_str (str): Genomic-level HGVS string (e.g., 'NC_000001.11:g.23603625_23603626del')

    Returns:
        dict or None: Dictionary with VCF-style keys (chrom, pos, ref, alt) or None on error
    """
    if not hgvs_g_str or pd.isna(hgvs_g_str):
        return None
    
    try:
        var_g = parser.parse_hgvs_variant(hgvs_g_str)
        ac = var_g.ac
        pos_hgvs = var_g.posedit.pos
        edit = var_g.posedit.edit
        
        # Extract chromosome ID from accession (e.g., 'NC_000001.11' -> '1')
        chrom = ac.split('.')[0].split('_')[-1].lstrip('0') or '0'
        
        # --- Case A: Duplication ---
        # Treat the duplicated sequence as if it's inserted at the end of the duplicated region.
        if edit.type == 'dup':
            # 1. Define the range of duplication
            start = pos_hgvs.start.base
            end = pos_hgvs.end.base
            
            # 2. Fetch the sequence being duplicated from the reference genome
            duplicated_seq = fetch_seq(ac, start_i=start-1, end_i=end)
            
            # 3. VCF representation: anchor on the last duplicated base (right-aligned)
            pos_vcf = end
            ref = get_reference_base(ac, pos_vcf)
            alt = ref + duplicated_seq

        # --- Case B: Insertion ---
        elif edit.type == 'ins':
            pos_vcf = pos_hgvs.start.base
            ref = get_reference_base(ac, pos_vcf)
            alt = ref + edit.alt

        # --- Case C: Deletion ---
        elif edit.type == 'del':
            # VCF deletions require an anchor base before the deletion
            start = pos_hgvs.start.base
            end = pos_hgvs.end.base
            pos_vcf, ref, alt = build_anchored_variant(ac, start, end, "")

        # --- Case D: Substitution ---
        elif edit.type == 'sub':
            pos_vcf = pos_hgvs.start.base
            # VCF stores reference and alternate alleles directly from HGVS edit
            ref = edit.ref
            alt = edit.alt

        # --- Case E: DelIns (deletion-insertion) ---
        elif edit.type == 'delins':
            # VCF: represented as a deletion followed by an insertion at the same position
            start = pos_hgvs.start.base
            end = pos_hgvs.end.base
            inserted_seq = edit.alt if edit.alt else ""
            pos_vcf, ref, alt = build_anchored_variant(ac, start, end, inserted_seq)

        # --- Case F: Inversion ---
        elif edit.type == 'inv':
            # VCF: represent an inversion as a deletion followed by an insertion of the reverse complement
            start = pos_hgvs.start.base
            end = pos_hgvs.end.base
            original_seq = fetch_seq(ac, start_i=start-1, end_i=end)
            inverted_seq = reverse_complement(original_seq)
            pos_vcf, ref, alt = build_anchored_variant(ac, start, end, inverted_seq)

        else:
            print(f"Unsupported type: {edit.type}")
            return None

        return {
            "chrom": int(chrom),
            "pos": int(pos_vcf),
            "ref": ref,
            "alt": alt
        }

    except Exception as e:
        print(f"Error converting {hgvs_g_str}: {e}")
        return None

if __name__ == "__main__":
    # Example test cases for various HGVS g. representations
    hgvs_list = [
        "NC_000015.10:g.48487139dup",                  # Example: Duplication case
        "NC_000016.10:g.23607966_23607967insA",        # Example: Insertion case
        "NC_000015.10:g.48644723del",                  # Deletion
        "NC_000015.10:g.48644723delinsA",              # DelIns (del+ins)
        "NC_000017.11:g.43094464_43094465inv",         # Inversion
        # "NC_000017.11:g.43093295_43093296inv",         # Inversion
        # "NC_000013.11:g.32355073_32355074inv"          # Inversion
        "NC_000001.11:g.23603625_23603626del",           # Deletion
        "NC_000001.11:g.216217352C>T",                   # Substitution
    ]
    for g in hgvs_list:
        vcf_data = hgvs_g_to_vcf(g)
        if vcf_data:
            print(vcf_data)
        else:
            print(f"Error converting {g}")
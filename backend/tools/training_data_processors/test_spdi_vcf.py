#!/usr/bin/env python3
"""
Test script for SPDI to VCF conversion with anchor base fetching.
"""
import re
from typing import Optional

def parse_spdi_to_vcf_with_anchor(spdi_notation: str) -> Optional[dict]:
    """
    Converts SPDI notation to VCF format using SPDI's sequence information.
    Simulates anchor base fetching (without actual network calls for testing).
    """
    if not isinstance(spdi_notation, str) or not spdi_notation.strip():
        return None
        
    match = re.match(r"^(NC_\d+\.\d+):(\d+):([ACGT]*):([ACGT]*)$", spdi_notation)
    
    if not match:
        return None
    
    sequence, pos_0based_str, deletion, insertion = match.groups()
    pos_0based = int(pos_0based_str)
    
    chrom_match = re.match(r"NC_0*(\d+)\.\d+", sequence)
    if chrom_match:
        chromosome = int(chrom_match.group(1))
    else:
        return None
    
    # For testing, simulate anchor base as 'N' (would be fetched from NCBI in real code)
    anchor = "N"
    
    if deletion and insertion:
        # Substitution or complex variant (delins)
        if len(deletion) == 1 and len(insertion) == 1:
            # Simple SNP: no anchor needed
            vcf_pos = pos_0based + 1
            ref = deletion
            alt = insertion
        else:
            # Complex delins: needs anchor base
            vcf_pos = pos_0based
            ref = anchor + deletion
            alt = anchor + insertion
            
    elif deletion and not insertion:
        # Pure deletion: VCF needs anchor base before deletion
        vcf_pos = pos_0based
        ref = anchor + deletion
        alt = anchor
        
    elif not deletion and insertion:
        # Pure insertion: VCF needs anchor base
        vcf_pos = pos_0based
        ref = anchor
        alt = anchor + insertion
        
    else:
        # No change (shouldn't happen)
        return None
    
    return {
        'chrom': chromosome,
        'pos': vcf_pos,
        'ref': ref,
        'alt': alt
    }


def main():
    """Test the SPDI to VCF conversion."""
    print("Testing SPDI to VCF conversion with anchor bases\n")
    
    test_cases = [
        # (SPDI, Description)
        ("NC_000011.10:108222767:C:T", "Simple SNP (substitution)"),
        ("NC_000011.10:108227637:TTAATGAT:", "Multi-base deletion"),
        ("NC_000011.10:108227631:T:", "Single base deletion"),
        ("NC_000011.10:108227639::AAA", "Insertion"),
        ("NC_000011.10:108227637:TT:AAA", "Delins (2 bases to 3 bases)"),
    ]
    
    print("=" * 80)
    for spdi, description in test_cases:
        result = parse_spdi_to_vcf_with_anchor(spdi)
        status = "✓ SUCCESS" if result else "✗ FAILED"
        
        print(f"\n{description}:")
        print(f"  SPDI:   {spdi}")
        if result:
            print(f"  VCF:    chr={result['chrom']}, pos={result['pos']}, ref={result['ref']}, alt={result['alt']}")
        else:
            print(f"  VCF:    None")
        print(f"  Status: {status}")
    
    print("\n" + "=" * 80)
    print("\nNOTE: 'N' is used as a placeholder for anchor bases in this test.")
    print("In production, actual anchor bases would be fetched from NCBI.")


if __name__ == "__main__":
    main()

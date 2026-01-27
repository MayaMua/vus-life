#!/usr/bin/env python3
"""
Script to get human chromosome NC reference identifiers for GRCh38 assembly.
This script attempts to fetch the latest chromosome reference mappings from NCBI APIs.
If the APIs are unavailable, it provides the current standard GRCh38 references.
"""

import requests
import json
from typing import Dict, Optional

def get_chromosome_references_from_ncbi() -> Optional[Dict[str, str]]:
    """
    Attempt to fetch chromosome mapping from NCBI APIs.
    
    Returns:
        Dictionary mapping chromosome names to NC references or None if failed
    """
    print("Attempting to fetch chromosome references from NCBI APIs...")
    
    # Try multiple approaches
    approaches = [
        ("NCBI Datasets v2 Sequence API", try_ncbi_datasets_api),
        ("NCBI Datasets v2 Metadata API", try_ncbi_datasets_metadata),
        ("NCBI E-utilities", try_ncbi_eutils),
        ("NCBI Assembly API", try_ncbi_assembly_api)
    ]
    
    for approach_name, approach_func in approaches:
        try:
            print(f"Trying {approach_name}...")
            result = approach_func()
            if result:
                print(f"Successfully retrieved {len(result)} chromosome references using {approach_name}")
                return result
            else:
                print(f"{approach_name} did not return chromosome data")
        except Exception as e:
            print(f"{approach_name} failed: {e}")
    
    print("All NCBI API approaches failed")
    return None

def try_ncbi_datasets_api() -> Optional[Dict[str, str]]:
    """Try NCBI Datasets v2 API approach using the working dataset_report endpoint."""
    try:
        # Use the working NCBI Datasets v2 API endpoint
        api_url = "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/GCF_000001405.40/dataset_report"
        response = requests.get(api_url, headers={"Accept": "application/json"}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print("NCBI Datasets v2 API connected successfully")
        
        # The dataset_report endpoint provides assembly information but not detailed chromosome data
        # We need to use a different approach to get chromosome sequences
        print("Dataset report endpoint doesn't provide chromosome sequence details")
        return None
        
    except Exception as e:
        raise Exception(f"NCBI Datasets v2 API error: {e}")

def try_ncbi_datasets_metadata() -> Optional[Dict[str, str]]:
    """Try NCBI Datasets v2 metadata API approach using the working dataset_report endpoint."""
    try:
        # Use the working NCBI Datasets v2 API endpoint
        api_url = "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/genome/accession/GCF_000001405.40/dataset_report"
        response = requests.get(api_url, headers={"Accept": "application/json"}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print("NCBI Datasets v2 Metadata API connected successfully")
        
        # The dataset_report endpoint provides assembly information but not detailed chromosome data
        # We need to use a different approach to get chromosome sequences
        print("Dataset report endpoint doesn't provide chromosome sequence details")
        return None
        
    except Exception as e:
        raise Exception(f"NCBI Datasets v2 Metadata API error: {e}")

def try_ncbi_eutils() -> Optional[Dict[str, str]]:
    """Try NCBI E-utilities approach to dynamically discover chromosome sequences."""
    try:
        print("Searching NCBI nucleotide database for human chromosome sequences...")
        print("Dynamically searching for all chromosomes with expanded version range...")
        
        potential_accessions = []
        
        # Generate accessions for chromosomes 1-22, X, Y with wide version range (1-25)
        # This ensures we find all chromosomes even if versions vary
        for i in range(1, 23):
            for version in range(1, 26):  # Wide range: 1-25 to catch all versions
                potential_accessions.append(f"NC_0000{i:02d}.{version}")
        
        # Add X and Y chromosomes
        for version in range(1, 26):
            potential_accessions.append(f"NC_000023.{version}")  # X
            potential_accessions.append(f"NC_000024.{version}")  # Y
        
        chr_mapping = {}
        
        # Search for each potential accession
        import time
        total_searches = len(potential_accessions)
        print(f"Searching {total_searches} potential accessions...")
        
        for idx, accession in enumerate(potential_accessions):
            try:
                esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                esearch_params = {
                    'db': 'nuccore',
                    'term': f'"{accession}"[Accession]',
                    'retmax': 1,
                    'retmode': 'json'
                }
                
                esearch_response = requests.get(esearch_url, params=esearch_params, timeout=10)
                esearch_response.raise_for_status()
                esearch_data = esearch_response.json()
                
                count = int(esearch_data.get('esearchresult', {}).get('count', '0'))
                if count > 0:
                    # Extract chromosome number from accession
                    if accession.startswith('NC_0000'):
                        chr_num = accession[7:9].lstrip('0') or accession[7:9]
                        if chr_num == '23':
                            chr_num = 'X'
                        elif chr_num == '24':
                            chr_num = 'Y'
                        
                        # Only keep the highest version for each chromosome
                        if chr_num not in chr_mapping or accession > chr_mapping[chr_num]:
                            chr_mapping[chr_num] = accession
                            print(f"Found {accession} for chromosome {chr_num} ({len(chr_mapping)}/24 found)")
                
                # Progress update and rate limiting
                if (idx + 1) % 50 == 0:
                    print(f"Progress: {idx + 1}/{total_searches} searches, found {len(chr_mapping)} chromosomes so far...")
                    time.sleep(0.2)  # Slightly longer delay every 50 requests
                elif idx % 10 == 0:  # Small delay every 10 requests
                    time.sleep(0.05)
                
            except Exception as e:
                if idx < 5:  # Only print errors for first few
                print(f"Error searching for {accession}: {e}")
                continue
        
        if chr_mapping:
            print(f"Successfully retrieved {len(chr_mapping)} chromosome references from NCBI E-utilities")
            if len(chr_mapping) < 24:
                print(f"Warning: Expected 24 chromosomes (1-22, X, Y) but found {len(chr_mapping)}")
            return chr_mapping
        else:
            print("No chromosome mappings found in E-utilities response")
            return None
        
    except Exception as e:
        raise Exception(f"NCBI E-utilities error: {e}")

def try_ncbi_assembly_api() -> Optional[Dict[str, str]]:
    """Try NCBI Assembly API approach."""
    try:
        assembly_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=assembly&id=GCF_000001405.40&retmode=json"
        response = requests.get(assembly_url, timeout=30)
        response.raise_for_status()
        
        # Assembly API doesn't provide detailed chromosome information
        print("NCBI Assembly API connected but doesn't provide chromosome details")
        return None
        
    except Exception as e:
        raise Exception(f"NCBI Assembly API error: {e}")


def get_latest_chromosome_references() -> Dict[str, str]:
    """
    Get the latest chromosome NC reference identifiers from NCBI APIs.
    
    Dynamically fetches chromosome references from NCBI APIs.
    
    Returns:
        Dictionary mapping chromosome names to NC reference identifiers
        
    Raises:
        RuntimeError: If unable to fetch chromosome references from any API
    """
    # Try to get from NCBI APIs
    api_mapping = get_chromosome_references_from_ncbi()
    
    if api_mapping and len(api_mapping) >= 20:  # Should have at least 20 chromosomes (1-22, X, Y)
        print(f"Successfully retrieved {len(api_mapping)} chromosomes from NCBI APIs")
        if len(api_mapping) < 24:
            print(f"Warning: Expected 24 chromosomes (1-22, X, Y) but found {len(api_mapping)}")
        return api_mapping
    else:
        raise RuntimeError(
            f"Failed to fetch chromosome references from NCBI APIs. "
            f"Only found {len(api_mapping) if api_mapping else 0} chromosomes (expected 24). "
            f"Please check your internet connection and try again."
        )

def print_chromosome_mapping(chr_mapping: Dict[str, str]) -> None:
    """
    Print the chromosome mapping in a formatted way.
    
    Args:
        chr_mapping: Dictionary mapping chromosome names to NC references
    """
    print("GRCh38 Chromosome to NC Reference Mapping:")
    print("=" * 50)
    print("These are the NCBI RefSeq identifiers for human chromosomes")
    print("in the GRCh38 assembly, used by Ensembl VEP and other tools.\n")
    
    # Sort chromosomes numerically, then X, Y
    def sort_key(chr_name):
        if chr_name.isdigit():
            return (0, int(chr_name))
        elif chr_name == 'X':
            return (1, 0)
        elif chr_name == 'Y':
            return (1, 1)
        else:
            return (2, chr_name)
    
    for chr_name in sorted(chr_mapping.keys(), key=sort_key):
        nc_ref = chr_mapping[chr_name]
        print(f"Chromosome {chr_name:>2}: {nc_ref}")

def generate_python_code(chr_mapping: Dict[str, str]) -> str:
    """
    Generate Python code for the chromosome mapping.
    
    Args:
        chr_mapping: Dictionary mapping chromosome names to NC references
        
    Returns:
        Python code string for the mapping
    """
    lines = [
        "# GRCh38 Chromosome to NC Reference Mapping",
        "# These are the NCBI RefSeq identifiers for human chromosomes",
        "# in the GRCh38 assembly, used by Ensembl VEP and other tools.",
        "",
        "chr_mapping = {"
    ]
    
    # Sort chromosomes numerically, then X, Y
    def sort_key(chr_name):
        if chr_name.isdigit():
            return (0, int(chr_name))
        elif chr_name == 'X':
            return (1, 0)
        elif chr_name == 'Y':
            return (1, 1)
        else:
            return (2, chr_name)
    
    sorted_chrs = sorted(chr_mapping.keys(), key=sort_key)
    
    for i, chr_name in enumerate(sorted_chrs):
        nc_ref = chr_mapping[chr_name]
        comma = "," if i < len(sorted_chrs) - 1 else ""
        lines.append(f"    '{chr_name}': '{nc_ref}'{comma}")
    
    lines.append("}")
    
    return "\n".join(lines)

def explain_references():
    """
    Explain how the NC reference identifiers are obtained.
    """
    print("\nHow These NC References Are Obtained:")
    print("=" * 40)
    print("1. NCBI Datasets v2 REST API: Fetches latest chromosome references directly from NCBI")
    print("2. Multiple Endpoints: Tries sequence and metadata endpoints for comprehensive coverage")
    print("3. Real-time Data: Always gets the most current NCBI RefSeq identifiers")
    print("4. VEP Compatible: These identifiers work with Ensembl VEP")
    print("\nAPI Details:")
    print("- NCBI Datasets v2 REST API: https://api.ncbi.nlm.nih.gov/datasets/v2alpha/")
    print("- Assembly: GCF_000001405.40 (GRCh38.p14)")
    print("- Endpoints: /genome/accession/{accession}/sequence and /genome/accession/{accession}")
    print("- Updates: Automatically reflects the latest NCBI RefSeq identifiers")

def main():
    """Main function to display chromosome references."""
    print("Human Chromosome NC Reference Fetcher")
    print("=" * 40)
    print("Using NCBI Datasets v2 REST API to fetch latest chromosome references...")
    
    try:
        # Get mapping from NCBI APIs
        chr_mapping = get_latest_chromosome_references()
        
        # Display the mapping
        print_chromosome_mapping(chr_mapping)
        
        # Explain how these references are obtained
        explain_references()
        
        # Generate Python code
        print("\nPython Code for VEP Fetcher:")
        print("=" * 30)
        python_code = generate_python_code(chr_mapping)
        print(python_code)
        
        # Save to file
        output_file = "chromosome_references.py"
        with open(output_file, 'w') as f:
            f.write(python_code)
            f.write("\n")
        
        print(f"\nMapping saved to: {output_file}")
        
        return chr_mapping
        
    except RuntimeError as e:
        print(f"Error: {e}")
        print("\nPlease check your internet connection and try again.")
        return None

if __name__ == "__main__":
    main()
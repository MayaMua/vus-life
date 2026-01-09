#!/usr/bin/env python3
"""
Script to get transcript accession (NM_) and genomic accession (NC_) for a gene symbol.

Uses NCBI E-utilities to dynamically fetch gene information and find the canonical
RefSeq transcript and corresponding genomic chromosome reference.
"""

import requests
import time
from typing import Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def get_chromosome_nc_accession(chromosome: str) -> Optional[str]:
    """
    Get NC genomic accession for a chromosome number.
    
    Args:
        chromosome: Chromosome number as string (e.g., "15", "X", "Y")
        
    Returns:
        NC accession (e.g., "NC_000015.10") or None if not found
    """
    # Map chromosome to NC accession pattern
    if chromosome == 'X':
        chr_num = '23'
    elif chromosome == 'Y':
        chr_num = '24'
    elif chromosome == 'M' or chromosome == 'MT':
        return 'NC_012920.1'  # Mitochondrial
    else:
        chr_num = str(int(chromosome)).zfill(2)  # Pad to 2 digits
    
    # Search for the latest version of the chromosome accession
    base_accession = f"NC_0000{chr_num}"
    
    # Try versions from high to low (most recent first)
    for version in range(25, 0, -1):
        accession = f"{base_accession}.{version}"
        try:
            esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            esearch_params = {
                'db': 'nuccore',
                'term': f'"{accession}"[Accession]',
                'retmax': 1,
                'retmode': 'json'
            }
            
            response = requests.get(esearch_url, params=esearch_params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            count = int(data.get('esearchresult', {}).get('count', '0'))
            if count > 0:
                return accession
            
            time.sleep(0.1)  # Rate limiting
            
        except Exception:
            continue
    
    return None


def get_gene_transcript_info(gene_symbol: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Get transcript accession (NM_) and genomic accession (NC_) for a gene symbol.
    
    Args:
        gene_symbol: Gene symbol (e.g., "FBN1", "BRCA1")
        
    Returns:
        Tuple of (transcript_accession, genomic_accession) or (None, None) if not found
        Example: ('NM_000138.5', 'NC_000015.10')
    """
    try:
        # Step 1: Search for the gene in NCBI Gene database
        print(f"Searching for gene: {gene_symbol}...")
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        esearch_params = {
            'db': 'gene',
            'term': f'"{gene_symbol}"[Gene Name] AND "Homo sapiens"[Organism]',
            'retmax': 5,
            'retmode': 'json'
        }
        
        response = requests.get(esearch_url, params=esearch_params, timeout=30)
        response.raise_for_status()
        esearch_data = response.json()
        
        gene_ids = esearch_data.get('esearchresult', {}).get('idlist', [])
        if not gene_ids:
            print(f"Gene {gene_symbol} not found in NCBI Gene database")
            return None, None
        
        gene_id = gene_ids[0]  # Use first result
        print(f"Found gene ID: {gene_id}")
        
        time.sleep(0.3)  # Rate limiting
        
        # Step 2: Get gene summary to find chromosome location
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        esummary_params = {
            'db': 'gene',
            'id': gene_id,
            'retmode': 'json'
        }
        
        response = requests.get(esummary_url, params=esummary_params, timeout=30)
        response.raise_for_status()
        esummary_data = response.json()
        
        gene_info = esummary_data.get('result', {}).get(gene_id, {})
        chromosome = gene_info.get('chromosome', '')
        
        if not chromosome:
            print(f"Could not determine chromosome for {gene_symbol}")
            return None, None
        
        print(f"Gene {gene_symbol} is on chromosome {chromosome}")
        
        # Step 3: Get genomic accession (NC_) for the chromosome
        genomic_accession = get_chromosome_nc_accession(chromosome)
        if not genomic_accession:
            print(f"Could not find NC accession for chromosome {chromosome}")
            return None, None
        
        print(f"Genomic accession: {genomic_accession}")
        
        time.sleep(0.3)  # Rate limiting
        
        # Step 4: Search for RefSeq transcripts (NM_) for this gene
        # Search in nucleotide database for transcripts
        esearch_params = {
            'db': 'nuccore',
            'term': f'"{gene_symbol}"[Gene Name] AND "Homo sapiens"[Organism] AND "NM_"[Accession]',
            'retmax': 20,
            'retmode': 'json'
        }
        
        response = requests.get(esearch_url, params=esearch_params, timeout=30)
        response.raise_for_status()
        esearch_data = response.json()
        
        transcript_ids = esearch_data.get('esearchresult', {}).get('idlist', [])
        if not transcript_ids:
            print(f"No RefSeq transcripts found for {gene_symbol}")
            return None, genomic_accession  # Return genomic accession even if transcript not found
        
        print(f"Found {len(transcript_ids)} potential transcripts, fetching details...")
        
        time.sleep(0.3)  # Rate limiting
        
        # Step 5: Get transcript summaries to find the best one
        esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        esummary_params = {
            'db': 'nuccore',
            'id': ','.join(transcript_ids[:15]),  # Limit to first 15
            'retmode': 'json'
        }
        
        response = requests.get(esummary_url, params=esummary_params, timeout=30)
        response.raise_for_status()
        esummary_data = response.json()
        
        transcripts = []
        for tid in transcript_ids[:15]:
            if tid in esummary_data.get('result', {}):
                transcript_info = esummary_data['result'][tid]
                accession = transcript_info.get('accessionversion', '')
                
                if accession and accession.startswith('NM_'):
                    # Get length if available
                    length = transcript_info.get('slen', 0)
                    title = transcript_info.get('title', '').lower()
                    
                    # Check if it's marked as canonical or primary
                    is_canonical = 'canonical' in title or 'primary' in title
                    
                    transcripts.append({
                        'accession': accession,
                        'length': length,
                        'is_canonical': is_canonical
                    })
        
        if not transcripts:
            print(f"Could not parse transcript information")
            return None, genomic_accession
        
        # Select best transcript: canonical first, then longest
        transcripts.sort(key=lambda x: (not x['is_canonical'], -x['length']))
        transcript_accession = transcripts[0]['accession']
        
        print(f"Selected transcript: {transcript_accession}")
        if transcripts[0]['length'] > 0:
            print(f"  Length: {transcripts[0]['length']} bp")
        if transcripts[0]['is_canonical']:
            print(f"  Marked as canonical/primary")
        
        return transcript_accession, genomic_accession
        
    except Exception as e:
        print(f"Error fetching gene information: {e}")
        return None, None


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python get_gene_transcript_info.py <gene_symbol>")
        print("Example: python get_gene_transcript_info.py FBN1")
        sys.exit(1)
    
    gene_symbol = sys.argv[1].upper()
    
    print(f"Fetching transcript and genomic accessions for {gene_symbol}...")
    print("=" * 60)
    
    transcript_accession, genomic_accession = get_gene_transcript_info(gene_symbol)
    
    print("=" * 60)
    if transcript_accession and genomic_accession:
        print(f"✓ Success!")
        print(f"  Gene: {gene_symbol}")
        print(f"  Transcript Accession: {transcript_accession}")
        print(f"  Genomic Accession: {genomic_accession}")
        return transcript_accession, genomic_accession
    else:
        print(f"✗ Failed to retrieve information for {gene_symbol}")
        if transcript_accession:
            print(f"  Transcript Accession: {transcript_accession}")
        if genomic_accession:
            print(f"  Genomic Accession: {genomic_accession}")
        return None, None


if __name__ == "__main__":
    main()


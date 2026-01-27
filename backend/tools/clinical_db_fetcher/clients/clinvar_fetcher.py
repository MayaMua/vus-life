"""ClinVar API client functions for fetching variant data."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Union, Optional
from functools import lru_cache
from dotenv import load_dotenv

from tools.clinical_db_fetcher.utils.http import RateLimiter, make_api_request

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# ClinVar API settings
API_KEY = os.getenv("NCBI_API_KEY")
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Rate limiter for ClinVar API (3 requests per second)
clinvar_limiter = RateLimiter(calls_per_second=3.0)

@lru_cache(maxsize=512)
def search_clinvar_by_hgvs_g(hgvs_g: str) -> List[str]:
    """
    Search ClinVar by genomic HGVS notation (e.g., "NC_000013.11:g.32332343A>G") and return IDs.

    Args:
        hgvs_g: Genomic HGVS notation string

    Returns:
        List of ClinVar variant IDs
    """
    if not hgvs_g:
        return []

    search_url = f"{BASE_URL}/esearch.fcgi"
    params = {
        "db": "clinvar",
        "term": f'"{hgvs_g}"',
        "retmode": "xml",
        "api_key": API_KEY,
        "retmax": 10,
    }

    response = make_api_request(search_url, params, clinvar_limiter)
    if not response:
        return []

    root = ET.fromstring(response.text)
    id_elements = root.findall(".//Id")
    return [id_elem.text for id_elem in id_elements] if id_elements else []

@lru_cache(maxsize=128)
def search_clinvar_variants(gene: str, transcript: str, variant: str = None) -> List[str]:
    """
    Search ClinVar for a gene or a specific variant and return matching variant IDs.
    Tries multiple search strategies to maximize chances of finding the variant.
    Uses caching to avoid redundant requests.
    
    Args:
        gene: Gene symbol
        transcript: Transcript ID
        variant: Variant notation (e.g., "c.5470A>G")
    
    Returns:
        List of ClinVar variant IDs
    """
    search_url = f"{BASE_URL}/esearch.fcgi"
    id_list = []
    
    # Make sure variant has appropriate prefix if needed
    if variant and not (variant.startswith("c.") or variant.startswith("p.") or variant.startswith("g.")):
        variant = f"c.{variant}"
    
    # Try several search strategies
    search_strategies = []
    
    # Start with AND pattern for gene and variant
    if transcript and variant:
        search_strategies.append(f'"{transcript}" AND "{variant}"')
    if gene and variant:
        search_strategies.append(f'"{gene}" AND "{variant}"')

    
    # Try each search strategy
    for search_term in search_strategies:
        logger.info(f"Searching ClinVar with term: {search_term}")
        
        params = {
            "db": "clinvar",
            "term": search_term,
            "retmode": "xml",
            "api_key": API_KEY,
            "retmax": 10,
        }
        
        response = make_api_request(search_url, params, clinvar_limiter)
        if not response:
            continue
            
        root = ET.fromstring(response.text)
        # Extract IDs from the response
        id_elements = root.findall(".//Id")
        current_ids = [id_elem.text for id_elem in id_elements]
        
        if current_ids:
            logger.info(f"Found {len(current_ids)} results with search term: {search_term}: {current_ids}")
            id_list.extend(current_ids)
            break  # Stop once we find results
        else:
            logger.info(f"No results found for {search_term}")
    
    # Return unique IDs
    return list(set(id_list)) if id_list else []

@lru_cache(maxsize=128)
def fetch_clinvar_details_by_id(ids: Union[List[str], str]) -> Optional[Dict]:
    """
    Fetch details for ClinVar variants by their IDs
    
    Args:
        ids: ClinVar variant ID or list of IDs
    
    Returns:
        Dictionary of variant details or None if failed
    """
    if isinstance(ids, list):
        id_param = ",".join(ids)
    else:
        id_param = ids
        
    fetch_url = f"{BASE_URL}/esummary.fcgi"
    params = {
        "db": "clinvar",
        "id": id_param,
        "retmode": "json",
        "api_key": API_KEY,
    }
    
    response = make_api_request(fetch_url, params, clinvar_limiter)
    if not response:
        logger.error(f"Failed to fetch details for IDs: {ids}")
        return None
        
    details = response.json()
    return details.get("result", {}) 
#!/usr/bin/env python3
"""
Common utility functions shared across display modules.

This module provides shared functionality to avoid code duplication:
- Loading training metadata from cache
- Loading pathogenicity mappings
"""

import streamlit as st
import json
from pathlib import Path
from typing import Optional, Dict


def load_training_metadata_from_cache(
    gene_symbol: str,
    config: Dict,
    get_user_training_metadata_dir_func
) -> Optional[Dict]:
    """
    Load training metadata from cached JSON file.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'FBN1')
        config: Configuration dictionary
        get_user_training_metadata_dir_func: Function to get metadata directory
        
    Returns:
        Training metadata dictionary or None if not found/error
    """
    try:
        metadata_dir = get_user_training_metadata_dir_func(config, gene_symbol)
        metadata_file = metadata_dir / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Could not load training metadata: {e}")
    
    return None


def load_pathogenicity_mapping(
    gene_symbol: str,
    config: Dict,
    get_user_training_metadata_dir_func
) -> Dict[str, str]:
    """
    Load pathogenicity mapping for training variants from metadata.json.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'FBN1')
        config: Configuration dictionary
        get_user_training_metadata_dir_func: Function to get metadata directory
        
    Returns:
        Dictionary mapping variant_id to pathogenicity_original
    """
    metadata = load_training_metadata_from_cache(
        gene_symbol,
        config,
        get_user_training_metadata_dir_func
    )
    
    pathogenicity_map = {}
    
    if metadata:
        training_variants = metadata.get('variants', [])
        for variant in training_variants:
            variant_id = variant.get('variant_id')
            pathogenicity = variant.get('pathogenicity_original', 'unknown')
            if variant_id:
                pathogenicity_map[variant_id] = pathogenicity
    
    return pathogenicity_map

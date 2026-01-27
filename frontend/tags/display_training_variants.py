#!/usr/bin/env python3
"""
Module for handling training variants retrieval functionality.

This module provides a modular interface for loading and fetching training variants
metadata for genes. It can load cached metadata from disk or fetch fresh data from
the API, and integrates with Streamlit session state.

Main functions:
    - load_or_fetch_metadata: Load from cache or fetch from API
    - handle_get_training_variants_button: Handle button click event
    - render_get_training_variants_button: Render button and handle event (all-in-one)
"""

import streamlit as st
import json
from pathlib import Path
from typing import Optional, Any

# Import common utilities
from frontend.tags.common_utils import load_training_metadata_from_cache


def load_or_fetch_metadata(gene_symbol: str, 
                            config: dict, 
                            get_metadata_gene_func,
                            get_user_training_metadata_dir_func) -> Optional[dict]:
    """
    Load metadata from file if exists, otherwise fetch from API.
    
    Args:
        gene_symbol: Gene symbol
        config: Configuration dictionary
        get_metadata_gene_func: Function to fetch metadata from API
        get_user_training_metadata_dir_func: Function to get metadata directory path
        
    Returns:
        Metadata dictionary or None if error
    """
    # Try to load from cache first
    metadata = load_training_metadata_from_cache(
        gene_symbol,
        config,
        get_user_training_metadata_dir_func
    )
    
    if metadata:
        return metadata
    
    # Fetch from API if not in cache
    try:
        metadata = get_metadata_gene_func(gene_symbol)
        
        # Save to file for future use
        metadata_dir = get_user_training_metadata_dir_func(config, gene_symbol)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / "metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    except Exception as e:
        st.error(f"Error fetching metadata: {e}")
        return None


def handle_get_training_variants_button(gene_symbol: str,
                                        config: dict,
                                        get_metadata_gene_func,
                                        get_user_training_metadata_dir_func) -> None:
    """
    Handle the "Get Training Variants" button click event.
    
    This function:
    1. Validates the gene symbol
    2. Checks if gene symbol changed and clears cached results if needed
    3. Loads or fetches training variants metadata
    4. Updates session state with the results
    5. Forces a rerun to display the new tab
    
    Args:
        gene_symbol: Gene symbol to fetch training variants for
        config: Configuration dictionary
        get_metadata_gene_func: Function to fetch metadata from API
        get_user_training_metadata_dir_func: Function to get metadata directory path
    """
    if not gene_symbol:
        st.error("Please select a gene symbol")
        return
    
    # Check if gene symbol changed
    if st.session_state.current_gene_symbol != gene_symbol:
        st.session_state.metadata_results = None
    
    # Load or fetch metadata
    with st.spinner(f"Loading training variants for {gene_symbol}..."):
        metadata = load_or_fetch_metadata(
            gene_symbol=gene_symbol,
            config=config,
            get_metadata_gene_func=get_metadata_gene_func,
            get_user_training_metadata_dir_func=get_user_training_metadata_dir_func
        )
        
        if metadata:
            st.session_state.metadata_results = metadata
            st.session_state.current_gene_symbol = gene_symbol
            
            variants_count = metadata.get('variants_count', 0)
            metadata_dir = get_user_training_metadata_dir_func(config, gene_symbol)
            metadata_file = metadata_dir / "metadata.json"
            
            if metadata_file.exists():
                st.success(f"✓ Loaded {variants_count} training variants from cache")
            else:
                st.success(f"✓ Fetched and saved {variants_count} training variants")
            
            # Force rerun to show the new tab
            st.rerun()
        else:
            st.error("Failed to load or fetch metadata")


def render_get_training_variants_button(config: dict,
                                        gene_symbol: str,
                                        get_metadata_gene_func,
                                        get_user_training_metadata_dir_func,
                                        use_container_width: bool = True) -> None:
    """
    Render the "Get Training Variants" button and handle its click event.
    
    Args:
        config: Configuration dictionary
        gene_symbol: Current gene symbol
        get_metadata_gene_func: Function to fetch metadata from API
        get_user_training_metadata_dir_func: Function to get metadata directory path
        use_container_width: Whether button should use container width
    """
    get_metadata_btn = st.button(
        "Get Training Variants", 
        use_container_width=use_container_width,
        help="Load or fetch training variants metadata for the selected gene"
    )
    
    # Handle button click
    if get_metadata_btn:
        handle_get_training_variants_button(
            gene_symbol=gene_symbol,
            config=config,
            get_metadata_gene_func=get_metadata_gene_func,
            get_user_training_metadata_dir_func=get_user_training_metadata_dir_func
        )

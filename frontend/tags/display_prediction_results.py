#!/usr/bin/env python3
"""
Module for displaying prediction results in the Streamlit app.

This module provides functionality to display prediction results including:
- Overview metrics (existing vs new variants)
- Detailed variant tables with predictions
- Model-specific results and error handling

Main functions:
    - display_prediction_results: Main function to render prediction results
    - display_existing_variants: Display existing variants from database
    - display_new_variants: Display newly processed variants
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List

# Import common utilities
from frontend.tags.common_utils import load_training_metadata_from_cache


def display_existing_variants(
    existing_variants: List[str],
    training_metadata: Optional[Dict],
    gene_symbol: str
) -> None:
    """
    Display existing variants that are already in the database.
    
    Args:
        existing_variants: List of variant IDs that exist in database
        training_metadata: Training metadata containing variant details
        gene_symbol: Gene symbol for context
    """
    st.subheader("Existing Variants (Already in Database)")
    
    # Show count of existing variants
    st.info(f"Found **{len(existing_variants)}** variants already in the training database")
    
    if training_metadata:
        # Convert metadata variants to DataFrame
        metadata_variants = training_metadata.get('variants', [])
        if metadata_variants:
            df_training_variants = pd.DataFrame(metadata_variants)
            
            # Filter to get only existing variants with full metadata
            existing_variant_ids = set(existing_variants)
            df_existing_variants = df_training_variants[
                df_training_variants['variant_id'].isin(existing_variant_ids)
            ]
            
            if len(df_existing_variants) > 0:
                st.success(f"✓ Loaded full metadata for {len(df_existing_variants)} existing variants")
                # Hide variant_id and variant_hash columns for display
                display_columns = [
                    col for col in df_existing_variants.columns 
                    if col not in ['variant_id', 'variant_hash']
                ]
                st.dataframe(
                    df_existing_variants[display_columns], 
                    use_container_width=True, 
                    height=400
                )
            else:
                st.warning(f"⚠️ Training metadata loaded but no matching variants found (metadata has {len(df_training_variants)} variants)")
                st.info("💡 Showing variant IDs only. The training metadata may be for a different set of variants.")
                # Fallback: show just variant IDs
                existing_df = pd.DataFrame(existing_variants, columns=['variant_id'])
                st.dataframe(existing_df, use_container_width=True, height=400)
        else:
            st.warning("Training metadata is empty (no variants).")
            st.info("💡 Showing variant IDs only. Click 'Get Training Variants' to reload metadata.")
            # Fallback: show just variant IDs
            existing_df = pd.DataFrame(existing_variants, columns=['variant_id'])
            st.dataframe(existing_df, use_container_width=True, height=400)
    else:
        st.warning(f"⚠️ Training metadata not loaded for gene **{gene_symbol}**")
        st.info("💡 Click the **'Get Training Variants'** button in the sidebar to load full metadata with annotations, consequences, and pathogenicity information.")
        # Fallback: show just variant IDs
        existing_df = pd.DataFrame(existing_variants, columns=['variant_id'])
        st.dataframe(existing_df, use_container_width=True, height=400)


def display_new_variants(
    new_variants: List[str],
    prediction_results_dict: Dict,
    existing_variants: List[str],
    model_names: List[str],
    training_metadata: Optional[Dict],
    gene_symbol: str,
    job_name: str,
    prediction_results_to_df_func
) -> None:
    """
    Display newly processed variants with predictions.
    
    Args:
        new_variants: List of new variant IDs
        prediction_results_dict: Dictionary of prediction results
        existing_variants: List of existing variant IDs
        model_names: List of model names used
        training_metadata: Training metadata for enrichment
        gene_symbol: Gene symbol for context
        job_name: Job name for caching
        prediction_results_to_df_func: Function to convert results to DataFrame
    """
    st.subheader("New Variants (Processed)")
    
    # K value selector
    k_value = st.selectbox(
        "K Value",
        options=[1, 5, 10, 15, 20],
        index=1,  # Default to 5
        help="Number of nearest neighbors to use for prediction",
        key=f"k_value_selector_{gene_symbol}_{job_name}"
    )
    
    # Convert prediction results to DataFrame
    df_new_variants = prediction_results_to_df_func(
        prediction_results=prediction_results_dict,
        existing_variants=existing_variants,
        model_names=model_names,
        k_value=k_value,
        training_metadata=training_metadata
    )
    
    if not df_new_variants.empty:
        st.dataframe(df_new_variants, use_container_width=True, height=400)
    else:
        st.info("No new variants to display")


def display_prediction_results(
    prediction_results: Dict[str, Any],
    training_metadata: Optional[Dict],
    gene_symbol: str,
    job_name: str,
    prediction_results_to_df_func,
    config: Dict,
    get_user_training_metadata_dir_func
) -> None:
    """
    Main function to display prediction results.
    
    Args:
        prediction_results: Full prediction results from API
        training_metadata: Training metadata for enrichment
        gene_symbol: Gene symbol
        job_name: Job name for caching
        prediction_results_to_df_func: Function to convert results to DataFrame
        config: Configuration dictionary
        get_user_training_metadata_dir_func: Function to get metadata directory
    """
    st.header("Prediction Results")
    
    # Get existing variants directly from API response
    existing_variants = prediction_results.get('existing_variants', [])
    
    # Get prediction results and model names
    prediction_results_dict = prediction_results.get('prediction_results', {})
    model_names = prediction_results.get('model_name', [])
    
    # Get new variants from prediction_results (variants not in existing_variants)
    existing_variant_set = set(existing_variants)
    new_variants = [
        vid for vid in prediction_results_dict.keys() 
        if vid not in existing_variant_set
    ]
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Existing Variants", len(existing_variants))
    with col2:
        st.metric("New Variants", len(new_variants))
    with col3:
        st.metric("Total Input Variants", prediction_results.get('variants_count', 0))
    
    # Load training metadata if not provided
    if training_metadata is None:
        training_metadata = load_training_metadata_from_cache(
            gene_symbol,
            config,
            get_user_training_metadata_dir_func
        )
        if training_metadata:
            st.success(f"✓ Training metadata loaded from cache ({len(training_metadata.get('variants', []))} training variants)")
        else:
            st.info(f"ℹ️ No training metadata found for **{gene_symbol}**. Click 'Get Training Variants' to load detailed annotations.")
    else:
        # Training metadata was provided (from session state)
        st.success(f"✓ Using training metadata from session ({len(training_metadata.get('variants', []))} training variants)")
    
    # Display existing variants
    if existing_variants:
        display_existing_variants(
            existing_variants=existing_variants,
            training_metadata=training_metadata,
            gene_symbol=gene_symbol
        )
    
    # Display new variants
    if new_variants:
        display_new_variants(
            new_variants=new_variants,
            prediction_results_dict=prediction_results_dict,
            existing_variants=existing_variants,
            model_names=model_names,
            training_metadata=training_metadata,
            gene_symbol=gene_symbol,
            job_name=job_name,
            prediction_results_to_df_func=prediction_results_to_df_func
        )

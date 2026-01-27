#!/usr/bin/env python3
"""
Module for displaying embedding plots in the Streamlit app.

This module provides functionality to display embedding visualizations including:
- Loading training and query coordinates
- PCA, t-SNE, and UMAP plots
- Single and multi-model comparisons

Main functions:
    - display_embedding_plots: Main function to render embedding plots
    - load_training_coordinates: Load training variant coordinates
    - load_query_coordinates_from_response: Load query coordinates from prediction results
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Import visualization utilities
from frontend.utils.parquet_manager import CoordinateParquetManager
from frontend.utils.embedding_visualization import (
    create_combined_embedding_figure,
    create_all_models_combined_figure
)

# Import common utilities
from frontend.tags.common_utils import load_pathogenicity_mapping


def load_training_coordinates(gene_symbol: str, 
                              embedding_model_name: str, 
                              annotation_method: str,
                              config: Dict,
                              get_user_training_metadata_dir_func,
                              label_mapping: bool = False) -> pd.DataFrame:
    """
    Load training variant coordinates from parquet file.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'FBN1')
        embedding_model_name: Name of the embedding model
        annotation_method: Annotation method (e.g., 'vep')
        config: Configuration dictionary
        get_user_training_metadata_dir_func: Function to get metadata directory
        label_mapping: If True, map pathogenicity to binary labels (pathogenic/benign)
        
    Returns:
        DataFrame with training variant coordinates and labels column
    """
    # Construct parquet file path
    base_dir = Path(config['paths']['user']['base_dir'])
    coordinates_dir = config['paths']['user']['training_results']['training_coordinates_dir']
    parquet_path = base_dir / coordinates_dir / gene_symbol / f"{gene_symbol}_{annotation_method}_coordinates.parquet"
    
    # Initialize parquet manager
    manager = CoordinateParquetManager(parquet_path)
    
    if not manager.exists():
        return pd.DataFrame()
    
    # Load coordinates for the specific model
    df_training = manager.get_coordinates_for_model(embedding_model_name)
    
    if df_training.empty:
        return pd.DataFrame()
    
    # Load pathogenicity mapping
    pathogenicity_map = load_pathogenicity_mapping(
        gene_symbol, 
        config,
        get_user_training_metadata_dir_func
    )
    
    # Add pathogenicity_original
    df_training['pathogenicity_original'] = df_training['variant_id'].map(
        lambda vid: pathogenicity_map.get(vid, 'unknown')
    )
    
    # Create labels column
    if label_mapping:
        def map_to_binary_label(pathogenicity):
            if pd.isna(pathogenicity):
                return 'unknown'
            pathogenicity_str = str(pathogenicity).lower()
            if 'pathogenic' in pathogenicity_str:
                return 'pathogenic'
            elif 'benign' in pathogenicity_str:
                return 'benign'
            else:
                return 'unknown'
        
        df_training['labels'] = df_training['pathogenicity_original'].apply(map_to_binary_label)
    else:
        df_training['labels'] = df_training['pathogenicity_original']
    
    return df_training


def load_query_coordinates_from_response(prediction_results: dict,
                                         embedding_model_name: str) -> pd.DataFrame:
    """
    Load query variant coordinates from prediction_results (new API format).
    
    Args:
        prediction_results: Dictionary of prediction results keyed by variant_id
        embedding_model_name: Name of the embedding model
        
    Returns:
        DataFrame with query variant coordinates
    """
    query_data = []
    
    for variant_id, variant_data in prediction_results.items():
        if embedding_model_name not in variant_data:
            continue
        
        model_result = variant_data[embedding_model_name]
        
        # Check for errors
        if 'error' in model_result:
            continue
        
        # Extract coordinates
        coordinates = model_result.get('coordinates', [])
        
        # Extract coordinates from the coordinates list
        pca_x = None
        pca_y = None
        tsne_x = None
        tsne_y = None
        umap_x = None
        umap_y = None
        
        for coord_dict in coordinates:
            if 'pca_x' in coord_dict:
                pca_x = coord_dict.get('pca_x')
                pca_y = coord_dict.get('pca_y')
            elif 't-sne_x' in coord_dict:
                tsne_x = coord_dict.get('t-sne_x')
                tsne_y = coord_dict.get('t-sne_y')
            elif 'umap_x' in coord_dict:
                umap_x = coord_dict.get('umap_x')
                umap_y = coord_dict.get('umap_y')
        
        query_data.append({
            'variant_id': variant_id,
            'embedding_model': embedding_model_name,
            'pca_x': pca_x,
            'pca_y': pca_y,
            't-sne_x': tsne_x,
            't-sne_y': tsne_y,
            'umap_x': umap_x,
            'umap_y': umap_y,
            'labels': 'query'
        })
    
    df_query = pd.DataFrame(query_data)
    return df_query


def display_embedding_plots(
    prediction_results: Dict[str, Any],
    gene_symbol: str,
    config: Dict,
    get_user_training_metadata_dir_func
) -> None:
    """
    Main function to display embedding plots.
    
    Args:
        prediction_results: Full prediction results from API
        gene_symbol: Gene symbol
        config: Configuration dictionary
        get_user_training_metadata_dir_func: Function to get metadata directory
    """
    st.header("Embedding Plots")
    
    if not prediction_results:
        st.info("Please process variants first to see embedding plots.")
        return
    
    prediction_results_dict = prediction_results.get('prediction_results', {})
    model_names = prediction_results.get('model_name', [])
    
    if not prediction_results_dict or not model_names:
        st.info("No prediction results available. Please process variants first.")
        return
    
    # Get annotation method from prediction results
    annotation_method = prediction_results.get('annotation_method', 'vep')
    
    # UI controls for plotting
    col1, col2 = st.columns(2)
    with col1:
        selected_models = st.multiselect(
            "Select Models to Plot",
            model_names,
            default=model_names,  # Default to ALL models
            help="Select embedding models to visualize"
        )
    with col2:
        label_mapping = st.checkbox(
            "Binary Labels (Pathogenic/Benign)",
            value=True,
            help="Map pathogenicity to binary labels"
        )
    
    if selected_models:
        plot_btn = st.button("📊 Generate Embedding Plots", use_container_width=True)
        
        if plot_btn:
            with st.spinner("Generating embedding plots..."):
                try:
                    models_data = {}
                    
                    # Load data for each selected model
                    for embedding_model_name in selected_models:
                        # Load training coordinates
                        df_training = load_training_coordinates(
                            gene_symbol, 
                            embedding_model_name, 
                            annotation_method,
                            config,
                            get_user_training_metadata_dir_func,
                            label_mapping=label_mapping
                        )
                        
                        if df_training.empty:
                            st.warning(f"No training coordinates found for {embedding_model_name}")
                            continue
                        
                        # Load query coordinates from prediction results
                        df_query = load_query_coordinates_from_response(
                            prediction_results_dict,
                            embedding_model_name
                        )
                        
                        if df_query.empty:
                            st.warning(f"No query coordinates found for {embedding_model_name}")
                            continue
                        
                        # Prepare columns for plotting
                        columns_needed = ['variant_id', 'pca_x', 'pca_y', 't-sne_x', 't-sne_y', 'umap_x', 'umap_y', 'labels']
                        
                        # Check for alternative column names and normalize
                        if 't-sne_x' not in df_training.columns and 'tsne_x' in df_training.columns:
                            df_training = df_training.rename(columns={'tsne_x': 't-sne_x', 'tsne_y': 't-sne_y'})
                        
                        # Select available columns
                        available_cols = [col for col in columns_needed if col in df_training.columns]
                        df_training_plot = df_training[available_cols].copy() if available_cols else df_training.copy()
                        df_query_plot = df_query[columns_needed].copy()
                        
                        # Combine dataframes
                        df_merged = pd.concat([df_training_plot, df_query_plot], ignore_index=True)
                        models_data[embedding_model_name] = df_merged
                    
                    if models_data:
                        # Calculate known and unknown variant counts
                        first_df = list(models_data.values())[0]
                        unknown_labels = ['query', 'unknown', 'not_yet_reviewed']
                        known_count = first_df[~first_df['labels'].isin(unknown_labels)].shape[0]
                        unknown_count = first_df[first_df['labels'].isin(unknown_labels)].shape[0]
                        
                        # Create figure
                        if len(selected_models) == 1:
                            # Single model plot
                            model_name = selected_models[0]
                            figure_title = f"{gene_symbol} - {model_name} ({annotation_method})"
                            
                            fig = create_combined_embedding_figure(
                                merged_df=models_data[model_name],
                                figure_title=figure_title,
                                model_name=model_name,
                                gene_symbol=gene_symbol,
                                figsize=(18, 8),
                                save_path=None,
                                show=False
                            )
                            
                            st.pyplot(fig)
                        else:
                            # Multiple models combined plot
                            fig = create_all_models_combined_figure(
                                models_data=models_data,
                                gene_symbol=gene_symbol,
                                figsize=(20, 6 * len(selected_models)),
                                save_path=None,
                                show=False,
                            )
                            
                            st.pyplot(fig)
                        
                        st.success(f"✓ Generated plots for {len(selected_models)} model(s). Known: {known_count}, Unknown: {unknown_count}")
                    
                except Exception as e:
                    st.error(f"Error generating plots: {e}")
                    st.exception(e)
    else:
        st.info("Please select at least one model to plot.")

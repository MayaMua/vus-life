#!/usr/bin/env python3
"""
Test variant plotting script.

This script loads training variant coordinates from parquet files and query variant
coordinates from prediction_results.json, then creates combined embedding visualizations.
"""

import json
import pandas as pd
import sys
import os
from pathlib import Path
from typing import Optional, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from frontend.utils.parquet_manager import CoordinateParquetManager
from frontend.utils.embedding_visualization import create_combined_embedding_figure, create_all_models_combined_figure


def load_training_pathogenicity_mapping(gene_symbol: str) -> dict:
    """
    Load pathogenicity mapping for training (known) variants from metadata.json.
    
    Note: Despite the key name "query_variant", these are actually known/training variants
    with established pathogenicity labels.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'ATM')
        
    Returns:
        Dictionary mapping variant_id to pathogenicity_original
    """
    # Load from training embedding results metadata
    metadata_path = Path(project_root) / "data_user" / "training_embedding_results" / "metadata" / gene_symbol / "metadata.json"
    
    pathogenicity_map = {}
    
    if not metadata_path.exists():
        print(f"  Warning: Metadata file not found: {metadata_path}")
        return pathogenicity_map
    
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        # The metadata.json contains training variants under 'query_variant' key
        # (Note: despite the name, these are the known/training variants)
        training_variants = data.get('variants', [])
        
        for variant in training_variants:
            variant_id = variant.get('variant_id')
            pathogenicity = variant.get('pathogenicity_original', 'unknown')
            if variant_id:
                pathogenicity_map[variant_id] = pathogenicity
        
        print(f"  Loaded pathogenicity for {len(pathogenicity_map)} training variants from {metadata_path}")
        
    except Exception as e:
        print(f"  Warning: Could not load pathogenicity from {metadata_path}: {e}")
    
    return pathogenicity_map


def load_training_coordinates(gene_symbol: str, 
                              embedding_model_name: str, 
                              annotation_method: str,
                              label_mapping: bool = False) -> pd.DataFrame:
    """
    Load training variant coordinates from parquet file.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'ATM')
        embedding_model_name: Name of the embedding model (e.g., 'all-mpnet-base-v2')
        annotation_method: Annotation method (e.g., 'vep')
        label_mapping: If True, map pathogenicity to binary labels (pathogenic/benign)
        
    Returns:
        DataFrame with training variant coordinates and labels column
    """
    # Construct parquet file path
    parquet_path = Path(project_root) / "data_user" / "training_embedding_results" / "coordinates" / gene_symbol / f"{gene_symbol}_{annotation_method}_coordinates.parquet"
    
    # Initialize parquet manager
    manager = CoordinateParquetManager(parquet_path)
    
    if not manager.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    # Load coordinates for the specific model
    df_training = manager.get_coordinates_for_model(embedding_model_name)
    
    if df_training.empty:
        raise ValueError(f"No coordinates found for model: {embedding_model_name}")
    
    # Load pathogenicity mapping for training variants
    pathogenicity_map = load_training_pathogenicity_mapping(gene_symbol)
    
    # Add pathogenicity_original for reference
    df_training['pathogenicity_original'] = df_training['variant_id'].map(
        lambda vid: pathogenicity_map.get(vid, 'unknown')
    )
    
    # Create labels column based on label_mapping setting
    if label_mapping:
        # Map to binary labels: pathogenic or benign
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
        # Use pathogenicity_original as labels
        df_training['labels'] = df_training['pathogenicity_original']
    
    return df_training


def load_query_coordinates(gene_symbol: str, 
                          embedding_model_name: str, 
                          annotation_method: str,
                          query_index: int,
                          k_value: int = 5) -> pd.DataFrame:
    """
    Load query variant coordinates from prediction_results.json.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'ATM')
        embedding_model_name: Name of the embedding model (e.g., 'all-mpnet-base-v2')
        annotation_method: Annotation method (e.g., 'vep')
        k_value: k value to select specific prediction result (default: 5)
        
    Returns:
        DataFrame with query variant coordinates
    """
    # Construct JSON file path
    json_path = Path(project_root) / "data_user" / "user_query" / "results" / gene_symbol \
    / f"query_{query_index}" / f"{embedding_model_name}_{annotation_method}" / "prediction_results.json"
    
    if not json_path.exists():
        raise FileNotFoundError(f"Prediction results file not found: {json_path}")
    
    # Load JSON file
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Handle new structure with "successful" wrapper (same as json_to_df.py)
    if 'successful' in data:
        results = data['successful'].get('results', [])
    else:
        # Fall back to old structure
        results = data.get('results', [])
    
    if not results:
        print(f"Warning: No results found in {json_path}")
        return pd.DataFrame()
    
    # Extract coordinates and metadata for each query variant
    query_data = []
    for result in results:
        variant_id = result.get('variant_id', '')
        coordinates = result.get('coordinates', [])
        
        # Get prediction result for the specified k value (same as json_to_df.py)
        prediction_result = result.get('prediction_result', {})
        if prediction_result and isinstance(prediction_result, dict):
            k_str = str(k_value)
            if k_str in prediction_result:
                pred_result = prediction_result[k_str].get('pred_result', 'unknown')
            else:
                # Use first available k value if specified k not found
                first_k = list(prediction_result.keys())[0] if prediction_result else None
                if first_k:
                    pred_result = prediction_result[first_k].get('pred_result', 'unknown')
                else:
                    pred_result = 'unknown'
        else:
            # Fall back to old structure (direct field)
            pred_result = result.get('pred_result', 'unknown')
        
        # Extract coordinates from the coordinates list
        # Format: [{"pca_x": ..., "pca_y": ...}, {"t-sne_x": ..., "t-sne_y": ...}, {"umap_x": ..., "umap_y": ...}]
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
            'labels': 'query'  # Use 'query' label for prediction variants (test dataset always uses 'query')
        })
    
    df_query = pd.DataFrame(query_data)
    
    return df_query


def plot_variant_embeddings(gene_symbol: str,
                           embedding_model_name: str,
                           annotation_method: str,
                           query_index: int,
                           k_value: int = 5,
                           label_mapping: bool = False,
                           save_path: Optional[str] = None,
                           show: bool = False) -> None:
    """
    Plot training and query variant embeddings together.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'ATM')
        embedding_model_name: Name of the embedding model (e.g., 'all-mpnet-base-v2')
        annotation_method: Annotation method (e.g., 'vep')
        k_value: k value to select specific prediction result (default: 5)
        label_mapping: If True, map pathogenicity to binary labels (pathogenic/benign) for training data
        save_path: Optional path to save the plot (if None, uses default path)
        show: Whether to display the plot
    """
    print(f"Loading training coordinates for {gene_symbol}...")
    df_training = load_training_coordinates(gene_symbol, embedding_model_name, annotation_method, label_mapping=label_mapping)
    print(f"  Loaded {len(df_training)} training variants")
    
    print(f"Loading query coordinates for {gene_symbol}...")
    df_query = load_query_coordinates(gene_symbol, embedding_model_name, annotation_method, query_index, k_value=k_value)
    print(f"  Loaded {len(df_query)} query variants")
    
    # Combine training and query variants
    # Select only the columns we need for plotting (use 'labels' instead of 'pathogenicity_original')
    columns_needed = ['variant_id', 'pca_x', 'pca_y', 't-sne_x', 't-sne_y', 'umap_x', 'umap_y', 'labels']
    
    df_training_plot = df_training[columns_needed].copy()
    df_query_plot = df_query[columns_needed].copy()
    
    # Combine dataframes
    df_merged = pd.concat([df_training_plot, df_query_plot], ignore_index=True)
    
    print(f"  Total variants for plotting: {len(df_merged)}")
    print(f"    Training: {len(df_training_plot)}")
    print(f"    Query: {len(df_query_plot)}")
    
    # Create figure title
    figure_title = f"{gene_symbol} - {embedding_model_name} ({annotation_method})"
    
    # Set default save path if not provided
    if save_path is None:
        save_dir = Path(project_root) / "data_user" / "user_query" / "results" / \
        gene_symbol / \
        f"query_{query_index}" / f"{embedding_model_name}_{annotation_method}" / "test_variant_plot"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"{gene_symbol}_{embedding_model_name}_{annotation_method}_combined_plot.png"
    
    # Create and save plot
    print(f"Creating combined embedding plot...")
    create_combined_embedding_figure(
        merged_df=df_merged,
        figure_title=figure_title,
        model_name=embedding_model_name,
        gene_symbol=gene_symbol,
        figsize=(18, 8),
        save_path=str(save_path),
        show=show
    )
    
    print(f"✓ Plot saved to: {save_path}")


def plot_all_models_combined(gene_symbol: str,
                             embedding_model_names: List[str],
                             annotation_method: str,
                             query_index: int,
                             k_value: int = 5,
                             label_mapping: bool = False,
                             save_path: Optional[str] = None,
                             show: bool = False) -> None:
    """
    Plot all embedding models together in a grid (one row per model, one column per reduction method).
    
    Args:
        gene_symbol: Gene symbol (e.g., 'ATM', 'FBN1')
        embedding_model_names: List of embedding model names (e.g., ['all-mpnet-base-v2', 'google-embedding', 'MedEmbed-large-v0.1'])
        annotation_method: Annotation method (e.g., 'vep')
        k_value: k value to select specific prediction result (default: 5)
        label_mapping: If True, map pathogenicity to binary labels (pathogenic/benign) for training data
        save_path: Optional path to save the plot (if None, uses default path)
        show: Whether to display the plot
    """
    models_data = {}
    
    # Load data for each model
    for embedding_model_name in embedding_model_names:
        print(f"Loading data for {embedding_model_name}...")
        
        # Load training coordinates
        df_training = load_training_coordinates(gene_symbol, embedding_model_name, annotation_method, label_mapping=label_mapping)
        print(f"  Loaded {len(df_training)} training variants")
        
        # Load query coordinates
        df_query = load_query_coordinates(gene_symbol, embedding_model_name, annotation_method, query_index, k_value=k_value)
        print(f"  Loaded {len(df_query)} query variants")
        
        # Combine training and query variants
        # Select only the columns we need for plotting (use 'labels' instead of 'pathogenicity_original')
        columns_needed = ['variant_id', 'pca_x', 'pca_y', 't-sne_x', 't-sne_y', 'umap_x', 'umap_y', 'labels']
        
        df_training_plot = df_training[columns_needed].copy()
        df_query_plot = df_query[columns_needed].copy()
        
        # Combine dataframes
        df_merged = pd.concat([df_training_plot, df_query_plot], ignore_index=True)
        models_data[embedding_model_name] = df_merged
        
        print(f"  Total variants for {embedding_model_name}: {len(df_merged)}")
    
    # Calculate known and unknown variant counts
    # Use first model's data for counts (all models should have same variants)
    first_df = list(models_data.values())[0]
    unknown_labels = ['query', 'unknown', 'not_yet_reviewed']
    known_count = first_df[~first_df['labels'].isin(unknown_labels)].shape[0]
    unknown_count = first_df[first_df['labels'].isin(unknown_labels)].shape[0]
    
    # Create title with known and unknown counts
    figure_title = f"Embedding results of {gene_symbol} - {known_count} known + {unknown_count} unknown variants"
    
    # Set default save path if not provided
    if save_path is None:
        save_dir = Path(project_root) / "data_user" / "user_query" / "results" / gene_symbol / f"query_{query_index}" / f"{embedding_model_names[0]}_{annotation_method}" / "test_variant_plot"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"{gene_symbol}_all_models_combined_plot.png"
    
    # Create and save combined plot
    print(f"Creating combined plot for all models...")
    print(f"  Known variants: {known_count}, Unknown variants: {unknown_count}")
    create_all_models_combined_figure(
        models_data=models_data,
        gene_symbol=gene_symbol,
        figsize=(20, 18),
        save_path=str(save_path),
        show=show,
        title=figure_title
    )
    
    print(f"✓ Combined plot saved to: {save_path}")


if __name__ == "__main__":
    # Example usage
    gene_symbol = "FBN1"
    embedding_model_names = ["all-mpnet-base-v2", "google-embedding", "MedEmbed-large-v0.1"]
    k_value = 5
    annotation_method = "vep"
    query_index = 2
    # Option 1: Plot each model separately (original behavior)
    # for embedding_model_name in embedding_model_names:
    #     plot_variant_embeddings(
    #         gene_symbol=gene_symbol,
    #         embedding_model_name=embedding_model_name,
    #         annotation_method=annotation_method,
    #         k_value=k_value,
    #         show=False
    #     )
    
    # Option 2: Plot all models together in a grid (new behavior)
    plot_all_models_combined(
        gene_symbol=gene_symbol,
        embedding_model_names=embedding_model_names,
        annotation_method=annotation_method,
        query_index=query_index,
        k_value=k_value,
        label_mapping=True,
        show=False
    )


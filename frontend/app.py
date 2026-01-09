#!/usr/bin/env python3
"""
Streamlit app for variant processing using the Variant Data Generation API.
"""

import streamlit as st
import pandas as pd
import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys
import os
from dotenv import load_dotenv
import time

# Add parent directories to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Load configuration
from frontend.configs.config_loader import (
    load_config, get_gene_names, get_annotation_method_names, 
    get_embedding_models, get_user_query_inputs_dir, 
    get_user_query_results_dir, get_user_query_processed_dir,
    get_user_training_metadata_dir
)
from frontend.api_sender import (
    get_prediction_results, get_metadata_gene, get_annotations_by_variant_ids,
    dataframe_to_api_format, load_test_data, save_results
)

# Import ClinVar functions
from tools.clinical_db_fetcher.clients.clinvar_fetcher import (
    search_clinvar_by_hgvs_g,
    fetch_clinvar_details_by_id,
)

# Import visualization utilities
from frontend.utils.parquet_manager import CoordinateParquetManager
from frontend.utils.embedding_visualization import (
    create_combined_embedding_figure,
    create_all_models_combined_figure
)

# Load config
CONFIG_PATH = Path(__file__).parent / "configs" / "frontend_config.toml"
config = load_config(str(CONFIG_PATH))

# Page configuration
st.set_page_config(
    page_title="Variant Processing Dashboard",
    page_icon="🧬",
    layout="wide"
)

# Initialize session state
if 'variants_df' not in st.session_state:
    st.session_state.variants_df = None
if 'prediction_results' not in st.session_state:
    st.session_state.prediction_results = None
if 'metadata_results' not in st.session_state:
    st.session_state.metadata_results = None
if 'current_gene_symbol' not in st.session_state:
    st.session_state.current_gene_symbol = None


def check_api_connection() -> bool:
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=2)
        return response.status_code == 200
    except:
        return False


def save_input_file(df: pd.DataFrame, gene_symbol: str, job_name: str, filename: str = None):
    """Save input variants to file in input directory."""
    input_dir = get_user_query_inputs_dir(config, gene_symbol, job_name)
    input_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = f"{gene_symbol}_variants.csv"
    
    file_path = input_dir / filename
    df.to_csv(file_path, index=False)
    return file_path


def load_or_fetch_metadata(gene_symbol: str) -> Optional[dict]:
    """
    Load metadata from file if exists, otherwise fetch from API.
    
    Args:
        gene_symbol: Gene symbol
        
    Returns:
        Metadata dictionary or None if error
    """
    metadata_dir = get_user_training_metadata_dir(config, gene_symbol)
    metadata_file = metadata_dir / "metadata.json"
    
    # Check if metadata file exists
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            st.warning(f"Error loading existing metadata: {e}. Will fetch from API.")
    
    # Fetch from API if not exists or loading failed
    try:
        metadata = get_metadata_gene(gene_symbol)
        
        # Save to file
        metadata_dir.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    except Exception as e:
        st.error(f"Error fetching metadata: {e}")
        return None


def fetch_clinvar_data_for_variants(hgvs_genomic_38_list: list) -> pd.DataFrame:
    """
    Query ClinVar data for a list of hgvs_genomic_38 values and return a DataFrame.
    Uses Streamlit progress bar for user feedback.
    
    Returns a DataFrame with columns:
    - hgvs_genomic_38: Input HGVS genomic notation
    - clinvar_id: ClinVar variant ID
    - clinvar_url: URL to ClinVar variant page
    - germline_classification: Germline classification description
    
    Args:
        hgvs_genomic_38_list: List of HGVS genomic notation strings
        
    Returns:
        DataFrame with columns: hgvs_genomic_38, clinvar_id, clinvar_url, germline_classification
    """
    # Remove duplicates and empty values
    unique_hgvs = [hgvs for hgvs in set(hgvs_genomic_38_list) if pd.notna(hgvs) and hgvs]
    
    if not unique_hgvs:
        return pd.DataFrame(columns=['hgvs_genomic_38', 'clinvar_id', 'clinvar_url', 'germline_classification'])
    
    # Initialize result list
    results = []
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Process each hgvs_genomic_38 value
    for idx, hgvs_g in enumerate(unique_hgvs):
        try:
            status_text.text(f"Querying ClinVar for variant {idx + 1}/{len(unique_hgvs)}: {hgvs_g}")
            
            # Search ClinVar by HGVS genomic notation
            ids = search_clinvar_by_hgvs_g(hgvs_g)
            clinvar_id = ids[0] if ids else None
            
            if clinvar_id:
                # Create ClinVar URL
                clinvar_url = f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{clinvar_id}"
                
                # Fetch details to get germline classification
                details_result = fetch_clinvar_details_by_id(clinvar_id)
                description = None
                
                if details_result:
                    record = details_result.get(str(clinvar_id), {})
                    germline = record.get("germline_classification", {})
                    description = germline.get("description")
                
                # Add result
                results.append({
                    'hgvs_genomic_38': hgvs_g,
                    'clinvar_id': clinvar_id,
                    'clinvar_url': clinvar_url,
                    'germline_classification': description
                })
            else:
                # No ClinVar ID found
                results.append({
                    'hgvs_genomic_38': hgvs_g,
                    'clinvar_id': None,
                    'clinvar_url': None,
                    'germline_classification': None
                })
                
        except Exception as e:
            st.warning(f"Error querying ClinVar for {hgvs_g}: {e}")
            results.append({
                'hgvs_genomic_38': hgvs_g,
                'clinvar_id': None,
                'clinvar_url': None,
                'germline_classification': None
            })
        
        # Update progress
        progress = (idx + 1) / len(unique_hgvs)
        progress_bar.progress(progress)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Create DataFrame
    df_result = pd.DataFrame(results)
    
    found_count = df_result['clinvar_id'].notna().sum() if len(df_result) > 0 else 0
    st.success(f"✓ Completed ClinVar queries. Found {found_count}/{len(unique_hgvs)} variants with ClinVar IDs.")
    
    return df_result


def load_training_pathogenicity_mapping(gene_symbol: str) -> dict:
    """
    Load pathogenicity mapping for training (known) variants from metadata.json.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'FBN1')
        
    Returns:
        Dictionary mapping variant_id to pathogenicity_original
    """
    metadata_dir = get_user_training_metadata_dir(config, gene_symbol)
    metadata_path = metadata_dir / "metadata.json"
    
    pathogenicity_map = {}
    
    if not metadata_path.exists():
        return pathogenicity_map
    
    try:
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        
        training_variants = data.get('variants', [])
        
        for variant in training_variants:
            variant_id = variant.get('variant_id')
            pathogenicity = variant.get('pathogenicity_original', 'unknown')
            if variant_id:
                pathogenicity_map[variant_id] = pathogenicity
        
    except Exception as e:
        st.warning(f"Could not load pathogenicity mapping: {e}")
    
    return pathogenicity_map


def load_training_coordinates(gene_symbol: str, 
                              embedding_model_name: str, 
                              annotation_method: str,
                              label_mapping: bool = False) -> pd.DataFrame:
    """
    Load training variant coordinates from parquet file.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'FBN1')
        embedding_model_name: Name of the embedding model
        annotation_method: Annotation method (e.g., 'vep')
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
    pathogenicity_map = load_training_pathogenicity_mapping(gene_symbol)
    
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
                                         embedding_model_name: str,
                                         k_value: int = 5) -> pd.DataFrame:
    """
    Load query variant coordinates from prediction_results (new API format).
    
    Args:
        prediction_results: Dictionary of prediction results keyed by variant_id
        embedding_model_name: Name of the embedding model
        k_value: k value to select specific prediction result (default: 5)
        
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


def prediction_results_to_df(prediction_results: dict, existing_variants: list, 
                              model_names: list, k_value: int = 5,
                              training_metadata: Optional[dict] = None) -> pd.DataFrame:
    """
    Convert prediction results to DataFrame for display.
    
    Args:
        prediction_results: Dictionary of prediction results keyed by variant_id
        existing_variants: List of existing variant IDs to exclude
        model_names: List of model names to process
        k_value: k value to use for prediction results (default: 5)
        training_metadata: Optional training metadata to enrich nearest variants
        
    Returns:
        DataFrame with variant metadata and prediction results for each model
    """
    existing_variant_set = set(existing_variants)
    
    # Create mapping from variant_id to hgvs_genomic_38 and pathogenicity from training metadata
    variant_id_to_info = {}
    if training_metadata:
        training_variants = training_metadata.get('variants', [])
        for variant in training_variants:
            variant_id = variant.get('variant_id')
            if variant_id:
                hgvs_genomic_38 = variant.get('hgvs_genomic_38', '')
                pathogenicity = variant.get('pathogenicity_original', 'unknown')
                variant_id_to_info[variant_id] = (hgvs_genomic_38, pathogenicity)
    
    parsed_results = []
    
    # Process each variant (only new variants, not existing ones)
    for variant_id, variant_data in prediction_results.items():
        if variant_id in existing_variant_set:
            continue  # Skip existing variants
        
        metadata = variant_data.get('metadata', {})
        
        # Initialize row with metadata
        row = {
            'variant_id': variant_id,
            'chromosome': metadata.get('chromosome', ''),
            'position': metadata.get('position', ''),
            'ref_allele': metadata.get('ref_allele', ''),
            'alt_allele': metadata.get('alt_allele', ''),
            'gene_symbol': metadata.get('gene_symbol', ''),
            'hgvs_coding': metadata.get('hgvs_coding', ''),
            'hgvs_genomic_38': metadata.get('hgvs_genomic_38', ''),
            'hgvs_protein': metadata.get('hgvs_protein', ''),
            'most_severe_consequence': metadata.get('most_severe_consequence', ''),
        }
        
        # Initialize sets for accumulating formatted variant strings across models
        top_similar_variants_sets = set()
        
        # Process each model
        for model_name in model_names:
            if model_name not in variant_data:
                # Model not available for this variant
                row[f'confidence_score_{model_name}'] = None
                row[f'pred_result_{model_name}'] = None
                continue
            
            model_result = variant_data[model_name]
            
            # Check for errors
            if 'error' in model_result:
                row[f'confidence_score_{model_name}'] = None
                row[f'pred_result_{model_name}'] = f"Error: {model_result['error']}"
                continue
            
            # Extract prediction result for k_value
            prediction_result = model_result.get('prediction_result', {})
            k_str = str(k_value)
            
            if k_str in prediction_result:
                pred_data = prediction_result[k_str]
                row[f'confidence_score_{model_name}'] = pred_data.get('confidence_score', '')
                row[f'pred_result_{model_name}'] = pred_data.get('pred_result', '')
            else:
                # Use first available k value if specified k not found
                first_k = list(prediction_result.keys())[0] if prediction_result else None
                if first_k:
                    pred_data = prediction_result[first_k]
                    row[f'confidence_score_{model_name}'] = pred_data.get('confidence_score', '')
                    row[f'pred_result_{model_name}'] = pred_data.get('pred_result', '')
                else:
                    row[f'confidence_score_{model_name}'] = None
                    row[f'pred_result_{model_name}'] = None
            
            # Extract and format nearest training variants
            nearest_variants = model_result.get('nearest_training_variants', [])
            for nv in nearest_variants[:k_value]:
                variant_id_nv = nv.get('variant_id')
                if variant_id_nv:
                    if variant_id_nv in variant_id_to_info:
                        hgvs_genomic_38, pathogenicity = variant_id_to_info[variant_id_nv]
                        if hgvs_genomic_38:
                            formatted_str = f"{hgvs_genomic_38} ({pathogenicity})"
                        else:
                            formatted_str = f"{variant_id_nv} ({pathogenicity})"
                    else:
                        # Use pathogenicity from nearest_variants if available
                        pathogenicity = nv.get('pathogenicity', 'unknown')
                        formatted_str = f"{variant_id_nv} ({pathogenicity})"
                    top_similar_variants_sets.add(formatted_str)
        
        # Add top similar variants as comma-separated string
        row['top_similar_variants'] = ', '.join(sorted(top_similar_variants_sets))
        
        parsed_results.append(row)
    
    # Create DataFrame
    if parsed_results:
        df = pd.DataFrame(parsed_results)
        return df
    else:
        return pd.DataFrame()


def _display_training_variants(metadata: dict):
    """Display training variants in a tab."""
    st.header("Training Variants")
    
    gene_symbol = metadata.get('gene_symbol', 'N/A')
    variants_count = metadata.get('variants_count', 0)
    
    st.metric("Total Training Variants", variants_count)
    st.info(f"Gene: {gene_symbol}")
    
    if variants_count > 0:
        variants = metadata.get('variants', [])
        if variants:
            # Convert to DataFrame for display
            variants_df = pd.DataFrame(variants)
            
            # Show summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                if 'pathogenicity_original' in variants_df.columns:
                    pathogenicity_counts = variants_df['pathogenicity_original'].value_counts()
                    st.metric("Pathogenicity Categories", len(pathogenicity_counts))
            with col2:
                if 'most_severe_consequence' in variants_df.columns:
                    consequence_counts = variants_df['most_severe_consequence'].value_counts()
                    st.metric("Consequence Types", len(consequence_counts))
            with col3:
                st.metric("Total Variants", len(variants_df))
            
            # Display variants table
            st.subheader("Variants Table")
            st.dataframe(variants_df, use_container_width=True, height=400)
            
            # Show pathogenicity distribution if available
            if 'pathogenicity_original' in variants_df.columns:
                st.subheader("Pathogenicity Distribution")
                pathogenicity_counts = variants_df['pathogenicity_original'].value_counts()
                st.bar_chart(pathogenicity_counts)
    else:
        st.warning("No training variants found for this gene.")


def parse_variant_input(input_text: str) -> pd.DataFrame:
    """Parse variant input text into DataFrame."""
    lines = [line.strip() for line in input_text.strip().split('\n') if line.strip()]
    variants = []
    
    for line in lines:
        # Try to parse different formats
        parts = line.split()
        if len(parts) >= 4:
            # Format: chromosome position ref alt [hgvs_genomic_38]
            variant = {
                'chromosome': parts[0],
                'position': parts[1],
                'ref_allele': parts[2],
                'alt_allele': parts[3]
            }
            if len(parts) >= 5:
                variant['hgvs_genomic_38'] = parts[4]
            variants.append(variant)
    
    if variants:
        return pd.DataFrame(variants)
    return pd.DataFrame()


def main():
    """Main Streamlit app."""
    st.title("🧬 Variant Processing Dashboard")
    
    # Check API connection
    if not check_api_connection():
        st.error(f"❌ Cannot connect to API at {API_BASE_URL}")
        st.info("Please start the API server first:\n```bash\nuvicorn backend.API.main:app --reload --host 0.0.0.0 --port 8000\n```")
        return
    
    st.success(f"✓ Connected to API at {API_BASE_URL}")
    
    # Sidebar for parameters
    with st.sidebar:
        st.header("⚙️ Parameters")
        
        # Gene selection
        gene_names = get_gene_names(config)
        gene_symbol = st.selectbox("Gene Symbol", gene_names, index=0 if gene_names else None)
        
        # Get Training Variants button (placed right after gene selection)
        get_metadata_btn = st.button("Get Training Variants", use_container_width=True, 
                                    help="Load or fetch training variants metadata for the selected gene")
        
        # Job name
        job_name = st.text_input("Job Name", value="default", help="Name for this processing job")
        
        # Annotation method
        annotation_methods = get_annotation_method_names(config)
        annotation_method = st.selectbox("Annotation Method", annotation_methods, index=0)
        
        # Embedding models (multi-select)
        embedding_models_list = get_embedding_models(config)
        embedding_models = st.multiselect(
            "Embedding Models",
            embedding_models_list,
            default=embedding_models_list if embedding_models_list else []
        )
        
        # Same severe consequence filter
        same_severe_consequence = st.checkbox("Filter by Same Severe Consequence", value=False)
        
        st.divider()
        
        # Variant input methods
        st.header("📥 Variant Input")
        input_method = st.radio(
            "Input Method",
            ["Upload File (CSV/TXT)", "Manual Entry", "Paste Variants"],
            index=0
        )
        
        variants_df = None
        
        if input_method == "Upload File (CSV/TXT)":
            uploaded_file = st.file_uploader(
                "Upload variant file",
                type=['csv', 'txt'],
                help="CSV file with columns: chromosome, position, ref_allele, alt_allele, hgvs_genomic_38"
            )
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        variants_df = pd.read_csv(uploaded_file)
                    else:
                        # Try to parse as CSV even if .txt
                        variants_df = pd.read_csv(uploaded_file)
                    
                    # Check required columns
                    required_cols = ['chromosome', 'position', 'ref_allele', 'alt_allele']
                    missing_cols = [col for col in required_cols if col not in variants_df.columns]
                    
                    if missing_cols:
                        st.error(f"Missing required columns: {missing_cols}")
                    else:
                        st.success(f"✓ Loaded {len(variants_df)} variants")
                        # Save to input directory
                        if gene_symbol and job_name:
                            file_path = save_input_file(variants_df, gene_symbol, job_name, uploaded_file.name)
                            st.info(f"Saved to: {file_path}")
                        
                except Exception as e:
                    st.error(f"Error loading file: {e}")
        
        elif input_method == "Manual Entry":
            st.info("Enter variants one per line:\nFormat: chromosome position ref_allele alt_allele [hgvs_genomic_38]")
            variant_text = st.text_area("Variants", height=200, placeholder="13 32316467 G A\n13 32316470 C T")
            
            if variant_text:
                variants_df = parse_variant_input(variant_text)
                if not variants_df.empty:
                    st.success(f"✓ Parsed {len(variants_df)} variants")
                    # Save to input directory
                    if gene_symbol and job_name:
                        file_path = save_input_file(variants_df, gene_symbol, job_name)
                        st.info(f"Saved to: {file_path}")
        
        elif input_method == "Paste Variants":
            variant_text = st.text_area("Paste variants", height=200)
            if variant_text:
                variants_df = parse_variant_input(variant_text)
                if not variants_df.empty:
                    st.success(f"✓ Parsed {len(variants_df)} variants")
                    # Save to input directory
                    if gene_symbol and job_name:
                        file_path = save_input_file(variants_df, gene_symbol, job_name)
                        st.info(f"Saved to: {file_path}")
        
        # Store in session state
        if variants_df is not None and not variants_df.empty:
            st.session_state.variants_df = variants_df
        
        st.divider()
        
        # Action button for processing variants
        st.header("🚀 Actions")
        process_btn = st.button("Process Variants", use_container_width=True, type="primary")
    
    # Main content area
    # Determine which tabs to show
    tabs_list = []
    if st.session_state.variants_df is not None:
        tabs_list.extend(["📋 Preview Input Data", "🔄 Existing vs New Variants", "📊 Embedding Plots"])
    if st.session_state.metadata_results is not None:
        tabs_list.append("📚 Training Variants")
    
    if tabs_list:
        tabs = st.tabs(tabs_list)
        tab_idx = 0
    else:
        tabs = [None] * 4
        tab_idx = 0
    
    # Preview Input Data tab
    if st.session_state.variants_df is not None:
        with tabs[tab_idx]:
            st.header("Input Variants Preview")
            st.dataframe(st.session_state.variants_df, use_container_width=True)
            st.info(f"Total variants: {len(st.session_state.variants_df)}")
        tab_idx += 1
        
        # Existing vs New Variants tab
        with tabs[tab_idx]:
            st.header("Existing vs New Variants")
            
            if st.session_state.prediction_results:
                # Get existing variants directly from API response
                existing_variants = st.session_state.prediction_results.get('existing_variants', [])
                
                # Get prediction results and model names (store once to avoid re-fetching)
                prediction_results_dict = st.session_state.prediction_results.get('prediction_results', {})
                model_names = st.session_state.prediction_results.get('model_name', [])
                
                # Get new variants from prediction_results (variants not in existing_variants)
                existing_variant_set = set(existing_variants)
                new_variants = [vid for vid in prediction_results_dict.keys() if vid not in existing_variant_set]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Existing Variants", len(existing_variants))
                with col2:
                    st.metric("New Variants", len(new_variants))
                
                if existing_variants:
                    st.subheader("Existing Variants (Already in Database)")
                    
                    # Load training variants metadata
                    training_metadata = None
                    if st.session_state.metadata_results:
                        training_metadata = st.session_state.metadata_results
                    else:
                        # Try to load from file
                        try:
                            metadata_dir = get_user_training_metadata_dir(config, gene_symbol)
                            metadata_file = metadata_dir / "metadata.json"
                            if metadata_file.exists():
                                with open(metadata_file, 'r') as f:
                                    training_metadata = json.load(f)
                        except Exception as e:
                            st.warning(f"Could not load training metadata: {e}")
                    
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
                                st.dataframe(df_existing_variants, use_container_width=True, height=400)
                            else:
                                st.warning("No matching variants found in training metadata.")
                                # Fallback: show just variant IDs
                                existing_df = pd.DataFrame(existing_variants, columns=['variant_id'])
                                st.dataframe(existing_df, use_container_width=True)
                        else:
                            st.warning("Training metadata has no variants.")
                            # Fallback: show just variant IDs
                            existing_df = pd.DataFrame(existing_variants, columns=['variant_id'])
                            st.dataframe(existing_df, use_container_width=True)
                    else:
                        st.info("Training metadata not available. Click 'Get Training Variants' to load full metadata.")
                        # Fallback: show just variant IDs
                        existing_df = pd.DataFrame(existing_variants, columns=['variant_id'])
                        st.dataframe(existing_df, use_container_width=True)
                
                if new_variants:
                    st.subheader("New Variants (Processed)")
                    
                    # Load training metadata for enriching nearest variants
                    
                    # Load training metadata for enriching nearest variants
                    training_metadata = None
                    if st.session_state.metadata_results:
                        training_metadata = st.session_state.metadata_results
                    else:
                        # Try to load from file
                        try:
                            metadata_dir = get_user_training_metadata_dir(config, gene_symbol)
                            metadata_file = metadata_dir / "metadata.json"
                            if metadata_file.exists():
                                with open(metadata_file, 'r') as f:
                                    training_metadata = json.load(f)
                        except Exception as e:
                            st.warning(f"Could not load training metadata: {e}")
                    
                    # Convert prediction results to DataFrame (use prediction_results_dict, not prediction_results)
                    df_new_variants = prediction_results_to_df(
                        prediction_results=prediction_results_dict,
                        existing_variants=existing_variants,
                        model_names=model_names,
                        k_value=5,  # Default k value
                        training_metadata=training_metadata
                    )
                    
                    if not df_new_variants.empty:
                        # Check if ClinVar data is already available in session state
                        # Use a key that includes gene_symbol and job_name to avoid conflicts
                        clinvar_key = f'df_new_variants_with_clinvar_{gene_symbol}_{job_name}'
                        if clinvar_key in st.session_state:
                            df_new_variants = st.session_state[clinvar_key]
                        
                        st.dataframe(df_new_variants, use_container_width=True, height=400)
                        
                        # Button to fetch ClinVar data
                        fetch_clinvar_btn = st.button(
                            "🔍 Fetch ClinVar Data",
                            help="Query ClinVar database for variant classifications",
                            key=f"fetch_clinvar_{gene_symbol}_{job_name}"
                        )
                        
                        # Handle ClinVar fetch button click
                        if fetch_clinvar_btn:
                            # Get original DataFrame (without ClinVar data) for merging
                            df_original = prediction_results_to_df(
                                prediction_results=prediction_results_dict,
                                existing_variants=existing_variants,
                                model_names=model_names,
                                k_value=5,
                                training_metadata=training_metadata
                            )
                            
                            # Extract hgvs_genomic_38 values
                            hgvs_list = df_original['hgvs_genomic_38'].dropna().unique().tolist()
                            
                            if hgvs_list:
                                # Fetch ClinVar data
                                clinvar_df = fetch_clinvar_data_for_variants(hgvs_list)
                                
                                # Merge with new variants DataFrame
                                df_new_variants = df_original.merge(
                                    clinvar_df,
                                    on='hgvs_genomic_38',
                                    how='left',
                                    suffixes=('', '_clinvar')
                                )
                                
                                # Store in session state for persistence
                                st.session_state[clinvar_key] = df_new_variants
                                
                                # Force rerun to show updated data
                                st.rerun()
                        
                        # Show ClinVar summary if available
                        if 'clinvar_id' in df_new_variants.columns:
                            clinvar_found = df_new_variants['clinvar_id'].notna().sum()
                            if clinvar_found > 0:
                                st.info(f"📊 ClinVar data found for {clinvar_found}/{len(df_new_variants)} variants")
                        
                        # Show summary statistics
                        st.subheader("Summary Statistics")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if 'most_severe_consequence' in df_new_variants.columns:
                                consequence_counts = df_new_variants['most_severe_consequence'].value_counts()
                                st.metric("Consequence Types", len(consequence_counts))
                        with col2:
                            # Count predictions by result type (use first model)
                            if model_names and f'pred_result_{model_names[0]}' in df_new_variants.columns:
                                pred_counts = df_new_variants[f'pred_result_{model_names[0]}'].value_counts()
                                st.metric("Prediction Categories", len(pred_counts))
                        with col3:
                            st.metric("Total New Variants", len(df_new_variants))
                    else:
                        st.warning("No new variants with prediction results found.")
                
                # Show model-specific summaries
                st.subheader("Model Processing Summary")
                # Use already-fetched model_names and prediction_results_dict
                for model_name in model_names:
                    # Count variants processed by this model
                    model_processed = 0
                    model_errors = 0
                    
                    for variant_id, variant_data in prediction_results_dict.items():
                        if model_name in variant_data:
                            model_result = variant_data[model_name]
                            if 'error' in model_result:
                                model_errors += 1
                            else:
                                model_processed += 1
                    
                    if model_errors > 0:
                        st.warning(f"**{model_name}**: {model_processed} processed, {model_errors} errors")
                    else:
                        st.info(f"**{model_name}**: {model_processed} variants processed successfully")
            else:
                st.info("Process variants first to see existing vs new variants")
        tab_idx += 1
        
        # Embedding Plots tab
        with tabs[tab_idx]:
            st.header("Embedding Plots")
            
            if st.session_state.prediction_results:
                prediction_results_dict = st.session_state.prediction_results.get('prediction_results', {})
                model_names = st.session_state.prediction_results.get('model_name', [])
                
                if not prediction_results_dict or not model_names:
                    st.info("No prediction results available. Please process variants first.")
                else:
                    # Get annotation method from prediction results
                    annotation_method = st.session_state.prediction_results.get('annotation_method', 'vep')
                    
                    # UI controls for plotting
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        selected_models = st.multiselect(
                            "Select Models to Plot",
                            model_names,
                            default=model_names[:1] if model_names else [],
                            help="Select embedding models to visualize"
                        )
                    with col2:
                        k_value = st.selectbox(
                            "K Value",
                            [5, 10, 15, 20],
                            index=0,
                            help="K value used for prediction"
                        )
                    with col3:
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
                                            label_mapping=label_mapping
                                        )
                                        
                                        if df_training.empty:
                                            st.warning(f"No training coordinates found for {embedding_model_name}")
                                            continue
                                        
                                        # Load query coordinates from prediction results
                                        df_query = load_query_coordinates_from_response(
                                            prediction_results_dict,
                                            embedding_model_name,
                                            k_value=k_value
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
            else:
                st.info("Please process variants first to see embedding plots.")
        tab_idx += 1
    
    # Training Variants tab
    if st.session_state.metadata_results is not None:
        if st.session_state.variants_df is not None:
            # If variants_df exists, use the next tab
            with tabs[tab_idx]:
                _display_training_variants(st.session_state.metadata_results)
        else:
            # If no variants_df, create a single tab
            with st.tabs(["📚 Training Variants"])[0]:
                _display_training_variants(st.session_state.metadata_results)
    
    if not tabs_list:
        st.info("👈 Please upload or enter variants in the sidebar, or click 'Get Training Variants' to get started")
    
    # Handle Get Training Variants button click
    if get_metadata_btn:
        if not gene_symbol:
            st.error("Please select a gene symbol")
        else:
            # Check if gene symbol changed
            if st.session_state.current_gene_symbol != gene_symbol:
                st.session_state.metadata_results = None
            
            # Load or fetch metadata
            with st.spinner(f"Loading training variants for {gene_symbol}..."):
                metadata = load_or_fetch_metadata(gene_symbol)
                
                if metadata:
                    st.session_state.metadata_results = metadata
                    st.session_state.current_gene_symbol = gene_symbol
                    
                    variants_count = metadata.get('variants_count', 0)
                    metadata_dir = get_user_training_metadata_dir(config, gene_symbol)
                    metadata_file = metadata_dir / "metadata.json"
                    
                    if metadata_file.exists():
                        st.success(f"✓ Loaded {variants_count} training variants from cache")
                    else:
                        st.success(f"✓ Fetched and saved {variants_count} training variants")
                    
                    # Force rerun to show the new tab
                    st.rerun()
                else:
                    st.error("Failed to load or fetch metadata")
    
    if process_btn:
        if st.session_state.variants_df is None or st.session_state.variants_df.empty:
            st.error("Please upload or enter variants first")
        elif not gene_symbol:
            st.error("Please select a gene symbol")
        elif not embedding_models:
            st.error("Please select at least one embedding model")
        else:
            with st.spinner(f"Processing {len(st.session_state.variants_df)} variants..."):
                try:
                    variants_list = dataframe_to_api_format(st.session_state.variants_df)
                    
                    # Get prediction results
                    prediction_result = get_prediction_results(
                        gene_symbol=gene_symbol,
                        variants=variants_list,
                        annotation_method=annotation_method,
                        embedding_models=embedding_models,
                        same_severe_consequence=same_severe_consequence
                    )
                    
                    st.session_state.prediction_results = prediction_result
                    # Store annotation_method for use in embedding plots
                    st.session_state.annotation_method = annotation_method
                    
                    # Get existing variants directly from API response
                    existing_variants = prediction_result.get('existing_variants', [])
                    
                    # Save existing variants at job level
                    if existing_variants:
                        results_dir = get_user_query_results_dir(config, gene_symbol, job_name)
                        results_dir.mkdir(parents=True, exist_ok=True)
                        existing_variants_path = results_dir / "existing_variants.json"
                        with open(existing_variants_path, 'w') as f:
                            json.dump({"variants": existing_variants}, f, indent=2)
                        st.info(f"💾 Saved {len(existing_variants)} existing variants to job folder")
                    
                    # Save all prediction results in one JSON file (all models integrated)
                    results_dir = get_user_query_results_dir(config, gene_symbol, job_name)
                    results_dir.mkdir(parents=True, exist_ok=True)
                    results_file = results_dir / "prediction_results.json"
                    with open(results_file, 'w') as f:
                        json.dump(prediction_result, f, indent=2)
                    st.info(f"💾 Saved all prediction results to: {results_file.name}")
                    
                    # TODO: Process and save processed results (CSV format)
                    # This would use json_to_df functions to convert to DataFrame
                    # and save to processed_dir
                    
                    st.success("✓ Variants processed successfully!")
                    st.info("💾 Raw results saved to results directory. Processed results (CSV) can be generated separately.")
                    
                    # Show summary
                    variants_count = prediction_result.get('variants_count', 0)
                    failed_count = prediction_result.get('failed', {}).get('results_count', 0)
                    new_count = variants_count - len(existing_variants) - failed_count
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Variants", variants_count)
                    with col2:
                        st.metric("Existing Variants", len(existing_variants))
                    with col3:
                        st.metric("New Variants", new_count)
                    
                    if failed_count > 0:
                        st.warning(f"⚠ {failed_count} variants failed processing")
                    
                    model_names = prediction_result.get('model_name', [])
                    if model_names:
                        st.info(f"Processed with models: {', '.join(model_names)}")
                    
                    # Force rerun to update tabs
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing variants: {e}")
                    st.exception(e)


if __name__ == "__main__":
    main()


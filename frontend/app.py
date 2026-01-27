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
import time

# Add parent directories to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load user settings
from frontend.configs.user_settings_manager import get_settings_manager

# Initialize settings manager
settings_manager = get_settings_manager()
API_BASE_URL = settings_manager.get_api_address()

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

# Import display modules
from frontend.tags.display_training_variants import (
    render_get_training_variants_button,
    load_or_fetch_metadata as load_or_fetch_metadata_from_page
)
from frontend.tags.display_prediction_results import display_prediction_results
from frontend.tags.display_embedding_plots import display_embedding_plots

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
    Wrapper function that calls the modularized version.
    
    Args:
        gene_symbol: Gene symbol
        
    Returns:
        Metadata dictionary or None if error
    """
    return load_or_fetch_metadata_from_page(
        gene_symbol=gene_symbol,
        config=config,
        get_metadata_gene_func=get_metadata_gene,
        get_user_training_metadata_dir_func=get_user_training_metadata_dir
    )



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
        
        # Process each model
        for model_name in model_names:
            if model_name not in variant_data:
                # Model not available for this variant
                row[f'confidence_score_{model_name}'] = None
                row[f'pred_result_{model_name}'] = None
                row[f'top_similar_variants_{model_name}'] = ''
                continue
            
            model_result = variant_data[model_name]
            
            # Check for errors
            if 'error' in model_result:
                row[f'confidence_score_{model_name}'] = None
                row[f'pred_result_{model_name}'] = f"Error: {model_result['error']}"
                row[f'top_similar_variants_{model_name}'] = ''
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
            
            # Extract and format nearest training variants for this model only
            nearest_variants = model_result.get('nearest_training_variants', [])
            similar_variants_list = []
            
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
                    similar_variants_list.append(formatted_str)
            
            # Add top similar variants as comma-separated string for this model
            row[f'top_similar_variants_{model_name}'] = ', '.join(similar_variants_list)
        
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
            # Hide variant_id and variant_hash columns for display
            display_columns = [col for col in variants_df.columns if col not in ['variant_id', 'variant_hash']]
            st.dataframe(variants_df[display_columns], use_container_width=True, height=400)
            
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


@st.dialog("⚙️ Configuration Settings")
def show_config_dialog():
    """Show configuration dialog for user settings."""
    st.write("Configure application settings below:")
    
    # Get current settings
    current_settings = settings_manager.get_settings()
    
    # API Address
    api_address = st.text_input(
        "API Address",
        value=current_settings.api_address,
        help="Base URL for the API server (e.g., http://localhost:8000)"
    )
    
    # Data Folder Name
    data_folder_name = st.text_input(
        "Data Folder Name",
        value=current_settings.data_folder_name,
        help="Name of the folder where data is stored (relative to project root)"
    )
    
    # Show current data folder path
    st.info(f"📁 Data folder path: `{settings_manager.get_data_folder_path()}`")
    
    # Config file location
    with st.expander("ℹ️ Configuration Details"):
        st.text(f"Config file location:\n{settings_manager.get_config_file_location()}")
        st.caption("Settings are saved automatically when you click 'Save Settings'")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 Save Settings", use_container_width=True, type="primary"):
            # Update settings
            settings_manager.update_settings(
                api_address=api_address,
                data_folder_name=data_folder_name
            )
            
            # Update global API_BASE_URL
            global API_BASE_URL
            API_BASE_URL = api_address
            
            st.success("✅ Settings saved successfully!")
            st.info("Please refresh the page if you changed the API address.")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            settings_manager.reset_to_defaults()
            st.success("✅ Settings reset to defaults!")
            time.sleep(1)
            st.rerun()
    
    with col3:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()


def main():
    """Main Streamlit app."""
    st.title("🧬 Variant Processing Dashboard")
    
    # Check API connection
    if not check_api_connection():
        st.error(f"❌ Cannot connect to API at {API_BASE_URL}")
        st.info("Please start the API server first or check your configuration:\n```bash\nuvicorn backend.API.main:app --reload --host 0.0.0.0 --port 8000\n```")
        return
    
    st.success(f"✓ Connected to API at {API_BASE_URL}")
    
    # Sidebar for parameters
    with st.sidebar:
        # Configuration button at the top
        if st.button("⚙️ Configuration", use_container_width=True, help="Open Configuration Settings"):
            show_config_dialog()
        
        st.divider()
        
        st.header("⚙️ Parameters")
        
        # Gene selection
        gene_names = get_gene_names(config)
        gene_symbol = st.selectbox("Gene Symbol", gene_names, index=0 if gene_names else None)
        
        # Get Training Variants button (placed right after gene selection)
        # Note: Rendering only, handling is done later in the main content area
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
        tabs = []
        tab_idx = 0
    
    # Preview Input Data tab
    if st.session_state.variants_df is not None and tab_idx < len(tabs):
        with tabs[tab_idx]:
            st.header("Input Variants Preview")
            st.dataframe(st.session_state.variants_df, use_container_width=True)
            st.info(f"Total variants: {len(st.session_state.variants_df)}")
        tab_idx += 1
        
        # Existing vs New Variants tab
        if tab_idx < len(tabs):
            with tabs[tab_idx]:
                if st.session_state.prediction_results:
                    display_prediction_results(
                        prediction_results=st.session_state.prediction_results,
                        training_metadata=st.session_state.metadata_results,
                        gene_symbol=gene_symbol,
                        job_name=job_name,
                        prediction_results_to_df_func=prediction_results_to_df,
                        config=config,
                        get_user_training_metadata_dir_func=get_user_training_metadata_dir
                    )
                else:
                    st.info("Process variants first to see prediction results")
            tab_idx += 1
        
        # Embedding Plots tab
        if tab_idx < len(tabs):
            with tabs[tab_idx]:
                display_embedding_plots(
                    prediction_results=st.session_state.prediction_results,
                    gene_symbol=gene_symbol,
                    config=config,
                    get_user_training_metadata_dir_func=get_user_training_metadata_dir
                )
            tab_idx += 1
    
    # Training Variants tab
    if st.session_state.metadata_results is not None and tab_idx < len(tabs):
        with tabs[tab_idx]:
            _display_training_variants(st.session_state.metadata_results)
    
    if not tabs_list:
        st.info("👈 Please upload or enter variants in the sidebar, or click 'Get Training Variants' to get started")
    
    # Handle Get Training Variants button click
    # Using modularized function from frontend.tags.display_training_variants
    if get_metadata_btn:
        from frontend.tags.display_training_variants import handle_get_training_variants_button
        handle_get_training_variants_button(
            gene_symbol=gene_symbol,
            config=config,
            get_metadata_gene_func=get_metadata_gene,
            get_user_training_metadata_dir_func=get_user_training_metadata_dir
        )
    
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
                    
                    # Get existing variants from API response
                    existing_variants = prediction_result.get('existing_variants', [])
                    
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


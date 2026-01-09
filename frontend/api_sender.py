#!/usr/bin/env python3
"""
Test script for the Variant Data Generation API.
Loads test data and sends requests to all endpoints.
"""

import os
import sys
import pandas as pd
import requests
import json
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add parent directories to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load environment variables
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Load configuration
from frontend.configs.config_loader import (
    load_config, get_gene_names, get_annotation_method_names, 
    get_embedding_models, get_user_query_inputs_dir, 
    get_user_query_results_dir, get_user_query_processed_dir
)

# Load config
CONFIG_PATH = Path(__file__).parent / "configs" / "frontend_config.toml"
config = load_config(str(CONFIG_PATH))



def print_separator(title: str = ""):
    """Print a separator line with optional title."""
    print(f"\n{'='*60}")
    if title:
        print(title)
        print(f"{'='*60}")


def make_api_request(endpoint: str, payload: dict, description: str) -> dict:
    """
    Generic function to make API requests with consistent error handling.
    
    Args:
        endpoint: API endpoint (without base URL)
        payload: Request payload
        description: Description for logging
    
    Returns:
        Response JSON
    """
    url = f"{API_BASE_URL}/{endpoint}"
    print_separator(f"Sending request: {description}")
    print(f"URL: {url}")
    print(f"Payload keys: {list(payload.keys())}")
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    result = response.json()
    print(f"\n✓ {description} completed")
    return result


def handle_request_error(e: Exception, context: str):
    """Handle request errors consistently."""
    if isinstance(e, requests.exceptions.HTTPError):
        print(f"\n✗ Error {context}: {e}")
        if e.response is not None:
            print(f"  Response: {e.response.text}")
    else:
        print(f"\n✗ Unexpected error {context}: {e}")
        traceback.print_exc()


def load_test_data(file_path: str) -> pd.DataFrame:
    """
    Load test variant data from CSV file.
    Only loads required columns: chromosome, position, ref_allele, alt_allele, hgvs_genomic_38
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        DataFrame with variant data containing only required columns
    
    Raises:
        ValueError: If any required column is missing
    """
    # Required columns for variant data
    required_columns = ['chromosome', 'position', 'ref_allele', 'alt_allele', 'hgvs_genomic_38']
    
    # Read CSV file
    df = pd.read_csv(file_path, dtype=str)
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns in {file_path}: {missing_columns}. "
            f"Found columns: {list(df.columns)}"
        )
    
    # Only load required columns, ignoring others
    df = df[required_columns].copy()
    
    # Drop rows where any required column has NaN values
    initial_count = len(df)
    df = df.dropna(subset=required_columns)
    dropped_count = initial_count - len(df)
    
    if dropped_count > 0:
        print(f"Warning: Dropped {dropped_count} row(s) with NaN values in required columns")
    
    print(f"Loaded {len(df)} variants from {file_path}")
    print(f"Required columns found: {required_columns}")
    print(f"\nFirst few rows:")
    print(df.head())
    return df


def dataframe_to_api_format(df: pd.DataFrame) -> list:
    """
    Convert DataFrame to list of dictionaries for API request.
    
    Args:
        df: DataFrame with variant data
    
    Returns:
        List of variant dictionaries
    """
    return df.to_dict(orient='records')


def get_prediction_results(gene_symbol: str, variants: list, 
annotation_method: str = "vep",
embedding_models: list = ["all-mpnet-base-v2"],
same_severe_consequence: bool = False) -> dict:
    """Send request to get prediction results endpoint for multiple embedding models."""
    payload = {
        "gene_symbol": gene_symbol,
        "variants": variants,
        "annotation_method": annotation_method,
        "embedding_models": embedding_models,
        "same_severe_consequence": same_severe_consequence
    }
    result = make_api_request("get-prediction-results", payload,
                             f"Getting prediction results (Gene: {gene_symbol}, Variants: {len(variants)}, Models: {len(embedding_models)})")
    
    # Print summary
    existing_count = len(result.get('existing_variants', []))
    variants_count = result.get('variants_count', 0)
    failed_count = result.get('failed', {}).get('results_count', 0)
    new_count = variants_count - existing_count - failed_count
    
    print(f"  Total variants: {variants_count}")
    print(f"  Existing variants: {existing_count}")
    print(f"  New variants processed: {new_count}")
    if failed_count > 0:
        print(f"  Failed variants: {failed_count}")
    
    return result


def get_all_training_variant_ids(prediction_response: Dict[str, Any]) -> List[str]:
    """
    Extract all training variant IDs from prediction results and remove duplicates.
    
    Args:
        prediction_response: Prediction response dictionary with 'prediction_results' key
        containing all model results integrated by variant_id
    
    Returns:
        List of unique training variant IDs across all models
    """
    all_variant_ids = []
    # Extract from prediction_results (all models integrated)
    prediction_results = prediction_response.get('prediction_results', {})
    model_names = prediction_response.get('model_name', [])
    
    for variant_id, variant_data in prediction_results.items():
        # Iterate through all models for this variant
        for model_name in model_names:
            if model_name in variant_data:
                model_result = variant_data[model_name]
                if 'error' not in model_result and 'nearest_training_variants' in model_result:
                    for neighbor in model_result['nearest_training_variants']:
                        if 'variant_id' in neighbor:
                            all_variant_ids.append(neighbor['variant_id'])
    
    # Remove duplicates while preserving order
    unique_variant_ids = list(dict.fromkeys(all_variant_ids))
    return unique_variant_ids


def get_annotations_by_variant_ids(variant_ids: list, annotation_method: str = "vep") -> dict:
    """Send request to get annotations by variant IDs endpoint."""
    payload = {"variant_ids": variant_ids, "annotation_method": annotation_method}
    result = make_api_request("get-annotations-by-variant-ids", payload,
                             f"Getting annotations ({len(variant_ids)} variants, method: {annotation_method})")
    return result


def get_metadata_gene(gene_symbol: str) -> dict:
    """
    Get metadata for all training variants in a gene.
    
    Args:
        gene_symbol: Gene symbol (e.g., "BRCA1", "FBN1")
    
    Returns:
        Dictionary with metadata results
    """
    payload = {"gene_symbol": gene_symbol}
    result = make_api_request("get-metadata-gene", payload,
                             f"Getting metadata for all variants in {gene_symbol}")
    return result


def save_results(model_name: str, annotation_method: str, results: dict, gene_symbol: str, job_name: str, 
                 file_name: str, is_raw: bool = True):
    """
    Save results to JSON files using config paths.
    
    Args:
        model_name: Model name
        annotation_method: Annotation method
        results: Results to save
        gene_symbol: Gene symbol
        job_name: Job name
        file_name: File name (without extension)
        is_raw: If True, save to results_dir (raw), else save to processed_dir
    """
    if is_raw:
        output_path = get_user_query_results_dir(config, gene_symbol, job_name) / f"{model_name}_{annotation_method}"
    else:
        output_path = get_user_query_processed_dir(config, gene_symbol, job_name) / f"{model_name}_{annotation_method}"
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    result_file = output_path / f"{file_name}.json"
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved results to: {result_file}")


def main():
    """Main test function"""
    print_separator("Variant Data Generation API Test Script")
    
    # Check if API is running
    try:
        requests.get(f"{API_BASE_URL}/docs", timeout=2)
        print(f"✓ API is running at {API_BASE_URL}")
    except requests.exceptions.ConnectionError:
        print(f"✗ ERROR: Cannot connect to API at {API_BASE_URL}")
        print("  Please start the API server first:")
        print("  uvicorn backend.API.main:app --reload --host 0.0.0.0 --port 8000")
        return
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return
    
    # Load test data
    print_separator("Loading test data...")
    gene_symbol = "FBN1"
    job_name = "test"
    annotation_method = "vep"
    embedding_models = get_embedding_models(config)
    
    # Use config to get input path
    input_dir = get_user_query_inputs_dir(config, gene_symbol, job_name)
    TEST_DATA_PATH = input_dir / f"{gene_symbol}_test.csv"

    test_df = load_test_data(TEST_DATA_PATH)
    variants_list = dataframe_to_api_format(test_df)

    # Request: Get prediction results for all embedding models in a single call
    # Existence checking is now integrated into the prediction endpoint
    # Variant-level caching allows reusing individual variants across requests
    print_separator("Getting prediction results for multiple embedding models (single API call)...")
    print("Note: Variant-level caching will reuse individual variants if they were processed in previous requests")
    
    # Common output path for saving results (using config)
    common_output_path = get_user_query_results_dir(config, gene_symbol, job_name)
    common_output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Single API call for all models
        # This will process variants and cache them at both request-level and variant-level
        import time
        start_time = time.time()
        
        prediction_result = get_prediction_results(
            gene_symbol, 
            variants_list, 
            annotation_method=annotation_method,
            embedding_models=embedding_models,
            same_severe_consequence=False
        )
        
        first_request_time = time.time() - start_time
        print(f"\n⏱ First request completed in {first_request_time:.2f} seconds")
        
        # Extract training variant IDs across all models
        all_training_variant_ids = get_all_training_variant_ids(prediction_result)
        print(f"Total unique training variant IDs across all models: {len(all_training_variant_ids)}")
        
        # Get existing variants directly from API response
        existing_variants = prediction_result.get('existing_variants', [])
        
        # Save existing variants once at job level
        if existing_variants:
            existing_variants_path = common_output_path / "existing_variants.json"
            with open(existing_variants_path, 'w') as f:
                json.dump({"variants": existing_variants}, f, indent=2)
            print(f"✓ Saved {len(existing_variants)} existing variants to: {existing_variants_path}")
        
        # Save all prediction results in one JSON file (all models integrated)
        prediction_results = prediction_result.get('prediction_results', {})
        if prediction_results:
            # Save to a common file for all models
            results_file = common_output_path / "prediction_results.json"
            with open(results_file, 'w') as f:
                json.dump(prediction_result, f, indent=2)
            print(f"✓ Saved all prediction results to: {results_file}")
        
        # Test variant-level caching: Make a second request with overlapping variants
        # This demonstrates that individual variants are reused from cache

    except Exception as e:
        handle_request_error(e, "getting prediction results")
        return
    
    # Request: Get annotations for training variants (done once, not per model)
    print_separator("Getting annotations for training variants (once per job)...")
    
    if all_training_variant_ids:
        try:
            annotations_result = get_annotations_by_variant_ids(all_training_variant_ids, annotation_method=annotation_method)
            
            # Save annotations (model-independent, save to common location)
            annotations_file = common_output_path / "annotations.json"
            with open(annotations_file, 'w') as f:
                json.dump(annotations_result, f, indent=2)
            print(f"✓ Saved annotations to: {annotations_file}")
        except Exception as e:
            handle_request_error(e, "getting annotations")
            print("⚠ Continuing despite annotation fetch error...")
    else:
        print("No training variant IDs to fetch annotations for.")
    
    print_separator("Test completed successfully!")

if __name__ == "__main__":
    main()


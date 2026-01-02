#!/usr/bin/env python3
"""
Script to convert existing variants JSON file to pandas DataFrame.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Optional
import sys
import os

# Add project root to path for importing clinvar_fetcher
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


from tools.clinical_db_fetcher.clients.clinvar_fetcher import (
    search_clinvar_by_hgvs_g,
    fetch_clinvar_details_by_id,
)


def load_existing_variants(gene_symbol: str,
                           model_name: str,
                           annotation_method: str) -> pd.DataFrame:
    """
    Load existing variants by merging variant IDs from existing_variants.json
    with full variant data from metadata.json.
    
    Args:
        gene_symbol: Gene symbol (e.g., 'FBN1')
        model_name: Embedding model name (e.g., 'all-mpnet-base-v2')
        annotation_method: Annotation method (e.g., 'vep')
        
    Returns:
        DataFrame with existing variant data
    """
    # Construct file paths
    existing_variants_path = os.path.join(
        project_root, "data_user", "user_query", "results", 
        gene_symbol, f"{model_name}_{annotation_method}", "existing_variants.json"
    )
    metadata_path = os.path.join(
        project_root, "data_user", "training_embedding_results", 
        "metadata", gene_symbol, "metadata.json"
    )
    
    # Check if files exist
    if not os.path.exists(existing_variants_path) or not os.path.exists(metadata_path):
        return pd.DataFrame()
    
    try:
        # Load existing variant IDs
        with open(existing_variants_path, 'r') as f:
            existing_variant_ids = set(json.load(f).get('variants', []))
        
        if not existing_variant_ids:
            return pd.DataFrame()
        
        # Load metadata variants
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Get variants from metadata (check both 'variants' and 'query_variant' keys)
        metadata_variants = metadata.get('variants') or metadata.get('query_variant', [])
        
        # Filter to only include existing variants
        filtered_variants = [
            v for v in metadata_variants 
            if v.get('variant_id') in existing_variant_ids
        ]
        
        df_existing = pd.DataFrame(filtered_variants)
        print(f"Loaded {len(df_existing)} existing variants from {len(existing_variant_ids)} variant IDs")
        return df_existing
        
    except Exception as e:
        print(f"Error loading existing variants: {e}")
        return pd.DataFrame()


def json_to_df(json_file_path: str, 
field_to_convert: str = 'variants',
drop_columns: Optional[list] = None) -> pd.DataFrame:
    """
    Convert existing variants JSON file to pandas DataFrame.
    
    Args:
        json_file_path: Path to the JSON file containing existing variants
        drop_columns: Optional list of column names to drop after conversion
        
    Returns:
        DataFrame with one row per variant
    """
    # Read JSON file
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Extract variants list
    variants = data.get(field_to_convert, [])
    
    if not variants:
        print(f"Warning: No variants found in {json_file_path}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(variants)
    
    # Add gene_symbol and count as columns if not already present
    if 'gene_symbol' in data and 'gene_symbol' not in df.columns:
        df['gene_symbol'] = data['gene_symbol']
    
    # Drop specified columns if they exist
    if drop_columns:
        columns_to_drop = [col for col in drop_columns if col in df.columns]
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
            print(f"Dropped columns: {columns_to_drop}")
    
    print(f"Successfully converted {len(df)} variants to DataFrame")
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    return df


def parse_prediction_results(json_file_path: str, 
                             df_all_training_variants: pd.DataFrame,
                             k: Optional[int] = None,
                             model_name: Optional[str] = None) -> pd.DataFrame:
    """
    Parse prediction_results.json and generate a DataFrame with specified columns.
    
    Args:
        json_file_path: Path to the prediction_results.json file
        df_all_training_variants: DataFrame containing all training variants with 
                                  variant_id and hgvs_genomic_38 columns
        k: Optional k value to select specific prediction result and top k neighbors.
           If provided, uses prediction_result[str(k)] for pred_result and confidence_score,
           and selects top k neighbors from nearest_training_variants.
           If None, uses the first available k value or falls back to old structure.
        model_name: Optional model name to include in column names (e.g., 'all-mpnet-base-v2').
                    If provided, confidence_score column will be named 'confidence_score {model_name}'.
        
    Returns:
        DataFrame with columns: vcf_string, chromosome, position, ref_allele, 
        alt_allele, gene_symbol, hgvs_coding, hgvs_genomic_38, protein_change, 
        most_severe_consequence, confidence_score, pred_result, top_similar_variants
    """
    # Read JSON file
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Handle new structure with "successful" wrapper
    if 'successful' in data:
        results = data['successful'].get('results', [])
    else:
        # Fall back to old structure
        results = data.get('results', [])
    
    if not results:
        print(f"Warning: No results found in {json_file_path}")
        return pd.DataFrame()
    
    # Create a mapping from variant_id to hgvs_genomic_38 from training variants
    # Check if variant_id column exists in df_all_training_variants
    if 'variant_id' not in df_all_training_variants.columns:
        raise ValueError("df_all_training_variants must contain 'variant_id' column")
    if 'hgvs_genomic_38' not in df_all_training_variants.columns:
        raise ValueError("df_all_training_variants must contain 'hgvs_genomic_38' column")
    
    # Create variant_id to hgvs_genomic_38 mapping
    variant_id_to_hgvs = dict(zip(
        df_all_training_variants['variant_id'], 
        df_all_training_variants['hgvs_genomic_38']
    ))
    
    # Parse each result
    parsed_results = []
    for result in results:
        metadata = result.get('metadata', {})
        
        # Extract nearest_training_variants
        nearest_variants = result.get('nearest_training_variants', [])
        
        # If k is specified, select top k neighbors
        if k is not None:
            nearest_variants = nearest_variants[:k]
        
        # Extract variant_ids from nearest_training_variants
        variant_ids = [nv.get('variant_id') for nv in nearest_variants if 'variant_id' in nv]
        
        # Map variant_ids to hgvs_genomic_38 annotations
        top_similar_variants = [
            variant_id_to_hgvs.get(vid) 
            for vid in variant_ids 
            if vid in variant_id_to_hgvs and pd.notna(variant_id_to_hgvs.get(vid))
        ]
        
        # Get prediction result and confidence score
        # Handle new structure with prediction_result dictionary
        prediction_result = result.get('prediction_result', {})
        if prediction_result and isinstance(prediction_result, dict):
            # If k is specified, use the corresponding k value
            if k is not None:
                k_str = str(k)
                if k_str in prediction_result:
                    pred_result = prediction_result[k_str].get('pred_result', '')
                    confidence_score = prediction_result[k_str].get('confidence_score', '')
                else:
                    print(f"Warning: k={k} not found in prediction_result, using first available")
                    # Use first available k value
                    first_k = list(prediction_result.keys())[0] if prediction_result else None
                    if first_k:
                        pred_result = prediction_result[first_k].get('pred_result', '')
                        confidence_score = prediction_result[first_k].get('confidence_score', '')
                    else:
                        pred_result = ''
                        confidence_score = ''
            else:
                # Use first available k value if k not specified
                first_k = list(prediction_result.keys())[0] if prediction_result else None
                if first_k:
                    pred_result = prediction_result[first_k].get('pred_result', '')
                    confidence_score = prediction_result[first_k].get('confidence_score', '')
                else:
                    pred_result = ''
                    confidence_score = ''
        else:
            # Fall back to old structure (direct fields)
            pred_result = result.get('pred_result', '')
            confidence_score = result.get('confidence_score', '')
        
        # Build the row data
        # Determine column names based on model_name
        confidence_col = f'confidence_score {model_name}' if model_name else 'confidence_score'
        pred_result_col = f'pred_result {model_name}' if model_name else 'pred_result'
        similar_variants_col = f'top_similar_variants {model_name}' if model_name else 'top_similar_variants'
        
        row = {
            # 'vcf_string': metadata.get('vcf_string', ''),
            'chromosome': metadata.get('chromosome', ''),
            'position': metadata.get('position', ''),
            'ref_allele': metadata.get('ref_allele', ''),
            'alt_allele': metadata.get('alt_allele', ''),
            'gene_symbol': metadata.get('gene_symbol', ''),
            'hgvs_coding': metadata.get('hgvs_coding', ''),
            'hgvs_genomic_38': metadata.get('hgvs_genomic_38', ''),
            'protein_change': metadata.get('protein_change', ''),
            'most_severe_consequence': metadata.get('most_severe_consequence', ''),
            confidence_col: confidence_score,
            pred_result_col: pred_result,
            similar_variants_col: top_similar_variants  # List of hgvs_genomic_38
        }
        parsed_results.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(parsed_results)
    
    k_info = f" (k={k})" if k is not None else ""
    print(f"Successfully parsed {len(df)} prediction results{k_info}")
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    return df


def add_clinvar_data(hgvs_genomic_38_list: list) -> pd.DataFrame:
    """
    Query ClinVar data for a list of hgvs_genomic_38 values and return a DataFrame.
    
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
    
    # Initialize result list
    results = []
    
    print(f"Querying ClinVar for {len(unique_hgvs)} variants...")
    
    # Process each hgvs_genomic_38 value
    for idx, hgvs_g in enumerate(unique_hgvs):
        try:
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
            print(f"Error querying ClinVar for {hgvs_g}: {e}")
            results.append({
                'hgvs_genomic_38': hgvs_g,
                'clinvar_id': None,
                'clinvar_url': None,
                'germline_classification': None
            })
        
        # Print progress every 10 variants
        if (idx + 1) % 10 == 0:
            print(f"Processed {idx + 1}/{len(unique_hgvs)} variants...")
    
    # Create DataFrame
    df_result = pd.DataFrame(results)
    
    found_count = df_result['clinvar_id'].notna().sum() if len(df_result) > 0 else 0
    print(f"Completed ClinVar queries. Found {found_count} variants with ClinVar IDs.")
    
    return df_result


def save_df_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"DataFrame saved to {output_path}")


if __name__ == "__main__":
    # Parse metadata.json to get all training variants
    # Note: Metadata has been moved to data_user/training_embedding_results/metadata/{gene_symbol}/metadata.json
    gene_symbols = [
                # "BRCA2", 
                # "BRCA1", 
                # "ATM",
                # "PALB2", 
                "FBN1" 
                ]
    embedding_model_names = [
        "all-mpnet-base-v2", 
        "google-embedding",
        "MedEmbed-large-v0.1"
    ]
    # vep_annotation_method = [
    #     "vep"
    # ]
    annotation_method = "vep"
    k_value = 5  # Select k=5 for prediction results
    job_name = "query_2"
    append_existing_variants = False
    check_clinvar = True
    load_test_data_metadata = True
    
    for gene_symbol in gene_symbols:

        # Load training variants from metadata.json
        metadata_path = f"data_user/training_embedding_results/metadata/{gene_symbol}/metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        metadata_variants = metadata.get('variants')
        df_training_variants = pd.DataFrame(metadata_variants)

        # Load existing variants from existing_variants.json
        existing_variants_path = f"data_user/user_query/results/{gene_symbol}/{job_name}/{embedding_model_names[0]}_{annotation_method}/existing_variants.json"
        with open(existing_variants_path, 'r') as f:
            existing_variants = json.load(f)
        existing_variant_ids = set(existing_variants.get('variants', []))
        df_existing_variants = df_training_variants[df_training_variants['variant_id'].isin(existing_variant_ids)]

        df_fininalized_results = pd.DataFrame()
        # Initialize list of sets to accumulate formatted variant strings across models (one set per result)
        top_similar_variants_sets = None
        
        # Create mapping from variant_id to (hgvs_genomic_38, pathogenicity_original) from training variants
        variant_id_to_info = {}
        for _, row in df_training_variants.iterrows():
            variant_id = row.get('variant_id')
            if variant_id:
                hgvs_genomic_38 = row.get('hgvs_genomic_38', '')
                pathogenicity = row.get('pathogenicity_original', 'unknown')
                variant_id_to_info[variant_id] = (hgvs_genomic_38, pathogenicity)
            
        for model_name in embedding_model_names:
            
            print(f"\n--- Processing model: {model_name} ---")
            
            # Parse prediction_results.json with k parameter
            # Try both k-specific and general prediction_results.json
            prediction_results_path = f"data_user/user_query/results/{gene_symbol}/{job_name}/{model_name}_{annotation_method}/prediction_results.json"
            
            if load_test_data_metadata:
                prediction_results = json.load(open(prediction_results_path, 'r'))
                results = prediction_results['successful'].get('results', [])
                df_fininalized_results["variant_id"] = [result['variant_id'] for result in results]                
                df_fininalized_results["chromosome"] = [result['metadata']['chromosome'] for result in results]
                df_fininalized_results["position"] = [result['metadata']['position'] for result in results]
                df_fininalized_results["ref_allele"] = [result['metadata']['ref_allele'] for result in results]
                df_fininalized_results["alt_allele"] = [result['metadata']['alt_allele'] for result in results]
                df_fininalized_results["gene_symbol"] = [result['metadata']['gene_symbol'] for result in results]
                df_fininalized_results["hgvs_coding"] = [result['metadata']['hgvs_coding'] for result in results]
                df_fininalized_results["hgvs_genomic_38"] = [result['metadata']['hgvs_genomic_38'] for result in results]
                df_fininalized_results["hgvs_protein"] = [result['metadata']['hgvs_protein'] for result in results]
                df_fininalized_results["most_severe_consequence"] = [result['metadata']['most_severe_consequence'] for result in results]
                if append_existing_variants:
                    df_fininalized_results["pathogenicity_original"] = "query"
                # Initialize sets for accumulating formatted variant strings across models
                top_similar_variants_sets = [set() for _ in results]
                load_test_data_metadata = False
            else:
                # Load results for current model
                prediction_results = json.load(open(prediction_results_path, 'r'))
                results = prediction_results['successful'].get('results', [])

            df_fininalized_results[f"confidence_score_{model_name}"] = [result['prediction_result'][str(k_value)]['confidence_score'] for result in results]
            df_fininalized_results[f"pred_result_{model_name}"] = [result['prediction_result'][str(k_value)]['pred_result'] for result in results]
            # Accumulate formatted variant strings from each model into sets (removes duplicates)
            for idx, result in enumerate(results):
                variant_ids = [nv['variant_id'] for nv in result['nearest_training_variants'][:k_value]]
                # Map variant_ids to formatted strings: "hgvs_genomic_38 (pathogenicity)"
                formatted_variants = []
                for vid in variant_ids:
                    if vid in variant_id_to_info:
                        hgvs_genomic_38, pathogenicity = variant_id_to_info[vid]
                        if hgvs_genomic_38:
                            formatted_str = f"{hgvs_genomic_38} ({pathogenicity})"
                        else:
                            formatted_str = f"{vid} ({pathogenicity})"  # Fallback to variant_id if hgvs_genomic_38 is missing
                    else:
                        formatted_str = f"{vid} (unknown)"  # Fallback if variant_id not found in metadata
                    formatted_variants.append(formatted_str)
                top_similar_variants_sets[idx].update(formatted_variants)
        
        # After all models are processed, convert sets to comma-separated strings
        df_fininalized_results["top_similar_variants"] = [', '.join(sorted(variant_set)) for variant_set in top_similar_variants_sets]
    save_dir = f"data_user/user_query/processed/{gene_symbol}/{job_name}/{annotation_method}"
    os.makedirs(save_dir, exist_ok=True)
    df_fininalized_results.to_csv(f"{save_dir}/prediction_results_k{k_value}.csv", index=False)
            
    # Add ClinVar data if requested (only for prediction variants, after merging existing variants)
    if check_clinvar:
        print("\nQuerying ClinVar for variant pathogenicity (prediction variants only)...")
        
        
        # Query ClinVar only for prediction variants
        if not df_fininalized_results.empty:
            # Extract list of hgvs_genomic_38 values
            hgvs_list = df_fininalized_results['hgvs_genomic_38'].dropna().unique().tolist()
            
            # Query ClinVar and get result DataFrame
            clinvar_data = add_clinvar_data(hgvs_list)
            
            # Merge back to df_fininalized_results
            df_fininalized_results = df_fininalized_results.merge(
                clinvar_data,
                on='hgvs_genomic_38',
                how='left',
                suffixes=('', '_new')
            )
            
            # Remove duplicate columns if any
            df_fininalized_results = df_fininalized_results.loc[:, ~df_fininalized_results.columns.duplicated()]
        else:
            print("  No prediction variants to query ClinVar for")
    
    # Add existing variants
    df_fininalized_results = pd.concat([df_existing_variants, df_fininalized_results], axis=0, join='outer', ignore_index=True)

    
    print(f"\nCombined results DataFrame shape: {df_fininalized_results.shape}")
    print(f"Columns: {list(df_fininalized_results.columns)}")
    print("\nCombined results DataFrame head:")
    print(df_fininalized_results.head())
    
    # print rows where the number of top variant id is not equal to 5
    print(df_fininalized_results[df_fininalized_results['top_similar_variants'].str.count(',') != 4])
    
    # Save combined results to new location

    combined_csv_path = f"data_user/user_query/processed/{gene_symbol}/{job_name}/{annotation_method}/prediction_results_k{k_value}_combined.csv"
    save_df_to_csv(df_fininalized_results, combined_csv_path)
    print(f"\n✓ Combined DataFrame saved to {combined_csv_path}")





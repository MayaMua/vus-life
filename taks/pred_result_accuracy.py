import json
import pandas as pd
from pathlib import Path
from typing import Optional
import sys
import os

# Add project root to path for importing clinvar_fetcher
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    gene_symbol = "FBN1"
                
    embedding_model_names = [
        "all-mpnet-base-v2", 
        "google-embedding",
        "MedEmbed-large-v0.1"
    ]
    annotation_method = "vep"
    k_value = 5  # Select k=5 for prediction results

    pred_result_df_path = f"data_user/user_query/processed/{gene_symbol}/{annotation_method}/prediction_results_k{k_value}_combined.csv"
    pred_result_df = pd.read_csv(pred_result_df_path)

    # Get total number of variants (all are Pathogenic according to user)
    total_variants = len(pred_result_df)
    print(f"Total variants: {total_variants}")
    print(f"All variants are Pathogenic\n")
    
    # Calculate accuracy for each model
    for model_name in embedding_model_names:
        # Get the prediction result column name
        pred_result_col = f"pred_result_{model_name}"
        
        if pred_result_col not in pred_result_df.columns:
            print(f"Model: {model_name}")
            print(f"  Error: Column '{pred_result_col}' not found in dataframe")
            print()
            continue
        
        # Count predictions that contain 'pathogenic' (case-insensitive)
        # Check if the value contains 'pathogenic' string
        pathogenic_predictions = pred_result_df[pred_result_col].str.contains('pathogenic', case=False, na=False).sum()
        
        # Calculate accuracy
        accuracy = (pathogenic_predictions / total_variants) * 100 if total_variants > 0 else 0
        
        print(f"Model: {model_name}")
        print(f"  Column: {pred_result_col}")
        print(f"  Pathogenic predictions: {pathogenic_predictions} / {total_variants}")
        print(f"  Accuracy: {accuracy:.2f}%")
        print()
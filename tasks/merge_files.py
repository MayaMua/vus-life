import pandas as pd
import sys
import os
from typing import Optional, List, Union, Dict
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


if __name__ == "__main__":
    csv_files = []
    combined_df = pd.DataFrame()
    gene_symbol = "FBN1"
    task_name = "query_2"
    gene_csv_dir = f"data_user/user_query/inputs/{gene_symbol}/{task_name}"
    if os.path.exists(gene_csv_dir):
        csv_files.extend([str(f) for f in Path(gene_csv_dir).glob("*.csv")])  

    for csv_file in csv_files:
        # Read CSV file
        # Remove files that contains 'test' in name
        base_name = Path(csv_file).stem
        if 'test' in base_name:
            continue
        df = pd.read_csv(csv_file)
        
        # Convert chromosome and position columns from float to integer if they exist
        # Use Int64 (nullable integer) to handle NaN values while converting floats to integers
        # This handles cases where CSV has values like 15.0 or 48644711.0
        for col in ['chromosome', 'position']:
            if col in df.columns:
                # First convert to float (handles string numbers), then to Int64 (nullable integer)
                # This converts 15.0 -> 15, 48644711.0 -> 48644711, NaN -> NaN
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
        
        df.dropna(subset=['hgvs_genomic_38'], inplace=True)
        combined_df = pd.concat([combined_df, df], axis=0, join='outer', ignore_index=True)
    
    combined_df.drop_duplicates(subset=['hgvs_genomic_38'], inplace=True)
    # All values are already strings since we read with dtype=str
    combined_df.to_csv(f"data_user/user_query/inputs/{gene_symbol}/{task_name}/{gene_symbol}_test.csv", index=False)
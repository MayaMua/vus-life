import pandas as pd
import numpy as np
import os 
import re
from pathlib import Path


original_folder = "data_local_raw/FBN1_phenotypes_v2"
processed_folder = "data_user/user_query/inputs/FBN1/query_1"

output_folder = 'data_user/user_query/inputs/FBN1/query_2'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


filter_col = 'HCD'
filter_keywords = ['Disulfide bonds', 'Ca2+ binding']

# Load all csv files from original_folder
csv_files = list(Path(original_folder).glob("*.csv"))
# csv_files = ["data_local_raw/FBN1_phenotypes_v2/Both Aortic Dilation and Mitral Valve Prolapse.csv"]
# Get base name of csv file

for csv_file in csv_files:
    base_name = Path(csv_file).stem
    df_original = pd.read_csv(csv_file)
    print(f"Processing {base_name}...")
    print(df_original.head())
    df_processed = pd.read_csv(os.path.join(processed_folder, f"{base_name}_processed.csv"))
    print(df_processed.head())
    # Escape special regex characters in keywords to match them literally
    escaped_keywords = [re.escape(kw) for kw in filter_keywords]
    pattern = '|'.join(escaped_keywords)
    filtered_df = df_original[df_original[filter_col].astype(str).str.contains(pattern, case=False, na=False, regex=True)]
    df_combined = df_processed.merge(filtered_df, on=['Protein nomenclature', 'cDNA Nomenclature'], how='inner')

    df_combined.to_csv(os.path.join(output_folder, f"{base_name}.csv"), index=False)

print("\n--- All Done ---")
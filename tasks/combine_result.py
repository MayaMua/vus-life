import json
import pandas as pd
from pathlib import Path
from typing import Optional
import sys
import os

def combine_result(existing_variants: pd.DataFrame, prediction_results: pd.DataFrame):
    combined_result = pd.concat([existing_variants, prediction_results], axis=0, join='outer', ignore_index=True)
    return combined_result

if __name__ == "__main__":
    gene_symbols = ["BRCA1", "BRCA2", "ATM", "PALB2"]
    combined_result_list = []
    for gene_symbol in gene_symbols:
        existing_variants_path = f"data_user/user_query/returns/{gene_symbol}/existing_variants.csv"
        prediction_results_path = f"data_user/user_query/returns/{gene_symbol}/prediction_results.csv"
        existing_variants = pd.read_csv(existing_variants_path)
        prediction_results = pd.read_csv(prediction_results_path)
        combined_result = combine_result(existing_variants, prediction_results)
        combined_result_list.append(combined_result)
    combined_result_all = pd.concat(combined_result_list, axis=0, join='outer', ignore_index=True)
    combined_result_all.to_csv("data_user/user_query/downloads/combined_result_tumor_normal.csv", index=False)
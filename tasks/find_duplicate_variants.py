import pandas as pd
import sys
import os
from typing import Optional, List, Union, Dict
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

test_variant_file = "data_user/user_query/inputs/FNB1_merged/combined_fbn1_phenotypes.csv"
training_variant_file = "data_user/training_data_processed/FBN1_variants.csv"

df_test_variants = pd.read_csv(test_variant_file)
df_training_variants = pd.read_csv(training_variant_file)

# find common variants between 2 df using chromosome,position,ref_allele,alt_allele as key
common_variants = pd.merge(df_test_variants, df_training_variants, on=['chromosome', 'position', 'ref_allele', 'alt_allele'], how='inner')
print(common_variants)

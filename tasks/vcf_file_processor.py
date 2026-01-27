#!/usr/bin/env python3
"""
Simplified VCF processor for loading and filtering variants by genes
"""

import pandas as pd
import sys
import os
from typing import Optional, List, Union, Dict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class VCF_Processor:
    """Simplified VCF processor for loading files and filtering by genes"""
    
    def __init__(self, file_paths: Union[str, List[str]]):
        """
        Initialize the VCF processor with file paths
        
        Args:
            file_paths: Single file path (str) or list of file paths
        """
        self.core_columns = ['chromosome', 'position', 'ref_allele', 'alt_allele']
        
        # Convert single file path to list
        if isinstance(file_paths, str):
            self.file_paths = [file_paths]
        else:
            self.file_paths = file_paths
        
        print(f"Initialized VCF processor with {len(self.file_paths)} file(s)")
    
    def load_vcf_file(self, vcf_path: str) -> pd.DataFrame:
        """
        Load VCF file into a pandas DataFrame
        
        Args:
            vcf_path: Path to the VCF file
            
        Returns:
            pandas.DataFrame: VCF data with proper column names
        """
        print(f"Loading VCF file: {vcf_path}")
        
        # Find the header line
        header_row_index = 0
        with open(vcf_path, 'r') as f:
            for i, line in enumerate(f):
                if line.startswith('#CHROM'):
                    header_row_index = i
                    break
        
        print(f"Header row found at line index: {header_row_index}")
        
        # Read the VCF file
        vcf_df = pd.read_csv(
            vcf_path, 
            sep='\t', 
            skiprows=header_row_index
        )
        
        # Rename columns to standard names
        column_mapping = {
            '#CHROM': 'chromosome', 
            'POS': 'position', 
            'REF': 'ref_allele', 
            'ALT': 'alt_allele', 
            'GENE_NAMES': 'gene_symbol'
        }
        vcf_df.rename(columns=column_mapping, inplace=True)
        
        # Remove 'chr' prefix from chromosome names
        vcf_df['chromosome'] = vcf_df['chromosome'].str.replace('chr', '', regex=False)
        
        print(f"Loaded {len(vcf_df)} variants from VCF file")
        return vcf_df

    
    def filter_by_gene(self, df: pd.DataFrame, gene_name: str) -> pd.DataFrame:
        """
        Filter variants by gene name
        
        Args:
            df: VCF DataFrame
            gene_name: Gene name to filter by
            
        Returns:
            pandas.DataFrame: Filtered variants
        """
        if 'gene_symbol' not in df.columns:
            print("Warning: gene_symbol column not found in DataFrame")
            return pd.DataFrame()
        
        gene_variants = df[df['gene_symbol'] == gene_name].copy()
        print(f"Found {len(gene_variants)} variants for gene: {gene_name}")
        
        return gene_variants
    
    def split_multiple_alleles(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Split rows with multiple alternative alleles into separate rows
        
        Args:
            df: DataFrame with alt_allele column that may contain comma-separated values
            
        Returns:
            pandas.DataFrame: DataFrame with each alternative allele in a separate row
        """
        if df.empty:
            return df
        
        print("Checking for multiple alternative alleles...")
        
        # Create a list to store expanded rows
        expanded_rows = []
        
        for idx, row in df.iterrows():
            alt_allele = str(row['alt_allele'])
            
            # Check if alt_allele contains multiple alleles (comma-separated)
            if ',' in alt_allele:
                # Split by comma and create separate rows for each allele
                alleles = [allele.strip() for allele in alt_allele.split(',')]
                print(f"Row {idx}: Found {len(alleles)} alternative alleles: {alleles}")
                
                for allele in alleles:
                    # Create a new row for each allele
                    new_row = row.copy()
                    new_row['alt_allele'] = allele
                    expanded_rows.append(new_row)
            else:
                # Single allele, keep as is
                expanded_rows.append(row)
        
        # Convert back to DataFrame
        expanded_df = pd.DataFrame(expanded_rows)
        
        # Reset index to avoid duplicate indices
        expanded_df = expanded_df.reset_index(drop=True)
        
        if len(expanded_df) > len(df):
            print(f"Expanded {len(df)} rows to {len(expanded_df)} rows due to multiple alleles")
        
        return expanded_df
    
    def get_variant_by_gene(self, gene_names: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Get variants for specified genes from all loaded files
        
        Args:
            gene_names: List of gene names to filter by
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary with gene names as keys and DataFrames as values
        """
        print(f"Processing {len(self.file_paths)} VCF file(s) for genes: {gene_names}")
        print("=" * 60)
        
        # Initialize result dictionary
        result = {gene: [] for gene in gene_names}
        
        # Process each file
        for i, vcf_path in enumerate(self.file_paths):
            print(f"Loading file {i+1}/{len(self.file_paths)}: {os.path.basename(vcf_path)}")
            
            try:
                # Load VCF file
                vcf_df = self.load_vcf_file(vcf_path)
                
                # Process each gene
                for gene_name in gene_names:
                    # Filter by gene
                    gene_df = self.filter_by_gene(vcf_df, gene_name)
                    
                    if not gene_df.empty:
                        # Split multiple alleles first
                        gene_df = self.split_multiple_alleles(gene_df)
                        
                        # Keep only core columns
                        gene_df = gene_df[self.core_columns]
                        result[gene_name].append(gene_df)
                        print(f"  Found {len(gene_df)} variants for {gene_name}")
                    else:
                        print(f"  No variants found for {gene_name}")
                
            except Exception as e:
                print(f"  Error loading {os.path.basename(vcf_path)}: {e}")
                continue
        
        # Combine and deduplicate for each gene
        final_result = {}
        for gene_name in gene_names:
            if result[gene_name]:
                # Combine all variants for this gene
                combined_df = pd.concat(result[gene_name], ignore_index=True)
                print(f"Total {gene_name} variants before deduplication: {len(combined_df)}")
                
                # Remove duplicates
                deduplicated_df = combined_df.drop_duplicates(
                    subset=['chromosome', 'position', 'ref_allele', 'alt_allele'],
                    keep='first'
                ).copy()
                
                removed_count = len(combined_df) - len(deduplicated_df)
                print(f"Removed {removed_count} duplicate {gene_name} variants")
                print(f"Final {gene_name} result: {len(deduplicated_df)} unique variants")
                
                final_result[gene_name] = deduplicated_df
            else:
                print(f"No variants found for {gene_name} in any files")
                final_result[gene_name] = pd.DataFrame()
        
        return final_result
    
    def get_unique_genes(self) -> List[str]:
        """
        Get list of unique genes present in all loaded VCF files
        
        Returns:
            List[str]: Sorted list of unique gene names
        """
        print("Scanning all files for unique genes...")
        print("=" * 50)
        
        all_genes = set()
        files_with_genes = 0
        
        for i, vcf_path in enumerate(self.file_paths):
            print(f"Scanning file {i+1}/{len(self.file_paths)}: {os.path.basename(vcf_path)}")
            
            try:
                # Load VCF file
                vcf_df = self.load_vcf_file(vcf_path)
                
                # Check if gene_symbol column exists
                if 'gene_symbol' in vcf_df.columns:
                    file_genes = set(vcf_df['gene_symbol'].dropna().unique())
                    all_genes.update(file_genes)
                    files_with_genes += 1
                    print(f"  Found {len(file_genes)} genes")
                else:
                    print(f"  No gene_symbol column found")
                    
            except Exception as e:
                print(f"  Error scanning {os.path.basename(vcf_path)}: {e}")
                continue
        
        unique_genes = sorted(list(all_genes))
        
        print(f"\nSummary:")
        print(f"  Files scanned: {len(self.file_paths)}")
        print(f"  Files with genes: {files_with_genes}")
        print(f"  Total unique genes: {len(unique_genes)}")
        
        if unique_genes:
            print(f"\nFirst 10 genes: {unique_genes[:10]}")
            if len(unique_genes) > 10:
                print(f"Last 10 genes: {unique_genes[-10:]}")
        
        return unique_genes




    

def main():
    """Main function to demonstrate the new VCF processing approach"""
    
    print("VCF Processing with Gene Dictionary")
    print("=" * 50)

    print("\n\n2. GETTING UNIQUE GENES")
    print("-" * 30)
    
    # Get some VCF files from directories
    from pathlib import Path
    tumor_dir = "data/input/vcf_input/TUMOR_VCFs"
    normal_dir = "data/input/vcf_input/NORMAL_VCFs"
    
    vcf_files = []
    if os.path.exists(tumor_dir):
        vcf_files.extend([str(f) for f in Path(tumor_dir).glob("*.vcf")])  
    if os.path.exists(normal_dir):
        vcf_files.extend([str(f) for f in Path(normal_dir).glob("*.vcf")]) 
    
    if vcf_files:
        # Initialize processor with multiple files
        processor = VCF_Processor(vcf_files)
        
        # Get unique genes
        unique_genes = processor.get_unique_genes()
        print(f"\nFound {len(unique_genes)} unique genes total")
        
        # Example 3: Process multiple files for specific genes
        print("\n\n3. PROCESSING MULTIPLE FILES")
        print("-" * 30)
        
        # Get variants for multiple genes
        result = processor.get_variant_by_gene(['BRCA1', 'BRCA2'])
        
        for gene, df in result.items():
            print(f"{gene}: {len(df)} variants")
            if not df.empty:
                df.to_csv(f"{gene}_test_2.csv", index=False)
    else:
        print("No VCF files found in directories")
    
    print("\n" + "=" * 50)
    print("Processing completed!")


if __name__ == "__main__":
    main()


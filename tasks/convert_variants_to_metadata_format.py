#!/usr/bin/env python3
"""
Script to convert variant JSON from flat structure to nested metadata structure.

Converts from:
[
  {
    'variant_id': '15-48408466-T-C',
    'variant_hash': '...',
    'vcf_string': '...',
    'hgvs_genomic_38': '...',
    ...
    'pathogenicity_original': 'benign_or_likely'
  }
]

To:
[
  {
    'variant_id': '15-48408466-T-C',
    'metadata': {
      'variant_hash': '...',
      'vcf_string': '...',
      'hgvs_genomic_38': '...',
      ...
    },
    'pathogenicity_original': 'benign_or_likely'
  }
]
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def convert_variant_to_metadata_format(variant: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a single variant from flat structure to nested metadata structure.
    
    Args:
        variant: Dictionary with variant data in flat format
        
    Returns:
        Dictionary with variant_id and pathogenicity_original at top level,
        and other fields nested under 'metadata'
    """
    # Fields that should stay at top level
    top_level_fields = ['variant_id', 'pathogenicity_original']
    
    # Create new structure
    converted = {}
    
    # Add top-level fields
    for field in top_level_fields:
        if field in variant:
            converted[field] = variant[field]
    
    # All other fields go into metadata
    metadata = {}
    for key, value in variant.items():
        if key not in top_level_fields:
            metadata[key] = value
    
    converted['metadata'] = metadata
    
    return converted


def convert_variants_json(input_path: str, output_path: str = None) -> List[Dict[str, Any]]:
    """
    Convert variants JSON file from flat structure to nested metadata structure.
    
    Args:
        input_path: Path to input JSON file
        output_path: Optional path to output JSON file (if None, overwrites input)
        
    Returns:
        List of converted variant dictionaries
    """
    # Read input JSON
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        # Direct list of variants
        variants = data
        gene_symbol = None
        variants_count = len(variants)
    elif isinstance(data, dict):
        # JSON with wrapper structure
        variants = data.get('variants', data.get('query_variant', []))
        gene_symbol = data.get('gene_symbol')
        variants_count = data.get('variants_count', len(variants))
    else:
        raise ValueError(f"Unexpected JSON structure in {input_path}")
    
    # Convert each variant
    converted_variants = [convert_variant_to_metadata_format(v) for v in variants]
    
    # Create output structure
    if gene_symbol:
        output_data = {
            'gene_symbol': gene_symbol,
            'variants_count': variants_count,
            'variants': converted_variants
        }
    else:
        output_data = converted_variants
    
    # Determine output path
    if output_path is None:
        output_path = input_path
    
    # Write output JSON
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✓ Converted {len(converted_variants)} variants")
    print(f"  Input: {input_path}")
    print(f"  Output: {output_path}")
    
    return converted_variants


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert variant JSON to metadata format')
    parser.add_argument('input_path', help='Path to input JSON file')
    parser.add_argument('-o', '--output', help='Path to output JSON file (default: overwrite input)')
    
    args = parser.parse_args()
    
    # Convert the file
    convert_variants_json(args.input_path, args.output)
    
    # Example: Convert metadata.json
    # python convert_variants_to_metadata_format.py data_user/training_embedding_results/metadata/FBN1/metadata.json


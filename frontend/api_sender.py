#!/usr/bin/env python3
"""
API Sender Script for Variant Analysis

This script sends the BRCA1_variants_test_all.csv file to the variant analysis API
and displays the results in the exact format returned by the server.
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, Any


def send_variants_to_api(
    csv_file_path: str,
    api_base_url: str = "http://localhost:8000",
    gene_symbol: str = "BRCA1",
    annotation_method: str = "vep",
    model_name: str = "all-mpnet-base-v2",
    n_neighbors: int = 20,
    metadata_need: bool = False
) -> Dict[str, Any]:
    """
    Send variants CSV file to the API and return the analysis results.
    
    Args:
        csv_file_path: Path to the CSV file containing variants
        api_base_url: Base URL of the API server
        gene_symbol: Gene symbol for analysis
        annotation_method: Annotation method (vep, annovar, snpeff)
        model_name: Embedding model name
        n_neighbors: Number of nearest neighbors to find
        
    Returns:
        Dictionary containing the API response
    """
    
    # Prepare the API endpoint
    endpoint = f"{api_base_url}/analyze-variants"
    
    # Prepare the file and form data
    csv_path = Path(csv_file_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    # Prepare form data
    form_data = {
        'gene_symbol': gene_symbol,
        'annotation_method': annotation_method,
        'model_name': model_name,
        'n_neighbors': n_neighbors,
        'metadata_need': metadata_need
    }
    
    # Prepare file data
    files = {
        'file': (csv_path.name, open(csv_path, 'rb'), 'text/csv')
    }
    
    print(f"🚀 Sending variants to API...")
    print(f"   File: {csv_path.name}")
    print(f"   Gene: {gene_symbol}")
    print(f"   Annotation: {annotation_method}")
    print(f"   Model: {model_name}")
    print(f"   Neighbors: {n_neighbors}")
    print(f"   Metadata needed: {metadata_need}")
    print(f"   Endpoint: {endpoint}")
    print()
    
    try:
        # Send the request
        start_time = time.time()
        response = requests.post(
            endpoint,
            data=form_data,
            files=files,
            timeout=300  # 5 minutes timeout
        )
        request_time = time.time() - start_time
        
        # Close the file
        files['file'][1].close()
        
        print(f"⏱️  Request completed in {request_time:.2f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Analysis completed successfully!")
            return result
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (5 minutes)")
        return {"error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the API server running?")
        return {"error": "Connection error - check if API server is running"}
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return {"error": str(e)}


def display_results(result: Dict[str, Any]) -> None:
    """
    Display the analysis results in a formatted way.
    
    Args:
        result: The API response dictionary
    """
    
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        return
    
    print("\n" + "="*80)
    print("📋 ANALYSIS RESULTS")
    print("="*80)
    
    # Display metadata
    if "metadata" in result:
        metadata = result["metadata"]
        print(f"\n📊 Metadata:")
        print(f"   Model: {metadata.get('model_name', 'N/A')}")
        print(f"   Annotation: {metadata.get('annotation_type', 'N/A')}")
        print(f"   Neighbors: {metadata.get('n_neighbors', 'N/A')}")
        print(f"   Total Variants: {metadata.get('total_test_variants', 'N/A')}")
        print(f"   Generated: {metadata.get('generated_at', 'N/A')}")
    
    # Display variant metadata if available
    if "variant_metadata" in result and result["variant_metadata"]:
        variant_metadata = result["variant_metadata"]
        print(f"\n📋 Variant Metadata:")
        print(f"   NEW variants with metadata: {len(variant_metadata)}")
        
        # Show sample metadata (now structured)
        if variant_metadata:
            sample_variant_id = list(variant_metadata.keys())[0]
            sample_metadata = variant_metadata[sample_variant_id]
            print(f"\n   Sample metadata for {sample_variant_id}:")
            print(f"      Consequence: {sample_metadata.get('consequence', 'N/A')}")
            print(f"      HGVS Coding: {sample_metadata.get('hgvs_coding', 'N/A')}")
            print(f"      Protein Change: {sample_metadata.get('protein_change', 'N/A')}")
            print(f"      Protein Position: {sample_metadata.get('protein_position', 'N/A')}")
            print(f"      Wild Type AA: {sample_metadata.get('wild_type_aa', 'N/A')}")
            print(f"      Mutant AA: {sample_metadata.get('mutant_aa', 'N/A')}")

    # Display results summary
    if "results" in result:
        results = result["results"]
        print(f"\n🔍 Results Summary:")
        print(f"   Variants analyzed: {len(results)}")
        
        # Show first few variants as examples
        if results:
            print(f"\n📝 Sample Results (first 3 variants):")
            variant_ids = list(results.keys())[:3]
            
            for i, variant_id in enumerate(variant_ids, 1):
                variant_data = results[variant_id]
                print(f"\n   {i}. Variant: {variant_id}")
                
                # Coordinates
                if "coordinates" in variant_data:
                    coords = variant_data["coordinates"]
                    if len(coords) >= 3:
                        print(f"      PCA: ({coords[0].get('pca_x', 'N/A'):.4f}, {coords[0].get('pca_y', 'N/A'):.4f})")
                        print(f"      t-SNE: ({coords[1].get('tsne_x', 'N/A'):.4f}, {coords[1].get('tsne_y', 'N/A'):.4f})")
                        print(f"      UMAP: ({coords[2].get('umap_x', 'N/A'):.4f}, {coords[2].get('umap_y', 'N/A'):.4f})")
                
                # Nearest neighbors
                if "nearest_training_variants" in variant_data:
                    neighbors = variant_data["nearest_training_variants"]
                    print(f"      Nearest neighbors: {len(neighbors)} found")
                    if neighbors:
                        print(f"      Top 3: {neighbors[:3]}")
                
                # Pathogenicity
                if "pathogenicity" in variant_data:
                    pathogenicity = variant_data["pathogenicity"]
                    if pathogenicity:
                        benign_count = pathogenicity.count("benign")
                        pathogenic_count = pathogenicity.count("pathogenic")
                        print(f"      Pathogenicity: {benign_count} benign, {pathogenic_count} pathogenic")
    
    print("\n" + "="*80)


def check_api_health(api_base_url: str = "http://localhost:8000") -> bool:
    """
    Check if the API server is running and healthy.
    
    Args:
        api_base_url: Base URL of the API server
        
    Returns:
        True if API is healthy, False otherwise
    """
    
    try:
        response = requests.get(f"{api_base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API is healthy: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def get_available_models(api_base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Get available models and annotation methods from the API.
    
    Args:
        api_base_url: Base URL of the API server
        
    Returns:
        Dictionary with available models and annotation methods
    """
    
    try:
        response = requests.get(f"{api_base_url}/models", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return {}


def main():
    """Main function to run the API sender."""
    
    print("🧬 Variant Analysis API Sender")
    print("="*50)
    
    # Configuration
    csv_file = "BRCA1_variants_test_all.csv"
    api_url = "http://localhost:8000"
    
    # Check if CSV file exists
    if not Path(csv_file).exists():
        print(f"❌ CSV file not found: {csv_file}")
        print("Please make sure the file exists in the current directory.")
        return
    
    # Check API health
    print("🔍 Checking API health...")
    if not check_api_health(api_url):
        print("\n💡 Make sure the API server is running:")
        print("   cd backend/API")
        print("   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Get available models
    print("\n🔍 Getting available models...")
    models_info = get_available_models(api_url)
    if models_info:
        print(f"   Available models: {models_info.get('models', [])}")
        print(f"   Available annotations: {models_info.get('annotation_methods', [])}")
    
    # Send variants for analysis
    print(f"\n🚀 Starting variant analysis...")
    result = send_variants_to_api(
        csv_file_path=csv_file,
        api_base_url=api_url,
        gene_symbol="BRCA1",
        annotation_method="vep",
        model_name="all-mpnet-base-v2",
        n_neighbors=20,
        metadata_need=True  # Test with metadata enabled
    )
    
    # Display results
    display_results(result)
    
    # Save results to file
    if "error" not in result:
        output_file = "api_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()

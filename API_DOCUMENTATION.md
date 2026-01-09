# Variant Data Generation API Documentation

## Overview

The Variant Data Generation API provides endpoints for processing genetic variants, generating predictions, and retrieving variant metadata and annotations. The API supports multiple embedding models and includes intelligent caching to optimize performance.

## Getting Started

### Starting the Server

```bash
uvicorn backend.API.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Interactive API Documentation

Once the server is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### 1. Get Prediction Results

**Endpoint**: `POST /get-prediction-results`

Get prediction results for variants including embeddings, coordinates, and nearest training variants. Processes multiple embedding models in a single request.

**Request Body**:
```json
{
  "gene_symbol": "BRCA2",
  "variants": [
    {
      "chromosome": "13",
      "position": "32316467",
      "ref_allele": "G",
      "alt_allele": "A",
      "hgvs_genomic_38": "13:g.32316467G>A"
    }
  ],
  "annotation_method": "vep",
  "embedding_models": ["all-mpnet-base-v2", "google-embedding"],
  "same_severe_consequence": false
}
```

**Request Parameters**:
- `gene_symbol` (string, required): Gene symbol (e.g., "BRCA2", "FBN1")
- `variants` (array, required): List of variant dictionaries. Each variant must contain:
  - `chromosome` (string): Chromosome number
  - `position` (string): Genomic position
  - `ref_allele` (string): Reference allele
  - `alt_allele` (string): Alternate allele
  - `hgvs_genomic_38` (string): HGVS genomic notation (GRCh38)
- `annotation_method` (string, optional): Annotation method. Default: `"vep"`. Options: `"vep"`, `"annovar"`
- `embedding_models` (array, optional): List of embedding model names. Default: `["all-mpnet-base-v2"]`. 
  Available models: `"all-mpnet-base-v2"`, `"google-embedding"`, `"MedEmbed-large-v0.1"`
- `same_severe_consequence` (boolean, optional): If `true`, filter training variants by the same most_severe_consequence. Default: `false`

**Response**:
```json
{
  "gene_symbol": "BRCA2",
  "model_name": ["all-mpnet-base-v2", "google-embedding"],
  "annotation_method": "vep",
  "same_severe_consequence": false,
  "variants_count": 1,
  "existing_variants": [],
  "prediction_results": {
    "13-32316467-G-A": {
      "metadata": {
        "vcf_string": "13:32316467:G:A",
        "chromosome": "13",
        "position": "32316467",
        "ref_allele": "G",
        "alt_allele": "A",
        "gene_symbol": "BRCA2",
        "hgvs_coding": "...",
        "hgvs_genomic_38": "13:g.32316467G>A",
        "hgvs_protein": "...",
        "most_severe_consequence": "missense_variant"
      },
      "annotation_raw": "{...}",
      "all-mpnet-base-v2": {
        "coordinates": [
          {"pca_x": 0.123, "pca_y": -0.456},
          {"t-sne_x": 1.234, "t-sne_y": 2.345},
          {"umap_x": -0.789, "umap_y": 0.321}
        ],
        "nearest_training_variants": [
          {
            "variant_id": "13-32316450-G-A",
            "distance": 0.123,
            "pathogenicity": "pathogenic"
          }
        ],
        "prediction_result": {
          "5": {
            "pred_result": "pathogenic",
            "confidence_score": 0.85
          },
          "10": {
            "pred_result": "pathogenic",
            "confidence_score": 0.82
          }
        }
      },
      "google-embedding": {
        "coordinates": [...],
        "nearest_training_variants": [...],
        "prediction_result": {...}
      }
    }
  },
  "failed": {
    "results_count": 0,
    "results": []
  }
}
```

**Response Structure**:
- `gene_symbol`: The gene symbol from the request
- `model_name`: List of embedding model names used for processing
- `annotation_method`: Annotation method used (e.g., "vep", "annovar")
- `same_severe_consequence`: Whether same_severe_consequence filtering was applied
- `variants_count`: Total number of input variants (existing + new)
- `existing_variants`: List of variant IDs that already existed in the database
- `prediction_results`: Dictionary organized by variant_id. Each variant contains:
  - `metadata`: Variant metadata (VCF string, coordinates, HGVS notations)
  - `annotation_raw`: Raw annotation data (JSON string)
  - `{model_name}`: Model-specific results containing:
    - `coordinates`: Dimension reduction coordinates (PCA, t-SNE, UMAP)
    - `nearest_training_variants`: Array of nearest training variants with distances and pathogenicity labels
    - `prediction_result`: Dictionary with predictions for different k values (5, 10, 15, 20)
    - `error` (optional): Error message if processing failed for this model
- `failed`: Object containing variants that failed processing for all models:
  - `results_count`: Number of failed variants
  - `results`: Array of failed variant objects with `variant_id`, `metadata`, and `error`

**Prediction Result Fields**:
- Each variant in `prediction_results` contains:
  - `metadata`: Variant metadata including VCF string, HGVS notations, chromosome, position, etc.
  - `annotation_raw`: Raw annotation data (JSON string)
  - `{model_name}`: Model-specific results for each embedding model:
    - `coordinates`: Array of dimension reduction coordinates:
      - `pca_x`, `pca_y`: PCA coordinates
      - `t-sne_x`, `t-sne_y`: t-SNE coordinates
      - `umap_x`, `umap_y`: UMAP coordinates
    - `nearest_training_variants`: Array of nearest training variants with:
      - `variant_id`: Training variant ID
      - `distance`: Distance metric
      - `pathogenicity`: Pathogenicity label
    - `prediction_result`: Dictionary with predictions for different k values (5, 10, 15, 20):
      - `pred_result`: Prediction class ("pathogenic", "benign", etc.)
      - `confidence_score`: Confidence score (0.0 to 1.0)
    - `error` (optional): Error message if processing failed for this model

**Example (Python)**:
```python
import requests

url = "http://localhost:8000/get-prediction-results"
payload = {
    "gene_symbol": "BRCA2",
    "variants": [
        {
            "chromosome": "13",
            "position": "32316467",
            "ref_allele": "G",
            "alt_allele": "A",
            "hgvs_genomic_38": "13:g.32316467G>A"
        }
    ],
    "annotation_method": "vep",
    "embedding_models": ["all-mpnet-base-v2", "google-embedding"],
    "same_severe_consequence": False
}

response = requests.post(url, json=payload)
result = response.json()

# Access results for a specific variant and model
variant_id = "13-32316467-G-A"
variant_result = result["prediction_results"][variant_id]
model_result = variant_result["all-mpnet-base-v2"]

# Access prediction for k=5
prediction_k5 = model_result["prediction_result"]["5"]
print(f"Prediction: {prediction_k5['pred_result']}, Confidence: {prediction_k5['confidence_score']}")

# Access existing variants
existing_count = len(result["existing_variants"])
print(f"Existing variants: {existing_count}")

# Access failed variants
failed_count = result["failed"]["results_count"]
print(f"Failed variants: {failed_count}")
```

**Example (cURL)**:
```bash
curl -X POST "http://localhost:8000/get-prediction-results" \
  -H "Content-Type: application/json" \
  -d '{
    "gene_symbol": "BRCA2",
    "variants": [
      {
        "chromosome": "13",
        "position": "32316467",
        "ref_allele": "G",
        "alt_allele": "A",
        "hgvs_genomic_38": "13:g.32316467G>A"
      }
    ],
    "embedding_models": ["all-mpnet-base-v2"]
  }'
```

---

### 2. Get Metadata by Gene

**Endpoint**: `POST /get-metadata-gene`

Get metadata for all variants stored in the database for a specific gene.

**Request Body**:
```json
{
  "gene_symbol": "BRCA2"
}
```

**Request Parameters**:
- `gene_symbol` (string, required): Gene symbol (e.g., "BRCA2", "FBN1")

**Response**:
```json
{
  "gene_symbol": "BRCA2",
  "variants_count": 1234,
  "variants": [
    {
      "variant_id": "13-32316467-G-A",
      "gene_symbol": "BRCA2",
      "chromosome": "13",
      "position": "32316467",
      "ref_allele": "G",
      "alt_allele": "A",
      "hgvs_genomic_38": "13:g.32316467G>A",
      ...
    }
  ]
}
```

**Example (Python)**:
```python
import requests

url = "http://localhost:8000/get-metadata-gene"
payload = {"gene_symbol": "BRCA2"}

response = requests.post(url, json=payload)
result = response.json()

print(f"Found {result['variants_count']} variants for {result['gene_symbol']}")
```

---

### 3. Get Annotations by Variant IDs

**Endpoint**: `POST /get-annotations-by-variant-ids`

Get annotations for specific variants by their variant IDs.

**Request Body**:
```json
{
  "variant_ids": [
    "13-32316467-G-A",
    "13-32316470-C-T"
  ],
  "annotation_method": "vep"
}
```

**Request Parameters**:
- `variant_ids` (array, required): List of variant IDs
- `annotation_method` (string, optional): Annotation method. Default: `"vep"`. Options: `"vep"`, `"annovar"`

**Response**:
```json
{
  "13-32316467-G-A": {
    "vep_raw": {...},
    "vep_processed": {...}
  },
  "13-32316470-C-T": {
    "vep_raw": {...},
    "vep_processed": {...}
  }
}
```

**Response Structure**:
- Keys are variant IDs
- Values contain:
  - `{annotation_method}_raw`: Raw annotation data
  - `{annotation_method}_processed`: Processed annotation data
- Variants not found will have empty annotation objects

**Example (Python)**:
```python
import requests

url = "http://localhost:8000/get-annotations-by-variant-ids"
payload = {
    "variant_ids": ["13-32316467-G-A", "13-32316470-C-T"],
    "annotation_method": "vep"
}

response = requests.post(url, json=payload)
annotations = response.json()

for variant_id, annotation_data in annotations.items():
    print(f"Variant {variant_id}: {annotation_data}")
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters (e.g., missing required fields, invalid variant format)
- `500 Internal Server Error`: Server-side error during processing

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

1. **Missing Required Columns**:
   ```json
   {
     "detail": "Missing required columns: ['chromosome', 'position']"
   }
   ```

2. **No Variants to Process**:
   ```json
   {
     "detail": "No new variants to process. All variants may already exist in the database."
   }
   ```

3. **Model Processing Failed**:
   The response will include an `error` field in the variant's model-specific result:
   ```json
   {
     "prediction_results": {
       "variant-id": {
         "metadata": {...},
         "model-name": {
           "error": "Model processing failed: ..."
         }
       }
     }
   }
   ```

4. **Variant Processing Failed**:
   Failed variants appear in the `failed` field:
   ```json
   {
     "failed": {
       "results_count": 1,
       "results": [
         {
           "variant_id": "13-32316467-G-A",
           "metadata": {...},
           "error": "Variant annotation not found"
         }
       ]
     }
   }
   ```

---

## Performance Optimization

### Caching

The API includes intelligent caching that:
- **Request-level caching**: Exact request matches are returned immediately
- **Variant-level caching**: Individual variants are cached and reused across different requests
  - Example: If Request 1 processes variants [A, B, C] and Request 2 processes [B, C, D], variants B and C will be reused from cache

### Best Practices

1. **Batch Processing**: Send multiple variants in a single request rather than multiple separate requests
2. **Multiple Models**: Process multiple embedding models in one request using the `embedding_models` array
3. **Reuse Variants**: If you need to process overlapping variant sets, the API will automatically reuse cached variants

---

## Example Workflow

```python
import requests

API_BASE_URL = "http://localhost:8000"

# 1. Get prediction results for multiple models
variants = [
    {
        "chromosome": "13",
        "position": "32316467",
        "ref_allele": "G",
        "alt_allele": "A",
        "hgvs_genomic_38": "13:g.32316467G>A"
    }
]

response = requests.post(
    f"{API_BASE_URL}/get-prediction-results",
    json={
        "gene_symbol": "BRCA2",
        "variants": variants,
        "embedding_models": ["all-mpnet-base-v2", "google-embedding"],
        "annotation_method": "vep"
    }
)

result = response.json()

# 2. Extract training variant IDs from results
training_variant_ids = []
model_names = result["model_name"]

for variant_id, variant_data in result["prediction_results"].items():
    for model_name in model_names:
        if model_name in variant_data:
            model_result = variant_data[model_name]
            if "error" not in model_result and "nearest_training_variants" in model_result:
                for neighbor in model_result["nearest_training_variants"]:
                    training_variant_ids.append(neighbor["variant_id"])

# Remove duplicates
training_variant_ids = list(set(training_variant_ids))

# 3. Get annotations for training variants
if training_variant_ids:
    response = requests.post(
        f"{API_BASE_URL}/get-annotations-by-variant-ids",
        json={
            "variant_ids": training_variant_ids,
            "annotation_method": "vep"
        }
    )
    annotations = response.json()
```

---

## Notes

- All endpoints use POST requests
- Request and response formats are JSON
- Variant IDs are automatically generated from chromosome, position, ref_allele, and alt_allele
- The API automatically handles existence checking and caching - no separate endpoint needed
- Annotations are processed once and reused across different embedding models for the same variant set


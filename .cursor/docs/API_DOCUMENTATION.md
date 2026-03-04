# Variant Data Generation API

Base URL (behind nginx): **`{api_url}/api`**

All endpoints are under `{api_url}/api/{endpoint}`. Replace `{api_url}` with your deployed API host (e.g. `https://your-aws-domain.com`).

---

## Response formats

- **Embedding (`POST /v1/get-embedding-results`)**: Response body is **gzip-compressed** (`Content-Encoding: gzip`). Decompress before parsing JSON (e.g. `gzip.decompress(response.content)` then `json.loads(...)`). Field names may be shortened (see `embedding_response_field_mapping.json`).
- **Metadata / annotations**: Endpoints return **presigned download URLs**. Client must **GET** each URL to download the file (e.g. `metadata.json` or per-variant annotation JSON).

---

## Endpoints

### 1. Health check

**`GET {api_url}/api/health`**

Returns service health (e.g. for monitoring).

**Response**:

```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T12:00:00.000000",
  "service": "vus-life-server"
}
```

**Example**:

```python
import requests
r = requests.get("{api_url}/api/health")
print(r.json())
```

---

### 2. Get server config

**`GET {api_url}/api/config`**

Returns gene list, embedding models, and annotation methods. No query or body.

**Response**:

```json
{
  "gene_names": ["FBN1", "BRCA1"],
  "embedding_models": [
    "all-mpnet-base-v2",
    "MedEmbed-large-v0.1",
    "gemini-embedding"
  ],
  "annotation_methods": ["vep"]
}
```

**Example**:

```python
import requests
r = requests.get("{api_url}/api/config", timeout=3)
if r.status_code == 200:
    cfg = r.json()
    gene_names = cfg["gene_names"]
    embedding_models = cfg["embedding_models"]
```

---

### 3. Get embedding results

**`POST {api_url}/api/v1/get-embedding-results`**

Runs pipeline: filter (training → production) → fetch annotations for new variants → embedding + k-NN. Response is **gzip-compressed**; decompress before parsing.

**Request body**:

```json
{
  "gene_symbol": "FBN1",
  "variants": [
    {
      "chromosome": "15",
      "position": 48487353,
      "ref_allele": "G",
      "alt_allele": "A",
      "hgvs_genomic_38": "NC_000015.10:g.48487353G>A"
    }
  ],
  "same_severe_consequence": false,
  "annotation_method": "vep",
  "embedding_models": ["all-mpnet-base-v2"]
}
```

| Field                     | Type    | Required | Description                                                                   |
| ------------------------- | ------- | -------- | ----------------------------------------------------------------------------- |
| `gene_symbol`             | string  | yes      | e.g. "FBN1", "BRCA1"                                                          |
| `variants`                | array   | yes      | Each: `chromosome`, `position`, `ref_allele`, `alt_allele`, `hgvs_genomic_38` |
| `same_severe_consequence` | boolean | no       | Default `false`                                                               |
| `annotation_method`       | string  | no       | Default `"vep"`                                                               |
| `embedding_models`        | array   | no       | Default `["all-mpnet-base-v2"]`                                               |

**Response** (after gzip decompress): `gene_symbol`, `model_name`, `annotation_method`, `same_severe_consequence`, `variants_count`, `existing_variants`, `results` (variant_id → metadata + per-model `nearest_training_variants`), `failed`, `request_time`.

**Example**:

```python
import gzip
import json
import requests

url = "{api_url}/api/v1/get-embedding-results"
payload = {
    "gene_symbol": "FBN1",
    "variants": [
        {
            "chromosome": "15",
            "position": 48487353,
            "ref_allele": "G",
            "alt_allele": "A",
            "hgvs_genomic_38": "NC_000015.10:g.48487353G>A"
        }
    ],
    "same_severe_consequence": False,
    "annotation_method": "vep",
    "embedding_models": ["all-mpnet-base-v2"],
}

resp = requests.post(url, json=payload, timeout=300, headers={"Accept-Encoding": "identity"})
resp.raise_for_status()

body = resp.content
if body[:2] == b"\x1f\x8b":
    result = json.loads(gzip.decompress(body).decode("utf-8"))
else:
    result = json.loads(body.decode("utf-8"))

print(result.get("variants_count"), result.get("results"))
```

---

### 4. Get metadata download URL

**`GET {api_url}/api/v1/download-urls/metadata`**

Returns a **presigned URL** to download metadata for a gene. Client must GET that URL to get the file.

**Query parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `gene` | string | yes | Gene symbol (e.g. "FBN1") |
| `expires_in` | int | no | URL validity in seconds; default 3600, range 60–86400 |

**Response**:

```json
{
  "url": "https://...",
  "expires_in": 3600,
  "gene_symbol": "FBN1",
  "s3_key": "vus-life/data_user/metadata/FBN1/metadata.json"
}
```

**Example**:

```python
import requests
from pathlib import Path

gene_symbol = "FBN1"
resp = requests.get(
    "{api_url}/api/v1/download-urls/metadata",
    params={"gene": gene_symbol},
    timeout=30
)
resp.raise_for_status()
data = resp.json()
url = data.get("url")
if not url:
    raise ValueError("No URL in metadata API response")

# Download from presigned URL
r = requests.get(url, timeout=60)
r.raise_for_status()

out_dir = Path("data_local/metadata") / gene_symbol
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "metadata.json").write_text(r.text, encoding="utf-8")
```

---

### 5. Get annotation download URLs

**`POST {api_url}/api/v1/download-urls/annotations`**

Returns annotation data for given variant IDs (inline `results` and presigned `urls`). Use `source` to choose training or production DB.

**Request body**:

```json
{
  "variant_ids": ["15-48487353-G-A", "15-48485397-A-G"],
  "gene_symbol": "FBN1",
  "annotation_method": "vep",
  "source": "production"
}
```

| Field               | Type   | Required | Description                    |
| ------------------- | ------ | -------- | ------------------------------ |
| `variant_ids`       | array  | yes      | List of variant IDs            |
| `gene_symbol`       | string | yes      | Gene symbol                    |
| `annotation_method` | string | no       | Default `"vep"`                |
| `source`            | string | yes      | `"training"` or `"production"` |

**Response**:

```json
{
  "gene_symbol": "FBN1",
  "annotation_method": "vep",
  "source": "production",
  "results": {
    "15-48487353-G-A": { "vep_raw": {...}, "vep_processed": {...} },
    "15-48485397-A-G": null
  },
  "urls": [
    { "variant_id": "15-48487353-G-A", "url": "https://..." }
  ]
}
```

**Example**:

```python
import requests

url = "{api_url}/api/v1/download-urls/annotations"
resp = requests.post(
    url,
    json={
        "variant_ids": ["15-48487353-G-A", "15-48485397-A-G"],
        "gene_symbol": "FBN1",
        "annotation_method": "vep",
        "source": "production",
    },
    timeout=60,
)
resp.raise_for_status()
data = resp.json()

# Use inline results or download from urls
for item in data.get("urls", []):
    vid, presigned_url = item["variant_id"], item["url"]
    r = requests.get(presigned_url, timeout=60)
    r.raise_for_status()
    # save or parse r.json() / r.text
```

---

## Example workflow

1. Call embedding API → decompress gzip → parse/save result.
2. From result, collect production and training variant IDs.
3. Get metadata: `GET {api_url}/api/v1/download-urls/metadata?gene=FBN1` → GET presigned URL → save file.
4. Get annotations: `POST {api_url}/api/v1/download-urls/annotations` with `source`: `"production"` or `"training"` → use `results` or download from `urls`.

```python
import gzip
import json
import requests
from pathlib import Path

API_BASE = "{api_url}/api"
GENE = "FBN1"

# 1. Embedding
variants = [
    {"chromosome": "15", "position": 48487353, "ref_allele": "G", "alt_allele": "A", "hgvs_genomic_38": "NC_000015.10:g.48487353G>A"},
]
resp = requests.post(
    f"{API_BASE}/v1/get-embedding-results",
    json={"gene_symbol": GENE, "variants": variants, "embedding_models": ["all-mpnet-base-v2"]},
    timeout=300,
    headers={"Accept-Encoding": "identity"},
)
resp.raise_for_status()
body = resp.content
result = json.loads(gzip.decompress(body).decode("utf-8")) if body[:2] == b"\x1f\x8b" else json.loads(body.decode("utf-8"))

# 2. Metadata
meta = requests.get(f"{API_BASE}/v1/download-urls/metadata", params={"gene": GENE}, timeout=30)
meta.raise_for_status()
meta_url = meta.json().get("url")
if meta_url:
    r = requests.get(meta_url, timeout=60)
    r.raise_for_status()
    Path("data_local/metadata").mkdir(parents=True, exist_ok=True)
    (Path("data_local/metadata") / GENE / "metadata.json").write_text(r.text, encoding="utf-8")

# 3. Annotations (production / training variant IDs from result)
prod_ids = list((result.get("results") or {}).keys())[:3]
if prod_ids:
    ann = requests.post(
        f"{API_BASE}/v1/download-urls/annotations",
        json={"variant_ids": prod_ids, "gene_symbol": GENE, "annotation_method": "vep", "source": "production"},
        timeout=60,
    )
    ann.raise_for_status()
    # ann.json() has "results" and "urls"
```

---

## Error handling

| Code | Meaning                                                                          |
| ---- | -------------------------------------------------------------------------------- |
| 200  | Success                                                                          |
| 400  | Bad request (e.g. missing `gene`, invalid `expires_in`, missing variant columns) |
| 500  | Internal server error                                                            |
| 503  | Service unavailable (e.g. training DB not found, presigned URL failed)           |

**Error body**:

```json
{
  "detail": "Error message"
}
```

- Embedding: missing required columns → `"Missing required columns: [...]"`. Failed variants appear in response `failed` (`results_count`, `results` with `variant_id`, `metadata`, `error`).
- Metadata: no `url` in response when server could not generate presigned URL (e.g. S3 not configured).

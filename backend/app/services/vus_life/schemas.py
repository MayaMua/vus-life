"""
Pydantic schemas for the VUS-Life AWS Variant Data Generation API.

Strict schemas matching API docs: EmbeddingRequest (gene_symbol + variants),
VariantItem (hgvs_genomic_38, chromosome, position, ref_allele, alt_allele),
PredictRequest (raw HGVS list from frontend), and presigned URL responses.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class VariantItem(BaseModel):
    """
    Single variant for embedding requests.

    Must validate hgvs_genomic_38, chromosome, position, ref_allele, alt_allele per API spec.
    """

    hgvs_genomic_38: str = Field(..., description="HGVS genomic (GRCh38) notation")
    chromosome: str = Field(..., description="Chromosome identifier")
    position: int = Field(..., description="Variant position (integer)")
    ref_allele: str = Field(..., description="Reference allele")
    alt_allele: str = Field(..., description="Alternate allele")


class EmbeddingRequest(BaseModel):
    """
    Request body for POST /api/get-embedding-results.

    Must include gene_symbol (str) and variants (List[VariantItem]) per API spec.
    """

    gene_symbol: str = Field(..., description="Gene symbol")
    variants: list[VariantItem] = Field(..., description="List of variants to embed")
    annotation_method: str | None = Field(
        default=None,
        description="Annotation method to use (e.g. 'vep')",
    )
    embedding_models: list[str] = Field(
        default_factory=list,
        description="Embedding models to use (e.g. ['all-mpnet-base-v2'])",
    )
    same_severe_consequence: bool = Field(
        default=False,
        description="Restrict nearest neighbours to same severe consequence",
    )


class PredictRequest(BaseModel):
    """
    Incoming request from the Electron frontend for POST /api/vus/predict.

    Contains raw HGVS genomic (GRCh38) strings; the backend converts them
    to VCF-style VariantItems via hgvs_g_to_vcf before forwarding to AWS.
    """

    gene_symbol: str = Field(..., min_length=1, description="Gene symbol (e.g. 'BRCA1')")
    hgvs_genomic_38: list[str] = Field(
        ..., min_length=1, description="List of HGVS g. strings to predict"
    )
    annotation_method: list[str] = Field(
        default_factory=list, description="Annotation methods"
    )
    embedding_models: list[str] = Field(
        default_factory=list, description="Embedding models"
    )
    same_severe_consequence: bool = Field(default=False)

    @field_validator("gene_symbol", mode="before")
    @classmethod
    def strip_gene_symbol(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v


class AwsConfigResponse(BaseModel):
    """Response from GET /api/config (gene list, embedding models, annotation methods)."""

    gene_names: list[str] = Field(default_factory=list)
    embedding_models: list[str] = Field(default_factory=list)
    annotation_methods: list[str] = Field(default_factory=list)


class PresignedUrlResponse(BaseModel):
    """Response from download-urls endpoints: contains a single S3 presigned URL."""

    url: str = Field(..., description="Presigned URL for file download")


class MetadataDownloadRequest(BaseModel):
    """Request body for POST /api/vus/metadata/download."""

    gene_symbol: str = Field(..., min_length=1, description="Gene symbol to download metadata for")

    @field_validator("gene_symbol", mode="before")
    @classmethod
    def strip_gene_symbol(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v


class AnnotationsDownloadRequest(BaseModel):
    """Request body for POST /api/download-urls/annotations."""

    gene_symbol: str = Field(..., description="Gene symbol")
    annotation_method: str | None = Field(
        default=None,
        description="Optional annotation method filter",
    )


# Embedding API returns complex JSON; results is dict keyed by variant_id.
# We do not enforce a strict shape for each result value here.
EmbeddingResultsMap = dict[str, Any]


class EmbeddingResponse(BaseModel):
    """Response from POST /api/get-embedding-results (results keyed by variant_id)."""

    results: EmbeddingResultsMap = Field(
        default_factory=dict,
        description="Embedding results keyed by variant_id",
    )

    model_config = {"extra": "allow"}

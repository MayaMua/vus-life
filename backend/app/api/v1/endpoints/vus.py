"""
VUS API endpoints.

Verify uses VUS API URL from config (config.json) and GET /api/health to validate.
Metadata: local existence check and stats (GET); download from AWS (POST).
Predict: parse HGVS strings → VCF variants → call VUS Life AWS API.
"""

import asyncio
import json
import logging
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings_manager
from app.services.variant_processor.hgvs_g_to_vcf import hgvs_g_to_vcf
from app.services.vus_life.client import VusLifeAPIError, VusLifeClient
from app.services.vus_life.schemas import (
    EmbeddingRequest,
    MetadataDownloadRequest,
    PredictRequest,
    VariantItem,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Metadata file path: general_settings.output_path / vus_results / gene_symbol / metadata.json
def _metadata_path_for_gene(gene_symbol: str) -> Path:
    manager = get_settings_manager()
    output_path = Path(manager.get().general_settings.output_path)
    return output_path / "vus_results" / gene_symbol / "metadata.json"


@router.get("/verify")
async def verify_vus_connection() -> dict:
    """
    Verify connection to the VUS API.

    Reads vus_api_settings.api_url from config (backend/configs/config.json),
    then GETs that URL's /api/health. Returns status and service name on success.
    """
    try:
        client = VusLifeClient()
        data = await client.health_check()
        return {
            "status": data.get("status", "healthy"),
            "service": data.get("service", "vus-life-server"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e) or "VUS API URL is not configured (vus_api_settings.api_url).",
        ) from e
    except VusLifeAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get("/config")
async def get_vus_config() -> dict:
    """
    Get VUS dashboard config (gene names, embedding models, annotation methods).

    Network-first: fetches from AWS API and persists to config.json on success;
    on failure returns local vus_dashboard_settings. Response includes from_cache
    so the frontend can show a stale indicator when appropriate.
    """
    client = VusLifeClient()
    return await client.get_config()


@router.get("/metadata/{gene_symbol}")
async def get_metadata(gene_symbol: str) -> dict:
    """
    Get metadata summary and preview for a gene.

    Checks existence at general_settings.output_path / vus_results / {gene_symbol} / metadata.json.
    If missing, returns 404. If exists, loads JSON, computes stats (total, pathogenicity/consequence
    distributions) and returns first 100 variants as preview_data.
    """
    path = _metadata_path_for_gene(gene_symbol)
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Metadata not found locally",
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    variants = data.get("variants") or []
    total = len(variants)
    pathogenicity_distribution = dict(Counter(v.get("pathogenicity_original") for v in variants))
    consequence_distribution = dict(Counter(v.get("most_severe_consequence") for v in variants))
    preview_data = variants[:100]
    return {
        "status": "success",
        "summary": {
            "total": total,
            "pathogenicity": pathogenicity_distribution,
            "consequence": consequence_distribution,
        },
        "preview_data": preview_data,
    }


@router.post("/metadata/download")
async def download_metadata(body: MetadataDownloadRequest) -> dict:
    """
    Download metadata for a gene from AWS (presigned URL) and save locally.

    Saves to general_settings.output_path / vus_results / {gene_symbol} / metadata.json.
    Creates parent directories if needed.
    """
    try:
        client = VusLifeClient()
        save_path = await client.download_metadata(body.gene_symbol)
        return {
            "status": "success",
            "message": f"Metadata saved for {body.gene_symbol}",
            "path": str(save_path),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except VusLifeAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post("/predict")
async def predict(body: PredictRequest) -> dict:
    """
    Run VUS embedding prediction for a list of HGVS genomic strings.

    Pipeline:
    1. Convert each HGVS g. string to VCF representation via hgvs_g_to_vcf
       (runs in threadpool to avoid blocking the event loop, since hgvs_g_to_vcf
       is synchronous and may do I/O).
    2. Skip strings that fail conversion and log them as warnings.
    3. Assemble an EmbeddingRequest and call the VUS Life AWS API.
    4. Normalise the response (alias 'results' → 'prediction_results' if needed).
    5. Return the full dict to the frontend.

    Raises:
        HTTPException 422: No variants could be converted from the supplied HGVS strings.
        HTTPException 400: VUS API URL not configured.
        HTTPException (pass-through): AWS API errors.
    """
    failed_hgvs: list[str] = []
    variant_items: list[VariantItem] = []

    async def _convert(hgvs: str) -> VariantItem | None:
        """Convert one HGVS string in a thread to avoid blocking the event loop."""
        vcf = await asyncio.to_thread(hgvs_g_to_vcf, hgvs)
        if vcf is None:
            logger.warning("HGVS conversion failed: %s", hgvs)
            return None
        return VariantItem(
            hgvs_genomic_38=hgvs,
            chromosome=str(vcf["chrom"]),
            position=int(vcf["pos"]),
            ref_allele=vcf["ref"],
            alt_allele=vcf["alt"],
        )

    results_raw = await asyncio.gather(*[_convert(h) for h in body.hgvs_genomic_38])

    for hgvs, item in zip(body.hgvs_genomic_38, results_raw):
        if item is None:
            failed_hgvs.append(hgvs)
        else:
            variant_items.append(item)

    if not variant_items:
        raise HTTPException(
            status_code=422,
            detail=(
                "All HGVS strings failed to convert to VCF format. "
                f"Failed: {failed_hgvs}"
            ),
        )

    logger.info(
        "Converted %d/%d HGVS strings for gene %s",
        len(variant_items),
        len(body.hgvs_genomic_38),
        body.gene_symbol,
    )

    embedding_payload = EmbeddingRequest(
        gene_symbol=body.gene_symbol,
        variants=variant_items,
        annotation_method=body.annotation_method[0] if body.annotation_method else None,
        embedding_models=body.embedding_models,
        same_severe_consequence=body.same_severe_consequence,
    )

    try:
        client = VusLifeClient()
        out = await client.get_embeddings_results(embedding_payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except VusLifeAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e

    # Normalise: some API versions return 'results' instead of 'prediction_results'
    if "results" in out and "prediction_results" not in out:
        out["prediction_results"] = out.pop("results")

    # Inject existing variant metadata from local metadata.json into prediction_results.
    # The AWS API only lists existing variants in `existing_variants` (by variant_id)
    # without their metadata. We load it from disk so the frontend table can render them.
    existing_ids: list[str] = out.get("existing_variants") or []
    if existing_ids:
        meta_path = _metadata_path_for_gene(body.gene_symbol)
        if meta_path.is_file():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                # Build a lookup: variant_id → metadata dict
                meta_lookup: dict[str, dict] = {
                    v["variant_id"]: v
                    for v in (meta_data.get("variants") or [])
                    if v.get("variant_id")
                }
                pred = out.setdefault("prediction_results", {})
                for vid in existing_ids:
                    if vid not in pred:
                        variant_meta = meta_lookup.get(vid)
                        if variant_meta:
                            pred[vid] = {"metadata": variant_meta}
                        else:
                            # Metadata not found locally — still surface the ID
                            pred[vid] = {"metadata": {"variant_id": vid}}
            except Exception as e:  # noqa: BLE001
                logger.warning("Could not load metadata for existing variants: %s", e)
        else:
            # No local metadata — still surface existing variant IDs so the table shows them
            pred = out.setdefault("prediction_results", {})
            for vid in existing_ids:
                if vid not in pred:
                    pred[vid] = {"metadata": {"variant_id": vid}}

    # Surface conversion failures so the frontend can display a warning
    if failed_hgvs:
        out["failed_hgvs"] = failed_hgvs

    return out

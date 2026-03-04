"""
VUS-Life client for the external Variant Data Generation API (AWS).

Implements embedding request (with gzip handling) and metadata/annotations
download (two-step presigned URL fetch, stream to disk) per AWS API rules.
Configuration: SettingsManager (vus_api_settings.api_url).
"""

import gzip
import json
import logging
from pathlib import Path

import httpx

from app.core.config import get_settings_manager
from app.services.vus_life.schemas import (
    AnnotationsDownloadRequest,
    AwsConfigResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    PresignedUrlResponse,
)

logger = logging.getLogger(__name__)


# Gzip magic bytes for manual decompression when Content-Encoding decode fails
GZIP_MAGIC = bytes([0x1F, 0x8B])


class VusLifeAPIError(Exception):
    """Raised on AWS API 4xx/5xx or network errors; route layer can map to HTTPException."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class VusLifeClient:
    """
    Async client for the VUS-Life AWS API.

    - Health: GET /api/health
    - Embeddings: POST /api/get-embedding-results (handles gzip response)
    - Metadata/Annotations: two-step fetch (get presigned URL, then stream download to disk)
    """

    def __init__(self) -> None:
        manager = get_settings_manager()
        self._manager = manager
        settings = manager.get()
        self.base_url = settings.vus_api_settings.api_url or ""
        self.timeout_embed = httpx.Timeout(300.0, connect=10.0)
        self.timeout_default = httpx.Timeout(60.0, connect=10.0)
        self.timeout_config = httpx.Timeout(5.0, connect=3.0)

    def _base_required(self) -> None:
        if not self.base_url:
            raise ValueError("VUS API base URL is not configured (vus_api_settings.api_url)")

    def _local_config_dict(self, from_cache: bool) -> dict:
        """Read vus_dashboard_settings from manager and return as API-shaped dict."""
        settings = self._manager.get()
        vus = settings.vus_dashboard_settings
        return {
            "gene_names": list(vus.gene_names),
            "embedding_models": list(vus.embedding_models),
            "annotation_methods": list(vus.annotation_methods),
            "from_cache": from_cache,
        }

    async def get_config(self) -> dict:
        """
        Network-first config fetch: GET /api/config from AWS; on success persist to
        vus_dashboard_settings and return; on failure return local config (no hardcoded fallbacks).
        """
        if not self.base_url:
            return self._local_config_dict(from_cache=True)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_config) as client:
                resp = await client.get(f"{self.base_url}/config")
                resp.raise_for_status()
            data = AwsConfigResponse.model_validate(resp.json())
            self._manager.save_vus_config(
                gene_names=data.gene_names,
                embedding_models=data.embedding_models,
                annotation_methods=data.annotation_methods,
            )
            return {
                "gene_names": data.gene_names,
                "embedding_models": data.embedding_models,
                "annotation_methods": data.annotation_methods,
                "from_cache": False,
            }
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
            logger.warning("AWS unreachable, loading local config: %s", e)
            return self._local_config_dict(from_cache=True)

    async def health_check(self) -> dict:
        """
        GET /api/health for connection verification.

        Returns:
            JSON response as dict.

        Raises:
            ValueError: If base URL is not configured.
            VusLifeAPIError: On non-2xx or network error (map to HTTPException in routes).
        """
        self._base_required()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_default) as client:
                resp = await client.get(f"{self.base_url}/health")
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            raise VusLifeAPIError(
                status_code=e.response.status_code,
                detail=e.response.text or str(e),
            ) from e
        except httpx.RequestError as e:
            raise VusLifeAPIError(status_code=503, detail=str(e)) from e

    async def get_embeddings_results(self, payload: EmbeddingRequest) -> dict:
        """
        POST /api/v1/get-embedding-results.

        Handles gzip: httpx decodes when Content-Encoding is set; if body
        starts with gzip magic bytes (0x1f 0x8b), decompress manually then parse JSON.

        Returns:
            Full JSON as dict (includes 'results' keyed by variant_id).

        Raises:
            ValueError: If base URL is not configured.
            VusLifeAPIError: On non-2xx or network error (map to HTTPException in routes).
        """
        self._base_required()
        body = payload.model_dump(mode="json")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_embed) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/get-embedding-results",
                    json=body,
                )
                resp.raise_for_status()
                raw = resp.content
                if len(raw) >= 2 and raw[:2] == GZIP_MAGIC:
                    raw = gzip.decompress(raw)
                if isinstance(raw, bytes):
                    return json.loads(raw.decode("utf-8"))
                return resp.json()
        except httpx.HTTPStatusError as e:
            raise VusLifeAPIError(
                status_code=e.response.status_code,
                detail=e.response.text or str(e),
            ) from e
        except httpx.RequestError as e:
            raise VusLifeAPIError(status_code=503, detail=str(e)) from e

    async def download_metadata(self, gene: str) -> Path:
        """
        Two-step fetch: GET /api/download-urls/metadata?gene=..., then
        GET presigned URL and stream content to disk (no full load into RAM).

        Save path: general_settings.output_path / vus_results / metadata / gene /

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If base URL or output_path is not configured.
            VusLifeAPIError: On API or download failure (map to HTTPException in routes).
        """
        self._base_required()
        settings = self._manager.get()
        output_path = Path(settings.general_settings.output_path)
        if not output_path.is_dir():
            raise ValueError(f"Output path is not a directory: {output_path}")
        save_dir = output_path / "vus_results" / "metadata" / gene
        save_dir.mkdir(parents=True, exist_ok=True)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_default) as client:
                resp = await client.get(
                    f"{self.base_url}/v1/download-urls/metadata",
                    params={"gene": gene, "expires_in": 3600},
                )
                resp.raise_for_status()
                data = PresignedUrlResponse.model_validate(resp.json())
                download_url = data.url

            async with httpx.AsyncClient(timeout=self.timeout_default) as client:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()
                    save_path = save_dir / "metadata.json"
                    with open(save_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            return save_path
        except httpx.HTTPStatusError as e:
            raise VusLifeAPIError(
                status_code=e.response.status_code,
                detail=e.response.text or str(e),
            ) from e
        except httpx.RequestError as e:
            raise VusLifeAPIError(status_code=503, detail=str(e)) from e

    async def download_annotations(
        self,
        gene_symbol: str,
        annotation_method: str | None = None,
    ) -> Path:
        """
        Two-step fetch: POST /api/v1/download-urls/annotations, then
        GET presigned URL and stream content to disk.

        Save path: output_path / vus_results / gene_symbol / annotations / annotation_method /

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If base URL or output_path is not configured.
            VusLifeAPIError: On API or download failure (map to HTTPException in routes).
        """
        self._base_required()
        settings = self._manager.get()
        output_path = Path(settings.general_settings.output_path)
        if not output_path.is_dir():
            raise ValueError(f"Output path is not a directory: {output_path}")
        method_dir = annotation_method or "default"
        save_dir = output_path / "vus_results" / gene_symbol / "annotations" / method_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        body = AnnotationsDownloadRequest(
            gene_symbol=gene_symbol,
            annotation_method=annotation_method,
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout_default) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/download-urls/annotations",
                    json=body.model_dump(mode="json", exclude_none=True),
                )
                resp.raise_for_status()
                data = PresignedUrlResponse.model_validate(resp.json())
                download_url = data.url

            async with httpx.AsyncClient(timeout=self.timeout_default) as client:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()
                    save_path = save_dir / "annotations.json"
                    with open(save_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            return save_path
        except httpx.HTTPStatusError as e:
            raise VusLifeAPIError(
                status_code=e.response.status_code,
                detail=e.response.text or str(e),
            ) from e
        except httpx.RequestError as e:
            raise VusLifeAPIError(status_code=503, detail=str(e)) from e

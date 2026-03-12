"""
Settings API endpoints.

Provides GET and PATCH for application settings (nested structure).
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import SettingsManager, get_settings_manager
from app.schemas.settings import (
    GeneralSettingsSchema,
    ProviderSchema,
    AllSettingsResponse,
    SettingsUpdateSchema,
    VusApiSettingsSchema,
    ModelSettingsSchema,
    ProviderVerifyRequest,
    ProviderVerifyResponse,
)

router = APIRouter()


def _general_config_to_response(manager: SettingsManager) -> GeneralSettingsSchema:
    c = manager.get()
    return GeneralSettingsSchema(
        output_path=c.general_settings.output_path,
        has_accepted_agreement=c.general_settings.has_accepted_agreement,
    )


def _vus_api_config_to_response(manager: SettingsManager) -> VusApiSettingsSchema:
    c = manager.get()
    return VusApiSettingsSchema(api_url=c.vus_api_settings.api_url)


def _llm_config_to_response(manager: SettingsManager) -> ModelSettingsSchema:
    c = manager.get()
    providers_response = {}
    for pid, p in c.model_settings.providers.items():
        providers_response[pid] = ProviderSchema(
            enabled=p.enabled,
            base_url=p.base_url,
            api_key=p.api_key,
            models=p.models
        )
    return ModelSettingsSchema(
        default_provider=c.model_settings.default_provider,
        default_model=c.model_settings.default_model,
        providers=providers_response
    )


def _config_to_response(manager: SettingsManager) -> AllSettingsResponse:
    return AllSettingsResponse(
        general_settings=_general_config_to_response(manager),
        vus_api_settings=_vus_api_config_to_response(manager),
        model_settings=_llm_config_to_response(manager),
    )


@router.get("/", response_model=AllSettingsResponse)
async def get_settings(
    manager: SettingsManager = Depends(get_settings_manager),
) -> AllSettingsResponse:
    """Get current application settings (nested structure)."""
    return _config_to_response(manager)


@router.patch("/", response_model=AllSettingsResponse)
async def update_settings(
    payload: SettingsUpdateSchema,
    manager: SettingsManager = Depends(get_settings_manager),
) -> AllSettingsResponse:
    """Update application settings (partial nested update supported)."""
    try:
        raw = payload.model_dump(exclude_unset=True)
        if not raw:
            return _config_to_response(manager)

        # Convert nested Pydantic models to dicts for merge
        updates: dict = {}
        if "general_settings" in raw and raw["general_settings"] is not None:
            updates["general_settings"] = {
                k: v
                for k, v in raw["general_settings"].items()
                if v is not None
            }
        if "vus_api_settings" in raw and raw["vus_api_settings"] is not None:
            updates["vus_api_settings"] = {
                k: v
                for k, v in raw["vus_api_settings"].items()
                if v is not None
            }
        if "model_settings" in raw and raw["model_settings"] is not None:
            model_updates = {}
            if "default_provider" in raw["model_settings"]:
                model_updates["default_provider"] = raw["model_settings"]["default_provider"]
            if "default_model" in raw["model_settings"]:
                model_updates["default_model"] = raw["model_settings"]["default_model"]
                
            providers_raw = raw["model_settings"].get("providers")
            if providers_raw is not None:
                model_updates["providers"] = {}
                for pid, pdata in providers_raw.items():
                    model_updates["providers"][pid] = {
                        k: v for k, v in pdata.items() if v is not None
                    }
            if model_updates:
                updates["model_settings"] = model_updates

        if not updates:
            return _config_to_response(manager)

        manager.update(updates)
        return _config_to_response(manager)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/verify-provider", response_model=ProviderVerifyResponse)
async def verify_provider(payload: ProviderVerifyRequest):
    """Verify provider connection and fetch available models."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            provider_id = payload.provider_id.lower()
            base_url = payload.base_url.rstrip('/')
            
            if provider_id == "gemini":
                # Google Gemini uses REST endpoint: /v1beta/models?key=API_KEY
                url = f"{base_url}/v1beta/models?key={payload.api_key}"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                
                # Filter for Gemini models that support generateContent
                models = []
                for m in data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        # Name format is "models/gemini-pro", strip prefix
                        name = m["name"].split("/")[-1]
                        models.append(name)
                        
                return ProviderVerifyResponse(success=True, message="Connected to Gemini successfully", models=models)
                
            elif provider_id == "ollama" and "/v1" not in base_url:
                # Ollama native API
                url = f"{base_url}/api/tags"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                return ProviderVerifyResponse(success=True, message="Connected to Ollama successfully", models=models)
                
            else:
                # OpenAI Compatible (OpenAI, DeepSeek, Ollama /v1)
                url = f"{base_url}/models"
                headers = {"Authorization": f"Bearer {payload.api_key}"}
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                models = [m.get("id") for m in data.get("data", [])]
                return ProviderVerifyResponse(success=True, message="Connected successfully", models=models)

    except httpx.HTTPStatusError as e:
        return ProviderVerifyResponse(
            success=False, 
            message=f"HTTP Error: {e.response.status_code} - {e.response.text}", 
            models=[]
        )
    except Exception as e:
        return ProviderVerifyResponse(
            success=False, 
            message=f"Connection failed: {str(e)}", 
            models=[]
        )


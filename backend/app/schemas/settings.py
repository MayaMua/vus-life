"""
Pydantic schemas for settings API endpoints.
Mirrors config.json structure: general_settings, vus_api_settings, model_settings.
"""

from typing import Optional, Dict, List

from pydantic import BaseModel


class GeneralSettingsSchema(BaseModel):
    """General settings (output path, agreement)."""

    output_path: str
    has_accepted_agreement: bool = False


class VusApiSettingsSchema(BaseModel):
    """VUS API settings."""

    api_url: str


class ProviderSchema(BaseModel):
    """Provider config."""
    enabled: bool = True
    base_url: str = ""
    api_key: str = ""
    models: List[str] = []


class ModelSettingsSchema(BaseModel):
    """Model settings by provider."""
    default_provider: str = "deepseek"
    default_model: str = "deepseek-chat"
    providers: Dict[str, ProviderSchema]


class SettingsResponse(BaseModel):
    """Response schema for GET /api/settings."""

    general_settings: GeneralSettingsSchema
    vus_api_settings: VusApiSettingsSchema
    model_settings: ModelSettingsSchema


class GeneralSettingsUpdate(BaseModel):
    """Partial update for general settings."""

    output_path: Optional[str] = None
    has_accepted_agreement: Optional[bool] = None


class VusApiSettingsUpdate(BaseModel):
    """Partial update for VUS API settings."""

    api_url: Optional[str] = None


class ProviderUpdate(BaseModel):
    """Partial update for provider."""
    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    models: Optional[List[str]] = None


class ModelSettingsUpdate(BaseModel):
    """Partial update for model settings."""
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    providers: Optional[Dict[str, ProviderUpdate]] = None


class SettingsUpdateSchema(BaseModel):
    """Request schema for PATCH /api/settings (partial nested update)."""

    general_settings: Optional[GeneralSettingsUpdate] = None
    vus_api_settings: Optional[VusApiSettingsUpdate] = None
    model_settings: Optional[ModelSettingsUpdate] = None


class ProviderVerifyRequest(BaseModel):
    """Request schema for verifying provider credentials."""
    provider_id: str
    base_url: str
    api_key: str

class ProviderVerifyResponse(BaseModel):
    """Response schema for provider verification."""
    success: bool
    message: str
    models: List[str] = []

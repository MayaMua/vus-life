from pydantic import BaseModel, Field
from .base import GeneralSettings
from .llm import ModelSettings
from .vus import VusApiSettings, VusDashboardSettings

class AppSettings(BaseModel):
    """Root configuration class for the application."""
    general_settings: GeneralSettings = Field(default_factory=GeneralSettings)
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    vus_api_settings: VusApiSettings = Field(default_factory=VusApiSettings)
    vus_dashboard_settings: VusDashboardSettings = Field(default_factory=VusDashboardSettings)
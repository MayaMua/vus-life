# """
# Configuration manager for the application.

# Implements a singleton pattern to ensure data consistency across API calls.
# Stores configuration in backend/configs/config.json with Pydantic validation.
# """

# import json
# import os
# from pathlib import Path
# from typing import Any, Optional

# from pydantic import BaseModel, Field


# class GeneralSettings(BaseModel):
#     """General app settings (e.g. output path, agreement)."""

#     output_path: str = Field(
#         default_factory=lambda: str(Path.home() / "Documents"),
#         description="Data output directory path",
#     )
#     has_accepted_agreement: bool = Field(
#         default=False,
#         description="Whether user has accepted the data usage agreement",
#     )


# class VusApiSettings(BaseModel):
#     """VUS API connection settings."""

#     api_url: str = ""


# class GeminiProviderSettings(BaseModel):
#     """Gemini model provider settings."""

#     api_key: str = ""
#     models: list[str] = Field(default_factory=lambda: ["gemini-2.0-flash"])


# class ModelSettings(BaseModel):
#     """Model provider settings keyed by provider name."""

#     gemini: GeminiProviderSettings = Field(default_factory=GeminiProviderSettings)


# class VusDashboardSettings(BaseModel):
#     """VUS dashboard metadata (gene list, embedding models, annotation methods). Synced from AWS API or local cache."""

#     gene_names: list[str] = Field(default_factory=list)
#     embedding_models: list[str] = Field(default_factory=list)
#     annotation_methods: list[str] = Field(default_factory=list)


# class AppSettings(BaseModel):
#     """Root application settings matching config.json structure."""

#     general_settings: GeneralSettings = Field(default_factory=GeneralSettings)
#     vus_api_settings: VusApiSettings = Field(default_factory=VusApiSettings)
#     model_settings: ModelSettings = Field(default_factory=ModelSettings)
#     vus_dashboard_settings: VusDashboardSettings = Field(default_factory=VusDashboardSettings)


# class SettingsManager:
#     """
#     Singleton configuration manager.

#     Manages application settings with persistent storage in JSON format.
#     Validates paths before saving to ensure they exist and are writable.
#     """

#     _instance: Optional["SettingsManager"] = None
#     _config: Optional[AppSettings] = None
#     _config_path: Path
#     _initialized: bool = False

#     def __new__(cls):
#         """Singleton pattern implementation."""
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#             cls._instance._initialized = False
#         return cls._instance

#     def _initialize(self):
#         """Initialize config directory and load existing config."""
#         if self._initialized:
#             return

#         backend_dir = Path(__file__).resolve().parent.parent.parent.parent
#         configs_dir = backend_dir / "configs"
#         configs_dir.mkdir(exist_ok=True)
#         self._config_path = configs_dir / "config.json"

#         if self._config_path.exists():
#             try:
#                 with open(self._config_path, "r") as f:
#                     data = json.load(f)
#                     self._config = AppSettings(**data)
#             except (json.JSONDecodeError, ValueError):
#                 self._config = AppSettings()
#                 self._save_to_disk()
#         else:
#             self._config = AppSettings()
#             self._save_to_disk()

#         self._initialized = True

#     def _save_to_disk(self):
#         """Save config to disk with human-readable formatting."""
#         with open(self._config_path, "w") as f:
#             f.write(self._config.model_dump_json(indent=2))

#     def _deep_merge(self, current: dict[str, Any], updates: dict[str, Any]) -> None:
#         """Merge updates into current in place (one level deep for nested objects)."""
#         for key, value in updates.items():
#             if (
#                 key in current
#                 and isinstance(current.get(key), dict)
#                 and isinstance(value, dict)
#             ):
#                 current[key] = {**current[key], **value}
#             else:
#                 current[key] = value

#     def get(self) -> AppSettings:
#         """Get current configuration."""
#         if not self._initialized:
#             self._initialize()
#         return self._config

#     def update(self, updates: dict[str, Any]) -> AppSettings:
#         """
#         Update configuration with validation (supports nested keys).

#         Args:
#             updates: Partial update dict (e.g. {"general_settings": {"output_path": "..."}})

#         Returns:
#             Updated AppSettings instance

#         Raises:
#             ValueError: If path validation fails
#         """
#         if not self._initialized:
#             self._initialize()

#         # Validate output_path if provided
#         gs = updates.get("general_settings") or {}
#         if "output_path" in gs:
#             path_str = gs["output_path"]
#             path = Path(path_str)
#             if not path.exists():
#                 raise ValueError(f"Path does not exist: {path}")
#             if not path.is_dir():
#                 raise ValueError(f"Path is not a directory: {path}")
#             if not os.access(path, os.W_OK):
#                 raise ValueError(f"Path is not writable: {path}")

#         current = self._config.model_dump()
#         self._deep_merge(current, updates)
#         self._config = AppSettings(**current)
#         self._save_to_disk()
#         return self._config

#     def save_vus_config(
#         self,
#         gene_names: list[str],
#         embedding_models: list[str],
#         annotation_methods: list[str],
#     ) -> AppSettings:
#         """Update only vus_dashboard_settings and persist to disk."""
#         return self.update(
#             {
#                 "vus_dashboard_settings": {
#                     "gene_names": gene_names,
#                     "embedding_models": embedding_models,
#                     "annotation_methods": annotation_methods,
#                 }
#             }
#         )


# def get_settings_manager() -> SettingsManager:
#     """Return the global settings manager instance (dependency injection)."""
#     manager = SettingsManager()
#     manager._initialize()
#     return manager


import json
import os
from pathlib import Path
from typing import Any, Optional
from app.schemas.config import AppSettings
from app.schemas.config.base import GeneralSettings
from app.schemas.config.llm import ModelSettings
from app.schemas.config.vus import VusApiSettings, VusDashboardSettings

class SettingsManager:
    _instance: Optional["SettingsManager"] = None
    _config: Optional[AppSettings] = None
    _config_dir: Path
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _initialize(self):
        if self._initialized: return
        
        # Determine config directory (backend/configs)
        backend_dir = Path(__file__).resolve().parent.parent.parent
        self._config_dir = backend_dir / "configs"
        self._config_dir.mkdir(parents=True, exist_ok=True)
        
        self._config = AppSettings()
        
        # Load multiple config files
        general_path = self._config_dir / "general_config.json"
        llm_path = self._config_dir / "llm_config.json"
        vus_path = self._config_dir / "vus_config.json"

        # General Settings
        if general_path.exists():
            try:
                with open(general_path, "r") as f:
                    self._config.general_settings = GeneralSettings(**json.load(f))
            except Exception:
                self._save_to_disk("general")
        else:
            default_data_dir = backend_dir / "configs"
            self._config.general_settings.output_path = str(default_data_dir)
            self._save_to_disk("general")

        # LLM Settings
        if llm_path.exists():
            try:
                with open(llm_path, "r") as f:
                    self._config.model_settings = ModelSettings(**json.load(f))
            except Exception:
                self._save_to_disk("llm")
        else:
            self._save_to_disk("llm")

        # VUS Settings
        if vus_path.exists():
            try:
                with open(vus_path, "r") as f:
                    data = json.load(f)
                    if "api_url" in data:
                        self._config.vus_api_settings = VusApiSettings(**data)
                    if "gene_names" in data:
                        self._config.vus_dashboard_settings = VusDashboardSettings(**data)
            except Exception:
                self._save_to_disk("vus")
        else:
            self._save_to_disk("vus")

        self._initialized = True

    def get(self) -> AppSettings:
        if not self._initialized: self._initialize()
        return self._config

    def update(self, updates: dict[str, Any]) -> AppSettings:
        """
        Supports deep updating nested partial data
        """
        if not self._initialized: self._initialize()
        
        current_data = self._config.model_dump()
        self._deep_merge(current_data, updates)
        self._config = AppSettings(**current_data)
        
        # Save specific files based on updates
        if "general_settings" in updates:
            self._save_to_disk("general")
        if "model_settings" in updates:
            self._save_to_disk("llm")
        if "vus_api_settings" in updates or "vus_dashboard_settings" in updates:
            self._save_to_disk("vus")
            
        return self._config

    def _save_to_disk(self, section: str = "all"):
        if section in ("all", "general"):
            with open(self._config_dir / "general_config.json", "w") as f:
                f.write(self._config.general_settings.model_dump_json(indent=2))
        if section in ("all", "llm"):
            with open(self._config_dir / "llm_config.json", "w") as f:
                f.write(self._config.model_settings.model_dump_json(indent=2))
        if section in ("all", "vus"):
            combined_vus = {
                **self._config.vus_api_settings.model_dump(),
                **self._config.vus_dashboard_settings.model_dump(),
            }
            with open(self._config_dir / "vus_config.json", "w") as f:
                json.dump(combined_vus, f, indent=2)

    def _deep_merge(self, current: dict, updates: dict):
        for key, value in updates.items():
            if (
                key in current 
                and isinstance(current[key], dict) 
                and isinstance(value, dict)
            ):
                self._deep_merge(current[key], value)
            else:
                current[key] = value

def get_settings_manager() -> SettingsManager:
    manager = SettingsManager()
    manager._initialize()
    return manager
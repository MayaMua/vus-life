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


# app/core/config.py

import json
import os
from pathlib import Path
from typing import Any, Optional
from app.schemas.config import AppSettings

class SettingsManager:
    _instance: Optional["SettingsManager"] = None
    _config: Optional[AppSettings] = None
    _config_path: Path
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _initialize(self):
        if self._initialized: return
        
        # 1. 配置文件永远保存在固定的、独立于数据的主目录下
        # Mac: /Users/user/.variant_insight/config.json
        # Windows: C:\Users\user\.variant_insight\config.json
        config_dir = Path.home() / ".variant_insight"
        config_dir.mkdir(exist_ok=True)
        self._config_path = config_dir / "config.json"

        if self._config_path.exists():
            try:
                with open(self._config_path, "r") as f:
                    data = json.load(f)
                    self._config = AppSettings(**data)
            except Exception:
                self._config = AppSettings()
                self._save_to_disk()
        else:
            self._config = AppSettings()
            # 2. 如果是第一次创建，可以在这里通过代码设置默认的 output_path
            # 为当前运行目录下的 data_local
            default_data_dir = Path.cwd() / "configs"
            default_data_dir.mkdir(parents=True, exist_ok=True)
            self._config.general_settings.output_path = str(default_data_dir)
            self._save_to_disk()

        self._initialized = True


    def get(self) -> AppSettings:
        if not self._initialized: self._initialize()
        return self._config

    def update(self, updates: dict[str, Any]) -> AppSettings:
        """
        支持深层更新 (Deep Update)
        前端传来的 JSON 可能是 partial 的，比如只改了 deepseek 的 key
        """
        if not self._initialized: self._initialize()
        
        current_data = self._config.model_dump()
        
        # 使用你之前的 _deep_merge 逻辑，或者使用第三方库如 deepmerge
        self._deep_merge(current_data, updates)
        
        # 重新验证并赋值
        self._config = AppSettings(**current_data)
        self._save_to_disk()
        return self._config

    def _save_to_disk(self):
        with open(self._config_path, "w") as f:
            f.write(self._config.model_dump_json(indent=2))

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
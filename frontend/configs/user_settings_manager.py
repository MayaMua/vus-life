#!/usr/bin/env python3
"""
User settings manager for persistent configuration.
Compatible with PyInstaller - stores settings in user's home directory.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class UserSettings:
    """User configuration settings."""
    api_address: str = "http://localhost:8000"
    data_folder_name: str = "data_user"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class UserSettingsManager:
    """Manager for user settings with persistent storage."""
    
    def __init__(self):
        """Initialize settings manager."""
        self.config_file = self._get_config_file_path()
        self.settings = self._load_settings()
    
    def _get_config_file_path(self) -> Path:
        """
        Get config file path that works with PyInstaller.
        Stores in user's home directory for persistence.
        """
        # Check if running as PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = Path.home() / '.vus-life'
        else:
            # Running as script - store in home directory for consistency
            app_dir = Path.home() / '.vus-life'
        
        # Create directory if it doesn't exist
        app_dir.mkdir(parents=True, exist_ok=True)
        
        return app_dir / 'user_settings.json'
    
    def _load_settings(self) -> UserSettings:
        """Load settings from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return UserSettings.from_dict(data)
            except Exception as e:
                print(f"Error loading settings: {e}. Using defaults.")
                return UserSettings()
        else:
            # Create default settings file
            default_settings = UserSettings()
            self._save_settings(default_settings)
            return default_settings
    
    def _save_settings(self, settings: UserSettings) -> None:
        """Save settings to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_settings(self) -> UserSettings:
        """Get current settings."""
        return self.settings
    
    def update_settings(self, **kwargs) -> None:
        """
        Update settings and save to file.
        
        Args:
            **kwargs: Settings to update (api_address, data_folder_name)
        """
        # Update only provided fields
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        
        # Save to file
        self._save_settings(self.settings)
    
    def get_api_address(self) -> str:
        """Get API address."""
        return self.settings.api_address
    
    def get_data_folder_name(self) -> str:
        """Get data folder name."""
        return self.settings.data_folder_name
    
    def get_data_folder_path(self) -> Path:
        """
        Get absolute path to data folder.
        Works with both development and PyInstaller modes.
        """
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            # Get the directory where the executable is located
            base_path = Path(sys.executable).parent
        else:
            # Running as script - use project root
            # frontend/configs/user_settings_manager.py -> go up 2 levels to project root
            base_path = Path(__file__).parent.parent.parent
        
        return base_path / self.settings.data_folder_name
    
    def reset_to_defaults(self) -> None:
        """Reset settings to defaults."""
        self.settings = UserSettings()
        self._save_settings(self.settings)
    
    def get_config_file_location(self) -> str:
        """Get the location of the config file for display."""
        return str(self.config_file)


# Global instance
_settings_manager: Optional[UserSettingsManager] = None


def get_settings_manager() -> UserSettingsManager:
    """Get or create global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = UserSettingsManager()
    return _settings_manager

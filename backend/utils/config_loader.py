"""
Configuration loader for variant research project.

This module provides a centralized way to access configuration settings,
particularly for path management. It allows for easy configuration changes
without modifying code.
"""

import tomllib
from pathlib import Path
from typing import Optional


class Config:
    """
    Configuration manager for the project.
    
    Loads settings from config.toml and provides easy access to paths
    and other configuration values.
    """
    
    _instance = None
    _config_data = None
    _project_root = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration by loading config.toml."""
        if self._config_data is None:
            self._load_config()
    
    def _load_config(self):
        """Load configuration from config.toml file."""
        # Find the project root (where config.toml is located)
        current_file = Path(__file__).resolve()
        
        # Go up from backend/utils/ to backend/
        backend_dir = current_file.parent.parent
        config_path = backend_dir / "config.toml"
        
        # Store project root (parent of backend/)
        self._project_root = backend_dir.parent
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at {config_path}. "
                "Please create a config.toml file in the backend directory."
            )
        
        # Load TOML configuration
        with open(config_path, "rb") as f:
            self._config_data = tomllib.load(f)
    
    def get_path(self, key: str, create_if_missing: bool = False) -> Path:
        """
        Get a path from configuration and resolve it relative to project root.
        
        Args:
            key: Dot-separated key path (e.g., 'paths.cache_root' or 'hgvs_vcf_cache')
            create_if_missing: If True, create the directory if it doesn't exist
        
        Returns:
            Absolute Path object
        
        Examples:
            >>> config = Config()
            >>> cache_dir = config.get_path('hgvs_vcf_cache', create_if_missing=True)
            >>> data_root = config.get_path('data_root')
        """
        # Handle nested keys
        if '.' in key:
            parts = key.split('.')
            value = self._config_data
            for part in parts:
                value = value.get(part, {})
            path_str = value
        else:
            # Try to find in paths section first
            path_str = self._config_data.get('paths', {}).get(key)
        
        if not path_str:
            raise KeyError(f"Path configuration '{key}' not found in config.toml")
        
        # Resolve path relative to project root
        abs_path = (self._project_root / path_str).resolve()
        
        # Create directory if requested
        if create_if_missing:
            abs_path.mkdir(parents=True, exist_ok=True)
        
        return abs_path
    
    def get(self, key: str, default=None):
        """
        Get any configuration value using dot notation.
        
        Args:
            key: Dot-separated key path (e.g., 'api.mutalyzer_timeout')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        
        Examples:
            >>> config = Config()
            >>> timeout = config.get('api.mutalyzer_timeout', 30)
        """
        parts = key.split('.')
        value = self._config_data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root
    
    def reload(self):
        """Reload configuration from file."""
        self._config_data = None
        self._load_config()


# Global singleton instance
_config = Config()


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config singleton instance
    
    Example:
        >>> from utils.config_loader import get_config
        >>> config = get_config()
        >>> cache_dir = config.get_path('hgvs_vcf_cache', create_if_missing=True)
    """
    return _config


# Convenience functions for common operations
def get_cache_dir(cache_name: str) -> Path:
    """
    Get a cache directory path and create it if it doesn't exist.
    
    Args:
        cache_name: Name of the cache (e.g., 'hgvs_vcf_cache', 'mutalyzer_cache')
    
    Returns:
        Absolute Path to the cache directory
    """
    return get_config().get_path(cache_name, create_if_missing=True)


def get_data_dir(data_type: str, dataset: Optional[str] = None) -> Path:
    """
    Get a data directory path.
    
    Args:
        data_type: Type of data ('raw' or 'processed')
        dataset: Optional dataset name (e.g., 'clinvar', 'lovd')
    
    Returns:
        Absolute Path to the data directory
    
    Examples:
        >>> get_data_dir('raw', 'clinvar')
        >>> get_data_dir('processed', 'lovd')
        >>> get_data_dir('raw')  # Gets general raw data directory
    """
    if dataset:
        key = f"paths.{dataset}.{data_type}"
    else:
        key = f"{data_type}_data"
    
    return get_config().get_path(key, create_if_missing=False)

"""
Configuration writer for updating config.toml from UI.

This module provides functions to safely update configuration values,
particularly for user-customizable paths through a UI.
"""

import tomllib
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigWriter:
    """
    Handles writing and updating configuration values in config.toml.
    Designed for use with UI configuration dialogs.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration writer.
        
        Args:
            config_path: Path to config.toml (defaults to backend/config.toml)
        """
        if config_path is None:
            # Find config.toml in backend directory
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent
            config_path = backend_dir / "config.toml"
        
        self.config_path = config_path
        self.project_root = config_path.parent.parent
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
    
    def read_config(self) -> Dict[str, Any]:
        """
        Read the current configuration.
        
        Returns:
            Dictionary containing the configuration
        """
        with open(self.config_path, "rb") as f:
            return tomllib.load(f)
    
    def update_path(self, path_key: str, new_path: str, relative_to_project: bool = True) -> bool:
        """
        Update a path in the configuration.
        
        Args:
            path_key: Key for the path (e.g., 'cache_root', 'mutalyzer_cache')
            new_path: New path value
            relative_to_project: If True, store as relative path; if False, store absolute
        
        Returns:
            True if successful, False otherwise
        
        Example:
            >>> writer = ConfigWriter()
            >>> writer.update_path('cache_root', '/mnt/external/cache', relative_to_project=False)
            >>> writer.update_path('cache_root', 'my_data/.cache', relative_to_project=True)
        """
        try:
            # Validate and convert path
            new_path_obj = Path(new_path)
            
            if relative_to_project:
                # Convert to relative path if it's absolute
                if new_path_obj.is_absolute():
                    try:
                        new_path_obj = new_path_obj.relative_to(self.project_root)
                    except ValueError:
                        # Path is outside project root, keep as absolute
                        relative_to_project = False
                
                path_to_write = str(new_path_obj)
            else:
                # Store as absolute path
                if not new_path_obj.is_absolute():
                    new_path_obj = (self.project_root / new_path_obj).resolve()
                path_to_write = str(new_path_obj)
            
            # Read current config
            config_lines = []
            with open(self.config_path, 'r') as f:
                config_lines = f.readlines()
            
            # Find and update the line
            updated = False
            in_paths_section = False
            
            for i, line in enumerate(config_lines):
                # Check if we're in the [paths] section
                if line.strip().startswith('[paths'):
                    in_paths_section = True
                    continue
                
                # Check if we've left the [paths] section
                if in_paths_section and line.strip().startswith('[') and not line.strip().startswith('[paths'):
                    in_paths_section = False
                
                # Update the matching key
                if in_paths_section and '=' in line:
                    key = line.split('=')[0].strip()
                    if key == path_key:
                        # Update the line
                        indent = len(line) - len(line.lstrip())
                        config_lines[i] = f"{' ' * indent}{path_key} = \"{path_to_write}\"\n"
                        updated = True
                        break
            
            if not updated:
                return False
            
            # Write back to file
            with open(self.config_path, 'w') as f:
                f.writelines(config_lines)
            
            return True
            
        except Exception as e:
            print(f"Error updating path: {e}")
            return False
    
    def update_multiple_paths(self, path_updates: Dict[str, str], relative_to_project: bool = True) -> Dict[str, bool]:
        """
        Update multiple paths at once.
        
        Args:
            path_updates: Dictionary of {path_key: new_path}
            relative_to_project: Whether to store paths as relative
        
        Returns:
            Dictionary of {path_key: success_bool}
        
        Example:
            >>> writer = ConfigWriter()
            >>> updates = {
            ...     'cache_root': '/mnt/external/cache',
            ...     'data_root': '/mnt/external/data'
            ... }
            >>> results = writer.update_multiple_paths(updates, relative_to_project=False)
        """
        results = {}
        for key, value in path_updates.items():
            results[key] = self.update_path(key, value, relative_to_project)
        return results
    
    def validate_path(self, path: str, should_exist: bool = False, 
                     should_be_writable: bool = True) -> tuple[bool, str]:
        """
        Validate a path before updating configuration.
        
        Args:
            path: Path to validate
            should_exist: If True, check if path exists
            should_be_writable: If True, check if path is writable
        
        Returns:
            Tuple of (is_valid, error_message)
        
        Example:
            >>> writer = ConfigWriter()
            >>> valid, msg = writer.validate_path('/mnt/external/cache')
            >>> if not valid:
            ...     print(f"Invalid path: {msg}")
        """
        try:
            path_obj = Path(path)
            
            # Check if absolute path is required for external locations
            if path_obj.is_absolute():
                # Check if path exists (if required)
                if should_exist and not path_obj.exists():
                    return False, f"Path does not exist: {path}"
                
                # Check if parent directory exists (for creation)
                if not should_exist and not path_obj.parent.exists():
                    return False, f"Parent directory does not exist: {path_obj.parent}"
                
                # Check if writable (if required)
                if should_be_writable:
                    # Test write permissions on existing directory or parent
                    test_dir = path_obj if path_obj.exists() else path_obj.parent
                    if not os.access(test_dir, os.W_OK):
                        return False, f"Path is not writable: {path}"
            else:
                # Relative path - resolve relative to project root
                full_path = self.project_root / path_obj
                
                if should_exist and not full_path.exists():
                    return False, f"Path does not exist: {path}"
                
                if not should_exist and not full_path.parent.exists():
                    return False, f"Parent directory does not exist: {full_path.parent}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error validating path: {str(e)}"
    
    def get_current_path(self, path_key: str, resolve: bool = True) -> Optional[Path]:
        """
        Get the current path value from config.
        
        Args:
            path_key: Key for the path
            resolve: If True, return absolute path; if False, return as-is from config
        
        Returns:
            Path object or None if not found
        """
        try:
            config = self.read_config()
            path_value = config.get('paths', {}).get(path_key)
            
            if path_value is None:
                return None
            
            path_obj = Path(path_value)
            
            if resolve and not path_obj.is_absolute():
                path_obj = (self.project_root / path_obj).resolve()
            
            return path_obj
            
        except Exception as e:
            print(f"Error getting path: {e}")
            return None


def update_paths_from_ui(path_updates: Dict[str, str], validate_first: bool = True) -> Dict[str, str]:
    """
    Convenience function for updating paths from UI.
    
    Args:
        path_updates: Dictionary of {path_key: new_path}
        validate_first: If True, validate all paths before updating
    
    Returns:
        Dictionary of {path_key: status_message}
    
    Example:
        >>> updates = {
        ...     'cache_root': '/mnt/external/cache',
        ...     'data_root': '/mnt/external/data',
        ...     'mutalyzer_cache': '/mnt/external/cache/mutalyzer'
        ... }
        >>> results = update_paths_from_ui(updates)
        >>> for key, msg in results.items():
        ...     print(f"{key}: {msg}")
    """
    writer = ConfigWriter()
    results = {}
    
    # Validate all paths first if requested
    if validate_first:
        validation_errors = {}
        for key, path in path_updates.items():
            valid, error_msg = writer.validate_path(path, should_exist=False, should_be_writable=True)
            if not valid:
                validation_errors[key] = error_msg
        
        if validation_errors:
            # Return validation errors
            for key, error in validation_errors.items():
                results[key] = f"Validation failed: {error}"
            return results
    
    # Update paths
    update_results = writer.update_multiple_paths(path_updates, relative_to_project=True)
    
    for key, success in update_results.items():
        if success:
            results[key] = "Successfully updated"
        else:
            results[key] = "Failed to update"
    
    # After successful updates, reload config
    from utils.config_loader import get_config
    get_config().reload()
    
    return results


# Example UI integration functions
def ui_get_all_paths() -> Dict[str, str]:
    """
    Get all configurable paths for display in UI.
    
    Returns:
        Dictionary of {path_key: current_path}
    """
    writer = ConfigWriter()
    config = writer.read_config()
    paths = config.get('paths', {})
    
    # Get main paths
    result = {}
    for key in ['data_root', 'cache_root', 'raw_data', 'processed_data',
                'hgvs_vcf_cache', 'mutalyzer_cache']:
        if key in paths:
            current_path = writer.get_current_path(key, resolve=True)
            result[key] = str(current_path) if current_path else paths[key]
    
    return result


def ui_create_directory(path: str) -> tuple[bool, str]:
    """
    Create a directory (for use with UI).
    
    Args:
        path: Path to create
    
    Returns:
        Tuple of (success, message)
    """
    try:
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return True, f"Directory created: {path}"
    except Exception as e:
        return False, f"Error creating directory: {str(e)}"

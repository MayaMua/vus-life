"""Configuration loader with variable substitution support."""

import tomllib
import re
from pprint import pprint
from pathlib import Path
from typing import Any, Dict, Union, List, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import settings manager for user-configurable data folder
from frontend.configs.user_settings_manager import get_settings_manager

# =============================================================================
# Load Basic Config and Settings
# =============================================================================

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from TOML file.
    
    Args:
        config_path: Path to the TOML configuration file
        
    Returns:
        Dict containing the configuration
    """
    with open(config_path, 'rb') as f:
        return tomllib.load(f)

def get_gene_names(config: Dict[str, Any]) -> List[str]:
    """
    Get the gene names from the configuration.
    """
    return config['genes']['gene_names']

def get_annotation_method_names(config: Dict[str, Any]) -> List[str]:
    """
    Get the annotation types from the configuration.
    """
    return config['annotation_methods']['method_names']


def get_embedding_models(config: Dict[str, Any]) -> List[str]:
    """
    Get the embedding models from the configuration.
    """
    return config['models'].get('embedding_models', [])


def get_log_dir(config: Dict[str, Any]) -> str:
    """
    Get the log directory from the configuration.
    """
    return config['paths']['others'].get('log_base_dir', 'logs')


# =============================================================================
# Data User Paths 
# =============================================================================

def get_user_data_base_dir(config: Dict[str, Any]) -> Path:
    """
    Get the data user base directory from the configuration.
    Uses user settings manager to get the configured data folder path.
    This ensures compatibility with PyInstaller and user-configured paths.
    """
    settings_manager = get_settings_manager()
    return settings_manager.get_data_folder_path()

def get_user_training_coordinates_dir(config: Dict[str, Any], gene_symbol: str = None) -> Path:
    """
    Get the training coordinates parquet directory for a specific gene.
    Structure: data_user/training_embedding_results/coordinates/{gene_symbol}/
    
    Args:
        config: Configuration dictionary
        gene_symbol: Optional gene symbol to append to path
        
    Returns:
        Path to training coordinates directory
    """
    path = get_user_data_base_dir(config) / \
        config['paths']['user']['training_results']['training_coordinates_dir']
    if gene_symbol:
        path = path / gene_symbol
    return path

def get_user_training_dimension_plots_dir(config: Dict[str, Any], gene_symbol: str = None) -> Path:
    """
    Get the training dimension plots directory.
    Structure: data_user/training_embedding_results/embedding_plot_dir/{gene_symbol}/
    
    Args:
        config: Configuration dictionary
        gene_symbol: Optional gene symbol to append to path
        
    Returns:
        Path to training dimension plots directory
    """
    path = get_user_data_base_dir(config) / \
        config['paths']['user']['training_results']['training_dimension_plots_dir']
    if gene_symbol:
        path = path / gene_symbol
    return path

def get_user_training_metadata_dir(config: Dict[str, Any], gene_symbol: str = None) -> Path:
    """
    Get the training metadata directory for a specific gene.
    Structure: data_user/training_embedding_results/metadata/{gene_symbol}/
    
    Args:
        config: Configuration dictionary
        gene_symbol: Optional gene symbol to append to path
        
    Returns:
        Path to training metadata directory
    """
    path = get_user_data_base_dir(config) / \
        config['paths']['user']['training_results']['training_metadata_dir']
    if gene_symbol:
        path = path / gene_symbol
    return path

def get_user_query_inputs_dir(config: Dict[str, Any], gene_symbol: str = None, job_name: str = None) -> Path:
    """
    Get the user query inputs directory.
    Structure: data_user/user_query/inputs/{gene_symbol}/{job_name}/
    
    Args:
        config: Configuration dictionary
        gene_symbol: Optional gene symbol to append to path
        job_name: Optional job name to append to path
        
    Returns:
        Path to user query inputs directory
    """
    path = get_user_data_base_dir(config) / \
        config['paths']['user']['user_query']['user_query_inputs_dir']
    if gene_symbol:
        path = path / gene_symbol
        if job_name is not None:
            path = path / job_name
    return path

def get_user_query_results_dir(config: Dict[str, Any], gene_symbol: str = None, job_name: str = None) -> Path:
    """
    Get the user query results directory.
    Structure: data_user/user_query/retrieval_results/{gene_symbol}/{job_name}/
    
    Args:
        config: Configuration dictionary
        gene_symbol: Optional gene symbol to append to path
        job_name: Optional job name to append to path
        
    Returns:
        Path to user query results directory
    """
    path = get_user_data_base_dir(config) / \
        config['paths']['user']['user_query']['user_query_results_dir']
    if gene_symbol:
        path = path / gene_symbol
        if job_name is not None:
            path = path / job_name
    return path

def get_user_query_processed_dir(config: Dict[str, Any], gene_symbol: str = None, job_name: str = None) -> Path:
    """
    Get the user query processed results directory.
    Structure: data_user/user_query/processed_results/{gene_symbol}/{job_name}/
    
    Args:
        config: Configuration dictionary
        gene_symbol: Optional gene symbol to append to path
        job_name: Optional job name to append to path
        
    Returns:
        Path to user query processed results directory
    """
    path = get_user_data_base_dir(config) / \
        config['paths']['user']['user_query']['user_query_processed_dir']
    if gene_symbol:
        path = path / gene_symbol
        if job_name is not None:
            path = path / job_name
    return path

"""
Parquet Manager for Training Embedding Results

This module provides base and specialized classes for managing parquet files efficiently.
- BaseParquetManager: Common functionality for all parquet managers
- CoordinateParquetManager: Manages embedding coordinates
"""



import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class BaseParquetManager:
    """
    Base class for parquet file management.
    
    Provides common functionality for:
    - File path management
    - Directory creation
    - Loading/saving parquet files
    - File existence checks
    - Deletion operations
    - Basic info retrieval
    """
    
    def __init__(self, parquet_path: Path, logger_name: str = None):
        """
        Initialize base parquet manager.
        
        Args:
            parquet_path: Path to the parquet file
            logger_name: Name for the logger (defaults to class name)
        """
        self.parquet_path = Path(parquet_path)
        self.parquet_dir = self.parquet_path.parent
        
        # Create directory if it doesn't exist
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        if logger_name is None:
            logger_name = self.__class__.__name__
        self.logger = logging.getLogger(logger_name)
    
    def exists(self) -> bool:
        """
        Check if the parquet file exists.
        
        Returns:
            True if file exists, False otherwise
        """
        return self.parquet_path.exists()
    
    def load_parquet(self) -> pd.DataFrame:
        """
        Load existing parquet file.
        
        Returns:
            DataFrame with existing data
            
        Raises:
            FileNotFoundError: If parquet file doesn't exist
        """
        if not self.exists():
            raise FileNotFoundError(f"Parquet file not found: {self.parquet_path}")
        
        try:
            df = pd.read_parquet(self.parquet_path)
            self.logger.debug(f"Loaded parquet file: {self.parquet_path} - Shape: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading parquet file: {e}")
            raise
    
    def save_parquet(self, df: pd.DataFrame) -> bool:
        """
        Save DataFrame to parquet file.
        
        Args:
            df: DataFrame to save
            
        Returns:
            True if saved successfully
        """
        try:
            df.to_parquet(self.parquet_path, index=False)
            self.logger.debug(f"Saved parquet file: {self.parquet_path} - Shape: {df.shape}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving parquet file: {e}")
            raise
    
    def delete_parquet(self) -> bool:
        """
        Delete the parquet file.
        
        Returns:
            True if deleted successfully, False if file didn't exist
        """
        try:
            if self.exists():
                self.parquet_path.unlink()
                self.logger.info(f"✓ Deleted parquet file: {self.parquet_path}")
                return True
            else:
                self.logger.info(f"Parquet file does not exist: {self.parquet_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting parquet file: {e}")
            raise
    
    def get_basic_info(self) -> Dict[str, Any]:
        """
        Get basic information about the parquet file.
        
        Returns:
            Dictionary with basic file information
        """
        try:
            if not self.exists():
                return {
                    'exists': False,
                    'path': str(self.parquet_path),
                    'size_bytes': 0
                }
            
            df = self.load_parquet()
            file_size = self.parquet_path.stat().st_size
            
            return {
                'exists': True,
                'path': str(self.parquet_path),
                'size_bytes': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'shape': df.shape,
                'columns': list(df.columns),
                'total_rows': len(df)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting basic info: {e}")
            return {
                'exists': False,
                'error': str(e),
                'path': str(self.parquet_path)
            }


class CoordinateParquetManager(BaseParquetManager):
    """
    Manages parquet files for training embedding results.
    
    Strategy:
    - Initialize parquet with variant_id and embedding_model only
    - Merge coordinates using variant_id + embedding_model as combined key
    - Store coordinates in columns: pca_x, pca_y, tsne_x, tsne_y, umap_x, umap_y
    - Save coordinates separately based on annotation methods (no annotation_method column)
    """
    
    def __init__(self, parquet_path: str = None):
        """
        Initialize CoordinateParquetManager for a specific gene and annotation method.
        
        Args:
            parquet_path: Path to the parquet file (optional, will use default if not provided)
        """

        parquet_path = Path(parquet_path)
        self.parquet_dir = parquet_path.parent
        
        # Initialize base class
        super().__init__(parquet_path)
    
    def initialize_parquet(self, variant_ids: List[str], embedding_models: List[str]) -> bool:
        """
        Initialize parquet file with variant_id and embedding_model columns.
        If parquet already exists, quickly check and add only missing rows for the current model.
        
        Args:
            variant_ids: List of variant IDs to initialize
            embedding_models: List of embedding model names (typically just one model)
            
        Returns:
            True if initialized or updated successfully, False if already exists with all models
        """
        if not self.exists():
            # Create new parquet file
            try:
                df_init = self._create_initial_dataframe(variant_ids, embedding_models)
                self.save_parquet(df_init)
                
                self.logger.info(f"✓ Initialized parquet file: {self.parquet_path}")
                self.logger.info(f"  Variants: {len(variant_ids)}, Models: {embedding_models}, Rows: {len(df_init)}")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error initializing parquet file: {e}")
                raise
        else:
            # Parquet exists - remove existing rows for the current model and add fresh ones
            try:
                model_to_add = embedding_models[0]  # Typically just one model
                
                # Load full file
                df_existing = self.load_parquet()
                
                # Remove all existing rows for this model
                rows_before = len(df_existing)
                df_existing = df_existing[df_existing['embedding_model'] != model_to_add]
                rows_removed = rows_before - len(df_existing)
                
                if rows_removed > 0:
                    self.logger.info(f"Removed {rows_removed} existing rows for model: {model_to_add}")
                
                # Create fresh rows for current model with all variant_ids
                new_data = []
                coordinate_columns = ['pca_x', 'pca_y', 't-sne_x', 't-sne_y', 'umap_x', 'umap_y']
                
                for variant_id in variant_ids:
                    row = {'variant_id': variant_id, 'embedding_model': model_to_add}
                    row.update({col: None for col in coordinate_columns})
                    new_data.append(row)
                
                # Combine: existing rows (without this model) + new rows for this model
                df_new = pd.DataFrame(new_data)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                self.save_parquet(df_combined)
                
                self.logger.info(f"✓ Replaced rows for model: {model_to_add} ({len(variant_ids)} variants)")
                self.logger.info(f"  New shape: {df_combined.shape}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating parquet file: {e}")
                raise
    
    def _create_initial_dataframe(self, variant_ids: List[str], embedding_models: List[str]) -> pd.DataFrame:
        """Create initial dataframe with all variant-model combinations."""
        data = []
        coordinate_columns = ['pca_x', 'pca_y', 't-sne_x', 't-sne_y', 'umap_x', 'umap_y']
        
        for variant_id in variant_ids:
            for model in embedding_models:
                row = {'variant_id': variant_id, 'embedding_model': model}
                row.update({col: None for col in coordinate_columns})
                data.append(row)
        
        return pd.DataFrame(data)
    
    
    def merge_coordinates(self, 
                         model_name: str, 
                         coordinates_data: Dict[str, Dict[str, Tuple[float, float]]],
                         reset_results: bool = False) -> bool:
        """
        Merge coordinates data into the parquet file.
        
        Args:
            model_name: Name of the embedding model
            coordinates_data: Dict mapping variant_id to coordinate methods
                             Format: {variant_id: {method: (x, y)}}
                             Example: {"17-43044346-C-T": {"pca": (1.0, 2.0), "t-sne": (3.0, 4.0)}}
            reset_results: If True, clear existing coordinates for this model before merging
        
        Returns:
            True if merge successful
        """
        try:
            import time
            start_time = time.time()
            
            # Load existing parquet
            load_start = time.time()
            df_existing = self.load_parquet()
            load_time = time.time() - load_start
            self.logger.debug(f"  Loaded parquet in {load_time:.2f}s")
            
            # If reset_results is True, clear existing coordinates for this model
            if reset_results:
                model_mask = df_existing['embedding_model'] == model_name
                coordinate_columns = ['pca_x', 'pca_y', 't-sne_x', 't-sne_y', 'umap_x', 'umap_y']
                for col in coordinate_columns:
                    if col in df_existing.columns:
                        df_existing.loc[model_mask, col] = None
                self.logger.info(f"  Cleared existing coordinates for model: {model_name}")
            
            # Update coordinates for the specific model
            merge_start = time.time()
            for variant_id, methods in coordinates_data.items():
                # Find the row for this variant_id and model_name combination
                mask = (df_existing['variant_id'] == variant_id) & (df_existing['embedding_model'] == model_name)
                
                if mask.any():
                    for method, (x, y) in methods.items():
                        # Map method names to column names
                        x_col = f"{method}_x"
                        y_col = f"{method}_y"
                        
                        if x_col in df_existing.columns and y_col in df_existing.columns:
                            df_existing.loc[mask, x_col] = x
                            df_existing.loc[mask, y_col] = y
                        else:
                            self.logger.warning(f"Columns {x_col} or {y_col} not found for method {method}")
                else:
                    self.logger.warning(f"No row found for variant_id={variant_id}, model={model_name}")
            
            merge_time = time.time() - merge_start
            self.logger.info(f"  Updated coordinates for {len(coordinates_data)} variants in {merge_time:.2f}s")
            
            # Save updated parquet using base class method
            save_start = time.time()
            self.save_parquet(df_existing)
            save_time = time.time() - save_start
            self.logger.debug(f"  Saved parquet in {save_time:.2f}s")
            
            total_time = time.time() - start_time
            self.logger.info(f"  Total merge time: {total_time:.2f}s")
            
            self.logger.info(f"✓ Merged coordinates for model: {model_name}")
            self.logger.info(f"  Variants updated: {len(coordinates_data)}")
            self.logger.info(f"  Updated shape: {df_existing.shape}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error merging coordinates: {e}")
            raise
    
    def get_coordinates_for_model(self, model_name: str) -> pd.DataFrame:
        """
        Get coordinates for a specific model.
        
        Args:
            model_name: Name of the embedding model
            
        Returns:
            DataFrame with coordinates for the specified model
        """
        try:
            df = self.load_parquet()
            
            # Filter rows for the specific model
            df_model = df[df['embedding_model'] == model_name].copy()
            
            if df_model.empty:
                self.logger.warning(f"No coordinates found for model: {model_name}")
                return pd.DataFrame()
            
            self.logger.info(f"Retrieved coordinates for model: {model_name}")
            self.logger.debug(f"  Retrieved coordinates for model: {model_name} - Rows: {len(df_model)}")
            
            return df_model
            
        except Exception as e:
            self.logger.error(f"Error getting coordinates for model: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """
        Get list of models that have coordinates stored.
        
        Returns:
            List of model names
        """
        try:
            df = self.load_parquet()
            
            if 'embedding_model' not in df.columns:
                self.logger.warning("embedding_model column not found")
                return []
            
            # Get unique embedding models
            models = df['embedding_model'].unique().tolist()
            models.sort()
            
            return models
            
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return []
    
    def get_coordinate_columns(self) -> List[str]:
        """Get list of coordinate columns (pca_x, pca_y, etc.)."""
        return ['pca_x', 'pca_y', 't-sne_x', 't-sne_y', 'umap_x', 'umap_y']
    
    def has_coordinates_for_model(self, model_name: str) -> bool:
        """Check if coordinates exist for a specific model."""
        try:
            df = self.load_parquet()
            model_data = df[df['embedding_model'] == model_name]
            if model_data.empty:
                return False
            
            # Check if any coordinate columns have non-null values
            coord_cols = self.get_coordinate_columns()
            return model_data[coord_cols].notna().any().any()
            
        except Exception:
            return False
    

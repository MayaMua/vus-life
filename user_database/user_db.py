#!/usr/bin/env python3
"""
Simple UserDB facade - delegates everything to UserDatabaseManager.
This provides backward compatibility and a clean interface.
"""

from typing import Optional, Dict, Any, List, Tuple
import pandas as pd

from .user_database_manager import UserDatabaseManager


class UserDB:
    """
    Simple facade for UserDatabaseManager.
    All methods delegate to the underlying manager.
    """
    
    def __init__(self, db_path: str):
        """Initialize UserDB facade."""
        self.manager = UserDatabaseManager(db_path)
    
    # Delegate all methods to the manager
    def __getattr__(self, name):
        """Delegate all unknown methods to the manager."""
        return getattr(self.manager, name)
    
    # Explicit delegation for clarity (optional)
    def exists(self) -> bool:
        return self.manager.exists()
    
    def initialize(self) -> bool:
        return self.manager.initialize()
    
    def validate_schema(self) -> Dict[str, bool]:
        return self.manager.validate_schema()
    
    def get_status(self) -> Dict[str, Any]:
        return self.manager.get_status()
    
    def clear_all_data(self) -> bool:
        return self.manager.clear_all_data()
    
    def reset_database(self) -> bool:
        return self.manager.reset_database()
    
    def insert_variant(self, variant_data: Dict[str, Any]) -> bool:
        return self.manager.insert_variant(variant_data)
    
    def insert_variants_batch(self, variants_df: pd.DataFrame) -> Tuple[int, int]:
        return self.manager.insert_variants_batch(variants_df)
    
    def save_annotation(self, variant_id: str, annotation_type: str,
                       raw_data: str = None, processed_data: str = None) -> bool:
        return self.manager.save_annotation(variant_id, annotation_type, raw_data, processed_data)
    
    def save_prediction(self, variant_id: str, model_name: str,
                       annotation_type: str, predicted_pathogenicity: str,
                       top_20_neighbors: List[str],
                       top_20_neighbors_original_pathogenicity: List[str]) -> bool:
        return self.manager.save_prediction(
            variant_id, model_name, annotation_type, 
            predicted_pathogenicity, top_20_neighbors,
            top_20_neighbors_original_pathogenicity
        )
    
    def get_all_variants(self) -> pd.DataFrame:
        return self.manager.get_all_variants()
    
    def get_variant_by_id(self, variant_id: str) -> Optional[Dict[str, Any]]:
        return self.manager.get_variant_by_id(variant_id)
    
    def get_variants_by_gene(self, gene: str) -> pd.DataFrame:
        return self.manager.get_variants_by_gene(gene)
    
    def get_predictions(self, variant_id: Optional[str] = None) -> pd.DataFrame:
        return self.manager.get_predictions(variant_id)
    
    def get_variant_with_prediction(self, variant_id: str) -> Dict[str, Any]:
        return self.manager.get_variant_with_prediction(variant_id)
    
    def get_annotation(self, variant_id: str, annotation_type: str = 'vep') -> Optional[Dict[str, str]]:
        return self.manager.get_annotation(variant_id, annotation_type)
    
    def get_statistics(self) -> Dict[str, Any]:
        return self.manager.get_statistics()
    
    def get_summary_report(self) -> Dict[str, Any]:
        return self.manager.get_summary_report()
    
    def print_statistics(self):
        return self.manager.print_statistics()
    
    def close(self):
        return self.manager.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
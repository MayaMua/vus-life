#!/usr/bin/env python3
"""
Neighbor Results Manager for user database.
Handles saving and retrieving neighbor analysis results.
"""

import json
import sqlite3
import logging
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.user_database.user_database_manager import UserDatabaseManager


class NeighborResultsManager:
    """
    Manager for neighbor analysis results in user database.
    
    Handles:
    - Saving neighbor results from JSON files
    - Retrieving neighbor results by variant/model/annotation
    - Coordinate data management
    - Neighbor information storage
    """
    
    def __init__(self, db_path: str):
        """
        Initialize neighbor results manager.
        
        Args:
            db_path: Path to the user database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure database exists with proper schema
        db_manager = UserDatabaseManager(db_path)
        if not db_manager.exists():
            self.logger.info("Database doesn't exist, creating with schema...")
            db_manager.create_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def save_neighbor_results_from_json(self, json_file_path: str) -> Dict[str, Any]:
        """
        Save neighbor results from JSON file to database.
        
        Args:
            json_file_path: Path to the JSON file containing neighbor results
            
        Returns:
            Dictionary with save results
        """
        try:
            # Load JSON data
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            results = data.get('results', {})
            
            model_name = metadata.get('model_name', 'unknown')
            annotation_method = metadata.get('annotation_type', 'unknown')
            n_neighbors = metadata.get('n_neighbors', 20)
            
            self.logger.info(f"Saving neighbor results: {model_name} + {annotation_method}")
            self.logger.info(f"Processing {len(results)} variants")
            
            # Prepare data for database insertion
            records_to_insert = []
            
            for variant_id, result_data in results.items():
                # Extract coordinates
                coordinates = result_data.get('coordinates', [])
                pca_coords = coordinates[0] if len(coordinates) > 0 else {}
                tsne_coords = coordinates[1] if len(coordinates) > 1 else {}
                umap_coords = coordinates[2] if len(coordinates) > 2 else {}
                
                # Extract neighbor information
                nearest_variants = result_data.get('nearest_training_variants', [])
                pathogenicity = result_data.get('pathogenicity', [])
                distances = result_data.get('distances', [])
                
                # Create record
                record = {
                    'variant_id': variant_id,
                    'embedding_model': model_name,
                    'annotation_method': annotation_method,
                    'pca_x': pca_coords.get('pca_x'),
                    'pca_y': pca_coords.get('pca_y'),
                    'tsne_x': tsne_coords.get('tsne_x'),
                    'tsne_y': tsne_coords.get('tsne_y'),
                    'umap_x': umap_coords.get('umap_x'),
                    'umap_y': umap_coords.get('umap_y'),
                    'nearest_training_variants': json.dumps(nearest_variants),
                    'neighbor_pathogenicity': json.dumps(pathogenicity),
                    'neighbor_distances': json.dumps(distances),
                    'n_neighbors': n_neighbors
                }
                
                records_to_insert.append(record)
            
            # Insert records into database
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Use INSERT OR REPLACE to handle duplicates
            insert_sql = """
            INSERT OR REPLACE INTO neighbor_results (
                variant_id, embedding_model, annotation_method,
                pca_x, pca_y, tsne_x, tsne_y, umap_x, umap_y,
                nearest_training_variants, neighbor_pathogenicity, neighbor_distances,
                n_neighbors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            inserted_count = 0
            for record in records_to_insert:
                cursor.execute(insert_sql, (
                    record['variant_id'],
                    record['embedding_model'],
                    record['annotation_method'],
                    record['pca_x'],
                    record['pca_y'],
                    record['tsne_x'],
                    record['tsne_y'],
                    record['umap_x'],
                    record['umap_y'],
                    record['nearest_training_variants'],
                    record['neighbor_pathogenicity'],
                    record['neighbor_distances'],
                    record['n_neighbors']
                ))
                inserted_count += 1
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✓ Saved {inserted_count} neighbor results to database")
            
            return {
                'success': True,
                'inserted_count': inserted_count,
                'model_name': model_name,
                'annotation_method': annotation_method,
                'n_neighbors': n_neighbors
            }
            
        except Exception as e:
            self.logger.error(f"Error saving neighbor results: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_neighbor_results(self, 
                           variant_id: Optional[str] = None,
                           embedding_model: Optional[str] = None,
                           annotation_method: Optional[str] = None,
                           limit: int = 100) -> pd.DataFrame:
        """
        Retrieve neighbor results from database.
        
        Args:
            variant_id: Filter by specific variant ID
            embedding_model: Filter by embedding model
            annotation_method: Filter by annotation method
            limit: Maximum number of results to return
            
        Returns:
            DataFrame with neighbor results
        """
        try:
            conn = self._get_connection()
            
            # Build query with optional filters
            where_conditions = []
            params = []
            
            if variant_id:
                where_conditions.append("variant_id = ?")
                params.append(variant_id)
            
            if embedding_model:
                where_conditions.append("embedding_model = ?")
                params.append(embedding_model)
            
            if annotation_method:
                where_conditions.append("annotation_method = ?")
                params.append(annotation_method)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            query = f"""
            SELECT * FROM neighbor_results 
            {where_clause}
            ORDER BY analysis_date DESC
            LIMIT ?
            """
            params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Parse JSON columns
            if not df.empty:
                df['nearest_training_variants'] = df['nearest_training_variants'].apply(
                    lambda x: json.loads(x) if x else []
                )
                df['neighbor_pathogenicity'] = df['neighbor_pathogenicity'].apply(
                    lambda x: json.loads(x) if x else []
                )
                df['neighbor_distances'] = df['neighbor_distances'].apply(
                    lambda x: json.loads(x) if x else []
                )
            
            self.logger.info(f"Retrieved {len(df)} neighbor results")
            return df
            
        except Exception as e:
            self.logger.error(f"Error retrieving neighbor results: {e}")
            return pd.DataFrame()
    
    def get_coordinates_for_visualization(self, 
                                        embedding_model: str,
                                        annotation_method: str) -> pd.DataFrame:
        """
        Get coordinates data for visualization.
        
        Args:
            embedding_model: Embedding model name
            annotation_method: Annotation method
            
        Returns:
            DataFrame with coordinates for visualization
        """
        try:
            conn = self._get_connection()
            
            query = """
            SELECT variant_id, pca_x, pca_y, tsne_x, tsne_y, umap_x, umap_y
            FROM neighbor_results
            WHERE embedding_model = ? AND annotation_method = ?
            AND pca_x IS NOT NULL AND pca_y IS NOT NULL
            """
            
            df = pd.read_sql_query(query, conn, params=[embedding_model, annotation_method])
            conn.close()
            
            self.logger.info(f"Retrieved coordinates for {len(df)} variants")
            return df
            
        except Exception as e:
            self.logger.error(f"Error retrieving coordinates: {e}")
            return pd.DataFrame()
    
    def get_neighbor_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored neighbor results.
        
        Returns:
            Dictionary with statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get basic counts
            cursor.execute("SELECT COUNT(*) FROM neighbor_results")
            total_records = cursor.fetchone()[0]
            
            # Get model distribution
            cursor.execute("""
                SELECT embedding_model, COUNT(*) as count
                FROM neighbor_results
                GROUP BY embedding_model
            """)
            model_distribution = dict(cursor.fetchall())
            
            # Get annotation method distribution
            cursor.execute("""
                SELECT annotation_method, COUNT(*) as count
                FROM neighbor_results
                GROUP BY annotation_method
            """)
            annotation_distribution = dict(cursor.fetchall())
            
            # Get date range
            cursor.execute("""
                SELECT MIN(analysis_date) as earliest, MAX(analysis_date) as latest
                FROM neighbor_results
            """)
            date_range = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_records': total_records,
                'model_distribution': model_distribution,
                'annotation_distribution': annotation_distribution,
                'date_range': {
                    'earliest': date_range[0],
                    'latest': date_range[1]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}


def main():
    """Test the neighbor results manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neighbor Results Manager")
    parser.add_argument("--db-path", default="user_exports/user_database.db",
                       help="Path to user database")
    parser.add_argument("--json-file", help="JSON file to import")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    manager = NeighborResultsManager(args.db_path)
    
    if args.json_file:
        result = manager.save_neighbor_results_from_json(args.json_file)
        print(f"Import result: {result}")
    
    if args.stats:
        stats = manager.get_neighbor_statistics()
        print(f"Statistics: {stats}")


if __name__ == "__main__":
    main()

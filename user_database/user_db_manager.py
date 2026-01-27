#!/usr/bin/env python3
"""
User database manager for storing user-submitted variants and predictions.
This database is personal to each user and not shared.

Database is automatically created when the frontend app initializes.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime


class UserDatabaseManager:
    """
    Manages user's personal variant database.
    Each user has their own database file.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize user database.
        
        Args:
            db_path: Path to the user's database file (will be created if doesn't exist)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables for user variants, annotations, and predictions."""
        
        # User variants table - stores uploaded variants
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_variants (
                variant_id TEXT PRIMARY KEY,
                hgvs_genomic_38 TEXT,
                hgvs_coding TEXT,
                hgvs_protein TEXT,
                gene TEXT,
                chromosome TEXT,
                position INTEGER,
                ref_allele TEXT,
                alt_allele TEXT,
                consequence TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Annotations table - stores VEP and other annotation data
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                variant_id TEXT PRIMARY KEY,
                
                -- VEP annotations
                vep_raw TEXT,
                vep_processed TEXT,
                
                -- AnnoVar annotations (placeholder for future)
                annovar_raw TEXT,
                annovar_processed TEXT,
                
                -- SnpEff annotations (placeholder for future)
                snpeff_raw TEXT,
                snpeff_processed TEXT,
                
                FOREIGN KEY (variant_id) REFERENCES user_variants(variant_id)
            )
        ''')
        
        # Prediction results table - stores predictions with top 20 neighbors
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_results (
                variant_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                annotation_type TEXT NOT NULL,
                predicted_pathogenicity TEXT,
                top_20_neighbors TEXT,
                top_20_neighbors_original_pathogenicity TEXT,
                prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (variant_id) REFERENCES user_variants(variant_id)
            )
        ''')
        
        self.conn.commit()
    
    def insert_variant(self, variant_data: Dict[str, Any]) -> bool:
        """
        Insert a single variant into the database.
        
        Args:
            variant_data: Dictionary with variant information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO user_variants 
                (variant_id, hgvs_genomic_38, hgvs_coding, hgvs_protein, 
                 gene, chromosome, position, ref_allele, alt_allele, consequence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                variant_data.get('variant_id'),
                variant_data.get('hgvs_genomic_38'),
                variant_data.get('hgvs_coding'),
                variant_data.get('hgvs_protein'),
                variant_data.get('gene'),
                variant_data.get('chromosome'),
                variant_data.get('position'),
                variant_data.get('ref_allele'),
                variant_data.get('alt_allele'),
                variant_data.get('consequence')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting variant: {e}")
            return False
    
    def insert_variants_batch(self, variants_df: pd.DataFrame) -> int:
        """
        Insert multiple variants from DataFrame.
        
        Args:
            variants_df: DataFrame with variant information
            
        Returns:
            Number of variants successfully inserted
        """
        success_count = 0
        
        for _, row in variants_df.iterrows():
            variant_data = {
                'variant_id': row.get('variant_id'),
                'hgvs_genomic_38': row.get('hgvs_genomic_38'),
                'hgvs_coding': row.get('hgvs_coding'),
                'hgvs_protein': row.get('hgvs_protein'),
                'gene': row.get('gene'),
                'chromosome': row.get('chromosome'),
                'position': row.get('position'),
                'ref_allele': row.get('ref_allele'),
                'alt_allele': row.get('alt_allele'),
                'consequence': row.get('consequence')
            }
            
            if self.insert_variant(variant_data):
                success_count += 1
        
        return success_count
    
    def save_annotation(self, variant_id: str, annotation_type: str, 
                       raw_data: str = None, processed_data: str = None) -> bool:
        """
        Save annotation data for a variant.
        
        Args:
            variant_id: Variant identifier
            annotation_type: Type of annotation ('vep', 'annovar', or 'snpeff')
            raw_data: Raw annotation data (JSON string)
            processed_data: Processed annotation text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing annotation if any
            self.cursor.execute('SELECT * FROM annotations WHERE variant_id = ?', (variant_id,))
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing annotation
                if annotation_type == 'vep':
                    self.cursor.execute('''
                        UPDATE annotations 
                        SET vep_raw = ?, vep_processed = ?
                        WHERE variant_id = ?
                    ''', (raw_data, processed_data, variant_id))
                elif annotation_type == 'annovar':
                    self.cursor.execute('''
                        UPDATE annotations 
                        SET annovar_raw = ?, annovar_processed = ?
                        WHERE variant_id = ?
                    ''', (raw_data, processed_data, variant_id))
                elif annotation_type == 'snpeff':
                    self.cursor.execute('''
                        UPDATE annotations 
                        SET snpeff_raw = ?, snpeff_processed = ?
                        WHERE variant_id = ?
                    ''', (raw_data, processed_data, variant_id))
            else:
                # Insert new annotation
                if annotation_type == 'vep':
                    self.cursor.execute('''
                        INSERT INTO annotations (variant_id, vep_raw, vep_processed)
                        VALUES (?, ?, ?)
                    ''', (variant_id, raw_data, processed_data))
                elif annotation_type == 'annovar':
                    self.cursor.execute('''
                        INSERT INTO annotations (variant_id, annovar_raw, annovar_processed)
                        VALUES (?, ?, ?)
                    ''', (variant_id, raw_data, processed_data))
                elif annotation_type == 'snpeff':
                    self.cursor.execute('''
                        INSERT INTO annotations (variant_id, snpeff_raw, snpeff_processed)
                        VALUES (?, ?, ?)
                    ''', (variant_id, raw_data, processed_data))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving annotation: {e}")
            return False
    
    def save_prediction(self, variant_id: str, model_name: str, 
                       annotation_type: str, predicted_pathogenicity: str,
                       top_20_neighbors: List[str],
                       top_20_neighbors_original_pathogenicity: List[str]) -> bool:
        """
        Save prediction result for a variant with top 20 nearest neighbors.
        
        Args:
            variant_id: Variant identifier
            model_name: Name of the embedding model used
            annotation_type: Type of annotation (e.g., 'vep')
            predicted_pathogenicity: Predicted pathogenicity classification
            top_20_neighbors: List of top 20 nearest neighbor variant IDs
            top_20_neighbors_original_pathogenicity: List of original pathogenicity labels for the 20 neighbors
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert lists to JSON strings
            neighbors_json = json.dumps(top_20_neighbors)
            neighbors_pathogenicity_json = json.dumps(top_20_neighbors_original_pathogenicity)
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO prediction_results 
                (variant_id, model_name, annotation_type, 
                 predicted_pathogenicity, top_20_neighbors, top_20_neighbors_original_pathogenicity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (variant_id, model_name, annotation_type, 
                  predicted_pathogenicity, neighbors_json, neighbors_pathogenicity_json))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving prediction: {e}")
            return False
    
    def get_all_variants(self) -> pd.DataFrame:
        """
        Get all user variants as DataFrame.
        
        Returns:
            DataFrame with all user variants
        """
        query = "SELECT * FROM user_variants"
        return pd.read_sql_query(query, self.conn)
    
    def get_predictions(self, variant_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get prediction results.
        
        Args:
            variant_id: Optional specific variant ID to query
            
        Returns:
            DataFrame with prediction results
        """
        if variant_id:
            query = "SELECT * FROM prediction_results WHERE variant_id = ?"
            return pd.read_sql_query(query, self.conn, params=(variant_id,))
        else:
            query = "SELECT * FROM prediction_results"
            return pd.read_sql_query(query, self.conn)
    
    def get_variant_with_prediction(self, variant_id: str) -> Dict[str, Any]:
        """
        Get complete information (variant + prediction) for a variant.
        
        Args:
            variant_id: Variant identifier
            
        Returns:
            Dictionary with variant and prediction information
        """
        query = """
            SELECT v.*, p.model_name, p.annotation_type, 
                   p.predicted_pathogenicity, 
                   p.top_20_neighbors, p.top_20_neighbors_original_pathogenicity,
                   p.prediction_date
            FROM user_variants v
            LEFT JOIN prediction_results p ON v.variant_id = p.variant_id
            WHERE v.variant_id = ?
        """
        
        self.cursor.execute(query, (variant_id,))
        row = self.cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            result = dict(zip(columns, row))
            
            # Parse JSON fields if present
            if result.get('top_20_neighbors'):
                result['top_20_neighbors'] = json.loads(result['top_20_neighbors'])
            if result.get('top_20_neighbors_original_pathogenicity'):
                result['top_20_neighbors_original_pathogenicity'] = json.loads(result['top_20_neighbors_original_pathogenicity'])
            
            return result
        
        return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        stats = {}
        
        # Total variants
        self.cursor.execute("SELECT COUNT(*) FROM user_variants")
        stats['total_variants'] = self.cursor.fetchone()[0]
        
        # Variants with predictions
        self.cursor.execute("SELECT COUNT(*) FROM prediction_results")
        stats['variants_with_predictions'] = self.cursor.fetchone()[0]
        
        # Variants by gene
        self.cursor.execute("""
            SELECT gene, COUNT(*) as count 
            FROM user_variants 
            GROUP BY gene
        """)
        stats['variants_by_gene'] = dict(self.cursor.fetchall())
        
        # Predicted pathogenicity distribution
        self.cursor.execute("""
            SELECT predicted_pathogenicity, COUNT(*) as count 
            FROM prediction_results 
            GROUP BY predicted_pathogenicity
        """)
        stats['pathogenicity_distribution'] = dict(self.cursor.fetchall())
        
        return stats
    
    def clear_all_data(self):
        """
        Clear all data from the database (keep tables).
        This deletes all records but preserves the table structure.
        """
        try:
            # Delete in order to respect foreign key constraints
            self.cursor.execute("DELETE FROM prediction_results")
            self.cursor.execute("DELETE FROM annotations")
            self.cursor.execute("DELETE FROM user_variants")
            self.conn.commit()
            print("✓ All data cleared from database")
        except Exception as e:
            print(f"Error clearing data: {e}")
            self.conn.rollback()
    
    def reset_database(self):
        """
        Complete database reset - drops all tables and recreates them.
        Use this for a fresh start.
        """
        try:
            # Drop all tables
            self.cursor.execute("DROP TABLE IF EXISTS prediction_results")
            self.cursor.execute("DROP TABLE IF EXISTS annotations")
            self.cursor.execute("DROP TABLE IF EXISTS user_variants")
            self.conn.commit()
            
            # Recreate tables
            self._create_tables()
            print("✓ Database reset complete - all tables recreated")
        except Exception as e:
            print(f"Error resetting database: {e}")
            self.conn.rollback()
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def get_user_database_path(user_id: Optional[str] = None) -> Path:
    """
    Get the path to the user's database file.
    
    Args:
        user_id: Optional user identifier (default: 'default_user')
        
    Returns:
        Path to the user's database file
    """
    if user_id is None:
        user_id = "default_user"
    
    # Store in user_exports/databases/
    db_dir = Path("user_exports/databases")
    db_dir.mkdir(parents=True, exist_ok=True)
    
    return db_dir / f"{user_id}_variants.db"


def initialize_user_database(user_id: Optional[str] = None) -> UserDatabaseManager:
    """
    Initialize user database (called automatically when frontend starts).
    
    Args:
        user_id: Optional user identifier
        
    Returns:
        UserDatabaseManager instance
    """
    db_path = get_user_database_path(user_id)
    return UserDatabaseManager(str(db_path))


# Example usage
if __name__ == "__main__":
    # Test database creation
    print("Testing user database creation...")
    
    with initialize_user_database() as db:
        print(f"✓ Database created at: {db.db_path}")
        
        # Test variant insertion
        test_variant = {
            'variant_id': '17-43044346-C-T',
            'hgvs_genomic_38': 'NC_000017.11:g.43044346C>T',
            'hgvs_coding': 'NM_007294.4:c.5266C>T',
            'hgvs_protein': 'p.Arg1756Ter',
            'gene': 'BRCA1',
            'chromosome': '17',
            'position': 43044346,
            'ref_allele': 'C',
            'alt_allele': 'T',
            'consequence': 'stop_gained'
        }
        
        if db.insert_variant(test_variant):
            print("✓ Test variant inserted")
        
        # Test prediction insertion
        top_20_variant_ids = [f"17-430{i:05d}-A-T" for i in range(20)]
        if db.save_prediction(
            variant_id='17-43044346-C-T',
            model_name='all-mpnet-base-v2',
            annotation_type='vep',  
            top_20_neighbors_original_pathogenicity=['pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic', 'pathogenic'],
            predicted_pathogenicity='pathogenic',
            top_20_neighbors=top_20_variant_ids
        ):
            print("✓ Test prediction saved")
        
        # Get statistics
        stats = db.get_statistics()
        print(f"\n✓ Database statistics:")
        print(f"  Total variants: {stats['total_variants']}")
        print(f"  Variants with predictions: {stats['variants_with_predictions']}")
        
        print("\n✅ Database initialization test passed!")


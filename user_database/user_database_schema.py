#!/usr/bin/env python3
"""
Schema definitions for user variant database.
Follows the same pattern as backend/database_operation/database_schema.py
"""

from typing import List, Dict, Any

# =============================================================================
# Table Schema Definitions
# =============================================================================

def get_user_variants_table_schema() -> str:
    """
    Get the SQL statement for creating the user_variants table.
    
    Returns:
        str: SQL CREATE TABLE statement for user_variants
    """
    return """
    CREATE TABLE IF NOT EXISTS user_variants (
        variant_id TEXT PRIMARY KEY,
        hgvs_genomic_38 TEXT,
        hgvs_coding TEXT,
        hgvs_protein TEXT,
        protein_position INTEGER,
        wild_type_aa TEXT,
        mutant_aa TEXT,
        gene TEXT,
        chromosome TEXT,
        position INTEGER,
        ref_allele TEXT,
        alt_allele TEXT,
        consequence TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """


def get_user_annotations_table_schema() -> str:
    """
    Get the SQL statement for creating the annotations table.
    
    Returns:
        str: SQL CREATE TABLE statement for annotations
    """
    return """
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
    );
    """


def get_prediction_results_table_schema() -> str:
    """
    Get the SQL statement for creating the prediction_results table.
    
    Returns:
        str: SQL CREATE TABLE statement for prediction_results
    """
    return """
    CREATE TABLE IF NOT EXISTS prediction_results (
        variant_id TEXT PRIMARY KEY,
        model_name TEXT NOT NULL,
        annotation_method TEXT NOT NULL,
        predicted_pathogenicity TEXT,
        top_20_neighbors TEXT,
        top_20_neighbors_original_pathogenicity TEXT,
        prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (variant_id) REFERENCES user_variants(variant_id)
    );
    """


def get_neighbor_results_table_schema() -> str:
    """
    Get the SQL statement for creating the neighbor_results table.
    Stores test variant neighbor analysis results including coordinates and nearest neighbors.
    
    Returns:
        str: SQL CREATE TABLE statement for neighbor_results
    """
    return """
    CREATE TABLE IF NOT EXISTS neighbor_results (
        variant_id TEXT NOT NULL,
        embedding_model TEXT NOT NULL,
        annotation_method TEXT NOT NULL,
        
        -- Dimension reduction coordinates (consistent with parquet structure)
        pca_x REAL,
        pca_y REAL,
        tsne_x REAL,
        tsne_y REAL,
        umap_x REAL,
        umap_y REAL,
        
        -- Neighbor information (JSON format for flexibility)
        nearest_training_variants TEXT,  -- JSON array of variant IDs
        neighbor_pathogenicity TEXT,     -- JSON array of pathogenicity labels
        neighbor_distances TEXT,         -- JSON array of distances
        
        -- Metadata
        n_neighbors INTEGER DEFAULT 20,
        analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        PRIMARY KEY (variant_id, embedding_model, annotation_method),
        FOREIGN KEY (variant_id) REFERENCES user_variants(variant_id)
    );
    """


# =============================================================================
# Index Definitions
# =============================================================================

def get_database_indexes() -> List[str]:
    """
    Get list of SQL statements for creating database indexes.
    
    Returns:
        List[str]: List of CREATE INDEX statements
    """
    return [
        "CREATE INDEX IF NOT EXISTS idx_user_variants_gene ON user_variants(gene);",
        "CREATE INDEX IF NOT EXISTS idx_user_variants_chromosome_position ON user_variants(chromosome, position);",
        "CREATE INDEX IF NOT EXISTS idx_predictions_model ON prediction_results(model_name);",
        "CREATE INDEX IF NOT EXISTS idx_predictions_pathogenicity ON prediction_results(predicted_pathogenicity);",
        "CREATE INDEX IF NOT EXISTS idx_neighbor_results_model ON neighbor_results(embedding_model);",
        "CREATE INDEX IF NOT EXISTS idx_neighbor_results_annotation ON neighbor_results(annotation_method);",
        "CREATE INDEX IF NOT EXISTS idx_neighbor_results_analysis_date ON neighbor_results(analysis_date);"
    ]


# =============================================================================
# Table Information
# =============================================================================

def get_required_tables() -> List[str]:
    """
    Get list of required table names.
    
    Returns:
        List[str]: List of table names
    """
    return ["user_variants", "annotations", "prediction_results", "neighbor_results"]


def get_schema_info() -> Dict[str, Any]:
    """
    Get comprehensive schema information.
    
    Returns:
        Dict containing schema version and table information
    """
    return {
        "version": "1.0.0",
        "tables": {
            "user_variants": {
                "description": "User-submitted variants",
                "primary_key": "variant_id"
            },
            "annotations": {
                "description": "VEP and other annotation data",
                "primary_key": "variant_id",
                "foreign_keys": ["variant_id -> user_variants"]
            },
            "prediction_results": {
                "description": "Prediction results with top 20 neighbors",
                "primary_key": "variant_id",
                "foreign_keys": ["variant_id -> user_variants"]
            },
            "neighbor_results": {
                "description": "Test variant neighbor analysis results with coordinates",
                "primary_key": "(variant_id, embedding_model, annotation_method)",
                "foreign_keys": ["variant_id -> user_variants"]
            }
        }
    }




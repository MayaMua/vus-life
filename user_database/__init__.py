#!/usr/bin/env python3
"""
Simplified user variant database management system.

This module provides a streamlined database system for managing user-submitted variants,
their annotations, and prediction results.

Main Components:
- UserDatabaseManager: All-in-one database operations
- UserDB: Simple facade (optional, for backward compatibility)

Example Usage:
    from frontend.user_database import initialize_user_database, UserDatabaseManager
    
    # Method 1: Use helper function (recommended)
    user_db = initialize_user_database()
    
    # Method 2: Direct instantiation
    user_db = UserDatabaseManager("user_exports/databases/my_variants.db")
    
    # Insert variant
    user_db.insert_variant({
        'variant_id': 'chr17_41234567_G_A',
        'gene': 'BRCA1',
        'chromosome': 'chr17',
        'position': 41234567
    })
    
    # Query
    variants = user_db.get_all_variants()
    
    # Statistics
    stats = user_db.get_statistics()
"""

from pathlib import Path
from .user_database_manager import UserDatabaseManager
from .user_db import UserDB

__all__ = [
    'UserDatabaseManager',
    'UserDB',
    'initialize_user_database',
    'get_default_database_path'
]


def get_default_database_path(user_id: str = "default") -> str:
    """
    Get the default database path for a user.
    
    Args:
        user_id: User identifier (default: "default")
        
    Returns:
        str: Path to the user database file
    """
    base_dir = Path("user_exports/databases")
    base_dir.mkdir(parents=True, exist_ok=True)
    return str(base_dir / f"{user_id}_user_variants.db")


def initialize_user_database(user_id: str = "default", db_path: str = None) -> UserDatabaseManager:
    """
    Initialize and return a UserDatabaseManager instance.
    
    If database doesn't exist, it will be created automatically.
    
    Args:
        user_id: User identifier (default: "default")
        db_path: Optional custom database path. If None, uses default path.
        
    Returns:
        UserDatabaseManager: Initialized database instance
        
    Example:
        >>> user_db = initialize_user_database()
        >>> user_db.insert_variant({'variant_id': 'chr1_12345_A_T', 'gene': 'BRCA1'})
    """
    if db_path is None:
        db_path = get_default_database_path(user_id)
    
    user_db = UserDatabaseManager(db_path)
    return user_db
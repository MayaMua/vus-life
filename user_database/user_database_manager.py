#!/usr/bin/env python3
"""
Simplified User Database Manager for variant annotation system.
Provides essential database operations for user-submitted variants.
"""

import sqlite3
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add parent directories to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import user database schema definitions
from frontend.user_database.user_database_schema import (
    get_user_variants_table_schema, get_user_annotations_table_schema, 
    get_prediction_results_table_schema, get_neighbor_results_table_schema,
    get_database_indexes, get_required_tables, get_schema_info
)


class UserDatabaseManager:
    """
    Simplified user database manager for variant annotation system.
    
    Core functionality:
    - Database creation and initialization
    - Basic operations (init, reset, clear, delete)
    - Status and statistics
    """
    
    def __init__(self, db_path: str):
        """Initialize UserDatabaseManager with database path."""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        if db_dir != Path('.'):
            db_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper settings."""
        if not self.db_path:
            raise ValueError("Database path not set")
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    
    def exists(self) -> bool:
        """Check if database file exists and is accessible."""
        if not os.path.exists(self.db_path):
            return False
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            return len(tables) > 0
        except sqlite3.Error:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive database status and statistics."""
        if not self.exists():
            return {
                "exists": False,
                "accessible": False,
                "schema_valid": False,
                "user_tables": [],
                "record_counts": {},
                "total_variants": 0,
                "variants_with_predictions": 0,
                "variants_with_annotations": 0
            }
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            user_tables = [row[0] for row in cursor.fetchall()]
            
            # Get record counts
            record_counts = {}
            for table in user_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                record_counts[table] = cursor.fetchone()[0]
            
            # Check schema validity
            required_tables = get_required_tables()
            schema_valid = all(table in user_tables for table in required_tables)
            
            # Get SQLite version
            cursor.execute("SELECT sqlite_version();")
            sqlite_version = cursor.fetchone()[0]
            
            # Check foreign keys
            cursor.execute("PRAGMA foreign_keys;")
            foreign_keys_enabled = bool(cursor.fetchone()[0])
            
            conn.close()
            
            return {
                "exists": True,
                "accessible": True,
                "schema_valid": schema_valid,
                "user_tables": user_tables,
                "record_counts": record_counts,
                "total_variants": record_counts.get("user_variants", 0),
                "variants_with_predictions": record_counts.get("prediction_results", 0),
                "variants_with_annotations": record_counts.get("annotations", 0),
                "sqlite_version": sqlite_version,
                "foreign_keys_enabled": foreign_keys_enabled,
                "missing_tables": [table for table in required_tables if table not in user_tables]
            }
            
        except sqlite3.Error as e:
            return {
                "exists": True,
                "accessible": False,
                "error": str(e),
                "schema_valid": False,
                "user_tables": [],
                "record_counts": {},
                "total_variants": 0,
                "variants_with_predictions": 0,
                "variants_with_annotations": 0
            }
    
    def create_database(self, reset: bool = False) -> bool:
        """Create database with user schema."""
        try:
            # Handle reset
            if reset and os.path.exists(self.db_path):
                os.remove(self.db_path)
                self.logger.info(f"Removed existing database: {self.db_path}")
            
            # Create database directory
            db_dir = Path(self.db_path).parent
            if db_dir != Path('.'):
                db_dir.mkdir(parents=True, exist_ok=True)
            
            # Create database and tables
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute(get_user_variants_table_schema())
            cursor.execute(get_user_annotations_table_schema())
            cursor.execute(get_prediction_results_table_schema())
            cursor.execute(get_neighbor_results_table_schema())
            
            # Create indexes
            for index_sql in get_database_indexes():
                cursor.execute(index_sql)
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Database created successfully: {self.db_path}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Database creation failed: {e}")
            return False
    
    def clear_all_data(self) -> bool:
        """Clear all data from database (keep tables)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            user_tables = [row[0] for row in cursor.fetchall()]
            
            # Clear each table
            for table in user_tables:
                cursor.execute(f"DELETE FROM {table};")
            
            conn.commit()
            conn.close()
            
            self.logger.info("All data cleared successfully")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to clear data: {e}")
            return False
    
    def reset_database(self) -> bool:
        """Reset database - delete file and recreate."""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                self.logger.info(f"Removed database: {self.db_path}")
            
            return self.create_database()
            
        except Exception as e:
            self.logger.error(f"Database reset failed: {e}")
            return False
    
    def delete_database(self) -> bool:
        """Delete database file completely."""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                self.logger.info(f"Deleted database: {self.db_path}")
                return True
            else:
                self.logger.warning(f"Database does not exist: {self.db_path}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete database: {e}")
            return False
    
    def initialize_database(self, reset: bool = False) -> bool:
        """Initialize database with schema creation."""
        success = self.create_database(reset=reset)
        
        if success:
            # Show created tables
            print("\nUser database tables created:")
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for table_name in ['user_variants', 'annotations', 'prediction_results']:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"\n{table_name.upper()} table columns:")
                for col in columns:
                    pk_indicator = " [PRIMARY KEY]" if col[5] == 1 else ""
                    print(f"  - {col[1]} ({col[2]}){pk_indicator}")
            
            conn.close()
        
        return success
    
    def print_status(self) -> None:
        """Print database status to console."""
        status = self.get_status()
        
        print(f"User Database: {self.db_path}")
        print("-" * 60)
        
        if not status['exists']:
            print("❌ Database file does not exist")
            return
        
        if not status['accessible']:
            print("❌ Database is not accessible")
            if 'error' in status:
                print(f"   Error: {status['error']}")
            return
        
        print("✅ Database file exists and accessible")
        print(f"📊 Tables: {len(status['user_tables'])} ({', '.join(status['user_tables'])})")
        
        if status['record_counts']:
            print("📈 Record counts:")
            for table, count in status['record_counts'].items():
                print(f"   - {table}: {count:,} records")
        
        if status['schema_valid']:
            print("✅ Schema is valid")
        else:
            print("⚠️  Schema validation issues:")
            if status.get('missing_tables'):
                print(f"   - Missing tables: {', '.join(status['missing_tables'])}")
        
        if status.get('sqlite_version'):
            print(f"🔧 SQLite version: {status['sqlite_version']}")
            print(f"🔧 Foreign keys enabled: {status['foreign_keys_enabled']}")
        
        print("-" * 60)
    
    def show_schema_info(self) -> None:
        """Display database schema information."""
        print("📋 User Database Schema")
        print("-" * 60)
        schema_info = get_schema_info()
        print(f"Version: {schema_info['version']}")
        print()
        
        for table_name, table_info in schema_info['tables'].items():
            print(f"📋 {table_name.upper()}")
            print(f"   Description: {table_info['description']}")
            print(f"   Primary Key: {table_info['primary_key']}")
            if 'foreign_keys' in table_info:
                print(f"   Foreign Keys: {', '.join(table_info['foreign_keys'])}")
            print()
    
    def close(self) -> None:
        """Close database connection (placeholder for compatibility)."""
        pass
    
    def run_cli(self, args: List[str] = None) -> None:
        """Run command-line interface."""
        parser = argparse.ArgumentParser(description='User Database Manager')
        parser.add_argument('--db-path', type=str, default=None,
                           help='Path to database file')
        parser.add_argument('--user-id', type=str, default='default',
                           help='User identifier (default: default)')
        parser.add_argument('--action', choices=['status', 'init', 'reset', 'clear', 'delete', 'schema'],
                           default='status', help='Action to perform')
        parser.add_argument('--reset', action='store_true',
                           help='Reset database (delete existing and create fresh)')
        
        if args is None:
            args = sys.argv[1:]
        
        parsed_args = parser.parse_args(args)
        
        # Set database path
        if parsed_args.db_path:
            self.db_path = parsed_args.db_path
        elif parsed_args.user_id != 'default':
            from frontend.user_database import get_default_database_path
            self.db_path = get_default_database_path(parsed_args.user_id)
        
        print(f"User Database: {self.db_path}")
        print("-" * 60)
        
        # Execute action
        if parsed_args.action == 'schema':
            self.show_schema_info()
            
        elif parsed_args.action == 'status':
            self.print_status()
            
        elif parsed_args.action in ['init', 'create']:
            if self.exists() and not parsed_args.reset:
                print("ℹ️  Database already exists. Use --reset to recreate.")
                self.print_status()
            else:
                success = self.initialize_database(reset=parsed_args.reset)
                if success:
                    print("✅ Database initialized successfully!")
                    print("\n🔍 Validation:")
                    status = self.get_status()
                    if status['schema_valid']:
                        print("✅ Schema validation passed")
                        print(f"📈 Records: {status['total_variants']} variants, {status['variants_with_predictions']} predictions")
                    else:
                        print("⚠️  Schema validation issues")
                else:
                    print("❌ Database initialization failed!")
                    
        elif parsed_args.action == 'reset':
            print("⚠️  This will DROP ALL TABLES and recreate them.")
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                success = self.reset_database()
                print("✅ Database reset successfully!" if success else "❌ Database reset failed!")
            else:
                print("❌ Operation cancelled.")
                
        elif parsed_args.action == 'clear':
            print("⚠️  This will DELETE ALL DATA but keep tables.")
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                success = self.clear_all_data()
                if success:
                    status = self.get_status()
                    print("✅ All data cleared successfully!")
                    print(f"📈 Records: {status['total_variants']} variants, {status['variants_with_predictions']} predictions")
                else:
                    print("❌ Failed to clear data.")
            else:
                print("❌ Operation cancelled.")
                
        elif parsed_args.action == 'delete':
            print("⚠️  This will PERMANENTLY DELETE the database file.")
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                success = self.delete_database()
                print("✅ Database deleted successfully!" if success else "❌ Failed to delete database.")
            else:
                print("❌ Operation cancelled.")


# =============================================================================
# Convenience Functions
# =============================================================================

def check_database_exists(db_path: str) -> bool:
    """Check if database file exists and is accessible."""
    manager = UserDatabaseManager(db_path)
    return manager.exists()


def validate_database_schema(db_path: str) -> Dict[str, Any]:
    """Validate database schema and return information."""
    manager = UserDatabaseManager(db_path)
    return manager.get_status()


def test_database_connection(db_path: str) -> bool:
    """Test database connection and basic operations."""
    manager = UserDatabaseManager(db_path)
    status = manager.get_status()
    return status.get('accessible', False)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    from frontend.user_database import get_default_database_path
    default_path = get_default_database_path()
    manager = UserDatabaseManager(default_path)
    manager.run_cli()
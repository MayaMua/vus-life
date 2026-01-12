#!/usr/bin/env python3
"""
Test script for user settings manager.
Demonstrates configuration functionality.
"""

from user_settings_manager import get_settings_manager


def main():
    """Test the configuration system."""
    print("=" * 60)
    print("User Settings Manager Test")
    print("=" * 60)
    
    # Get settings manager instance
    sm = get_settings_manager()
    
    # Display current settings
    print("\n1. Current Settings:")
    print(f"   API Address: {sm.get_api_address()}")
    print(f"   Data Folder Name: {sm.get_data_folder_name()}")
    print(f"   Data Folder Path: {sm.get_data_folder_path()}")
    print(f"   Config File Location: {sm.get_config_file_location()}")
    
    # Test updating settings
    print("\n2. Testing Settings Update:")
    print("   Updating API address to http://127.0.0.1:9000...")
    sm.update_settings(api_address="http://127.0.0.1:9000")
    print(f"   New API Address: {sm.get_api_address()}")
    
    # Verify persistence
    print("\n3. Testing Persistence:")
    print("   Creating new settings manager instance...")
    sm2 = get_settings_manager()
    print(f"   API Address from new instance: {sm2.get_api_address()}")
    print("   ✓ Settings persisted correctly!")
    
    # Reset to defaults
    print("\n4. Resetting to Defaults:")
    sm.reset_to_defaults()
    print(f"   API Address after reset: {sm.get_api_address()}")
    print(f"   Data Folder after reset: {sm.get_data_folder_name()}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

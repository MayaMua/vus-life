# User Configuration System

## Overview

The application includes a persistent configuration system that allows users to customize settings without using environment variables. This system is fully compatible with PyInstaller for creating standalone executables.

## Features

### Configurable Settings

1. **API Address**: Base URL for the API server
   - Default: `http://localhost:8000`
   - Example: `http://192.168.1.100:8000`

2. **Data Folder Name**: Name of the folder where data is stored
   - Default: `data_user`
   - The folder is created relative to the project root (or executable location in PyInstaller mode)

### Persistent Storage

- Settings are saved to: `~/.vus-life/user_settings.json`
- This location is consistent across both development and PyInstaller modes
- Settings persist between application restarts

## Usage

### Opening Configuration

1. Launch the Streamlit app
2. Click the **⚙️** (gear) button in the top-right corner of the dashboard
3. The configuration dialog will open

### Modifying Settings

1. Update the API Address or Data Folder Name fields
2. Click **"💾 Save Settings"** to save your changes
3. The app will reload to apply the new settings

### Resetting to Defaults

1. Open the configuration dialog
2. Click **"🔄 Reset to Defaults"**
3. Settings will be restored to default values

## PyInstaller Compatibility

The configuration system is designed to work seamlessly with PyInstaller:

### Development Mode
- Config file: `~/.vus-life/user_settings.json`
- Data folder: `{project_root}/{data_folder_name}`

### PyInstaller Mode
- Config file: `~/.vus-life/user_settings.json` (same location)
- Data folder: `{executable_directory}/{data_folder_name}`

### Building with PyInstaller

When creating an executable with PyInstaller, the configuration system will automatically:
1. Store user settings in the user's home directory (persistent)
2. Look for the data folder relative to the executable's location
3. Create the data folder if it doesn't exist

Example PyInstaller command:
```bash
pyinstaller --name="VUS-Life" \
            --onefile \
            --add-data "frontend/configs:frontend/configs" \
            frontend/app.py
```

## Technical Details

### File Structure

```
~/.vus-life/
└── user_settings.json    # User configuration file

{project_root}/
├── data_user/            # Default data folder (configurable)
│   ├── user_query/
│   └── training_embedding_results/
└── frontend/
    ├── app.py
    └── configs/
        ├── user_settings_manager.py   # Settings manager
        └── frontend_config.toml       # Static configuration
```

### Settings File Format

```json
{
  "api_address": "http://localhost:8000",
  "data_folder_name": "data_user"
}
```

### Architecture

- **`user_settings_manager.py`**: Core settings management
  - `UserSettings`: Data class for settings
  - `UserSettingsManager`: Handles load/save operations
  - `get_settings_manager()`: Global singleton access

- **`config_loader.py`**: Path resolution
  - `get_user_data_base_dir()`: Uses settings manager for data folder path
  - Other functions build paths relative to the base data directory

- **`app.py`**: UI integration
  - `show_config_dialog()`: Configuration dialog UI
  - Settings button in the main dashboard

## Notes

1. **No Environment Variables**: The system does not rely on `.env` files
2. **User-Specific**: Each user has their own settings (stored in home directory)
3. **Portable**: The executable can be moved to different locations
4. **Automatic Creation**: Data folders are created automatically if they don't exist
5. **Safe Defaults**: If the config file is corrupted, defaults are used

## Troubleshooting

### Configuration File Location

To find where your settings are stored, open the configuration dialog and expand "ℹ️ Configuration Details".

### Resetting Configuration

If you encounter issues:
1. Delete the file: `~/.vus-life/user_settings.json`
2. Restart the application (new default config will be created)

Or use the "Reset to Defaults" button in the configuration dialog.

### Data Folder Not Found

If the data folder path is incorrect:
1. Check the "Data Folder Path" shown in the configuration dialog
2. Ensure the folder name is correct (no special characters)
3. Check write permissions for the application directory

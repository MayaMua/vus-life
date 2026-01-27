# Configuration Quick Start Guide

## 🚀 Getting Started

### Step 1: Launch the App

```bash
streamlit run frontend/app.py
```

### Step 2: Open Configuration

Look for the **⚙️** button in the top-right corner of the dashboard and click it.

### Step 3: Configure Settings

You'll see a dialog with two configuration options:

#### 📡 API Address
- **Default**: `http://localhost:8000`
- **What it does**: Sets the base URL for your API server
- **Examples**:
  - Local: `http://localhost:8000`
  - Network: `http://192.168.1.100:8000`
  - Remote: `http://example.com:8000`

#### 📁 Data Folder Name
- **Default**: `data_user`
- **What it does**: Sets the name of the folder where all data is stored
- **Examples**:
  - `data_user` (default)
  - `my_data`
  - `variant_data`
  - `project_2024`

The dialog will show you the full path where your data folder is located.

### Step 4: Save Your Settings

Click **"💾 Save Settings"** to save your configuration. The app will reload automatically.

## 🔄 Quick Actions

### View Current Settings
Click the ⚙️ button and expand "ℹ️ Configuration Details" to see:
- Where your settings file is stored
- Current configuration values

### Reset to Defaults
If you want to start fresh:
1. Open configuration
2. Click **"🔄 Reset to Defaults"**
3. Confirm

### Check Data Folder Location
The configuration dialog always shows you the current data folder path, so you know exactly where your data is being stored.

## 📂 Where Are My Settings Stored?

Your settings are saved in: `~/.vus-life/user_settings.json`

### On macOS/Linux:
```
/Users/your-username/.vus-life/user_settings.json
```

### On Windows:
```
C:\Users\your-username\.vus-life\user_settings.json
```

This location is independent of where the app is installed, so your settings persist even if you move or update the app.

## 💡 Tips

1. **Network Setup**: If you're running the API on a different machine, just change the API address to that machine's IP address.

2. **Multiple Projects**: You can use different data folders for different projects by changing the "Data Folder Name" setting.

3. **Backup Settings**: Your settings file is just a JSON file. You can back it up or share it with others.

4. **First Time**: When you first run the app, default settings are created automatically. No setup required!

5. **PyInstaller**: When running as a standalone executable, everything works the same way.

## ⚠️ Troubleshooting

### Can't Connect to API
- Check that your API server is running
- Verify the API address in configuration
- Try the default: `http://localhost:8000`

### Data Folder Not Found
- The app creates the folder automatically
- Check the path shown in the configuration dialog
- Make sure you have write permissions

### Settings Not Saving
- Check that `~/.vus-life/` directory exists and is writable
- Try clicking "Reset to Defaults" to recreate the config file

### Configuration Dialog Won't Open
- Refresh the browser page
- Restart the Streamlit app

## 🎯 Common Scenarios

### Scenario 1: Running API on Same Computer
```
API Address: http://localhost:8000
Data Folder Name: data_user
```
✓ Use default settings

### Scenario 2: API on Different Computer on Network
```
API Address: http://192.168.1.50:8000
Data Folder Name: data_user
```
✓ Change only API address

### Scenario 3: Multiple Projects
```
Project A:
  API Address: http://localhost:8000
  Data Folder Name: project_a_data

Project B:
  API Address: http://localhost:8000
  Data Folder Name: project_b_data
```
✓ Change data folder name for each project

### Scenario 4: Using PyInstaller Executable
```
Same as above - configuration works identically!
```

## 📝 Configuration File Format

If you want to manually edit the settings (advanced):

```json
{
  "api_address": "http://localhost:8000",
  "data_folder_name": "data_user"
}
```

Location: `~/.vus-life/user_settings.json`

## ✅ Verification

To verify your settings are working:

1. Open configuration dialog
2. Check the "📁 Data folder path" shown
3. Check if the API connection status shows ✓ or ❌
4. If connected: Settings are working correctly!

## 🆘 Need Help?

1. Check the full documentation: `CONFIG_README.md`
2. Run the test script: `python frontend/configs/test_config.py`
3. Check the implementation details: `CONFIGURATION_IMPLEMENTATION.md`

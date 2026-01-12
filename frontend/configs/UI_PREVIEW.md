# 🎨 Configuration UI Preview

## Main Dashboard with Configuration Button

```
┌────────────────────────────────────────────────────────────────────┐
│  🧬 Variant Processing Dashboard                              ⚙️   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ✓ Connected to API at http://localhost:8000                      │
│                                                                    │
│  ┌──────────────────┐                                             │
│  │ ⚙️ Parameters    │                                             │
│  ├──────────────────┤                                             │
│  │ Gene Symbol      │                                             │
│  │ [BRCA1     ▾]    │                                             │
│  │                  │                                             │
│  │ [Get Training    │                                             │
│  │  Variants]       │                                             │
│  │                  │                                             │
│  │ Job Name         │                                             │
│  │ [default    ]    │                                             │
│  │                  │                                             │
│  │ ...              │                                             │
│  └──────────────────┘                                             │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
      ▲
      │
      └─── Click this ⚙️ button to open configuration
```

## Configuration Dialog (Opened)

```
┌────────────────────────────────────────────────────────────────────┐
│  🧬 Variant Processing Dashboard                              ⚙️   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  ⚙️ Configuration Settings                        [×]     │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │                                                           │    │
│  │  Configure application settings below:                   │    │
│  │                                                           │    │
│  │  API Address ❓                                           │    │
│  │  ┌────────────────────────────────────────────────────┐  │    │
│  │  │ http://localhost:8000                              │  │    │
│  │  └────────────────────────────────────────────────────┘  │    │
│  │  Base URL for the API server (e.g., http://localhost:8000)│   │
│  │                                                           │    │
│  │  Data Folder Name ❓                                      │    │
│  │  ┌────────────────────────────────────────────────────┐  │    │
│  │  │ data_user                                          │  │    │
│  │  └────────────────────────────────────────────────────┘  │    │
│  │  Name of the folder where data is stored               │    │
│  │                                                           │    │
│  │  📁 Data folder path:                                    │    │
│  │  /Users/jiawu/Workspace/.../vus-life/data_user          │    │
│  │                                                           │    │
│  │  ▼ ℹ️ Configuration Details                              │    │
│  │    Config file location:                                 │    │
│  │    /Users/jiawu/.vus-life/user_settings.json            │    │
│  │    Settings are saved automatically when you click       │    │
│  │    'Save Settings'                                       │    │
│  │                                                           │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │    │
│  │  │ 💾 Save      │ │ 🔄 Reset     │ │ ❌ Cancel    │    │    │
│  │  │   Settings   │ │   to Defaults│ │              │    │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘    │    │
│  │                                                           │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Button States

### Normal State
```
┌─────┐
│  ⚙️  │  ← Gray button, hover to see tooltip
└─────┘
```

### Hover State
```
┌─────────────────────────────────┐
│  ⚙️  │ Open Configuration Settings │
└─────────────────────────────────┘
```

### After Clicking
```
Configuration dialog appears as a modal overlay
```

## Interactive Elements

### 1. API Address Input Field
```
┌────────────────────────────────────────────────────┐
│ http://localhost:8000                              │ ← Type here
└────────────────────────────────────────────────────┘
Help text: Base URL for the API server (e.g., http://localhost:8000)
```

### 2. Data Folder Name Input Field
```
┌────────────────────────────────────────────────────┐
│ data_user                                          │ ← Type here
└────────────────────────────────────────────────────┘
Help text: Name of the folder where data is stored (relative to project root)
```

### 3. Info Section (Expandable)
```
▼ ℹ️ Configuration Details
  Config file location:
  /Users/jiawu/.vus-life/user_settings.json
  Settings are saved automatically when you click 'Save Settings'
```

### 4. Action Buttons

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ 💾 Save         │  │ 🔄 Reset        │  │ ❌ Cancel       │
│   Settings      │  │   to Defaults   │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
     Primary            Secondary            Secondary
   (Blue/Green)        (Orange/Yellow)         (Gray/Red)
```

## User Flow Diagram

```
                    START
                      │
                      ▼
              ┌───────────────┐
              │  Open App     │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ See ⚙️ Button │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Click Button  │
              └───────┬───────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Configuration Dialog  │
         │      Opens              │
         └────────┬───────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
   ┌─────────┐        ┌──────────┐
   │ Modify  │        │  Cancel  │
   │ Settings│        └────┬─────┘
   └────┬────┘             │
        │                  │
        ▼                  │
   ┌─────────┐            │
   │  Save   │            │
   │ Settings│            │
   └────┬────┘            │
        │                 │
        ▼                 ▼
   ┌─────────────────────────┐
   │  Settings Saved         │
   │  App Reloads            │
   └──────────┬──────────────┘
              │
              ▼
        ┌───────────┐
        │  Success! │
        │  ✅        │
        └───────────┘
```

## Color Scheme

### Button Colors (Streamlit Default)
- **⚙️ Config Button**: Gray/Secondary (non-intrusive)
- **💾 Save Settings**: Primary (Blue/Green - call to action)
- **🔄 Reset**: Secondary (Orange/Yellow - warning)
- **❌ Cancel**: Secondary (Gray - neutral)

### Status Colors
- **✓ Connected**: Green (success)
- **❌ Cannot connect**: Red (error)
- **📁 Data folder path**: Blue (info)
- **ℹ️ Configuration Details**: Light blue (info)

## Responsive Behavior

### Desktop (Wide Screen)
```
┌────────────────────────────────────────────┐
│  Title                               ⚙️    │
│                                            │
│  [Full width configuration dialog]         │
└────────────────────────────────────────────┘
```

### Mobile/Tablet (Narrow Screen)
```
┌──────────────────────┐
│  Title          ⚙️   │
│                      │
│  [Configuration      │
│   dialog adapts      │
│   to width]          │
└──────────────────────┘
```

## Accessibility

- ✅ **Keyboard Navigation**: Tab through fields, Enter to submit
- ✅ **Screen Readers**: All fields properly labeled
- ✅ **Help Text**: Tooltips and descriptions for all inputs
- ✅ **Visual Feedback**: Success/error messages
- ✅ **Clear Actions**: Obvious button labels with icons

## Animation

### Dialog Open
```
Fade in + Slide down
Duration: ~300ms
```

### Dialog Close
```
Fade out + Slide up
Duration: ~200ms
```

### Save Success
```
Success message appears
Auto-reload after 1 second
```

## Example States

### Initial Load (First Time User)
```
Settings: Default values loaded
Dialog: Closed
Button: Visible in top-right
```

### Configured User
```
Settings: User's saved values loaded
Dialog: Closed
Button: Visible in top-right
API Status: Shows connection status with saved API address
```

### During Configuration
```
Dialog: Open
Fields: Editable
Buttons: All active
```

### After Save
```
Message: "✅ Settings saved successfully!"
Action: Auto-reload after 1 second
Result: App uses new settings
```

## Tips for Using the UI

1. **Hover over inputs** to see help tooltips
2. **Expand "Configuration Details"** to see where settings are stored
3. **Use Tab key** to move between fields quickly
4. **Press Enter** in input fields to trigger save (future enhancement)
5. **Check the data folder path** to verify where your data goes

## Common UI Patterns

### Pattern 1: Quick Config Change
```
⚙️ → Change API → Save → Done (3 clicks)
```

### Pattern 2: Review Settings
```
⚙️ → View current values → Cancel (2 clicks)
```

### Pattern 3: Reset Everything
```
⚙️ → Reset to Defaults → Confirm (2 clicks)
```

## UI Best Practices Used

- ✅ **Consistent Icons**: Same icons throughout (⚙️ 💾 🔄 ❌ 📁 ℹ️)
- ✅ **Clear Labels**: No jargon, descriptive text
- ✅ **Help Text**: Every input has context
- ✅ **Visual Hierarchy**: Important actions stand out
- ✅ **Feedback**: Immediate response to actions
- ✅ **Safe Defaults**: Sensible default values
- ✅ **Non-Destructive**: Cancel option always available

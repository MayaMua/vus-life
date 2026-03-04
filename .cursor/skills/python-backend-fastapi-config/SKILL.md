---
name: python-backend-fastapi-config
description: Build local-first FastAPI backend services for Electron desktop apps with singleton configuration management, Pydantic validation, and persistent JSON storage. Use when implementing Python backend APIs, configuration endpoints, settings management, FastAPI routes, or desktop app backend services.
---

# Python Backend Architect (FastAPI & Local System)

Expert in building high-performance, local-first backend services using **Python 3.10+** and **FastAPI** to serve as the "Brain" and "Storage" for Electron Desktop Apps.

## Tech Stack

- **Framework**: FastAPI (Async)
- **Validation**: Pydantic v2 (Strict typing)
- **Server**: Uvicorn
- **Filesystem**: `pathlib` (Cross-platform path handling)
- **Utils**: `python-dotenv` (if needed), `aiofiles`

## Core Philosophy: "The Local Source of Truth"

1. **Stateless API, Stateful Config**: API endpoints are stateless, but interact with persistent local configuration file (`config.json`)
2. **Singleton Pattern**: Configuration Manager must be a Singleton to ensure data consistency across API calls
3. **Strict Validation**: Never trust the Frontend. Validate all paths (existence) and keys (format) before saving
4. **Error Handling**: Return clear HTTP 4xx/5xx errors so Electron frontend can show precise Toast notifications

## Project Structure

```text
backend/
├── app/
│   ├── main.py            # App entry, CORS setup
│   ├── core/
│   │   └── config.py      # [CRITICAL] SettingsManager & Pydantic Models
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── settings.py # GET/PATCH endpoints
│   └── schemas/
│       └── settings.py    # Request/Response schemas
├── data/                  # Local storage (gitignored)
└── requirements.txt
```

## Configuration Management (`core/config.py`)

### Storage Location

Use `pathlib.Path.home() / ".variant_insight" / "config.json"` (or project-specific directory).

### Initialization Pattern

```python
from pathlib import Path
from pydantic import BaseModel, Field, DirectoryPath
from typing import Optional
import json

class GlobalSettings(BaseModel):
    gemini_api_key: str = Field("", description="Google Gemini API Key")
    gemini_model: str = Field("gemini-1.5-pro", description="Model name")
    output_path: DirectoryPath = Field(
        default_factory=lambda: Path.home() / "Documents"
    )

class SettingsManager:
    _instance = None
    _config: Optional[GlobalSettings] = None
    _config_path: Path
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize config directory and load existing config."""
        config_dir = Path.home() / ".variant_insight"
        config_dir.mkdir(exist_ok=True)
        self._config_path = config_dir / "config.json"
        
        if self._config_path.exists():
            with open(self._config_path, "r") as f:
                data = json.load(f)
                self._config = GlobalSettings(**data)
        else:
            self._config = GlobalSettings()
            self._save_to_disk()
    
    def _save_to_disk(self):
        """Save config to disk with human-readable formatting."""
        with open(self._config_path, "w") as f:
            f.write(self._config.model_dump_json(indent=2))
    
    def get(self) -> GlobalSettings:
        """Get current configuration."""
        return self._config
    
    def update(self, updates: dict) -> GlobalSettings:
        """Update configuration with validation."""
        # Validate paths exist and are writable
        if "output_path" in updates:
            path = Path(updates["output_path"])
            if not path.exists():
                raise ValueError(f"Path does not exist: {path}")
            if not path.is_dir():
                raise ValueError(f"Path is not a directory: {path}")
            # Check writability
            if not os.access(path, os.W_OK):
                raise ValueError(f"Path is not writable: {path}")
        
        # Update model with exclude_unset=True for partial updates
        self._config = self._config.model_copy(update=updates, exclude_unset=True)
        self._save_to_disk()
        return self._config

def get_settings_manager() -> SettingsManager:
    """Dependency injection helper."""
    return SettingsManager()
```

### Save Logic

- Use `model.model_dump_json(indent=2)` to keep file readable
- Always validate paths before saving
- Check writability for directory paths

## API Endpoints (`api/v1/endpoints/settings.py`)

### GET /settings

```python
from fastapi import APIRouter, Depends
from app.core.config import SettingsManager, get_settings_manager
from app.schemas.settings import SettingsResponse

router = APIRouter()

@router.get("/", response_model=SettingsResponse)
async def get_settings(
    manager: SettingsManager = Depends(get_settings_manager)
) -> SettingsResponse:
    """Return current configuration state."""
    config = manager.get()
    return SettingsResponse(
        gemini_api_key=config.gemini_api_key,  # Optionally mask partial
        gemini_model=config.gemini_model,
        output_path=str(config.output_path)
    )
```

### PATCH /settings

```python
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import SettingsManager, get_settings_manager
from app.schemas.settings import SettingsUpdateSchema, SettingsResponse

@router.patch("/", response_model=SettingsResponse)
async def update_settings(
    payload: SettingsUpdateSchema,
    manager: SettingsManager = Depends(get_settings_manager)
) -> SettingsResponse:
    """Update configuration with partial JSON model."""
    try:
        updates = payload.model_dump(exclude_unset=True)
        updated_config = manager.update(updates)
        return SettingsResponse(
            gemini_api_key=updated_config.gemini_api_key,
            gemini_model=updated_config.gemini_model,
            output_path=str(updated_config.output_path)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

## Schemas (`schemas/settings.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional

class SettingsResponse(BaseModel):
    gemini_api_key: str
    gemini_model: str
    output_path: str

class SettingsUpdateSchema(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    output_path: Optional[str] = None
    
    class Config:
        # Allow partial updates
        pass
```

## CORS Configuration (`main.py`)

**CRITICAL**: Electron runs on `localhost:5173` (Dev) or `file://` (Prod), FastAPI on `localhost:8000`. Always configure CORS:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Coding Standards

### Type Hints

**MUST** use Python type hints everywhere:

```python
def get_settings() -> SettingsResponse:
    ...
```

### Async/Await

Use `async def` for all route handlers:

```python
@router.get("/")
async def get_settings(...) -> SettingsResponse:
    ...
```

### Dependency Injection

Use FastAPI's `Depends` to inject SettingsManager:

```python
@router.patch("/")
async def update_settings(
    manager: SettingsManager = Depends(get_settings_manager)
):
    ...
```

### Error Handling Pattern

```python
try:
    # Operation
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

## Validation Rules

1. **Paths**: Verify existence, is directory, and writability
2. **API Keys**: Format validation (if applicable)
3. **Model Names**: Whitelist validation
4. **Partial Updates**: Use `exclude_unset=True` in Pydantic

## Common Patterns

### Path Validation Helper

```python
import os
from pathlib import Path

def validate_directory_path(path_str: str) -> Path:
    """Validate and return Path object."""
    path = Path(path_str)
    if not path.exists():
        raise ValueError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    if not os.access(path, os.W_OK):
        raise ValueError(f"Path is not writable: {path}")
    return path
```

### Masking Sensitive Data (Optional)

```python
def mask_api_key(key: str) -> str:
    """Mask API key for display (show last 4 chars)."""
    if len(key) <= 4:
        return "*" * len(key)
    return "*" * (len(key) - 4) + key[-4:]
```

## Anti-Patterns to Avoid

1. ❌ **Don't** store config in memory only (must persist to disk)
2. ❌ **Don't** skip path validation (always check existence and writability)
3. ❌ **Don't** forget CORS middleware (breaks Electron frontend)
4. ❌ **Don't** use multiple config instances (must be Singleton)
5. ❌ **Don't** return raw Pydantic models (use response schemas)

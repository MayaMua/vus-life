---
trigger: always_on
---

# Backend Architecture & Skills

The backend follows a strict layered architecture using FastAPI.

## Skill 1: Infrastructure & Settings (The Foundation)

- **File Path**: `app/core/config.py`, `app/schemas/settings.py`
- **Rules**:
  - Use `SettingsManager` singleton for all config access.
  - Never hardcode paths; use `pathlib`.
  - Persist all changes to `config.json` immediately.
  - When creating APIs for settings, use `PATCH` for partial updates.

## Skill 2: AI & LLM Management (The Brain)

- **File Path**: `app/core/llm_factory.py`, `app/agents/`
- **Rules**:
  - Isolate LLM provider logic in `llm_factory.py`.
  - Do not instantiate LLM clients inside API routes; use the factory.
  - Use **LangChain** for all Agent logic (Chains, Prompts, OutputParsers).
  - If a feature requires "thinking" (e.g., summarizing PDF), put it in `app/agents/`.

## Skill 3: Business Services (The Hands)

- **File Path**: `app/services/`
- **Rules**:
  - **VUS Service**: This is deterministic. Use `httpx` or `aiohttp` to call the external VUS server. Do NOT use LLMs for the raw API call.
  - **PDF Service**: Use `app/services/file_service.py` for raw parsing (MinerU/PyPDF) to get text. Then pass text to an Agent for analysis.
  - Keep services stateless.

## Workflow Example

1. User uploads PDF -> `api/v1/analysis.py`
2. API calls `services/file_service.py` to extract text.
3. API calls `agents/pdf_agent.py` (which uses `core/llm_factory.py`) to summarize text.
4. API returns JSON to Electron.

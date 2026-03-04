from app.core.config import get_settings_manager
from app.prompts.clinical import LOCAL_OCR_PROMPT, CLOUD_FULL_ANALYSIS_PROMPT

def analyze_pdf(pdf_path):
    settings = get_settings_manager().get()
    provider = settings.model_settings.default_provider

    if provider == "ollama":
        # 本地模式：Prompt 要简单直接
        prompt = LOCAL_OCR_PROMPT 
        # ... 调用本地模型 ...
    else:
        # 云端模式：Prompt 可以复杂
        prompt = CLOUD_FULL_ANALYSIS_PROMPT
        # ... 调用云端模型 ...
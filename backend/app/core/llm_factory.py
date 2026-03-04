# app/core/llm_factory.py

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings_manager

def get_llm(provider_key: str = None, model_name: str = None, temperature: float = 0.7):
    """
    通用 LLM 工厂。
    provider_key: 对应 settings.providers 中的 key (如 "uuid-1", "custom-deepseek")
    """
    settings = get_settings_manager().get()
    model_config = settings.model_settings
    
    # 1. 确定 Target Key
    target_key = provider_key or model_config.default_provider
    if not target_key or target_key not in model_config.providers:
        raise ValueError(f"Provider '{target_key}' not found. Please add it in Settings.")
    
    # 2. 获取配置对象
    provider_conf = model_config.providers[target_key]
    
    if not provider_conf.enabled:
        raise ValueError(f"Provider '{provider_conf.name}' is disabled.")

    # 3. 确定模型名称
    target_model = model_name or model_config.default_model

    # 4. 根据协议类型 (provider_type) 实例化不同的 Client
    
    # === 分支 A: Google Gemini (特殊 SDK) ===
    if provider_conf.provider_type == "gemini":
        return ChatGoogleGenerativeAI(
            model=target_model,
            google_api_key=provider_conf.api_key,
            temperature=temperature,
            convert_system_message_to_human=True
        )
    
    # === 分支 B: OpenAI 兼容协议 (DeepSeek, Ollama, Kimi, etc.) ===
    elif provider_conf.provider_type == "openai":
        # 处理 Ollama 这种不需要 Key 的情况
        final_api_key = provider_conf.api_key
        if not final_api_key and "localhost" in provider_conf.base_url:
            final_api_key = "ollama" # LangChain 甚至不需要这个，但不传可能报错

        return ChatOpenAI(
            model=target_model,
            openai_api_key=final_api_key,
            openai_api_base=provider_conf.base_url,
            temperature=temperature,
            max_tokens=4096
        )
        
    # === 分支 C: Anthropic (如果未来需要) ===
    # elif provider_conf.provider_type == "anthropic":
    #     return ChatAnthropic(...)

    else:
        raise ValueError(f"Unsupported provider type: {provider_conf.provider_type}")
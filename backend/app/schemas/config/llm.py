# app/schemas/config/llm.py

from pydantic import BaseModel, Field
from typing import Dict, List, Literal

# 定义支持的协议类型
# 大多数模型（DeepSeek, Moonshot, Local）都走 openai 协议
ProviderType = Literal["openai", "gemini", "anthropic", "azure"]

class ProviderSettings(BaseModel):
    """
    单个 Provider 的配置。
    不再硬编码具体名字，而是由前端传入。
    """
    name: str = ""              # 显示名称，如 "My DeepSeek"
    provider_type: ProviderType = "openai"  # 关键字段：决定后端用哪个 Client 类
    enabled: bool = True
    base_url: str = ""          # OpenAI 兼容接口必填
    api_key: str = ""
    models: List[str] = Field(default_factory=list) # 该服务商下的模型列表

class ModelSettings(BaseModel):
    """
    所有模型配置。
    默认可以是空的！完全由用户在前端添加。
    """
    default_provider: str = "" # 存 provider 的 key
    default_model: str = ""
    
    # 这是一个开放的字典，Key 由用户定义 (uid)，Value 是配置
    providers: Dict[str, ProviderSettings] = Field(default_factory=dict)
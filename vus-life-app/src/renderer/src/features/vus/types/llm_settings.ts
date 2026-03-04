export interface LLMProviderSettings {
  api_key: string;
  models: string[];
}

export interface ModelSettings {
  gemini: LLMProviderSettings;
  ollama: LLMProviderSettings;
}

export interface LLMSettings {
  model_settings: ModelSettings;
}

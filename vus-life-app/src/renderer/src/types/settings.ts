/**
 * TypeScript interfaces matching backend config.json structure.
 */

export interface GeneralSettings {
  output_path: string
  has_accepted_agreement?: boolean
}

export interface VusApiSettings {
  api_url: string
}

export interface ProviderSettings {
  name?: string
  provider_type?: string
  enabled: boolean
  base_url: string
  api_key: string
  models: string[]
}

export interface ModelSettings {
  default_provider: string
  default_model: string
  providers: Record<string, ProviderSettings>
}

export interface SettingsResponse {
  general_settings: GeneralSettings
  vus_api_settings: VusApiSettings
  model_settings: ModelSettings
}

/** Partial update for PATCH /api/settings */
export interface SettingsUpdateRequest {
  general_settings?: { output_path?: string; has_accepted_agreement?: boolean }
  vus_api_settings?: { api_url?: string }
  model_settings?: {
    default_provider?: string
    default_model?: string
    providers?: Record<string, Partial<ProviderSettings>>
  }
}

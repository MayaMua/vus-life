/**
 * Global settings store: storage path and model provider configs.
 * Persisted to localStorage so settings survive app restarts.
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface ProviderConfig {
  apiKey: string
  enabled: boolean
}

export interface SettingsState {
  storagePath: string
  modelProviders: Record<string, ProviderConfig>
  setStoragePath: (path: string) => void
  updateProviderConfig: (providerId: string, config: Partial<ProviderConfig>) => void
  toggleProvider: (providerId: string, enabled: boolean) => void
}

const defaultProviders: Record<string, ProviderConfig> = {
  gemini: { apiKey: '', enabled: true },
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      storagePath: '',
      modelProviders: defaultProviders,
      setStoragePath: (path) => set({ storagePath: path }),
      updateProviderConfig: (providerId, config) =>
        set((state) => ({
          modelProviders: {
            ...state.modelProviders,
            [providerId]: {
              ...state.modelProviders[providerId],
              ...config,
            },
          },
        })),
      toggleProvider: (providerId, enabled) =>
        set((state) => ({
          modelProviders: {
            ...state.modelProviders,
            [providerId]: {
              ...(state.modelProviders[providerId] ?? { apiKey: '', enabled: false }),
              enabled,
            },
          },
        })),
    }),
    {
      name: 'app-settings-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

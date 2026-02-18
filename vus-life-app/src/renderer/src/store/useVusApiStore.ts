/**
 * VUS API settings store: endpoint URL and connection status.
 * Only apiUrl is persisted; isConnected and status message reset on restart.
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export type ConnectionStatusType = 'success' | 'error' | null

export interface VusApiState {
  apiUrl: string
  isConnected: boolean
  /** Non-persisted: last verification result message for modal/toast. */
  connectionMessage: string
  connectionType: ConnectionStatusType
  isVerifying: boolean
  setApiUrl: (url: string) => void
  setConnectionStatus: (connected: boolean, message: string, type: ConnectionStatusType) => void
  clearConnectionStatus: () => void
  setVerifying: (verifying: boolean) => void
}

export const useVusApiStore = create<VusApiState>()(
  persist(
    (set) => ({
      apiUrl: '',
      isConnected: false,
      connectionMessage: '',
      connectionType: null,
      isVerifying: false,
      setApiUrl: (url) => set({ apiUrl: url }),
      setConnectionStatus: (connected, message, type) =>
        set({ isConnected: connected, connectionMessage: message, connectionType: type }),
      clearConnectionStatus: () =>
        set({ connectionMessage: '', connectionType: null }),
      setVerifying: (verifying) => set({ isVerifying: verifying }),
    }),
    {
      name: 'vus-api-settings',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ apiUrl: state.apiUrl }),
    }
  )
)

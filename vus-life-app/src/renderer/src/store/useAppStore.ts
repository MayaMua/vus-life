// src/renderer/src/stores/useAppStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface AppState {
  hasAcceptedAgreement: boolean;
  acceptAgreement: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      hasAcceptedAgreement: false,
      acceptAgreement: () => set({ hasAcceptedAgreement: true }),
    }),
    {
      name: 'app-global-storage', 
      storage: createJSONStorage(() => localStorage),
    }
  )
);
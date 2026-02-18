import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI & {
      openFolderDialog: () => Promise<string | null>
    }
    api: unknown
  }
}

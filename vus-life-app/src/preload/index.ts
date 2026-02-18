import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {}

// Electron API extended with app-specific IPC (folder dialog for settings)
const electronWithFolderDialog = {
  ...electronAPI,
  openFolderDialog: (): Promise<string | null> => ipcRenderer.invoke('open-folder-dialog')
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronWithFolderDialog)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronWithFolderDialog
  // @ts-ignore (define in dts)
  window.api = api
}

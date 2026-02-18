/**
 * General Settings: storage paths. Browse opens Electron folder dialog via IPC.
 */

import React from 'react'
import { FolderOpen, Database } from 'lucide-react'
import { useSettingsStore } from '../../../store/useSettingsStore'

export const GeneralSettings: React.FC = () => {
  const storagePath = useSettingsStore((s) => s.storagePath)
  const setStoragePath = useSettingsStore((s) => s.setStoragePath)

  const handleBrowse = async () => {
    const path = await window.electron.openFolderDialog()
    if (path != null) setStoragePath(path)
  }

  const displayPath = storagePath || 'No path selected'

  return (
    <>
      <header>
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">General Settings</h1>
        <p className="text-slate-500 text-sm mt-1 font-medium">Manage local storage and environment preferences.</p>
      </header>

      <section className="space-y-6">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <Database className="w-4 h-4 text-blue-500" />
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-tight">Storage Paths</h3>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Data Output Directory</label>
            <div className="flex gap-3">
              <input
                readOnly
                value={displayPath}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-mono text-slate-600 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleBrowse}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl shadow-md transition-all active:scale-95 flex items-center gap-2"
              >
                <FolderOpen className="w-4 h-4" />
                Browse...
              </button>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">
              The app will automatically create{' '}
              <code className="bg-slate-100 px-1 rounded font-mono">/vus_results</code> and{' '}
              <code className="bg-slate-100 px-1 rounded font-mono">/pdf_parsed</code> subfolders in this location.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}

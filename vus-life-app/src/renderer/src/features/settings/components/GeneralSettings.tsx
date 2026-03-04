/**
 * General Settings: storage paths. Browse opens Electron folder dialog via IPC.
 * Uses TanStack Query to fetch and update settings from FastAPI backend.
 */

import React from 'react'
import { FolderOpen, Database } from 'lucide-react'
import { useSettings, useUpdateSettings } from '../useSettings'

export const GeneralSettings: React.FC = () => {
  const { data: settings, isLoading, error } = useSettings()
  const updateSettingsMutation = useUpdateSettings()

  const handleBrowse = async () => {
    const path = await window.electron.openFolderDialog()
    if (path != null) {
      try {
        await updateSettingsMutation.mutateAsync({
          general_settings: { output_path: path },
        })
      } catch (err) {
        // Error is handled by mutation error state
        console.error('Failed to update storage path:', err)
      }
    }
  }

  const displayPath =
    settings?.general_settings?.output_path ?? (isLoading ? 'Loading...' : 'No path selected')
  const isSaving = updateSettingsMutation.isPending

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
                disabled={isLoading}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-mono text-slate-600 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                type="button"
                onClick={handleBrowse}
                disabled={isLoading || isSaving}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white text-sm font-bold rounded-xl shadow-md transition-all active:scale-95 flex items-center gap-2"
              >
                <FolderOpen className="w-4 h-4" />
                {isSaving ? 'Saving...' : 'Browse...'}
              </button>
            </div>
            {error && (
              <p className="text-[11px] text-red-500 font-medium">
                Error: {error instanceof Error ? error.message : 'Failed to load settings'}
              </p>
            )}
            {updateSettingsMutation.isError && (
              <p className="text-[11px] text-red-500 font-medium">
                Error: {updateSettingsMutation.error instanceof Error ? updateSettingsMutation.error.message : 'Failed to save settings'}
              </p>
            )}
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

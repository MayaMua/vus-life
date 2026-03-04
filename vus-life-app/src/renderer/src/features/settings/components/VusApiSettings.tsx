/**
 * VUS API URL and Verify. Reads/updates API URL via FastAPI (GET/PATCH /api/settings).
 * Verify calls backend GET /api/vus/verify; backend reads URL from config and validates via /health.
 */

import React, { useState, useEffect } from 'react'
import { Globe, Zap, Activity, Info } from 'lucide-react'
import { verifyVusConnection as verifyVusConnectionApi } from '../../../api/endpoints'
import { useSettings, useUpdateSettings } from '../useSettings'
import { ConnectionStatusModal, type ConnectionStatusType } from './ConnectionStatusModal'

export const VusApiSettings: React.FC = () => {
  const { data: settings, isLoading } = useSettings()
  const updateSettingsMutation = useUpdateSettings()

  const apiUrlFromApi = settings?.vus_api_settings?.api_url ?? ''
  const [localApiUrl, setLocalApiUrl] = useState(apiUrlFromApi)
  useEffect(() => {
    setLocalApiUrl(apiUrlFromApi)
  }, [apiUrlFromApi])

  const [isVerifying, setVerifying] = useState(false)
  const [connectionType, setConnectionType] = useState<ConnectionStatusType>(null)
  const [connectionMessage, setConnectionMessage] = useState('')

  const setConnectionStatus = (
    _connected: boolean,
    message: string,
    type: ConnectionStatusType
  ): void => {
    setConnectionMessage(message)
    setConnectionType(type)
  }
  const clearConnectionStatus = (): void => {
    setConnectionMessage('')
    setConnectionType(null)
  }

  const handleApiUrlBlur = (): void => {
    const trimmed = localApiUrl.trim().replace(/\/$/, '')
    if (trimmed === apiUrlFromApi.trim().replace(/\/$/, '')) return
    updateSettingsMutation.mutateAsync({ vus_api_settings: { api_url: trimmed } }).catch(() => {})
  }

  const verifyVusConnection = async (): Promise<void> => {
    setVerifying(true)
    clearConnectionStatus()

    try {
      const data = await verifyVusConnectionApi()
      setConnectionStatus(
        true,
        `Connection Successful! Service: ${data.service ?? 'vus-life-server'}`,
        'success'
      )
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Failed to connect. Check that the URL is saved and the backend is running.'
      setConnectionStatus(false, msg, 'error')
    } finally {
      setVerifying(false)
    }
  }

  return (
    <>
      <ConnectionStatusModal
        visible={!!connectionType}
        type={connectionType}
        message={connectionMessage}
        onClose={clearConnectionStatus}
      />

      <header>
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">VUS Prediction API</h1>
        <p className="text-slate-500 text-sm mt-1 font-medium">
          Configure the remote backend for high-performance variant embedding calculations.
        </p>
      </header>

      <section className="space-y-6">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <Activity className="w-4 h-4 text-emerald-500" />
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-tight">
            API Configuration
          </h3>
        </div>

        <div className="bg-slate-50 rounded-2xl p-6 border border-slate-100 space-y-6">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">
              Server Endpoint (URL)
            </label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Globe className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  value={localApiUrl}
                  onChange={(e) => setLocalApiUrl(e.target.value)}
                  onBlur={handleApiUrlBlur}
                  disabled={isLoading}
                  placeholder="https://your-api-server.com"
                  className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm font-mono text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-inner transition-all disabled:opacity-50"
                />
              </div>
              <button
                type="button"
                onClick={verifyVusConnection}
                disabled={isVerifying || !apiUrlFromApi.trim()}
                className={`px-8 py-3 rounded-xl text-sm font-bold transition-all flex items-center gap-2 shadow-sm ${
                  isVerifying
                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                    : 'bg-slate-900 text-white hover:bg-slate-800 active:scale-95 shadow-slate-200'
                }`}
              >
                {isVerifying ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Verify
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="flex items-start gap-4 p-5 bg-blue-50/50 border border-blue-100 rounded-2xl">
            <div className="bg-blue-600 rounded-lg p-1.5 shrink-0">
              <Info className="w-4 h-4 text-white" />
            </div>
            <div className="space-y-1.5">
              <p className="text-[10px] font-bold text-blue-900 uppercase tracking-widest">
                Integration Note
              </p>
              <p className="text-xs text-blue-800 leading-relaxed font-medium">
                The VUS Prediction module uses this endpoint to process HGVS strings. If using{' '}
                <span className="font-bold">ngrok</span>, ensure the tunnel is active. Verify uses
                the <strong>saved</strong> URL from settings (save with the input field first). The
                backend checks the{' '}
                <code className="bg-blue-100/50 px-1 rounded font-mono">/api/health</code> endpoint
                for a successful heartbeat.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

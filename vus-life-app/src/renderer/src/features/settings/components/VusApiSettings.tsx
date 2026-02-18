/**
 * VUS API URL and Verify; uses useVusApiStore and verifyVusConnection.
 * Contains full verification logic with AbortController timeout; shows ConnectionStatusModal.
 */

import React from 'react'
import { Globe, Zap, Activity, Info } from 'lucide-react'
import { useVusApiStore } from '../../../store/useVusApiStore'
import { ConnectionStatusModal } from './ConnectionStatusModal'

const VERIFY_TIMEOUT_MS = 8000

export const VusApiSettings: React.FC = () => {
  const apiUrl = useVusApiStore((s) => s.apiUrl)
  const setApiUrl = useVusApiStore((s) => s.setApiUrl)
  const isVerifying = useVusApiStore((s) => s.isVerifying)
  const connectionType = useVusApiStore((s) => s.connectionType)
  const connectionMessage = useVusApiStore((s) => s.connectionMessage)
  const setConnectionStatus = useVusApiStore((s) => s.setConnectionStatus)
  const clearConnectionStatus = useVusApiStore((s) => s.clearConnectionStatus)
  const setVerifying = useVusApiStore((s) => s.setVerifying)

  const verifyVusConnection = async () => {
    const trimmedUrl = apiUrl.trim().replace(/\/$/, '')
    setVerifying(true)
    clearConnectionStatus()

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), VERIFY_TIMEOUT_MS)

      const response = await fetch(`${trimmedUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
      })

      clearTimeout(timeoutId)

      if (response.ok) {
        const contentType = response.headers.get('content-type')
        if (!contentType || !contentType.includes('application/json')) {
          throw new Error(
            'Received non-JSON response. Ensure the URL is correct and the server is running.'
          )
        }

        const data = (await response.json()) as { status?: string; service?: string }
        if (data.status === 'healthy') {
          setConnectionStatus(
            true,
            `Connection Successful! Service: ${data.service ?? 'vus-life-server'}`,
            'success'
          )
        } else {
          throw new Error('Service reported unhealthy status.')
        }
      } else {
        const errorText = await response.text().catch(() => 'Unknown error')
        throw new Error(`Server error (${response.status}): ${errorText.slice(0, 50)}...`)
      }
    } catch (err: unknown) {
      let msg = 'Failed to connect.'
      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          msg = 'Connection timed out (8s). The server might be offline.'
        } else if (err instanceof TypeError) {
          msg = 'Network error or CORS block. Check if the server allows cross-origin requests.'
        } else {
          msg = err.message
        }
      }
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
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-tight">API Configuration</h3>
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
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="https://your-api-server.com"
                  className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-3 text-sm font-mono text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-inner transition-all"
                />
              </div>
              <button
                type="button"
                onClick={verifyVusConnection}
                disabled={isVerifying || !apiUrl.trim()}
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
                <span className="font-bold">ngrok</span>, ensure the tunnel is active. The verify tool
                checks the{' '}
                <code className="bg-blue-100/50 px-1 rounded font-mono">/health</code> endpoint for a
                successful heartbeat.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}

/**
 * Model Provider settings: Gemini/LLM configs from useSettingsStore.
 */

import React, { useState } from 'react'
import { Search, ExternalLink, Settings, Eye, EyeOff } from 'lucide-react'
import { useSettingsStore } from '../../../store/useSettingsStore'

const GEMINI_LOGO_URL = 'https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg'

export const ModelProviderSettings: React.FC = () => {
  const [showApiKey, setShowApiKey] = useState(false)
  const geminiConfig = useSettingsStore((s) => s.modelProviders.gemini)
  const updateProviderConfig = useSettingsStore((s) => s.updateProviderConfig)
  const toggleProvider = useSettingsStore((s) => s.toggleProvider)

  const isGeminiOn = geminiConfig?.enabled ?? true
  const apiKey = geminiConfig?.apiKey ?? ''

  const handleToggleGemini = () => {
    toggleProvider('gemini', !isGeminiOn)
  }

  return (
    <>
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Model Providers</h1>
        <p className="text-slate-500 text-sm mt-1 font-medium">Configure external AI services for analysis and parsing.</p>
      </header>

      <div className="flex border border-slate-100 rounded-2xl overflow-hidden shadow-sm h-[500px]">
        {/* Provider Sub-list */}
        <div className="w-72 bg-slate-50/50 border-r border-slate-100">
          <div className="p-4 border-b border-slate-100 relative">
            <Search className="absolute left-7 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
            <input
              placeholder="Search Providers..."
              className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="p-2">
            <button
              type="button"
              className="w-full flex items-center justify-between p-3 bg-white border border-blue-100 rounded-xl shadow-sm text-left"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-white border border-slate-100 rounded-lg flex items-center justify-center p-1 shadow-sm overflow-hidden">
                  <img src={GEMINI_LOGO_URL} alt="Gemini" className="w-full h-full object-contain p-0.5" />
                </div>
                <span className="text-sm font-bold text-slate-800">Google Gemini</span>
              </div>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase border ${
                  isGeminiOn ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-slate-100 text-slate-500 border-slate-200'
                }`}
              >
                {isGeminiOn ? 'ON' : 'OFF'}
              </span>
            </button>
          </div>
        </div>

        {/* Provider Detail Config */}
        <div className="flex-1 bg-white p-8 overflow-y-auto">
          <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-800 uppercase tracking-tight">Gemini</h2>
              <ExternalLink className="w-4 h-4 text-slate-300 hover:text-blue-500 cursor-pointer transition-colors" />
            </div>
            <button
              type="button"
              onClick={handleToggleGemini}
              className={`w-11 h-6 rounded-full flex items-center px-1 transition-all cursor-pointer ${
                isGeminiOn ? 'bg-emerald-500 justify-end' : 'bg-slate-200 justify-start'
              }`}
            >
              <div className="w-4 h-4 bg-white rounded-full shadow-md" />
            </button>
          </div>

          <div className="space-y-8">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">API Key</label>
                <Settings className="w-3.5 h-3.5 text-slate-300 cursor-pointer hover:text-slate-500 transition-colors" />
              </div>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => updateProviderConfig('gemini', { apiKey: e.target.value })}
                    placeholder="••••••••••••••••"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl py-2.5 pl-4 pr-10 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  type="button"
                  className="px-6 py-2.5 border border-slate-200 rounded-xl text-sm font-bold text-slate-700 hover:bg-slate-50 transition-all active:scale-95"
                >
                  Check
                </button>
              </div>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block text-[11px] text-blue-600 font-bold hover:underline"
              >
                Get API Key from Google AI Studio
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

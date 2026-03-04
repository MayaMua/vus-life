/**
 * Model Provider settings: Cherry Studio–style layout.
 * Reads and updates config via FastAPI (GET/PATCH /api/settings).
 */

import React, { useState, useEffect } from 'react'
import { Plus } from 'lucide-react'
import toast from 'react-hot-toast'
import { useSettings, useUpdateSettings } from '../useSettings'
import { ProviderDetailPanel } from './ProviderDetailPanel'

const LOGOS: Record<string, string> = {
  gemini: 'https://img.icons8.com/?size=100&id=17949&format=png&color=000000',
  openai: 'https://img.icons8.com/?size=100&id=ApdV0R6qI7aG&format=png&color=000000',
  deepseek: 'https://img.icons8.com/?size=100&id=w18I4Y4R6b3w&format=png&color=000000',
  ollama: 'https://img.icons8.com/?size=100&id=jC9ZtCqE0hhp&format=png&color=000000'
}

const DEFAULT_URLS: Record<string, string> = {
  gemini: 'https://generativelanguage.googleapis.com',
  openai: 'https://api.openai.com/v1',
  deepseek: 'https://api.deepseek.com',
  ollama: 'http://localhost:11434/v1'
}

const GET_KEY_URLS: Record<string, string> = {
  gemini: 'https://aistudio.google.com/app/apikey',
  openai: 'https://platform.openai.com/api-keys',
  deepseek: 'https://platform.deepseek.com/keys'
}

const DISPLAY_NAMES: Record<string, string> = {
  gemini: 'Google Gemini',
  openai: 'OpenAI',
  deepseek: 'DeepSeek',
  ollama: 'Ollama'
}

export const ModelProviderSettings: React.FC = () => {
  const { data: settings, isLoading } = useSettings()
  const updateSettingsMutation = useUpdateSettings()
  const [selectedProviderId, setSelectedProviderId] = useState<string>('')

  const modelSettings = settings?.model_settings
  const providers = modelSettings?.providers || {}

  // Add Provider state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [newProviderName, setNewProviderName] = useState('')
  const [newProviderType, setNewProviderType] = useState('openai')

  // Initialize selected provider
  useEffect(() => {
    if (!selectedProviderId && Object.keys(providers).length > 0) {
      if (providers['gemini']) setSelectedProviderId('gemini')
      else setSelectedProviderId(Object.keys(providers)[0])
    }
  }, [providers, selectedProviderId])

  const handleCreateProvider = async () => {
    if (!newProviderName.trim()) {
      toast.error('Provider name is required')
      return
    }
    const newId = crypto.randomUUID()
    const newProvider = {
      name: newProviderName.trim(),
      provider_type: newProviderType,
      enabled: true,
      base_url: DEFAULT_URLS[newProviderType] || '',
      api_key: '',
      models: []
    }

    try {
      await updateSettingsMutation.mutateAsync({
        model_settings: {
          providers: {
            [newId]: newProvider
          }
        }
      })
      toast.success('Provider added')
      setSelectedProviderId(newId)
      setIsAddModalOpen(false)
      setNewProviderName('')
      setNewProviderType('openai')
    } catch (e) {
      toast.error('Failed to create provider')
    }
  }

  if (isLoading) {
    return <div className="flex h-full items-center justify-center"><span className="loading loading-spinner text-[#00B96B]"></span></div>
  }

  return (
    <div className="flex flex-col h-full bg-[#FAFAFA]">
      <header className="px-8 py-6 shrink-0 bg-white border-b border-gray-200">
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Model Providers</h1>
        <p className="text-slate-500 text-sm mt-1 font-medium">
          Configure external AI services for analysis and parsing.
        </p>

      </header>

      {/* Two-Pane Layout */}
      <div className="flex flex-1 min-h-0">
        {/* Left Pane: Provider List */}
        <div className="w-64 flex flex-col border-r border-gray-200 bg-[#F3F4F6]/30 overflow-y-auto">
          <div className="p-3">
             <div className="relative mb-3">
                <input 
                  type="text" 
                  placeholder="Search Providers..."
                  className="w-full h-9 pl-4 pr-4 rounded-lg border border-gray-200 bg-white text-xs focus:outline-none focus:border-[#00B96B] shadow-sm"
                />
             </div>
             <div className="flex flex-col gap-1.5">
               {Object.entries(providers).map(([pid, pSettings]) => {
                 const isSelected = selectedProviderId === pid
                 const isEnabled = pSettings.enabled
                 const pType = pSettings.provider_type || pid
                 const displayName = pSettings.name || DISPLAY_NAMES[pType] || pType
                 const logoUrl = LOGOS[pType] || ''

                 return (
                   <button
                     key={pid}
                     onClick={() => setSelectedProviderId(pid)}
                     className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left transition-all ${
                       isSelected 
                         ? 'bg-white shadow-sm border border-gray-200' 
                         : 'hover:bg-gray-200/50 border border-transparent'
                     }`}
                   >
                     <div className="flex items-center gap-3 overflow-hidden">
                       <div className="w-6 h-6 rounded flex items-center justify-center overflow-hidden shrink-0">
                         {logoUrl ? <img src={logoUrl} alt={displayName} className="w-4 h-4 object-contain" /> : <div className="w-4 h-4 bg-gray-200 rounded-full" />}
                       </div>
                       <span className={`text-sm tracking-tight truncate ${isSelected ? 'font-bold text-slate-800' : 'font-medium text-slate-600'}`}>
                         {displayName}
                       </span>
                     </div>
                     
                     {/* Green ON badge / Gray UN badge */}
                     <div className={`px-1.5 py-[2px] rounded text-[10px] font-bold tracking-widest border shrink-0 ${
                       isEnabled 
                         ? 'bg-[#00B96B]/10 text-[#00B96B] border-[#00B96B]/20' 
                         : 'bg-gray-100 text-gray-400 border-gray-200'
                     }`}>
                       {isEnabled ? 'ON' : 'OFF'}
                     </div>
                   </button>
                 )
               })}
             </div>
             <div className="mt-4 px-1">
               <button
                 onClick={() => setIsAddModalOpen(true)}
                 className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-dashed border-gray-300 text-sm font-medium text-slate-500 hover:border-[#00B96B] hover:text-[#00B96B] group transition-colors"
               >
                 <Plus className="w-4 h-4 text-gray-400 group-hover:text-[#00B96B] transition-colors" />
                 Add
               </button>
             </div>
          </div>
        </div>

        {/* Right Pane: Provider Configuration */}
        {selectedProviderId && providers[selectedProviderId] && (
          <ProviderDetailPanel
            key={selectedProviderId}
            providerId={selectedProviderId}
            name={providers[selectedProviderId].name || DISPLAY_NAMES[providers[selectedProviderId].provider_type || selectedProviderId] || selectedProviderId}
            logoUrl={LOGOS[providers[selectedProviderId].provider_type || selectedProviderId] || ''}
            settings={providers[selectedProviderId]}
            defaultBaseUrl={DEFAULT_URLS[providers[selectedProviderId].provider_type || selectedProviderId] || ''}
            getApiKeyUrl={GET_KEY_URLS[providers[selectedProviderId].provider_type || selectedProviderId]}
          />
        )}
      </div>

      {/* Add Provider Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-100 flex items-center justify-center bg-black/30 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-sm rounded-[24px] bg-white p-7 shadow-2xl animate-in zoom-in-95 duration-200">
            <h2 className="mb-6 text-xl font-bold tracking-tight text-slate-800">Add Provider</h2>
            
            <div className="flex flex-col gap-5">
              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">Provider Name</label>
                <input
                  type="text"
                  placeholder="Example: OpenAI"
                  value={newProviderName}
                  onChange={(e) => setNewProviderName(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-white px-4 h-11 text-sm shadow-sm transition-colors focus:border-[#00B96B] focus:outline-none focus:ring-1 focus:ring-[#00B96B]"
                  autoFocus
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700">Provider Type</label>
                <select
                  value={newProviderType}
                  onChange={(e) => setNewProviderType(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-white px-4 h-11 text-sm shadow-sm transition-colors focus:border-[#00B96B] focus:outline-none focus:ring-1 focus:ring-[#00B96B]"
                >
                  <option value="openai">OpenAI</option>
                  <option value="ollama">Ollama</option>
                  <option value="gemini">Gemini</option>
                </select>
              </div>
            </div>

            <div className="mt-8 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                className="btn btn-ghost rounded-xl border border-gray-200 hover:bg-gray-50 h-10 px-5 text-sm font-semibold text-slate-600 shadow-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateProvider}
                className="btn border-transparent bg-[#00B96B] hover:bg-[#00B96B]/90 rounded-xl h-10 px-6 text-sm font-semibold text-white shadow-sm"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

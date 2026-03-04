import React, { useState, useEffect } from 'react'
import { ExternalLink, Eye, EyeOff, Loader2, Minus, Plus, Settings2, Brain, Globe, Sun, Wrench } from 'lucide-react'
import { useUpdateSettings, useVerifyProvider } from '../useSettings'
import type { ProviderSettings } from '../../../types/settings'
import toast from 'react-hot-toast'
import { ModelManager } from './ModelManager'
import { parseModelCapabilities } from '../utils/modelUtils'

interface ProviderDetailPanelProps {
  providerId: string
  name: string
  logoUrl: string
  settings: ProviderSettings
  defaultBaseUrl: string
  getApiKeyUrl?: string
}

const PRIMARY = '#00B96B'

export const ProviderDetailPanel: React.FC<ProviderDetailPanelProps> = ({
  providerId,
  name,
  settings,
  defaultBaseUrl,
  getApiKeyUrl,
}) => {
  const [showApiKey, setShowApiKey] = useState(false)
  const [localApiKey, setLocalApiKey] = useState(settings?.api_key ?? '')
  const [localBaseUrl, setLocalBaseUrl] = useState(settings?.base_url || defaultBaseUrl)
  
  const [isManagerOpen, setIsManagerOpen] = useState(false)
  const [isAddingCustom, setIsAddingCustom] = useState(false)
  const [customModelId, setCustomModelId] = useState('')

  const updateSettingsMutation = useUpdateSettings()
  const verifyProviderMutation = useVerifyProvider()

  useEffect(() => {
    setLocalApiKey(settings?.api_key ?? '')
    setLocalBaseUrl(settings?.base_url || defaultBaseUrl)
  }, [providerId, settings?.api_key, settings?.base_url, defaultBaseUrl])

  const handleBlur = () => {
    if (localApiKey === settings?.api_key && localBaseUrl === settings?.base_url) return
    
    updateSettingsMutation.mutateAsync({
      model_settings: {
        providers: {
          [providerId]: { 
            api_key: localApiKey,
            base_url: localBaseUrl || defaultBaseUrl,
          }
        }
      }
    }).catch(() => toast.error('Failed to update config'))
  }

  const handleToggleEnabled = () => {
    const newEnabled = !settings?.enabled
    updateSettingsMutation.mutateAsync({
      model_settings: {
        providers: {
          [providerId]: { enabled: newEnabled }
        }
      }
    }).catch(() => {})
  }

  const handleCheck = async () => {
    if (!localApiKey && providerId !== 'ollama') {
      toast.error('Please enter an API key first')
      return
    }
    
    try {
      const res = await verifyProviderMutation.mutateAsync({
        provider_id: settings.provider_type || providerId,
        base_url: localBaseUrl || defaultBaseUrl,
        api_key: localApiKey
      })
      
      if (res.success) {
        toast.success(res.message)
        // Auto-save the fetched models and the current credentials if there are no models yet
        if (!settings?.models || settings.models.length === 0) {
           await updateSettingsMutation.mutateAsync({
            model_settings: {
              providers: {
                [providerId]: {
                  api_key: localApiKey,
                  base_url: localBaseUrl || defaultBaseUrl,
                  models: res.models
                }
              }
            }
          })
        } else {
           // just update credentials
           await updateSettingsMutation.mutateAsync({
            model_settings: {
              providers: {
                [providerId]: {
                  api_key: localApiKey,
                  base_url: localBaseUrl || defaultBaseUrl,
                }
              }
            }
          })
        }
      } else {
        toast.error(res.message || 'Connection failed')
      }
    } catch (err: any) {
      toast.error(err.message || 'Connection failed')
    }
  }

  const handleRemoveModel = async (modelId: string) => {
    const newModels = (settings.models || []).filter(m => m !== modelId)
    await updateSettingsMutation.mutateAsync({
      model_settings: { providers: { [providerId]: { models: newModels } } }
    })
  }

  const handleAddCustomModel = async () => {
    if (!customModelId.trim()) {
      setIsAddingCustom(false)
      return
    }
    if ((settings.models || []).includes(customModelId.trim())) {
      toast.error('Model already exists')
      return
    }
    const newModels = [...(settings.models || []), customModelId.trim()]
    await updateSettingsMutation.mutateAsync({
      model_settings: { providers: { [providerId]: { models: newModels } } }
    })
    setCustomModelId('')
    setIsAddingCustom(false)
  }

  const models = settings?.models || []

  const CapabilityBadge = ({ icon: Icon, active, colorClass }: { icon: any, active: boolean, colorClass: string }) => {
    if (!active) return null
    return (
      <div className={`w-5 h-5 rounded flex items-center justify-center bg-gray-50 border border-gray-100 ${colorClass}`}>
        <Icon className="w-3 h-3" />
      </div>
    )
  }

  return (
    <div className="flex-1 min-w-0 bg-white p-8 overflow-y-auto">
      <div className="max-w-3xl mx-auto flex flex-col gap-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-slate-800 tracking-tight">{name}</h2>
            {getApiKeyUrl && (
              <a
                href={getApiKeyUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-ghost btn-xs text-xs text-[#00B96B] hover:text-[#00B96B] hover:bg-[#00B96B]/10 gap-1.5 font-semibold"
              >
                <ExternalLink className="w-3 h-3" />
                API Key
              </a>
            )}
          </div>
          <input 
            type="checkbox" 
            className="toggle toggle-success" 
            checked={settings?.enabled ?? true}
            onChange={handleToggleEnabled}
          />
        </div>

        {/* API Info */}
        <div className="flex flex-col gap-5">
          <div>
            <label className="flex text-sm font-bold text-slate-700 mb-2 items-center justify-between">
              API Key
              <button 
                className="text-xs font-semibold text-slate-400 hover:text-slate-600 flex items-center gap-1 transition-colors"
                onClick={() => document.getElementById('base-url-wrapper')?.classList.toggle('hidden')}
              >
                <Settings2 className="w-3.5 h-3.5" />
                Advanced
              </button>
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1 flex items-center">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={localApiKey}
                  onChange={(e) => setLocalApiKey(e.target.value)}
                  onBlur={handleBlur}
                  placeholder="••••••••••••••••••••••••"
                  className="w-full h-10 pl-4 pr-10 rounded-lg border border-gray-200 bg-white text-sm font-mono transition-colors focus:outline-none focus:border-[#00B96B] focus:ring-1 focus:ring-[#00B96B] shadow-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <button
                type="button"
                onClick={handleCheck}
                disabled={verifyProviderMutation.isPending}
                className="h-10 px-6 rounded-lg text-sm font-semibold text-white transition-all shadow-sm shrink-0 w-[100px] flex items-center justify-center hover:opacity-90 active:scale-95 disabled:opacity-50"
                style={{ backgroundColor: PRIMARY }}
              >
                {verifyProviderMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Check'}
              </button>
            </div>
          </div>

          <div id="base-url-wrapper" className="hidden animate-in fade-in slide-in-from-top-2 duration-200">
            <label className="block text-sm font-bold text-slate-700 mb-2">API Host</label>
            <input
              type="text"
              value={localBaseUrl}
              onChange={(e) => setLocalBaseUrl(e.target.value)}
              onBlur={handleBlur}
              placeholder={defaultBaseUrl}
              className="w-full h-10 px-4 rounded-lg border border-gray-200 bg-white text-sm font-mono transition-colors focus:outline-none focus:border-[#00B96B] focus:ring-1 focus:ring-[#00B96B] shadow-sm"
            />
            <p className="text-xs text-slate-400 mt-1.5 ml-1">Leave empty to use the default provider URL.</p>
          </div>
        </div>

        {/* Model List section */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800">
              Models <span className="ml-1 px-1.5 py-0.5 rounded-full bg-gray-100 text-xs text-gray-500 font-medium">{models.length}</span>
            </h3>
          </div>
          
          <div className="rounded-xl border border-gray-200 shadow-sm bg-white overflow-hidden flex flex-col">
            {models.length === 0 ? (
              <div className="p-8 flex flex-col items-center justify-center text-center">
                <div className="w-12 h-12 rounded-full bg-gray-50 flex items-center justify-center mb-3">
                  <Brain className="w-6 h-6 text-gray-300" />
                </div>
                <p className="text-sm font-medium text-slate-600 mb-1">No models configured</p>
                <p className="text-xs text-slate-400 max-w-[200px]">Click Check to auto-discover models or click Manage to select them manually.</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100 max-h-[400px] overflow-y-auto">
                {models.map(modelId => {
                  const caps = parseModelCapabilities(modelId)
                  return (
                    <li key={modelId} className="px-4 py-3 flex items-center justify-between group hover:bg-gray-50/50 transition-colors">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-slate-800 font-mono tracking-tight">{modelId}</span>
                        <div className="flex gap-1">
                          <CapabilityBadge icon={Eye} active={caps.vision} colorClass="text-emerald-600" />
                          <CapabilityBadge icon={Globe} active={caps.webSearch} colorClass="text-blue-500" />
                          <CapabilityBadge icon={Brain} active={caps.reasoning} colorClass="text-purple-600" />
                          <CapabilityBadge icon={Sun} active={caps.flash} colorClass="text-amber-500" />
                          <CapabilityBadge icon={Wrench} active={caps.toolUse} colorClass="text-orange-500" />
                        </div>
                      </div>
                      <button 
                        onClick={() => handleRemoveModel(modelId)}
                        className="w-7 h-7 rounded-md text-gray-400 hover:text-red-500 hover:bg-red-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all focus:opacity-100"
                        title="Remove model"
                      >
                        <Minus className="w-4 h-4" />
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}

            {/* Action Bar */}
            <div className="p-3 bg-gray-50/50 border-t border-gray-100 flex items-center gap-2">
              <button 
                onClick={() => setIsManagerOpen(true)}
                className="btn btn-sm bg-[#00B96B] hover:bg-[#00B96B]/90 text-white border-transparent font-medium shadow-sm hover:shadow"
              >
                <Settings2 className="w-4 h-4 mr-1" />
                Manage Models
              </button>
              
              {!isAddingCustom ? (
                <button 
                  onClick={() => setIsAddingCustom(true)}
                  className="btn btn-sm btn-ghost font-medium text-slate-600 border border-gray-200 hover:bg-white"
                >
                  <Plus className="w-4 h-4" />
                  Add Custom
                </button>
              ) : (
                <div className="flex items-center gap-2 animate-in fade-in slide-in-from-left-2 duration-200">
                  <input
                    type="text"
                    value={customModelId}
                    onChange={(e) => setCustomModelId(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddCustomModel()}
                    placeholder="Enter model id..."
                    autoFocus
                    className="h-8 px-3 rounded-md border border-[#00B96B] focus:outline-none focus:ring-1 focus:ring-[#00B96B] text-sm w-48 shadow-sm"
                  />
                  <button 
                    onClick={handleAddCustomModel}
                    className="btn btn-sm btn-square bg-[#00B96B] hover:bg-[#00B96B]/90 text-white border-transparent min-h-8 h-8 w-8"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={() => setIsAddingCustom(false)}
                    className="btn btn-sm btn-square btn-ghost min-h-8 h-8 w-8"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      <ModelManager 
        isOpen={isManagerOpen}
        onClose={() => setIsManagerOpen(false)}
        providerId={providerId}
        providerName={name}
        settings={settings}
        defaultBaseUrl={defaultBaseUrl}
      />
    </div>
  )
}

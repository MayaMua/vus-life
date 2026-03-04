import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Search, Eye, Globe, Sun, Wrench, Plus, Minus, Filter, RefreshCw, Loader2, Brain } from 'lucide-react'
import { parseModelCapabilities, parseModelFamily } from '../utils/modelUtils'
import { useUpdateSettings, useVerifyProvider } from '../useSettings'
import toast from 'react-hot-toast'
import type { ProviderSettings } from '../../../types/settings'

interface ModelManagerProps {
  isOpen: boolean
  onClose: () => void
  providerId: string
  providerName: string
  settings: ProviderSettings
  defaultBaseUrl: string
}

export const ModelManager: React.FC<ModelManagerProps> = ({
  isOpen,
  onClose,
  providerId,
  providerName,
  settings,
  defaultBaseUrl,
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState<string>('All')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [hasRefreshedOnce, setHasRefreshedOnce] = useState(false)
  
  // Available Models state (could also be kept in React Query cache if built out)
  const [availableModels, setAvailableModels] = useState<string[]>(settings?.models || [])

  const updateSettingsMutation = useUpdateSettings()
  const verifyProviderMutation = useVerifyProvider()

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      const res = await verifyProviderMutation.mutateAsync({
        provider_id: settings.provider_type || providerId,
        base_url: settings?.base_url || defaultBaseUrl,
        api_key: settings?.api_key || ''
      })
      if (res.success) {
        toast.success(`Discovered ${res.models?.length || 0} models`)
        setAvailableModels(res.models || [])
        setHasRefreshedOnce(true)
      } else {
        toast.error(res.message || 'Failed to fetch models')
      }
    } catch (e: any) {
      toast.error(e.message || 'Connection failed')
    } finally {
      setIsRefreshing(false)
    }
  }

  // Active models from config.json (source of truth)
  const activeModels = new Set(settings?.models || [])

  const handleToggleModel = async (modelId: string) => {
    const isAdded = activeModels.has(modelId)
    const newModels = isAdded 
      ? (settings.models || []).filter(m => m !== modelId)
      : [...(settings.models || []), modelId]

    await updateSettingsMutation.mutateAsync({
      model_settings: {
        providers: {
          [providerId]: { models: newModels }
        }
      }
    }).catch(() => toast.error('Failed to update models'))
  }

  // Filter and Group
  const filteredModels = useMemo(() => {
    let list = availableModels
    
    // Auto-populate from active models if availableModels is empty (first load edge case before refresh)
    if (list.length === 0 && settings?.models?.length > 0) {
      list = [...settings.models]
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      list = list.filter(m => m.toLowerCase().includes(q))
    }

    if (activeFilter !== 'All') {
      list = list.filter(m => {
        const caps = parseModelCapabilities(m)
        if (activeFilter === 'Vision') return caps.vision
        if (activeFilter === 'Reasoning') return caps.reasoning
        if (activeFilter === 'WebSearch') return caps.webSearch
        if (activeFilter === 'Tool') return caps.toolUse
        if (activeFilter === 'Embedding') return caps.embedding
        if (activeFilter === 'Free') return caps.free
        return true
      })
    }

    // Grouping
    const grouped: Record<string, string[]> = {}
    list.forEach(m => {
      const family = parseModelFamily(m, providerId)
      if (!grouped[family]) grouped[family] = []
      grouped[family].push(m)
    })
    
    // Sort groups alphabetically
    return Object.keys(grouped).sort().map(family => ({
      family,
      models: grouped[family].sort()
    }))
  }, [availableModels, searchQuery, activeFilter, providerId, settings.models])

  const CapabilityBadge = ({ icon: Icon, active, colorClass }: { icon: any, active: boolean, colorClass: string }) => {
    if (!active) return null
    return (
      <div className={`w-6 h-6 rounded-md flex items-center justify-center bg-gray-50 border border-gray-100 ${colorClass}`}>
        <Icon className="w-3.5 h-3.5" />
      </div>
    )
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end">
        {/* Backdrop */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/20 backdrop-blur-sm"
        />

        {/* Slide-over Panel */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="relative w-full max-w-2xl bg-[#FAFAFA] h-full shadow-2xl flex flex-col pt-safe"
        >
          {/* Header */}
          <div className="px-6 py-4 bg-white border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-800">{providerName} Models</h2>
              <p className="text-xs text-slate-500 mt-0.5">Manage available models for this provider</p>
            </div>
            <div className="flex items-center gap-2">
              <button 
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="btn btn-ghost btn-circle btn-sm"
                title="Fetch latest models"
              >
                <RefreshCw className={`w-4 h-4 text-slate-600 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
              <button onClick={onClose} className="btn btn-ghost btn-circle btn-sm">
                <X className="w-5 h-5 text-slate-600" />
              </button>
            </div>
          </div>

          {/* Search & Filters */}
          <div className="bg-white border-b border-gray-200 px-6 py-4 flex flex-col gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input 
                type="text" 
                placeholder="Search model id or name"
                className="w-full h-10 pl-9 pr-4 rounded-lg border border-gray-200 bg-white text-sm focus:outline-none focus:border-[#00B96B] focus:ring-1 focus:ring-[#00B96B] transition-colors shadow-sm"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-1 overflow-x-auto no-scrollbar pb-1">
              {['All', 'Reasoning', 'Vision', 'WebSearch', 'Free', 'Embedding', 'Tool'].map(f => (
                <button
                  key={f}
                  onClick={() => setActiveFilter(f)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                    activeFilter === f 
                      ? 'bg-[#00B96B]/10 text-[#00B96B] border border-[#00B96B]/20' 
                      : 'bg-white text-slate-600 border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {isRefreshing && !hasRefreshedOnce && filteredModels.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 gap-3 text-gray-400">
                <Loader2 className="w-6 h-6 animate-spin" />
                <p className="text-sm">Discovering available models...</p>
              </div>
            ) : filteredModels.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 gap-3 text-gray-400">
                <Filter className="w-8 h-8 opacity-20" />
                <p className="text-sm text-center">No models found.<br/>Try adjusting filters or refreshing.</p>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                {filteredModels.map((group) => (
                  <div key={group.family} className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                    {/* Group Header */}
                    <div className="bg-[#F8F9FA] px-4 py-2.5 border-b border-gray-200 flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-800">{group.family}</span>
                      <span className="text-xs font-medium text-slate-500 bg-gray-200/50 px-2 py-0.5 rounded-full">
                        {group.models.length}
                      </span>
                    </div>
                    {/* Models List */}
                    <div className="divide-y divide-gray-100">
                      {group.models.map(modelId => {
                        const caps = parseModelCapabilities(modelId)
                        const isAdded = activeModels.has(modelId)
                        
                        return (
                          <div key={modelId} className="px-4 py-3 flex items-center justify-between hover:bg-gray-50/50 transition-colors group">
                            <div className="flex items-center gap-3">
                              {/* Logo placeholder - using generic shapes based on Provider */}
                              <div className="w-8 h-8 rounded-lg bg-linear-to-tr from-indigo-500/10 to-purple-500/10 border border-indigo-500/10 flex items-center justify-center shrink-0">
                                <div className="w-3 h-3 rounded-full bg-indigo-500/80" />
                              </div>
                              <div className="flex flex-col">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-semibold text-slate-800 font-mono tracking-tight">{modelId}</span>
                                  <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                                    <CapabilityBadge icon={Eye} active={caps.vision} colorClass="text-emerald-600" />
                                    <CapabilityBadge icon={Globe} active={caps.webSearch} colorClass="text-blue-500" />
                                    <CapabilityBadge icon={Brain} active={caps.reasoning} colorClass="text-purple-600" />
                                    <CapabilityBadge icon={Sun} active={caps.flash} colorClass="text-amber-500" />
                                    <CapabilityBadge icon={Wrench} active={caps.toolUse} colorClass="text-orange-500" />
                                  </div>
                                </div>
                              </div>
                            </div>
                            
                            <button
                              onClick={() => handleToggleModel(modelId)}
                              className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                                isAdded 
                                  ? 'bg-red-50 text-red-500 hover:bg-red-100 border border-red-100' 
                                  : 'bg-gray-50 text-gray-400 hover:bg-[#00B96B] hover:text-white border border-gray-200 hover:border-[#00B96B]'
                              }`}
                            >
                              {isAdded ? <Minus className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}

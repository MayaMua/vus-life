/**
 * Left configuration sidebar: API status, gene/model/input, run prediction.
 * Resizable; supports manual input and file upload (CSV/VCF) with drag-drop.
 */

import React, { useEffect, useRef, useState } from 'react'
import {
  Settings2,
  Wifi,
  WifiOff,
  RefreshCw,
  ChevronDown,
  X,
  Check,
  Upload,
  Loader2,
  BrainCircuit,
  Download,
  AlertCircle,
} from 'lucide-react'
import { useVusStore } from '../stores/useVusStore'

export const VusSidebar: React.FC = () => {
  const {
    config,
    configLoading: isConfigLoading,
    isApiConnected,
    fetchConfig,
    selectedGene,
    setSelectedGene,
    isMetadataReady,
    isDownloadingMetadata,
    downloadMetadata,
    selectedAnnotation,
    setSelectedAnnotation,
    selectedModels,
    toggleModel,
    removeModel,
    filterSameConsequence,
    setFilterSameConsequence,
    manualInput,
    setManualInput,
    activeTab,
    setActiveTab,
    resultsLoading: isPredictionLoading,
    runPrediction,
    sidebarWidth,
    setSidebarWidth,
    isResizing,
    setIsResizing,
  } = useVusStore()

  const sidebarRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const startResizing = (e: React.MouseEvent) => {
    setIsResizing(true)
    e.preventDefault()
  }

  const stopResizing = () => setIsResizing(false)

  const resize = (e: MouseEvent) => {
    if (isResizing) {
      const newWidth = e.clientX - 64
      if (newWidth > 300 && newWidth < 600) setSidebarWidth(newWidth)
    }
  }

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize)
      window.addEventListener('mouseup', stopResizing)
    }
    return () => {
      window.removeEventListener('mousemove', resize)
      window.removeEventListener('mouseup', stopResizing)
    }
  }, [isResizing])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const processFile = (file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result
      if (typeof text !== 'string') return

      if (file.name.toLowerCase().endsWith('.csv')) {
        const lines = text.split(/\r?\n/).filter((line) => line.trim() !== '')
        if (lines.length > 0) {
          const headerRow = lines[0]
          const headers = headerRow.split(',').map((h) => h.trim().toLowerCase().replace(/^"|"$/g, ''))
          let targetCol = headers.findIndex((h) => h.includes('hgvs') || h === 'variant' || h === 'genomic')
          if (targetCol === -1 && lines.length > 1) {
            const firstData = lines[1].split(',')
            targetCol = firstData.findIndex((d) => {
              const val = d.trim()
              return (
                val.startsWith('NC_') ||
                val.startsWith('NM_') ||
                val.startsWith('NG_') ||
                val.includes(':g.') ||
                val.includes(':c.')
              )
            })
          }
          if (targetCol !== -1) {
            const extractedVariants = lines
              .slice(1)
              .map((line) => {
                const cols = line.split(',')
                return cols[targetCol] ? cols[targetCol].trim().replace(/^"|"$/g, '') : null
              })
              .filter((v): v is string => !!v)
            if (extractedVariants.length > 0) {
              setManualInput(extractedVariants.join('\n'))
              setActiveTab('manual')
              return
            }
          }
        }
      }
      setManualInput(text)
      setActiveTab('manual')
    }
    reader.readAsText(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = e.dataTransfer.files
    if (files?.length) processFile(files[0])
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files?.length) processFile(files[0])
  }

  const geneNames = config?.gene_names ?? []
  const annotationMethods = config?.annotation_methods ?? []
  const embeddingModelsList = config?.embedding_models ?? []

  return (
    <div
      ref={sidebarRef}
      style={{ width: `${sidebarWidth}px` }}
      className="flex flex-col bg-white border-r border-slate-200 relative shrink-0 shadow-sm z-10"
    >
      <div className="p-6 border-b border-slate-100 shrink-0">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-xl">
            <BrainCircuit className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-black text-slate-800 tracking-tighter">Variant Insight</h1>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 pb-32 scrollbar-hide">
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex flex-col gap-1">
              <label className="flex items-center gap-2 text-xs font-black text-slate-400 uppercase tracking-[0.2em]">
                <Settings2 className="w-4 h-4 text-blue-500" />
                Configuration
              </label>
              <div className="flex items-center gap-1.5 ml-6">
                {isApiConnected === true ? (
                  <span className="flex items-center gap-1 text-[9px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                    <Wifi className="w-3 h-3" /> API Online
                  </span>
                ) : isApiConnected === false ? (
                  <span className="flex items-center gap-1 text-[9px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-100">
                    <WifiOff className="w-3 h-3" /> Offline Mode
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[9px] font-bold text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full border border-slate-100">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Checking...
                  </span>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => fetchConfig()}
              disabled={isConfigLoading}
              className={`p-2 rounded-xl transition-all ${isConfigLoading ? 'bg-blue-50 text-blue-600' : 'text-slate-300 hover:text-slate-900 hover:bg-slate-50'}`}
              title="Refresh Configuration"
            >
              <RefreshCw className={`w-4 h-4 ${isConfigLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="space-y-5">
            <div>
              <span className="text-[10px] font-black text-slate-400 block mb-2 uppercase tracking-widest">
                Gene Symbol
              </span>
              <div className="flex items-start gap-2">
                <div className="relative flex-1">
                  <select
                    value={selectedGene}
                    onChange={(e) => setSelectedGene(e.target.value)}
                    disabled={isConfigLoading}
                    className={`w-full border rounded-xl px-4 py-2.5 text-sm font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/10 appearance-none disabled:opacity-50 transition-all ${!isMetadataReady && selectedGene ? 'bg-red-50 border-red-300' : 'bg-slate-50 border-slate-200'}`}
                  >
                    {geneNames.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
                {!isMetadataReady && selectedGene && (
                  <button
                    type="button"
                    onClick={() => downloadMetadata()}
                    disabled={isDownloadingMetadata}
                    className="p-2.5 bg-red-100 text-red-600 rounded-xl hover:bg-red-200 transition-colors shadow-sm relative group"
                    title="Download all training variant data for this gene."
                  >
                    {isDownloadingMetadata ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Download className="w-5 h-5" />
                    )}
                    <div className="absolute bottom-full right-0 mb-2 w-48 p-2 bg-slate-800 text-white text-[10px] rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                      Missing training data. Click to download.
                    </div>
                  </button>
                )}
              </div>
              {!isMetadataReady && selectedGene && (
                <div className="flex items-center gap-1.5 mt-2 text-red-600">
                  <AlertCircle className="w-3 h-3" />
                  <span className="text-[10px] font-bold">Local training data missing for {selectedGene}</span>
                </div>
              )}
            </div>

            <div>
              <span className="text-[10px] font-black text-slate-400 block mb-2 uppercase tracking-widest">
                Annotation Method
              </span>
              <div className="relative">
                <select
                  value={selectedAnnotation}
                  onChange={(e) => setSelectedAnnotation(e.target.value)}
                  disabled={isConfigLoading}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/10 appearance-none disabled:opacity-50"
                >
                  {annotationMethods.map((a) => (
                    <option key={a} value={a}>
                      {a.toUpperCase()}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>

            <div className="space-y-3">
              <span className="text-[10px] font-black text-slate-400 block uppercase tracking-widest">
                Embedding Models
              </span>
              <div className="flex flex-wrap gap-1.5 min-h-[36px] bg-slate-50/50 p-2 rounded-xl border border-slate-100">
                {selectedModels.map((m) => (
                  <div
                    key={m}
                    className="bg-slate-900 text-white pl-3 pr-1.5 py-1 rounded-lg text-[10px] font-black flex items-center gap-2 shadow-sm animate-in zoom-in-90 duration-200"
                  >
                    {m}
                    <button
                      type="button"
                      onClick={() => removeModel(m)}
                      className="p-0.5 hover:bg-white/20 rounded-md"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
                {selectedModels.length === 0 && (
                  <span className="text-[10px] text-slate-300 italic py-1">No models selected</span>
                )}
              </div>
              <div className="max-h-48 overflow-y-auto border border-slate-200 rounded-2xl p-2 space-y-1 bg-white shadow-inner">
                {embeddingModelsList.map((m) => {
                  const active = selectedModels.includes(m)
                  return (
                    <button
                      key={m}
                      type="button"
                      onClick={() => toggleModel(m)}
                      disabled={isConfigLoading}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold transition-all text-left ${active ? 'bg-blue-50 text-blue-700 shadow-sm border border-blue-100' : 'text-slate-500 hover:bg-slate-50'}`}
                    >
                      {m}
                      {active && <Check className="w-4 h-4" />}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="pt-2">
              <label className="flex items-center gap-3 cursor-pointer group p-3 bg-slate-50 rounded-2xl border border-transparent hover:border-slate-200 transition-all">
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={filterSameConsequence}
                    onChange={(e) => setFilterSameConsequence(e.target.checked)}
                    className="peer sr-only"
                  />
                  <div className="w-5 h-5 border-2 border-slate-300 rounded-md bg-white peer-checked:bg-blue-600 peer-checked:border-blue-600 transition-all shadow-sm flex items-center justify-center">
                    <Check className="w-3.5 h-3.5 text-white opacity-0 peer-checked:opacity-100" />
                  </div>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs font-bold text-slate-700">Filter by Severe Consequence</span>
                  <span className="text-[10px] text-slate-400 font-medium">Match within genomic subset</span>
                </div>
              </label>
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex bg-slate-100 p-1 rounded-2xl">
            <button
              type="button"
              onClick={() => setActiveTab('manual')}
              className={`flex-1 py-2.5 rounded-xl text-xs font-bold transition-all ${activeTab === 'manual' ? 'bg-white shadow-sm' : 'text-slate-500'}`}
            >
              Manual
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('file')}
              className={`flex-1 py-2.5 rounded-xl text-xs font-bold transition-all ${activeTab === 'file' ? 'bg-white shadow-sm' : 'text-slate-500'}`}
            >
              Upload
            </button>
          </div>
          {activeTab === 'manual' ? (
            <textarea
              value={manualInput}
              onChange={(e) => setManualInput(e.target.value)}
              placeholder="Paste HGVS genomic variants..."
              className="w-full h-32 bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs font-mono focus:ring-2 focus:ring-blue-500/10 resize-none outline-none"
            />
          ) : (
            <div
              role="button"
              tabIndex={0}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-3xl p-10 flex flex-col items-center gap-2 transition-all cursor-pointer ${
                isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-slate-50 hover:bg-blue-50/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.vcf,.txt"
                className="hidden"
                onChange={handleFileSelect}
              />
              <Upload className={`w-8 h-8 ${isDragging ? 'text-blue-500' : 'text-slate-300'}`} />
              <p className={`text-xs font-bold ${isDragging ? 'text-blue-600' : 'text-slate-500'}`}>
                {isDragging ? 'Drop file here' : 'Drop VCF or CSV'}
              </p>
            </div>
          )}
        </section>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-6 bg-white border-t border-slate-100 shadow-xl">
        <button
          type="button"
          onClick={() => runPrediction()}
          disabled={isPredictionLoading || !manualInput.trim() || selectedModels.length === 0}
          className="w-full py-4 bg-slate-900 text-white font-black rounded-2xl shadow-xl hover:bg-black transition-all active:scale-[0.98] disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isPredictionLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              {isApiConnected ? 'RUN PREDICTION' : 'RUN MOCK PREDICTION'}
              {!isApiConnected && <WifiOff className="w-4 h-4 opacity-50" />}
            </>
          )}
        </button>
      </div>

      <div
        role="separator"
        onMouseDown={startResizing}
        className="absolute right-0 top-0 bottom-0 w-1 hover:bg-blue-400 cursor-col-resize z-20"
      />
    </div>
  )
}

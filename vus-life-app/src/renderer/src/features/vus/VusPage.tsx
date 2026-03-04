/**
 * VUS Prediction page: left config sidebar, right results + variant detail sheet.
 * Agreement modal inline; API status from useVusApiConnected. No store.
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Search, Database, ArrowLeft } from 'lucide-react'
import { useVusApiConnected } from './useVusApiConnected'
import { useVusConfig } from './useVusConfig'
import { LeftPanel } from './components/LeftPanel'
import { VusResultsTable } from './components/VusResultsTable'
import { VariantDetails } from './components/VariantDetails'
import { MetadataView } from './components/MetadataView'
import { buildVariantRows } from './utils/buildVariantRows'
import { getPredictionResults } from '../../api/endpoints'
import type { VariantRow } from './types'



/** Payload passed from LeftPanel when user clicks Run Prediction. */
export interface RunPredictionPayload {
  gene_symbol: string
  annotation_method: string
  embedding_models: string[]
  same_severe_consequence: boolean
  manual_input: string
}

export const VusPage: React.FC = () => {
  const { isApiConnected } = useVusApiConnected()
  const { data: configData } = useVusConfig()
  const [selectedGene, setSelectedGene] = useState('')
  const [variantRows, setVariantRows] = useState<VariantRow[]>([])
  const [resultsLoading, setResultsLoading] = useState(false)
  const [resultsError, setResultsError] = useState<string | null>(null)
  const showResultsError = resultsError
  const [selectedVariant, setSelectedVariant] = useState<VariantRow | null>(null)
  const [hasRunPrediction, setHasRunPrediction] = useState(false)

  const showMetadataView = !hasRunPrediction

  // Set initial selected gene from API config (GET /api/vus/config) when gene list is loaded
  useEffect(() => {
    const genes = configData?.gene_names
    if (genes?.length && !selectedGene) {
      setSelectedGene(genes[0])
    }
  }, [configData?.gene_names, selectedGene])

  const runPrediction = useCallback(async (payload: RunPredictionPayload) => {
    const lines = payload.manual_input
      .trim()
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
      .slice(0, 20)

    if (lines.length === 0) {
      setResultsError('Please add at least one variant (manual entry or file).')
      return
    }
    if (!payload.gene_symbol) {
      setResultsError('Please select a gene symbol.')
      return
    }
    if (payload.embedding_models.length === 0) {
      setResultsError('Please select at least one embedding model.')
      return
    }

    setResultsLoading(true)
    setResultsError(null)
    setHasRunPrediction(true)
    try {
      const response = await getPredictionResults({
        gene_symbol: payload.gene_symbol,
        hgvs_genomic_38: lines,
        annotation_method: [payload.annotation_method],
        embedding_models: payload.embedding_models,
        same_severe_consequence: payload.same_severe_consequence,
      })

      console.log("Prediction API Response:", response);

      // Warn user if some HGVS strings could not be converted
      const failed = (response as unknown as Record<string, unknown>).failed_hgvs as string[] | undefined
      if (failed && failed.length > 0) {
        setResultsError(`${failed.length} variant(s) could not be parsed and were skipped: ${failed.join(', ')}`)
      }

      setVariantRows(buildVariantRows(response))
    } catch (e) {
      setResultsError(e instanceof Error ? e.message : 'Prediction failed')
    } finally {
      setResultsLoading(false)
    }
  }, [])

  return (
    <div className="flex h-full bg-[#f8fafc] text-slate-900 overflow-hidden select-none font-sans">
      <LeftPanel
        selectedGene={selectedGene}
        setSelectedGene={setSelectedGene}
        onRunPrediction={runPrediction}
        resultsLoading={resultsLoading}
      />

      <div className="flex-1 flex flex-col overflow-hidden relative min-w-[800px]">
        <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-3">
            <div className="bg-slate-900 p-1.5 rounded-lg">
              <Database className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-black text-slate-900 uppercase tracking-tighter">
              Variant Explorer
            </span>
          </div>
          <div className="flex items-center gap-4">
            {!showMetadataView && (
              <button
                type="button"
                onClick={() => {
                  setVariantRows([])
                  setHasRunPrediction(false)
                  setResultsError(null)
                }}
                className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Metadata
              </button>
            )}
            {isApiConnected && (
              <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-50 text-emerald-600 rounded-full border border-emerald-100 text-[10px] font-black uppercase tracking-widest">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                Live Sync
              </div>
            )}
            <button
              type="button"
              className="p-2.5 hover:bg-slate-100 rounded-xl text-slate-400"
              aria-label="Search"
            >
              <Search className="w-5 h-5" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8 bg-slate-50/30 scrollbar-hide min-w-0">
          {showResultsError && (
            <div className="mb-4 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-800">
              {showResultsError}
            </div>
          )}
          <div className="max-w-full">
            {showMetadataView ? (
              <MetadataView geneSymbol={selectedGene} />
            ) : (
              <VusResultsTable
                variantRows={variantRows}
                resultsLoading={resultsLoading}
                selectedVariant={selectedVariant}
                onSelectVariant={setSelectedVariant}
              />
            )}
          </div>
        </main>

        <VariantDetails
          selectedVariant={selectedVariant}
          onClose={() => setSelectedVariant(null)}
        />
      </div>
    </div>
  )
}

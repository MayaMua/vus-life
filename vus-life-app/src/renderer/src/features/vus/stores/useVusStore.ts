/**
 * Zustand store for VUS page: config, variants, results, and agreement state.
 * Persists agreement acceptance to localStorage via a thin wrapper.
 * isApiConnected is set by pinging the VUS API (from useVusApiStore) in fetchConfig.
 */

import { create } from 'zustand'
import { useVusApiStore } from '../../../store/useVusApiStore'
import type { VusConfig, PredictionResultsResponse, VariantRow, VariantMetadata } from '../types'

const AGREEMENT_KEY = 'vus_agreement_accepted'

function getAgreementAccepted(): boolean {
  try {
    return localStorage.getItem(AGREEMENT_KEY) === 'true'
  } catch {
    return false
  }
}

function setAgreementAccepted(value: boolean): void {
  try {
    localStorage.setItem(AGREEMENT_KEY, value ? 'true' : 'false')
  } catch {
    // ignore
  }
}

export interface VusState {
  // Agreement
  showAgreement: boolean
  agreementAccepted: boolean
  setShowAgreement: (show: boolean) => void
  /** Accept and close. If dontShowAgain is true, persist so dialog won't show on next launch. */
  acceptAgreement: (dontShowAgain?: boolean) => void

  // Config (from "server" / mock)
  config: VusConfig | null
  configLoading: boolean
  configError: string | null
  /** true = online, false = offline, undefined = checking */
  isApiConnected: boolean | undefined
  fetchConfig: () => Promise<void>

  // Form state (left panel) – aliased for VusSidebar
  geneSymbol: string
  annotationMethod: string
  embeddingModels: string[]
  sameSevereConsequence: boolean
  setGeneSymbol: (v: string) => void
  setAnnotationMethod: (v: string) => void
  setEmbeddingModels: (v: string[]) => void
  setSameSevereConsequence: (v: boolean) => void
  selectedGene: string
  setSelectedGene: (v: string) => void
  selectedAnnotation: string
  setSelectedAnnotation: (v: string) => void
  selectedModels: string[]
  toggleModel: (m: string) => void
  removeModel: (m: string) => void
  filterSameConsequence: boolean
  setFilterSameConsequence: (v: boolean) => void
  manualInput: string
  setManualInput: (v: string) => void
  activeTab: 'manual' | 'file'
  setActiveTab: (v: 'manual' | 'file') => void

  // Input: manual text or file (internal)
  inputMethod: 'manual' | 'file'
  manualInputText: string
  setInputMethod: (v: 'manual' | 'file') => void
  setManualInputText: (v: string) => void

  // Sidebar resize and metadata (stubs)
  sidebarWidth: number
  setSidebarWidth: (w: number) => void
  isResizing: boolean
  setIsResizing: (v: boolean) => void
  isMetadataReady: boolean
  isDownloadingMetadata: boolean
  downloadMetadata: () => Promise<void>
  /** Parsed variants ready for API (VCF-like). */
  inputVariants: Array<{ chromosome: string; position: number; ref_allele: string; alt_allele: string; hgvs_genomic_38?: string }>
  setInputVariants: (v: VusState['inputVariants']) => void

  // Results
  predictionResults: PredictionResultsResponse | null
  resultsLoading: boolean
  resultsError: string | null
  setPredictionResults: (r: PredictionResultsResponse | null) => void
  runPrediction: () => Promise<void>

  // Combined table rows (existing + new) for display
  variantRows: VariantRow[]
  setVariantRows: (rows: VariantRow[]) => void

  // Detail sheet
  selectedVariant: VariantRow | null
  setSelectedVariant: (v: VariantRow | null) => void
}

export const useVusStore = create<VusState>((set, get) => ({
  showAgreement: false,
  agreementAccepted: getAgreementAccepted(),
  setShowAgreement: (show) => set({ showAgreement: show }),
  acceptAgreement: (dontShowAgain = false) => {
    if (dontShowAgain) {
      setAgreementAccepted(true)
      set({ agreementAccepted: true, showAgreement: false })
    } else {
      set({ showAgreement: false })
    }
  },

  config: null,
  configLoading: false,
  configError: null,
  isApiConnected: undefined as boolean | undefined,
  fetchConfig: async () => {
    if (get().config) return
    set({ configLoading: true, configError: null, isApiConnected: undefined })
    try {
      const { fetchMockConfig } = await import('../services/mockPredictionApi')
      const config = await fetchMockConfig()
      const current = get()
      const embeddingModels =
        current.embeddingModels.length === 0 ? (config?.embedding_models ?? []) : current.embeddingModels
      set({
        config,
        configLoading: false,
        embeddingModels,
        selectedModels: embeddingModels,
      })
      const apiUrl = useVusApiStore.getState().apiUrl?.trim()?.replace(/\/$/, '')
      if (!apiUrl) {
        set({ isApiConnected: false })
      } else {
        try {
          const ctrl = new AbortController()
          const t = setTimeout(() => ctrl.abort(), 5000)
          const r = await fetch(`${apiUrl}/health`, {
            signal: ctrl.signal,
            headers: { Accept: 'application/json', 'ngrok-skip-browser-warning': 'true' },
          })
          clearTimeout(t)
          set({ isApiConnected: r.ok })
        } catch {
          set({ isApiConnected: false })
        }
      }
    } catch (e) {
      set({
        configLoading: false,
        configError: e instanceof Error ? e.message : 'Failed to load config',
        isApiConnected: false,
      })
    }
  },

  geneSymbol: 'ATM',
  annotationMethod: 'vep',
  embeddingModels: [],
  sameSevereConsequence: false,
  setGeneSymbol: (v) => set({ geneSymbol: v, selectedGene: v }),
  setAnnotationMethod: (v) => set({ annotationMethod: v, selectedAnnotation: v }),
  setEmbeddingModels: (v) => set({ embeddingModels: v, selectedModels: v }),
  setSameSevereConsequence: (v) => set({ sameSevereConsequence: v, filterSameConsequence: v }),
  selectedGene: 'ATM',
  setSelectedGene: (v) => set({ geneSymbol: v, selectedGene: v }),
  selectedAnnotation: 'vep',
  setSelectedAnnotation: (v) => set({ annotationMethod: v, selectedAnnotation: v }),
  selectedModels: [],
  toggleModel: (m) => {
    const list = get().embeddingModels
    const next = list.includes(m) ? list.filter((x) => x !== m) : [...list, m]
    set({ embeddingModels: next, selectedModels: next })
  },
  removeModel: (m) => {
    const next = get().embeddingModels.filter((x) => x !== m)
    set({ embeddingModels: next, selectedModels: next })
  },
  filterSameConsequence: false,
  setFilterSameConsequence: (v) => set({ sameSevereConsequence: v, filterSameConsequence: v }),
  manualInput: '',
  setManualInput: (v) => set({ manualInputText: v, manualInput: v }),
  activeTab: 'manual' as const,
  setActiveTab: (v) => set({ inputMethod: v, activeTab: v }),

  inputMethod: 'manual',
  manualInputText: '',
  setInputMethod: (v) => set({ inputMethod: v, activeTab: v }),
  setManualInputText: (v) => set({ manualInputText: v, manualInput: v }),
  inputVariants: [],
  setInputVariants: (v) => set({ inputVariants: v }),

  sidebarWidth: 360,
  setSidebarWidth: (w) => set({ sidebarWidth: w }),
  isResizing: false,
  setIsResizing: (v) => set({ isResizing: v }),
  isMetadataReady: true,
  isDownloadingMetadata: false,
  downloadMetadata: async () => {
    set({ isDownloadingMetadata: true })
    await new Promise((r) => setTimeout(r, 800))
    set({ isDownloadingMetadata: false, isMetadataReady: true })
  },

  predictionResults: null,
  resultsLoading: false,
  resultsError: null,
  setPredictionResults: (r) => set({ predictionResults: r, resultsError: null }),
  runPrediction: async () => {
    const state = get()
    let variants = state.inputVariants
    if (state.inputMethod === 'manual' && state.manualInputText.trim()) {
      const lines = state.manualInputText.trim().split('\n').map((l) => l.trim()).filter(Boolean).slice(0, 20)
      variants = lines.map((_, i) => ({
        chromosome: '17',
        position: 43064189 + i,
        ref_allele: 'T',
        alt_allele: 'C',
        hgvs_genomic_38: lines[i] ?? '',
      }))
    }
    if (variants.length === 0) {
      set({ resultsError: 'Please add at least one variant (manual entry or file).' })
      return
    }
    if (!state.geneSymbol) {
      set({ resultsError: 'Please select a gene symbol.' })
      return
    }
    if (state.embeddingModels.length === 0) {
      set({ resultsError: 'Please select at least one embedding model.' })
      return
    }
    set({ resultsLoading: true, resultsError: null })
    try {
      const { getMockPredictionResults } = await import('../services/mockPredictionApi')
      const payload = {
        gene_symbol: state.geneSymbol,
        variants,
        annotation_method: state.annotationMethod,
        embedding_models: state.embeddingModels,
        same_severe_consequence: state.sameSevereConsequence,
      }
      const response = await getMockPredictionResults(payload)
      set({ predictionResults: response, resultsLoading: false })
      // Build combined variant rows for table
      const rows = buildVariantRows(response)
      set({ variantRows: rows })
    } catch (e) {
      set({
        resultsLoading: false,
        resultsError: e instanceof Error ? e.message : 'Prediction failed',
      })
    }
  },

  variantRows: [],
  setVariantRows: (rows) => set({ variantRows: rows }),

  selectedVariant: null,
  setSelectedVariant: (v) => set({ selectedVariant: v }),
}))

/** Build combined table rows from API response (existing + new) with Status. */
function buildVariantRows(res: PredictionResultsResponse): VariantRow[] {
  const existingSet = new Set(res.existing_variants ?? [])
  const pred = res.prediction_results ?? {}
  const modelNames = res.model_name ?? []
  const k = '5'

  const rows: VariantRow[] = []

  for (const variantId of Object.keys(pred)) {
    const data = pred[variantId]
    const metadata = (data?.metadata ?? data) as VariantMetadata
    const isExisting = existingSet.has(variantId)
    const status: 'existing' | 'new' = isExisting ? 'existing' : 'new'

    let prediction_score: string | undefined
    let prediction_label: string | undefined
    if (!isExisting && modelNames.length > 0) {
      const firstModel = modelNames[0]
      const modelData = (data as Record<string, unknown>)[firstModel]
      if (modelData && typeof modelData === 'object' && !('error' in modelData)) {
        const predResult = (modelData as Record<string, unknown>).prediction_result as Record<string, { confidence_score?: string; pred_result?: string }> | undefined
        const kData = predResult?.[k] ?? predResult?.['1']
        prediction_score = kData?.confidence_score ?? ''
        prediction_label = kData?.pred_result ?? prediction_score
      }
    }

    rows.push({
      variant_id: variantId,
      hgvs_genomic_38: metadata?.hgvs_genomic_38 ?? variantId,
      most_severe_consequence: metadata?.most_severe_consequence ?? '—',
      pathogenicity_original: metadata?.pathogenicity_original,
      prediction_score: status === 'new' ? prediction_score : undefined,
      prediction_label: status === 'new' ? prediction_label : undefined,
      status,
      metadata: metadata ?? {},
    })
  }

  return rows
}

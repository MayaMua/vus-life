/**
 * Left panel: Gene & model config, input (Manual / File), and Run Prediction button.
 */

import React, { useCallback } from 'react'
import { useVusStore } from '../stores/useVusStore'

const MAX_VARIANTS = 20

/** Simple HGVS→VCF mock for file upload; real conversion would run in backend. */
function toVcfLike(
  items: Array<{ hgvs_genomic_38: string }>
): Array<{ chromosome: string; position: number; ref_allele: string; alt_allele: string; hgvs_genomic_38?: string }> {
  return items.map((item, i) => ({
    chromosome: '17',
    position: 43064189 + i,
    ref_allele: 'T',
    alt_allele: 'C',
    hgvs_genomic_38: item.hgvs_genomic_38,
  }))
}

export const LeftPanel: React.FC = () => {
  const config = useVusStore((s) => s.config)
  const configLoading = useVusStore((s) => s.configLoading)
  const geneSymbol = useVusStore((s) => s.geneSymbol)
  const annotationMethod = useVusStore((s) => s.annotationMethod)
  const embeddingModels = useVusStore((s) => s.embeddingModels)
  const sameSevereConsequence = useVusStore((s) => s.sameSevereConsequence)
  const inputMethod = useVusStore((s) => s.inputMethod)
  const manualInputText = useVusStore((s) => s.manualInputText)
  const resultsLoading = useVusStore((s) => s.resultsLoading)

  const setGeneSymbol = useVusStore((s) => s.setGeneSymbol)
  const setAnnotationMethod = useVusStore((s) => s.setAnnotationMethod)
  const setEmbeddingModels = useVusStore((s) => s.setEmbeddingModels)
  const setSameSevereConsequence = useVusStore((s) => s.setSameSevereConsequence)
  const setInputMethod = useVusStore((s) => s.setInputMethod)
  const setManualInputText = useVusStore((s) => s.setManualInputText)
  const setInputVariants = useVusStore((s) => s.setInputVariants)
  const runPrediction = useVusStore((s) => s.runPrediction)

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) {
        setInputVariants([])
        return
      }
      const reader = new FileReader()
      reader.onload = () => {
        const text = String(reader.result ?? '')
        const lines = text
          .trim()
          .split(/\r?\n/)
          .map((l) => l.trim())
          .filter(Boolean)
        let items: Array<{ hgvs_genomic_38: string }>
        if (text.includes(',') && lines[0]?.toLowerCase().includes('hgvs')) {
          const header = lines[0].toLowerCase().split(',')
          const colIdx = header.findIndex((h) => h.includes('hgvs'))
          if (colIdx >= 0) {
            items = lines.slice(1, MAX_VARIANTS + 1).map((line) => ({
              hgvs_genomic_38: line.split(',')[colIdx]?.trim() ?? line,
            }))
          } else {
            items = lines.slice(0, MAX_VARIANTS).map((line) => ({ hgvs_genomic_38: line }))
          }
        } else {
          items = lines.slice(0, MAX_VARIANTS).map((line) => ({ hgvs_genomic_38: line }))
        }
        setInputVariants(toVcfLike(items))
      }
      reader.readAsText(file)
      e.target.value = ''
    },
    [setInputVariants]
  )

  const handleRun = useCallback(() => {
    runPrediction()
  }, [runPrediction])

  const toggleModel = (name: string) => {
    if (embeddingModels.includes(name)) {
      setEmbeddingModels(embeddingModels.filter((m) => m !== name))
    } else {
      setEmbeddingModels([...embeddingModels, name])
    }
  }

  return (
    <div className="w-full max-w-md flex flex-col gap-5 p-5 border-r border-base-300 bg-base-200/40 overflow-y-auto">
      {/* Gene & Model Config */}
      <div className="card bg-base-100 shadow-md border border-base-200">
        <div className="card-body gap-4">
          <h4 className="card-title text-base font-semibold">Gene & Model Config</h4>

          <label className="form-control w-full">
            <span className="label-text">Gene Symbol</span>
            <select
              className="select select-bordered w-full"
              value={geneSymbol}
              onChange={(e) => setGeneSymbol(e.target.value)}
              disabled={configLoading}
            >
              {(config?.gene_names ?? []).map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
              {!config?.gene_names?.length && !configLoading && (
                <option value="">—</option>
              )}
            </select>
          </label>

          <label className="form-control w-full">
            <span className="label-text">Annotation Method</span>
            <select
              className="select select-bordered w-full"
              value={annotationMethod}
              onChange={(e) => setAnnotationMethod(e.target.value)}
              disabled={configLoading}
            >
              {(config?.annotation_methods ?? []).map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>

          <div className="form-control">
            <span className="label-text">Embedding Models</span>
            <div className="flex flex-wrap gap-2 mt-1">
              {(config?.embedding_models ?? []).map((m) => (
                <button
                  key={m}
                  type="button"
                  className={`btn btn-sm ${embeddingModels.includes(m) ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => toggleModel(m)}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <label className="label cursor-pointer justify-start gap-2">
            <input
              type="checkbox"
              className="checkbox checkbox-sm"
              checked={sameSevereConsequence}
              onChange={(e) => setSameSevereConsequence(e.target.checked)}
            />
            <span className="label-text">Filter by same severe consequence</span>
          </label>
        </div>
      </div>

      {/* Input: Tabs Manual / File */}
      <div className="card bg-base-100 shadow-md border border-base-200 flex-1 min-h-0 flex flex-col">
        <div className="card-body gap-3 flex-1 min-h-0">
          <h4 className="card-title text-base font-semibold">Input</h4>
          <div role="tablist" className="join tabs tabs-boxed tabs-sm w-full">
            <button
              type="button"
              role="tab"
              className={`join-item tab flex-1 ${inputMethod === 'manual' ? 'tab-active' : ''}`}
              onClick={() => setInputMethod('manual')}
            >
              Manual Entry
            </button>
            <button
              type="button"
              role="tab"
              className={`join-item tab flex-1 ${inputMethod === 'file' ? 'tab-active' : ''}`}
              onClick={() => setInputMethod('file')}
            >
              File Upload
            </button>
          </div>

          {inputMethod === 'manual' && (
            <>
              <p className="text-xs text-base-content/70">One HGVS genomic 38 per line (max {MAX_VARIANTS})</p>
              <textarea
                className="textarea textarea-bordered w-full flex-1 min-h-[140px] font-mono text-sm resize-y"
                placeholder="NC_000017.11:g.43064189T>C&#10;NC_000017.11:g.43097353del"
                value={manualInputText}
                onChange={(e) => setManualInputText(e.target.value)}
              />
            </>
          )}

          {inputMethod === 'file' && (
            <div className="flex-1 flex flex-col gap-2">
              <p className="text-xs text-base-content/70">CSV or TXT, one HGVS per line or column hgvs_genomic_38 (max {MAX_VARIANTS})</p>
              <label className="flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-base-300 bg-base-200/50 p-8 cursor-pointer hover:bg-base-200 hover:border-primary/30 transition-colors">
                <input
                  type="file"
                  accept=".csv,.txt"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <span className="text-sm text-base-content/70">Drop file or click to upload</span>
              </label>
            </div>
          )}
        </div>
      </div>

      <button
        type="button"
        className="btn btn-primary w-full btn-md shadow-md"
        disabled={resultsLoading}
        onClick={handleRun}
      >
        {resultsLoading ? 'Running…' : 'Run Prediction'}
      </button>
    </div>
  )
}

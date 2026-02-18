/**
 * Side drawer (DaisyUI drawer) opened when a table row is clicked.
 * Shows full variant details, embedding plot placeholder (Recharts), and "Ask AI" with mock streaming.
 */

import React, { useState, useEffect, useRef } from 'react'
import type { VariantRow } from '../types'

interface VariantDetailSheetProps {
  variant: VariantRow | null
  onClose: () => void
}

const MOCK_STREAMING_TEXT =
  'This variant is classified as a missense substitution. Based on the embedding similarity to training variants, the model suggests **uncertain significance** with moderate confidence. Consider reviewing the top similar variants and clinical evidence.'

export const VariantDetailSheet: React.FC<VariantDetailSheetProps> = ({ variant, onClose }) => {
  const [aiResponse, setAiResponse] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!variant) return
    setAiResponse('')
    setIsStreaming(false)
  }, [variant])

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  const handleAnalyze = () => {
    if (!variant) return
    if (intervalRef.current) clearInterval(intervalRef.current)
    setIsStreaming(true)
    setAiResponse('')
    let i = 0
    intervalRef.current = setInterval(() => {
      setAiResponse(MOCK_STREAMING_TEXT.slice(0, i + 1))
      i += 1
      if (i >= MOCK_STREAMING_TEXT.length) {
        if (intervalRef.current) clearInterval(intervalRef.current)
        intervalRef.current = null
        setIsStreaming(false)
      }
    }, 20)
  }

  if (!variant) return null

  const meta = variant.metadata ?? {}

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-30" aria-hidden onClick={onClose} />
      <div className="fixed top-0 right-0 bottom-0 w-full max-w-lg bg-base-100 shadow-xl z-40 overflow-y-auto flex flex-col p-4 gap-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-lg">Variant details</h3>
            <button type="button" className="btn btn-ghost btn-sm btn-circle" onClick={onClose} aria-label="Close">
              ✕
            </button>
          </div>

          <div className="card bg-base-200 shadow-sm">
            <div className="card-body gap-2">
              <p><span className="font-semibold">Variant ID:</span> {variant.variant_id}</p>
              <p><span className="font-semibold">HGVS (genomic):</span> {variant.hgvs_genomic_38}</p>
              <p><span className="font-semibold">Consequence:</span> {variant.most_severe_consequence}</p>
              <p><span className="font-semibold">Pathogenicity:</span> {variant.pathogenicity_original ?? '—'}</p>
              {variant.prediction_score != null && (
                <p><span className="font-semibold">Prediction score:</span> {variant.prediction_score}</p>
              )}
              {meta.gene_symbol != null && <p><span className="font-semibold">Gene:</span> {String(meta.gene_symbol)}</p>}
              {meta.hgvs_coding && <p><span className="font-semibold">HGVS (coding):</span> {String(meta.hgvs_coding)}</p>}
              {meta.hgvs_protein && <p><span className="font-semibold">HGVS (protein):</span> {String(meta.hgvs_protein)}</p>}
            </div>
          </div>

          <div className="card bg-base-200 shadow-sm">
            <div className="card-body gap-2">
              <h4 className="font-semibold">Embedding plot</h4>
              <div className="h-48 rounded-lg bg-base-300 flex items-center justify-center text-base-content/60 text-sm">
                Recharts placeholder (embedding visualization)
              </div>
            </div>
          </div>

          <div className="card bg-base-200 shadow-sm">
            <div className="card-body gap-2">
              <h4 className="font-semibold">Ask AI</h4>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                disabled={isStreaming}
                onClick={handleAnalyze}
              >
                {isStreaming ? 'Analyzing…' : 'Analyze this Variant'}
              </button>
              {aiResponse && (
                <div className="mt-2 p-3 rounded-lg bg-base-100 text-sm whitespace-pre-wrap">
                  {aiResponse}
                </div>
              )}
            </div>
          </div>
      </div>
    </>
  )
}

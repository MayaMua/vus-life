/**
 * Slide-over variant detail: score gauge and info grid.
 */

import React from 'react'
import { X, PlusCircle } from 'lucide-react'
import { ScoreGauge } from '../../../components/ScoreGauge'
import type { VariantRow } from '../types'

export interface VariantDetailsProps {
  selectedVariant: VariantRow | null
  onClose: () => void
}

/** Derive detail display fields from VariantRow. */
function toDetailShape(row: VariantRow): {
  id: string
  score: number
  pathogenicity: string
  gene: string
  ref: string
  alt: string
  position: number
  consequence: string
} {
  const scoreNum = row.prediction_score != null ? parseFloat(row.prediction_score) : 0
  return {
    id: row.variant_id,
    score: Number.isFinite(scoreNum) ? scoreNum : 0,
    pathogenicity:
      row.prediction_label ?? row.pathogenicity_original ?? row.most_severe_consequence ?? 'Uncertain',
    gene: String(row.metadata?.gene_symbol ?? '—'),
    ref: String(row.metadata?.ref_allele ?? '—'),
    alt: String(row.metadata?.alt_allele ?? '—'),
    position: parseInt(String(row.metadata?.position ?? '0'), 10) || 0,
    consequence: row.most_severe_consequence ?? '—',
  }
}

export const VariantDetails: React.FC<VariantDetailsProps> = ({ selectedVariant, onClose }) => {
  if (!selectedVariant) return null

  const detail = toDetailShape(selectedVariant)

  return (
    <div className="absolute inset-y-0 right-0 w-[500px] bg-white border-l border-slate-200 shadow-2xl z-30 flex flex-col animate-in slide-in-from-right duration-500">
      <div className="p-8 border-b border-slate-100 flex items-center justify-between shrink-0 bg-slate-50/50">
        <div className="flex items-center gap-4">
          <div className="bg-slate-900 p-3 rounded-2xl">
            <PlusCircle className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">Variant Profile</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-2.5 hover:bg-slate-200 rounded-xl text-slate-400 hover:text-slate-900 transition-colors"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-8 space-y-10 scrollbar-hide">
        <section className="bg-slate-900 rounded-[2.5rem] p-10 text-center shadow-2xl relative overflow-hidden">
          <ScoreGauge score={detail.score} />
          <p className="text-2xl font-black text-white tracking-tight mt-6 uppercase">
            {detail.pathogenicity}
          </p>
          <p className="text-[10px] text-slate-500 font-black tracking-widest mt-2 uppercase">
            Synthesized Confidence
          </p>
        </section>

        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Gene', value: detail.gene },
            { label: 'Ref/Alt', value: `${detail.ref} > ${detail.alt}` },
            { label: 'Position', value: detail.position.toLocaleString() },
            { label: 'Consequence', value: detail.consequence },
          ].map((item, i) => (
            <div key={i} className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                {item.label}
              </span>
              <span className="text-sm font-black text-slate-800 break-all">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * Results table: loading state, empty state, or rows with Source/HGVS/Prediction/Risk/Details.
 * Row click opens VariantDetails; data derived from variantRows.
 */

import React from 'react'
import { Dna, ChevronRight, Loader2 } from 'lucide-react'
import { useVusStore } from '../stores/useVusStore'
import type { VariantRow } from '../types'

/** Map store variant row to table row shape (id, score, pathogenicity, status label). */
function toTableRow(row: VariantRow): {
  id: string
  hgvs_genomic_38: string
  pathogenicity: string
  score: number
  status: string
} {
  const scoreNum = row.prediction_score != null ? parseFloat(row.prediction_score) : 0
  const pathogenicity =
    row.prediction_label ?? row.pathogenicity_original ?? row.most_severe_consequence ?? '—'
  return {
    id: row.variant_id,
    hgvs_genomic_38: row.hgvs_genomic_38,
    pathogenicity: String(pathogenicity),
    score: Number.isFinite(scoreNum) ? scoreNum : 0,
    status: row.status === 'new' ? 'New' : 'Existing',
  }
}

export const VusResultsTable: React.FC = () => {
  const variantRows = useVusStore((s) => s.variantRows)
  const isPredictionLoading = useVusStore((s) => s.resultsLoading)
  const selectedVariant = useVusStore((s) => s.selectedVariant)
  const setSelectedVariant = useVusStore((s) => s.setSelectedVariant)

  const results = variantRows.map(toTableRow)

  if (isPredictionLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-8">
        <div className="w-16 h-16 border-8 border-slate-200 border-t-blue-600 rounded-full animate-spin" />
        <p className="text-sm font-black text-slate-800 uppercase tracking-widest animate-pulse">
          Calculating Pathogenicity...
        </p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-300 gap-6">
        <Dna className="w-24 h-24 stroke-[1]" />
        <p className="text-sm font-black text-slate-400 uppercase tracking-widest">Awaiting Input Parameters</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-[2rem] shadow-xl border border-slate-200 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-700">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200">
            <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
              Source
            </th>
            <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
              HGVS Genomic
            </th>
            <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
              Prediction
            </th>
            <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
              Risk Score
            </th>
            <th className="px-8 py-5 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] text-right">
              Details
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {results.map((v, idx) => {
            const row = variantRows[idx]
            return (
              <tr
                key={v.id}
                onClick={() => setSelectedVariant(row)}
                className={`hover:bg-blue-50/50 cursor-pointer transition-all group ${selectedVariant?.variant_id === v.id ? 'bg-blue-50' : ''}`}
              >
                <td className="px-8 py-5">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border ${v.status === 'New' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'}`}
                  >
                    {v.status}
                  </span>
                </td>
                <td className="px-8 py-5 font-mono text-xs font-bold text-slate-500">{v.hgvs_genomic_38}</td>
                <td className="px-8 py-5">
                  <span
                    className={`px-3 py-1 rounded-full text-[10px] font-black uppercase border tracking-tight ${
                      v.pathogenicity.includes('Pathogenic')
                        ? 'bg-red-50 text-red-700 border-red-100'
                        : v.pathogenicity.includes('Benign')
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                          : 'bg-amber-50 text-amber-700 border-amber-100'
                    }`}
                  >
                    {v.pathogenicity}
                  </span>
                </td>
                <td className="px-8 py-5">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-1000 ${v.score > 0.7 ? 'bg-red-500' : v.score > 0.4 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                        style={{ width: `${v.score * 100}%` }}
                      />
                    </div>
                    <span className="text-xs font-black text-slate-800">{(v.score * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-8 py-5 text-right">
                  <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-blue-600 transition-colors inline" />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

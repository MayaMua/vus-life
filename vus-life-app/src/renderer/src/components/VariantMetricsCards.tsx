/**
 * Variant metrics cards: total count, pathogenicity distribution, consequence distribution.
 * Scrollable lists at half height for compact display.
 */

import React from 'react'
import { BarChart3 } from 'lucide-react'

export interface VariantMetricsSummary {
  total: number
  pathogenicity: Record<string, number>
  consequence: Record<string, number>
}

interface VariantMetricsCardsProps {
  summary: VariantMetricsSummary
  className?: string
}

export const VariantMetricsCards: React.FC<VariantMetricsCardsProps> = ({ summary, className = '' }) => {
  const { total, pathogenicity, consequence } = summary

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-3 gap-4 min-w-[700px] ${className}`}>
      {/* Total Variants */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm min-w-0">
        <div className="flex items-center gap-3 mb-2">
          <div className="bg-blue-50 p-2 rounded-xl">
            <BarChart3 className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Total Variants</p>
            <p className="text-2xl font-black text-slate-900">{total.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Pathogenicity Distribution — scroll area half height (max-h-24 = 96px) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm min-w-0 flex flex-col">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 shrink-0">Pathogenicity</p>
        <div className="scroll-area-stable space-y-2 max-h-24 overscroll-contain">
          {Object.entries(pathogenicity)
            .sort(([, a], [, b]) => b - a)
            .map(([key, count]) => (
              <div key={key} className="flex items-center justify-between gap-2 shrink-0">
                <span className="text-xs font-bold text-slate-700 capitalize truncate">{key.replace(/_/g, ' ')}</span>
                <span className="text-xs font-black text-slate-900 shrink-0">{count.toLocaleString()}</span>
              </div>
            ))}
        </div>
      </div>

      {/* Consequence Distribution — scroll area half height (max-h-24 = 96px) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm min-w-0 flex flex-col">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 shrink-0">Consequence</p>
        <div className="scroll-area-stable space-y-2 max-h-24 overscroll-contain">
          {Object.entries(consequence)
            .sort(([, a], [, b]) => b - a)
            .map(([key, count]) => (
              <div key={key} className="flex items-center justify-between gap-2 shrink-0">
                <span className="text-xs font-bold text-slate-700 capitalize truncate">{key.replace(/_/g, ' ')}</span>
                <span className="text-xs font-black text-slate-900 shrink-0">{count.toLocaleString()}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}

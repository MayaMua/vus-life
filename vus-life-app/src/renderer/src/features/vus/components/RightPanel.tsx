/**
 * Right panel: summary cards (Total / New / Existing) and combined variants table.
 * Row click opens VariantDetailSheet.
 */

import React from 'react'
import { useVusStore } from '../stores/useVusStore'
import { VariantDetailSheet } from './VariantDetailSheet'
import type { VariantRow } from '../types'

function SummaryCards({
  total,
  existing,
  newCount,
}: {
  total: number
  existing: number
  newCount: number
}) {
  return (
    <div className="stats stats-vertical sm:stats-horizontal shadow-md w-full bg-base-100 border border-base-200">
      <div className="stat py-4 px-5">
        <div className="stat-title text-base-content/70">Total Variants</div>
        <div className="stat-value text-2xl text-primary">{total}</div>
      </div>
      <div className="stat py-4 px-5">
        <div className="stat-title text-base-content/70">New</div>
        <div className="stat-value text-2xl text-success">{newCount}</div>
      </div>
      <div className="stat py-4 px-5">
        <div className="stat-title text-base-content/70">Existing</div>
        <div className="stat-value text-2xl">{existing}</div>
      </div>
    </div>
  )
}

export const RightPanel: React.FC = () => {
  const variantRows = useVusStore((s) => s.variantRows)
  const predictionResults = useVusStore((s) => s.predictionResults)
  const resultsError = useVusStore((s) => s.resultsError)
  const selectedVariant = useVusStore((s) => s.selectedVariant)
  const setSelectedVariant = useVusStore((s) => s.setSelectedVariant)

  const total = predictionResults?.variants_count ?? 0
  const existingCount = predictionResults?.existing_variants?.length ?? 0
  const newCount = total - existingCount - (predictionResults?.failed?.results_count ?? 0)
  const hasResults = variantRows.length > 0

  return (
    <div className="flex-1 flex flex-col min-w-0 p-5 gap-5">
      {resultsError && (
        <div className="alert alert-error text-sm shadow-md">
          <span>{resultsError}</span>
        </div>
      )}

      {hasResults && (
        <SummaryCards total={total} existing={existingCount} newCount={Math.max(0, newCount)} />
      )}

      <div className="card bg-base-100 shadow-md border border-base-200 flex-1 min-h-0 flex flex-col">
        <div className="card-body gap-3 flex-1 min-h-0 overflow-hidden">
          <h4 className="card-title text-base font-semibold">Variants</h4>
          {hasResults ? (
            <div className="overflow-auto flex-1 border border-base-300 rounded-xl">
              <table className="table table-zebra table-pin-rows table-pin-cols text-sm">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Variant ID</th>
                    <th>HGVS</th>
                    <th>Consequence</th>
                    <th>Pathogenicity</th>
                    <th>Prediction Score</th>
                  </tr>
                </thead>
                <tbody>
                  {variantRows.map((row: VariantRow) => (
                    <tr
                      key={row.variant_id}
                      className="cursor-pointer hover:bg-base-200"
                      onClick={() => setSelectedVariant(row)}
                    >
                      <td>
                        <span
                          className={`badge badge-sm ${
                            row.status === 'existing' ? 'badge-ghost' : 'badge-success'
                          }`}
                        >
                          {row.status === 'existing' ? 'Existing' : 'New'}
                        </span>
                      </td>
                      <td className="font-mono text-xs">{row.variant_id}</td>
                      <td className="font-mono text-xs max-w-48 truncate" title={row.hgvs_genomic_38}>
                        {row.hgvs_genomic_38}
                      </td>
                      <td>{row.most_severe_consequence}</td>
                      <td>{row.pathogenicity_original ?? '—'}</td>
                      <td>{row.prediction_score ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-base-300 bg-base-200/30 py-12 px-6">
              <p className="text-base-content/60 text-sm text-center max-w-xs">
                Run a prediction to see variants here.
              </p>
              <p className="text-base-content/50 text-xs text-center">
                Configure gene & model, enter HGVS variants, then click Run Prediction.
              </p>
            </div>
          )}
        </div>
      </div>

      <VariantDetailSheet
        variant={selectedVariant}
        onClose={() => setSelectedVariant(null)}
      />
    </div>
  )
}

/**
 * Build combined table rows from prediction API response (existing + new) with status.
 */

import type { PredictionResultsResponse, VariantRow, VariantMetadata } from '../types'

export function buildVariantRows(res: PredictionResultsResponse): VariantRow[] {
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
        const predResult = (modelData as Record<string, unknown>).prediction_result as Record<
          string,
          { confidence_score?: string; pred_result?: string }
        > | undefined
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

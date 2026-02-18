/**
 * Mock API for get_prediction_results. Simulates delay and returns
 * a response shape aligned with the Python backend.
 */

import type { VusConfig, PredictionResultPayload, PredictionResultsResponse } from '../types'

const MOCK_DELAY_MS = 1500

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Mock config (genes, annotation methods, embedding models). */
export async function fetchMockConfig(): Promise<VusConfig> {
  await delay(400)
  return {
    gene_names: ['ATM', 'BRCA1', 'BRCA2', 'USH2A'],
    annotation_methods: ['vep'],
    embedding_models: ['all-mpnet-base-v2', 'e5-small-v2'],
  }
}

/** Mock get_prediction_results: timeout + dummy JSON. */
export async function getMockPredictionResults(
  payload: PredictionResultPayload
): Promise<PredictionResultsResponse> {
  await delay(MOCK_DELAY_MS)

  const variants = payload.variants.slice(0, 20)
  const existingCount = Math.min(2, Math.floor(variants.length / 2))
  const existing_variants = variants.slice(0, existingCount).map((v) => {
    const id = [v.chromosome, v.position, v.ref_allele, v.alt_allele].join('_')
    return `variant_${id}`
  })

  const prediction_results: PredictionResultsResponse['prediction_results'] = {}
  const modelNames = payload.embedding_models.length ? payload.embedding_models : ['all-mpnet-base-v2']

  variants.forEach((v, i) => {
    const variantId = `variant_${v.chromosome}_${v.position}_${v.ref_allele}_${v.alt_allele}`
    const isExisting = existing_variants.includes(variantId)
    const metadata = {
      chromosome: v.chromosome,
      position: String(v.position),
      ref_allele: v.ref_allele,
      alt_allele: v.alt_allele,
      gene_symbol: payload.gene_symbol,
      hgvs_genomic_38: v.hgvs_genomic_38 ?? `${v.chromosome}:g.${v.position}${v.ref_allele}>${v.alt_allele}`,
      hgvs_coding: '',
      hgvs_protein: '',
      most_severe_consequence: isExisting ? 'missense_variant' : (i % 2 === 0 ? 'missense_variant' : 'synonymous_variant'),
      pathogenicity_original: isExisting ? (i % 2 === 0 ? 'Pathogenic' : 'Benign') : undefined,
    }

    const modelData: Record<string, unknown> = {}
    modelNames.forEach((name) => {
      modelData[name] = {
        prediction_result: {
          '1': { confidence_score: '0.82', pred_result: 'Likely pathogenic' },
          '5': { confidence_score: '0.78', pred_result: 'Uncertain significance' },
        },
        nearest_training_variants: [
          { variant_id: 'train_1', pathogenicity: 'Pathogenic' },
          { variant_id: 'train_2', pathogenicity: 'Benign' },
        ],
      }
    })

    prediction_results[variantId] = {
      metadata,
      ...modelData,
    } as PredictionResultsResponse['prediction_results'][string]
  })

  return {
    variants_count: variants.length,
    existing_variants,
    model_name: modelNames,
    annotation_method: payload.annotation_method,
    failed: { results_count: 0 },
    prediction_results,
  }
}

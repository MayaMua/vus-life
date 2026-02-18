/**
 * VUS feature types – variant metadata, config, and API response shapes.
 */

export interface VariantMetadata {
  variant_id?: string
  chromosome?: string
  position?: string
  ref_allele?: string
  alt_allele?: string
  gene_symbol?: string
  hgvs_coding?: string
  hgvs_genomic_38?: string
  hgvs_protein?: string
  most_severe_consequence?: string
  pathogenicity_original?: string
  [key: string]: unknown
}

/** Single variant row for the combined table (existing + new). */
export interface VariantRow {
  variant_id: string
  hgvs_genomic_38: string
  most_severe_consequence: string
  pathogenicity_original?: string
  /** Prediction score for new variants (e.g. confidence or pred result). */
  prediction_score?: string
  /** 'existing' | 'new' */
  status: 'existing' | 'new'
  /** Full metadata for detail sheet. */
  metadata?: VariantMetadata
}

export interface VusConfig {
  gene_names: string[]
  annotation_methods: string[]
  embedding_models: string[]
}

export interface PredictionResultPayload {
  gene_symbol: string
  variants: Array<{ chromosome: string; position: number; ref_allele: string; alt_allele: string; hgvs_genomic_38?: string }>
  annotation_method: string
  embedding_models: string[]
  same_severe_consequence: boolean
}

/** API response shape aligned with Python get_prediction_results. */
export interface PredictionResultsResponse {
  variants_count: number
  existing_variants: string[]
  model_name: string[]
  annotation_method?: string
  failed?: { results_count: number }
  prediction_results: Record<
    string,
    {
      metadata: VariantMetadata
      [modelName: string]: {
        error?: string
        prediction_result?: Record<string, { confidence_score?: string; pred_result?: string }>
        nearest_training_variants?: Array<{ variant_id: string; pathogenicity?: string }>
      } | VariantMetadata
    }
  >
}

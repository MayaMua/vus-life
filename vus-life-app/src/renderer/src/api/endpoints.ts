/**
 * API endpoint definitions.
 */

import { apiClient } from './client'
import type { SettingsResponse, SettingsUpdateRequest } from '../types/settings'

/**
 * Get current application settings.
 */
export const getSettings = async (): Promise<SettingsResponse> => {
  const response = await apiClient.get<SettingsResponse>('/api/settings/')
  return response.data
}

/**
 * Update application settings (partial update supported).
 */
export const updateSettings = async (
  updates: SettingsUpdateRequest
): Promise<SettingsResponse> => {
  const response = await apiClient.patch<SettingsResponse>('/api/settings/', updates)
  return response.data
}

export interface ProviderVerifyRequest {
  provider_id: string
  base_url: string
  api_key: string
}

export interface ProviderVerifyResponse {
  success: boolean
  message: string
  models: string[]
}

/**
 * Verify provider connection and fetch available models.
 */
export const verifyProvider = async (
  payload: ProviderVerifyRequest
): Promise<ProviderVerifyResponse> => {
  const response = await apiClient.post<ProviderVerifyResponse>('/api/settings/verify-provider', payload)
  return response.data
}

/** Response from GET /api/vus/verify (backend validates VUS API URL from config). */
export interface VusVerifyResponse {
  status: string
  service?: string
}

/**
 * Verify connection to the VUS API.
 * Backend reads URL from config and calls that URL's /api/health.
 */
export const verifyVusConnection = async (): Promise<VusVerifyResponse> => {
  const response = await apiClient.get<VusVerifyResponse>('/api/vus/verify')
  return response.data
}

/** Response from GET /api/vus/config (network-first, then local cache). */
export interface VusConfigResponse {
  gene_names: string[]
  embedding_models: string[]
  annotation_methods: string[]
  from_cache?: boolean
}

/**
 * Get VUS dashboard config (genes, models, annotation methods).
 * Backend fetches from AWS when possible and persists to config; returns local on failure.
 */
export const getVusConfig = async (): Promise<VusConfigResponse> => {
  const response = await apiClient.get<VusConfigResponse>('/api/vus/config')
  return response.data
}

/** Response from GET /api/vus/metadata/{gene_symbol} */
export interface MetadataResponse {
  status: 'success'
  summary: {
    total: number
    pathogenicity: Record<string, number>
    consequence: Record<string, number>
  }
  preview_data: Array<{
    variant_id: string
    variant_hash?: string
    vcf_string?: string
    hgvs_genomic_38: string
    hgvs_coding?: string
    hgvs_protein?: string
    chromosome: string
    position: number
    ref_allele: string
    alt_allele: string
    gene_symbol: string
    most_severe_consequence: string
    pathogenicity_original: string
  }>
}

/**
 * Get metadata summary and preview for a gene.
 * Returns 404 if metadata not found locally.
 */
export const getMetadata = async (geneSymbol: string): Promise<MetadataResponse> => {
  try {
    const response = await apiClient.get<MetadataResponse>(`/api/vus/metadata/${encodeURIComponent(geneSymbol)}`)
    return response.data
  } catch (error: unknown) {
    // Preserve axios error structure before interceptor transforms it
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as { response?: { status?: number }; message?: string }
      if (axiosError.response?.status === 404) {
        const metadataError = new Error('Metadata not found locally') as Error & { status?: number }
        metadataError.status = 404
        throw metadataError
      }
    }
    throw error
  }
}

/** Response from POST /api/vus/metadata/download */
export interface MetadataDownloadResponse {
  status: 'success'
  message: string
  path: string
}

/**
 * Download metadata for a gene from AWS and save locally.
 */
export const downloadMetadata = async (geneSymbol: string): Promise<MetadataDownloadResponse> => {
  const response = await apiClient.post<MetadataDownloadResponse>('/api/vus/metadata/download', {
    gene_symbol: geneSymbol,
  })
  return response.data
}

// ---------------------------------------------------------------------------
// Prediction
// ---------------------------------------------------------------------------

import type { PredictionResultsResponse } from '../features/vus/types'

/** Request body for POST /api/vus/predict */
export interface PredictPayload {
  gene_symbol: string
  /** Raw HGVS g. strings – backend converts to VCF via hgvs_g_to_vcf */
  hgvs_genomic_38: string[]
  annotation_method: string[]
  embedding_models: string[]
  same_severe_consequence: boolean
}

/**
 * Run VUS embedding prediction.
 *
 * Sends raw HGVS genomic strings to the backend, which converts them to VCF,
 * calls the VUS Life AWS API, and returns the full prediction results.
 */
export const getPredictionResults = async (
  payload: PredictPayload,
): Promise<PredictionResultsResponse> => {
  const response = await apiClient.post<PredictionResultsResponse>('/api/vus/predict', payload)
  return response.data
}


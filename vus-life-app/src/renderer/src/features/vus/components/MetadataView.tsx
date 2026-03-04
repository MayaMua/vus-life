/**
 * Metadata view: Empty state (404) or data display (success).
 * Shows metrics and preview table when metadata is loaded.
 */

import React, { useState } from 'react'
import { Dna, FileX, Download, Loader2, ChevronDown, ChevronRight, Clock, Beaker } from 'lucide-react'
import { useMetadata, useDownloadMetadata } from '../useMetadata'
import { VariantMetricsCards } from '../../../components/VariantMetricsCards'
import type { MetadataResponse } from '../../../api/endpoints'

interface MetadataViewProps {
  geneSymbol: string | null
}

/**
 * Empty state component shown when metadata is not found (404).
 */
const EmptyState: React.FC<{ geneSymbol: string; onDownload: () => void; isDownloading: boolean }> = ({
  geneSymbol,
  onDownload,
  isDownloading,
}) => {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-8 p-8">
      <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200">
        <FileX className="w-24 h-24 text-slate-300 stroke-[1]" />
      </div>
      <div className="text-center space-y-3">
        <p className="text-sm font-black text-slate-800 uppercase tracking-widest">
          No training variants about {geneSymbol} found.
        </p>
        <p className="text-xs text-slate-500 font-medium max-w-md">
          Download metadata from the AWS API to view variant statistics and preview data.
        </p>
      </div>
      <button
        type="button"
        onClick={onDownload}
        disabled={isDownloading}
        className="px-8 py-4 bg-slate-900 text-white font-black rounded-2xl shadow-xl hover:bg-black transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3"
      >
        {isDownloading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Downloading...</span>
          </>
        ) : (
          <>
            <Download className="w-5 h-5" />
            <span>Download Metadata</span>
          </>
        )}
      </button>
    </div>
  )
}

// --- Mock Data for History (Temporarily placed here) ---
const MOCK_HISTORY = [
  {
    id: 'req-1',
    time: '2 hours ago',
    models: ['all-mpnet-base-v2', 'gemini-embedding'],
    annotation: 'VEP',
    variantCount: 15,
  },
  {
    id: 'req-2',
    time: 'Yesterday',
    models: ['MedEmbed-large-v0.1'],
    annotation: 'VEP',
    variantCount: 3,
  },
  {
    id: 'req-3',
    time: 'Mar 01, 2024',
    models: ['all-mpnet-base-v2'],
    annotation: 'SnpEff',
    variantCount: 124,
  }
]

/**
 * Data table component showing preview variants.
 */
const PreviewTable: React.FC<{ previewData: MetadataResponse['preview_data']; isExpanded: boolean; onToggle: () => void }> = ({ previewData, isExpanded, onToggle }) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden min-w-[700px]">
      <div 
        className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2 cursor-pointer hover:bg-slate-100 transition-colors"
        onClick={onToggle}
      >
        {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest select-none">
          Preview Data (First {previewData.length} variants)
        </p>
      </div>
      
      {isExpanded && (
        <div className="overflow-x-auto min-w-0 animate-in fade-in slide-in-from-top-2 duration-300">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {/* <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Variant ID</th> */}
              <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">VCF String</th>
              <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">HGVS Genomic</th>
              <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">HGVS Coding</th>
              <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">HGVS Protein</th>
              <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Consequence</th>
              <th className="px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Pathogenicity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {previewData.map((variant) => (
              <tr key={variant.variant_id} className="hover:bg-blue-50/50 transition-colors">
                {/* <td className="px-6 py-3 font-mono text-xs font-bold text-slate-700">{variant.variant_id}</td> */}
                <td className="px-6 py-3 font-mono text-xs font-medium text-slate-600">{variant.vcf_string || '—'}</td>
                <td className="px-6 py-3 font-mono text-xs font-medium text-slate-600">{variant.hgvs_genomic_38 || '—'}</td>
                <td className="px-6 py-3 font-mono text-xs font-medium text-slate-600">{variant.hgvs_coding || '—'}</td>
                <td className="px-6 py-3 font-mono text-xs font-medium text-slate-600">{variant.hgvs_protein || '—'}</td>
                <td className="px-6 py-3">
                  <span className="px-2 py-1 rounded-lg text-[10px] font-bold text-slate-700 bg-slate-100 capitalize">
                    {variant.most_severe_consequence?.replace(/_/g, ' ') || '—'}
                  </span>
                </td>
                <td className="px-6 py-3">
                  <span
                    className={`px-2 py-1 rounded-lg text-[10px] font-bold uppercase border ${
                      variant.pathogenicity_original?.toLowerCase().includes('pathogenic')
                        ? 'bg-red-50 text-red-700 border-red-100'
                        : variant.pathogenicity_original?.toLowerCase().includes('benign')
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                          : 'bg-amber-50 text-amber-700 border-amber-100'
                    }`}
                  >
                    {variant.pathogenicity_original?.replace(/_/g, ' ') || '—'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}
    </div>
  )
}

/**
 * Main metadata view component.
 * Shows empty state on 404, or metrics + table on success.
 */
export const MetadataView: React.FC<MetadataViewProps> = ({ geneSymbol }) => {
  const { data, isLoading, error } = useMetadata(geneSymbol)
  const downloadMutation = useDownloadMetadata()
  
  // UI State for expandable sections
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true)
  const [isPreviewExpanded, setIsPreviewExpanded] = useState(true)

  // Loading state
  if (isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-8">
        <div className="w-16 h-16 border-8 border-slate-200 border-t-blue-600 rounded-full animate-spin" />
        <p className="text-sm font-black text-slate-800 uppercase tracking-widest animate-pulse">Loading Metadata...</p>
      </div>
    )
  }

  // Error state (404 or other) - show empty state
  if (error || !data) {
    // Check if it's a 404 error (metadata not found)
    const is404 = error && 'status' in error && error.status === 404

    if (is404 && geneSymbol) {
      return (
        <EmptyState
          geneSymbol={geneSymbol}
          onDownload={() => downloadMutation.mutate(geneSymbol)}
          isDownloading={downloadMutation.isPending}
        />
      )
    }
    // Other errors - show generic empty state
    return (
      <div className="h-full flex flex-col items-center justify-center gap-8 p-8">
        <div className="bg-slate-50 p-8 rounded-3xl border border-slate-200">
          <Dna className="w-24 h-24 text-slate-300 stroke-1" />
        </div>
        <p className="text-sm font-black text-slate-800 uppercase tracking-widest">
          {geneSymbol ? `Unable to load metadata for ${geneSymbol}` : 'Select a gene to view metadata'}
        </p>
      </div>
    )
  }

  // Success state - show metrics and table
  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 w-full max-w-full pb-12">
      <VariantMetricsCards summary={data.summary} className="mb-6" />
      
      {/* 1. Expandable History Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden min-w-[700px]">
        <div 
          className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between cursor-pointer hover:bg-slate-100 transition-colors"
          onClick={() => setIsHistoryExpanded(!isHistoryExpanded)}
        >
          <div className="flex items-center gap-2">
            {isHistoryExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest select-none">
              Recent Predictions
            </p>
          </div>
          <div className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded-md text-[9px] font-black">
            {MOCK_HISTORY.length} RUNS
          </div>
        </div>
        
        {isHistoryExpanded && (
          <div className="p-6 bg-slate-50/30 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
              {MOCK_HISTORY.map(record => (
                <div 
                  key={record.id}
                  // onClick={() => handleLoadHistory(record)} // TO-DO in the future
                  className="min-w-[280px] p-5 bg-white border border-slate-200 rounded-2xl hover:border-blue-400 hover:shadow-lg transition-all cursor-pointer group flex flex-col gap-3"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      {record.time}
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-100 text-[9px] font-black uppercase rounded-lg tracking-widest">
                      {record.variantCount} VARIANTS
                    </span>
                  </div>
                  
                  <div className="space-y-1.5">
                    <div className="flex items-start gap-2">
                      <Beaker className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
                      <div className="flex flex-wrap gap-1">
                        {record.models.map(m => (
                          <span key={m} className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[9px] font-bold">
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 pl-5">
                      <span className="px-1.5 py-0.5 border border-slate-200 text-slate-500 rounded text-[9px] font-bold">
                        {record.annotation}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 2. Expandable Preview Data Section */}
      <PreviewTable 
        previewData={data.preview_data} 
        isExpanded={isPreviewExpanded}
        onToggle={() => setIsPreviewExpanded(!isPreviewExpanded)}
      />
    </div>
  )
}

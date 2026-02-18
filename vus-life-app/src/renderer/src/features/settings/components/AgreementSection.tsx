/**
 * Data Usage Agreement static content (scratch copy).
 */

import React from 'react'
import { ShieldCheck } from 'lucide-react'

export const AgreementSection: React.FC = () => {
  return (
    <>
      <header>
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Data Usage Agreement</h1>
        <p className="text-slate-500 text-sm mt-1 font-medium">
          Review the community and research data policies.
        </p>
      </header>

      <div className="bg-slate-50 border border-slate-100 rounded-2xl p-8 space-y-6">
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 prose prose-sm prose-slate max-w-none">
          <h3 className="font-bold text-slate-900 tracking-tight">1. Data Collection</h3>
          <p className="text-slate-600 leading-relaxed">
            The application collects genomic coordinates (chromosome, position, alleles) and prediction
            results for the purpose of maintaining a community cache. No patient-identifying
            information (PII) is ever collected or transmitted.
          </p>

          <h3 className="font-bold text-slate-900 tracking-tight mt-6">2. Community Database</h3>
          <p className="text-slate-600 leading-relaxed">
            Variants processed by users are contributed to a shared research database. This allows all
            users to benefit from previously computed pathogenicity scores, reducing redundant
            computation and server load.
          </p>
        </div>

        <div className="flex items-center justify-between p-5 bg-emerald-50 border border-emerald-100 rounded-2xl shadow-sm shadow-emerald-100/50">
          <div className="flex items-center gap-4">
            <div className="bg-emerald-500 p-2.5 rounded-xl shadow-md shadow-emerald-500/30">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-emerald-900">Agreement Status</p>
              <p className="text-xs text-emerald-600 font-bold uppercase tracking-tight">
                Verified Accepted on 2026/01/20
              </p>
            </div>
          </div>
          <button
            type="button"
            className="px-5 py-2.5 bg-white border border-emerald-200 text-emerald-700 text-xs font-bold rounded-xl hover:bg-emerald-50 transition-all active:scale-95 shadow-sm"
          >
            Review Changes
          </button>
        </div>
      </div>
    </>
  )
}

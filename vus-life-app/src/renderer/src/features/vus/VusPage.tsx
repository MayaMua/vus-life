/**
 * VUS Prediction page: left config sidebar, right results + variant detail sheet.
 * Agreement modal inline; API status from store (synced with Settings VUS verify).
 */

import React, { useState, useEffect } from 'react'
import { Search, Database, ShieldCheck, CheckCircle2 } from 'lucide-react'
import { useVusStore } from './stores/useVusStore'
import { VusSidebar } from './components/VusSidebar'
import { VusResultsTable } from './components/VusResultsTable'
import { VariantDetails } from './components/VariantDetails'

export const VusPage: React.FC = () => {
  const fetchConfig = useVusStore((s) => s.fetchConfig)
  const showAgreement = useVusStore((s) => s.showAgreement)
  const setShowAgreement = useVusStore((s) => s.setShowAgreement)
  const acceptAgreement = useVusStore((s) => s.acceptAgreement)
  const isApiConnected = useVusStore((s) => s.isApiConnected)
  const agreementAccepted = useVusStore((s) => s.agreementAccepted)
  const [dontShowAgain, setDontShowAgain] = useState(true)

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  useEffect(() => {
    if (!agreementAccepted) setShowAgreement(true)
  }, [agreementAccepted, setShowAgreement])

  return (
    <div className="flex h-full bg-[#f8fafc] text-slate-900 overflow-hidden select-none font-sans">
      {/* AGREEMENT MODAL */}
      {showAgreement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-300">
          <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full flex flex-col overflow-hidden border border-slate-200 animate-in zoom-in-95 duration-300">
            <div className="p-8 border-b border-slate-100 flex items-center gap-4">
              <div className="bg-blue-50 p-3 rounded-2xl">
                <ShieldCheck className="w-8 h-8 text-blue-600" />
              </div>
              <h2 className="text-2xl font-black text-slate-800 tracking-tight">Data Usage Agreement</h2>
            </div>
            <div className="p-8 text-sm leading-relaxed text-slate-600 space-y-4">
              <p className="font-bold text-slate-800">Community Knowledge Access</p>
              <p>
                To accelerate clinical discovery, Variant Insight caches processed variant coordinates in a secure,
                anonymized community database.
              </p>
              <ul className="space-y-2">
                {[
                  'Variants are shared for research speed.',
                  'No patient identifiers are stored.',
                  'Predictions are for research use only.',
                ].map((t, i) => (
                  <li key={i} className="flex gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
              <label className="flex items-center gap-3 pt-6 cursor-pointer">
                <input
                  type="checkbox"
                  checked={dontShowAgain}
                  onChange={(e) => setDontShowAgain(e.target.checked)}
                  className="w-5 h-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-bold text-slate-600">Don't show this again</span>
              </label>
            </div>
            <div className="p-8 bg-slate-50 border-t border-slate-100 flex justify-end">
              <button
                type="button"
                onClick={() => acceptAgreement(dontShowAgain)}
                className="px-8 py-3 bg-slate-900 text-white font-bold rounded-2xl hover:bg-black transition-all active:scale-95"
              >
                I Agree
              </button>
            </div>
          </div>
        </div>
      )}

      {/* LEFT PANEL: CONFIGURATION */}
      <VusSidebar />

      {/* RIGHT PANEL: RESULTS */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-3">
            <div className="bg-slate-900 p-1.5 rounded-lg">
              <Database className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-black text-slate-900 uppercase tracking-tighter">
              Variant Explorer
            </span>
          </div>
          <div className="flex items-center gap-4">
            {isApiConnected && (
              <div className="flex items-center gap-2 px-4 py-1.5 bg-emerald-50 text-emerald-600 rounded-full border border-emerald-100 text-[10px] font-black uppercase tracking-widest">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                Live Sync
              </div>
            )}
            <button
              type="button"
              className="p-2.5 hover:bg-slate-100 rounded-xl text-slate-400"
              aria-label="Search"
            >
              <Search className="w-5 h-5" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8 bg-slate-50/30 scrollbar-hide">
          <VusResultsTable />
        </main>

        <VariantDetails />
      </div>
    </div>
  )
}

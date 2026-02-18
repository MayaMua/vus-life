/**
 * About & Feedback static content.
 */

import React from 'react'
import { BrainCircuit } from 'lucide-react'

export const AboutSection: React.FC = () => {
  return (
    <>
      <div className="mx-auto w-28 h-28 bg-slate-50 rounded-[2rem] flex items-center justify-center shadow-inner relative group border border-slate-100">
        <BrainCircuit className="w-14 h-14 text-blue-600 group-hover:scale-110 transition-transform duration-500" />
      </div>

      <div className="space-y-2">
        <h1 className="text-4xl font-black text-slate-900 tracking-tighter">Variant Insight</h1>
        <p className="text-slate-400 font-bold tracking-[0.2em] uppercase text-xs">
          Professional Genomic Assistant
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6 max-w-sm mx-auto">
        <div className="p-5 bg-slate-50 border border-slate-100 rounded-3xl shadow-sm">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
            Core Version
          </p>
          <p className="text-lg font-black text-slate-800">v1.2.4</p>
        </div>
        <div className="p-5 bg-slate-50 border border-slate-100 rounded-3xl shadow-sm">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">
            Model Version
          </p>
          <p className="text-lg font-black text-slate-800">Embed-3.0</p>
        </div>
      </div>

      <div className="space-y-6 pt-6">
        <div className="flex items-center justify-center gap-4">
          <button
            type="button"
            className="text-xs text-blue-600 font-bold hover:underline"
          >
            Support
          </button>
          <span className="w-1 h-1 bg-slate-300 rounded-full" />
          <button
            type="button"
            className="text-xs text-blue-600 font-bold hover:underline"
          >
            Feature Request
          </button>
          <span className="w-1 h-1 bg-slate-300 rounded-full" />
          <button
            type="button"
            className="text-xs text-blue-600 font-bold hover:underline"
          >
            Privacy
          </button>
        </div>
        <p className="text-xs text-slate-400 font-medium">
          © 2026 Variant Insight Labs. Built for Clinical Research.
        </p>
      </div>
    </>
  )
}

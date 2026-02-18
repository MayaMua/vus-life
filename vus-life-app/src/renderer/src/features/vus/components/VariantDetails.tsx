/**
 * Slide-over variant detail: score gauge, info grid, AI chat.
 * selectedVariant is VariantRow; we derive display fields for gauge and askVariantAgent.
 */

import React, { useState, useEffect, useRef } from 'react'
import { X, PlusCircle, BrainCircuit, Send, Loader2 } from 'lucide-react'
import { useVusStore } from '../stores/useVusStore'
import { ScoreGauge } from '../../../components/ScoreGauge'
import { askVariantAgent } from '../../../services/geminiService'
import type { VariantRow } from '../types'

/** Derive detail display fields from VariantRow. */
function toDetailShape(row: VariantRow): {
  id: string
  score: number
  pathogenicity: string
  gene: string
  ref: string
  alt: string
  position: number
  consequence: string
} {
  const meta = row.metadata ?? {}
  const scoreNum = row.prediction_score != null ? parseFloat(row.prediction_score) : 0
  return {
    id: row.variant_id,
    score: Number.isFinite(scoreNum) ? scoreNum : 0,
    pathogenicity:
      row.prediction_label ?? row.pathogenicity_original ?? row.most_severe_consequence ?? 'Uncertain',
    gene: String(meta.gene_symbol ?? '—'),
    ref: String(meta.ref_allele ?? '—'),
    alt: String(meta.alt_allele ?? '—'),
    position: parseInt(String(meta.position ?? '0'), 10) || 0,
    consequence: row.most_severe_consequence ?? '—',
  }
}

export const VariantDetails: React.FC = () => {
  const selectedVariant = useVusStore((s) => s.selectedVariant)
  const setSelectedVariant = useVusStore((s) => s.setSelectedVariant)

  const [chatInput, setChatInput] = useState('')
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'assistant'; text: string }[]>([])
  const [isChatLoading, setIsChatLoading] = useState(false)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setChatHistory([])
    setChatInput('')
  }, [selectedVariant?.variant_id])

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatHistory, isChatLoading])

  if (!selectedVariant) return null

  const detail = toDetailShape(selectedVariant)

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return

    const userMsg = chatInput
    setChatInput('')
    setChatHistory((prev) => [...prev, { role: 'user', text: userMsg }])
    setIsChatLoading(true)

    const aiResponse = await askVariantAgent(
      {
        id: detail.id,
        score: detail.score,
        pathogenicity: detail.pathogenicity,
        gene: detail.gene,
        ref: detail.ref,
        alt: detail.alt,
        position: detail.position,
        consequence: detail.consequence,
        hgvs_genomic_38: selectedVariant.hgvs_genomic_38,
      },
      userMsg
    )

    setChatHistory((prev) => [...prev, { role: 'assistant', text: aiResponse }])
    setIsChatLoading(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="absolute inset-y-0 right-0 w-[500px] bg-white border-l border-slate-200 shadow-2xl z-30 flex flex-col animate-in slide-in-from-right duration-500">
      <div className="p-8 border-b border-slate-100 flex items-center justify-between shrink-0 bg-slate-50/50">
        <div className="flex items-center gap-4">
          <div className="bg-slate-900 p-3 rounded-2xl">
            <PlusCircle className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-xl font-black text-slate-900 tracking-tight">Variant Profile</h2>
        </div>
        <button
          type="button"
          onClick={() => setSelectedVariant(null)}
          className="p-2.5 hover:bg-slate-200 rounded-xl text-slate-400 hover:text-slate-900 transition-colors"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-8 space-y-10 scrollbar-hide">
        <section className="bg-slate-900 rounded-[2.5rem] p-10 text-center shadow-2xl relative overflow-hidden">
          <ScoreGauge score={detail.score} />
          <p className="text-2xl font-black text-white tracking-tight mt-6 uppercase">
            {detail.pathogenicity}
          </p>
          <p className="text-[10px] text-slate-500 font-black tracking-widest mt-2 uppercase">
            Synthesized Confidence
          </p>
        </section>

        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Gene', value: detail.gene },
            { label: 'Ref/Alt', value: `${detail.ref} > ${detail.alt}` },
            { label: 'Position', value: detail.position.toLocaleString() },
            { label: 'Consequence', value: detail.consequence },
          ].map((item, i) => (
            <div key={i} className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">
                {item.label}
              </span>
              <span className="text-sm font-black text-slate-800 break-all">{item.value}</span>
            </div>
          ))}
        </div>

        <section className="border-t border-slate-100 pt-10 space-y-6 flex flex-col h-[400px]">
          <h3 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em] flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-purple-600" />
            AI Interpretations
          </h3>

          <div
            ref={chatContainerRef}
            className="bg-slate-50 rounded-3xl p-6 flex-1 border border-slate-100 overflow-y-auto"
          >
            {chatHistory.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-2">
                <p className="text-xs font-bold italic text-center">Start a clinical inquiry below...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {chatHistory.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div
                      className={`max-w-[85%] px-5 py-3 rounded-2xl text-[13px] font-medium leading-relaxed ${
                        m.role === 'user'
                          ? 'bg-slate-900 text-white'
                          : 'bg-white border border-slate-200 text-slate-700 shadow-sm'
                      }`}
                    >
                      {m.text}
                    </div>
                  </div>
                ))}
                {isChatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-slate-200 px-4 py-3 rounded-2xl shadow-sm">
                      <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="relative shrink-0">
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask clinical impact questions..."
              className="w-full bg-white border border-slate-200 rounded-2xl py-4 pl-6 pr-14 text-sm font-medium outline-none focus:ring-4 focus:ring-purple-500/10 shadow-lg"
            />
            <button
              type="button"
              onClick={handleSendMessage}
              disabled={!chatInput.trim() || isChatLoading}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 bg-purple-600 text-white rounded-xl shadow-md hover:bg-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}

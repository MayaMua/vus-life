/**
 * Modal for VUS API connection verification result (success or error).
 * Same overlay/card design as scratch; receives type, message, onClose.
 */

import React from 'react'
import { Check, X } from 'lucide-react'
import type { ConnectionStatusType } from '../../../store/useVusApiStore'

interface ConnectionStatusModalProps {
  visible: boolean
  type: ConnectionStatusType
  message: string
  onClose: () => void
}

export const ConnectionStatusModal: React.FC<ConnectionStatusModalProps> = ({
  visible,
  type,
  message,
  onClose,
}) => {
  if (!visible || !type) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/40 backdrop-blur-[4px] p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl shadow-[0_32px_64px_-16px_rgba(0,0,0,0.2)] border border-slate-200 p-8 max-w-sm w-full text-center space-y-6 animate-in zoom-in-95 duration-200">
        <div
          className={`mx-auto w-20 h-20 rounded-full flex items-center justify-center ${
            type === 'success' ? 'bg-emerald-50 text-emerald-500 shadow-inner' : 'bg-red-50 text-red-500 shadow-inner'
          }`}
        >
          {type === 'success' ? (
            <Check className="w-10 h-10 stroke-[3]" />
          ) : (
            <X className="w-10 h-10 stroke-[3]" />
          )}
        </div>
        <div>
          <h3 className="text-xl font-bold tracking-tight text-slate-900">
            {type === 'success' ? 'Connection Verified' : 'Connection Failed'}
          </h3>
          <p className="text-sm text-slate-500 mt-2 leading-relaxed px-4">{message}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="w-full py-3.5 bg-slate-900 text-white rounded-2xl font-bold hover:bg-slate-800 transition-all active:scale-[0.98] shadow-lg shadow-slate-200"
        >
          Close
        </button>
      </div>
    </div>
  )
}

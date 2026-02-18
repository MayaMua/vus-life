/**
 * Global Data Usage Agreement modal. Shown on first app launch.
 * Subscribes to useAppStore; when user confirms with "Don't show again" checked, persists via store.
 */

import React, { useState, useEffect } from 'react'
import { useAppStore } from '../store/useAppStore'
import { DATA_USAGE_AGREEMENT_MD } from '../constants/agreementContent'

export const GlobalAgreementDialog: React.FC = () => {
  const { hasAcceptedAgreement, acceptAgreement } = useAppStore()
  const [isOpen, setIsOpen] = useState(false)
  const [dontShowAgain, setDontShowAgain] = useState(true)

  // Only show dialog when store says user has not accepted yet
  useEffect(() => {
    if (!hasAcceptedAgreement) {
      setIsOpen(true)
    }
  }, [hasAcceptedAgreement])

  const handleConfirm = () => {
    if (dontShowAgain) {
      acceptAgreement()
    }
    setIsOpen(false)
  }

  if (!isOpen) return null

  return (
    <dialog className="modal modal-open" open>
      <div className="modal-box max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <h3 className="font-bold text-lg mb-2">Data Usage Agreement</h3>
        <div className="overflow-y-auto flex-1 pr-2 prose prose-sm max-w-none">
          <pre className="whitespace-pre-wrap font-sans text-base bg-base-200 p-4 rounded-lg">
            {DATA_USAGE_AGREEMENT_MD}
          </pre>
        </div>
        <label className="label cursor-pointer justify-start gap-2 mt-2">
          <input
            type="checkbox"
            className="checkbox checkbox-sm"
            checked={dontShowAgain}
            onChange={(e) => setDontShowAgain(e.target.checked)}
          />
          <span className="label-text">Don&apos;t show this again</span>
        </label>
        <div className="modal-action mt-4">
          <button type="button" className="btn btn-primary" onClick={handleConfirm}>
            I Agree
          </button>
        </div>
      </div>
      <div className="modal-backdrop bg-black/60" aria-hidden />
    </dialog>
  )
}

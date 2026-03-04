/**
 * Global Data Usage Agreement modal. Shown on first app launch.
 * Reads and updates agreement state via FastAPI settings (GET/PATCH /api/settings).
 */

import React, { useState, useEffect } from 'react'
import { useSettings, useUpdateSettings } from '../features/settings/useSettings'
import { DATA_USAGE_AGREEMENT_MD } from '../constants/agreementContent'

export const GlobalAgreementDialog: React.FC = () => {
  const { data: settings, isLoading } = useSettings()
  const updateSettingsMutation = useUpdateSettings()
  const [isOpen, setIsOpen] = useState(false)
  const [dontShowAgain, setDontShowAgain] = useState(true)

  const hasAcceptedAgreement = settings?.general_settings?.has_accepted_agreement ?? false

  // Show dialog when config says user has not accepted yet (after settings loaded)
  useEffect(() => {
    if (!isLoading && !hasAcceptedAgreement) {
      setIsOpen(true)
    }
  }, [isLoading, hasAcceptedAgreement])

  const handleConfirm = async () => {
    if (dontShowAgain) {
      try {
        await updateSettingsMutation.mutateAsync({
          general_settings: { has_accepted_agreement: true },
        })
      } catch {
        // Still close dialog; user can re-accept later
      }
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

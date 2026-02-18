/**
 * Data Usage Agreement content (from DATA_USAGE_AGREEMENT.md).
 * Replace or load from file when the real markdown is available.
 */

export const DATA_USAGE_AGREEMENT_MD = `
# Data Usage Agreement

This application is a **research tool** for variant interpretation and is not intended for direct clinical decision-making.

## Data storage and sharing

- Variant prediction results may be stored locally and, in future versions, shared with the research community to improve variant interpretation.
- By using this tool, you acknowledge that variant data you submit may contribute to a shared resource.

## Your responsibilities

- You have read and understood this agreement.
- You consent to the storage and sharing of variant prediction results as described.
- You understand this is a research tool, not for clinical decision-making.
- You agree to help build a community resource for variant research.

## Consent

By clicking **"I Agree"**, you confirm that you accept these terms and wish to proceed.
`.trim()

/** Alias for use in GlobalAgreementDialog. */
export const AGREEMENT_TEXT = DATA_USAGE_AGREEMENT_MD

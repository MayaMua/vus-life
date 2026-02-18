/**
 * Stub for Gemini-based variant interpretation. Replace with real API when available.
 */

export interface VariantForAgent {
  id: string
  score?: number
  pathogenicity?: string
  gene?: string
  ref?: string
  alt?: string
  position?: number
  consequence?: string
  hgvs_genomic_38?: string
  [key: string]: unknown
}

/**
 * Ask the variant interpretation agent a question. Returns a placeholder response.
 */
export async function askVariantAgent(
  _variant: VariantForAgent,
  userMessage: string
): Promise<string> {
  await new Promise((r) => setTimeout(r, 600))
  return `Based on the variant context and your question: "${userMessage.slice(0, 80)}${userMessage.length > 80 ? '…' : ''}" — This is a placeholder response. Connect the Gemini API in Settings to enable AI interpretations.`
}

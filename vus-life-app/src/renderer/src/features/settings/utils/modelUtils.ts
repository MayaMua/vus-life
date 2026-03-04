/**
 * Utilities for parsing model IDs to extract capabilities and family groups.
 */

export interface ModelCapabilities {
  vision: boolean
  reasoning: boolean
  embedding: boolean
  webSearch: boolean
  toolUse: boolean
  flash: boolean
  free: boolean
}

export function parseModelCapabilities(id: string): ModelCapabilities {
  const lowerId = id.toLowerCase()
  return {
    vision: lowerId.includes('vision') || lowerId.includes('vl') || lowerId.includes('image'),
    reasoning: lowerId.includes('reasoning') || lowerId.includes('r1') || lowerId.includes('o1') || lowerId.includes('o3') || lowerId.includes('think'),
    embedding: lowerId.includes('embed'),
    webSearch: lowerId.includes('online') || lowerId.includes('search') || lowerId.includes('web'),
    toolUse: lowerId.includes('tool') || lowerId.includes('func') || lowerId.includes('pro') || lowerId.includes('flash'), // Assuming pro/flash usually support tools
    flash: lowerId.includes('flash') || lowerId.includes('fast') || lowerId.includes('haiku') || lowerId.includes('mini'),
    free: lowerId.includes('free'),
  }
}

export function parseModelFamily(id: string, provider: string): string {
  const lowerId = id.toLowerCase()
  
  if (provider === 'gemini') {
    if (lowerId.includes('gemini-2.5')) return 'Gemini 2.5'
    if (lowerId.includes('gemini-3')) return 'Gemini 3'
    if (lowerId.includes('gemini-2.0')) return 'Gemini 2.0'
    if (lowerId.includes('gemini-1.5')) return 'Gemini 1.5'
    return 'models'
  }
  
  if (provider === 'openai') {
    if (lowerId.includes('o1')) return 'o1 Series'
    if (lowerId.includes('o3')) return 'o3 Series'
    if (lowerId.includes('gpt-4o')) return 'GPT-4o Series'
    if (lowerId.includes('gpt-4')) return 'GPT-4 Series'
    return 'models'
  }
  
  if (provider === 'deepseek') {
    if (lowerId.includes('r1')) return 'DeepSeek R1'
    if (lowerId.includes('v3')) return 'DeepSeek V3'
    return 'models'
  }
  
  // Default fallback grouping
  const prefix = id.split('-')[0]
  if (prefix && prefix !== id) {
    return prefix.charAt(0).toUpperCase() + prefix.slice(1)
  }
  
  return 'models'
}

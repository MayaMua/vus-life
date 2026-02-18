/**
 * Circular score gauge for variant detail (0–1 score).
 */

import React from 'react'

interface ScoreGaugeProps {
  score: number
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({ score }) => {
  const clamped = Math.max(0, Math.min(1, score))
  const deg = clamped * 360
  const color = clamped > 0.7 ? '#ef4444' : clamped > 0.4 ? '#f59e0b' : '#10b981'

  return (
    <div className="relative w-32 h-32 mx-auto">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-slate-700/30"
        />
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${(deg / 360) * 263.9} 263.9`}
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-black text-white">{(clamped * 100).toFixed(0)}%</span>
      </div>
    </div>
  )
}

export default ScoreGauge

import React from 'react';

export default function ConfidenceScore({ confidence, label = "Confidence" }) {
  if (confidence === undefined || confidence === null) return null;

  const pct = Math.round(confidence <= 1.0 ? confidence * 100 : confidence);

  return (
    <div className="confidence-indicator" title={`${label}: ${pct}%`}>
      <span>{label}: <strong>{pct}%</strong></span>
      <div className="confidence-bar-bg">
        <div
          className="confidence-bar-fill"
          style={{ width: `${Math.min(100, Math.max(5, pct))}%` }}
        />
      </div>
    </div>
  );
}

import React from 'react';
import { CheckCircle, Info, Sparkles } from 'lucide-react';

export default function AnalysisResult({ answer }) {
  if (!answer) return null;

  const { summary, key_findings, explanation } = answer;

  return (
    <>
      {summary && (
        <div className="answer-summary-section">
          <p>{summary}</p>
        </div>
      )}

      {key_findings && key_findings.length > 0 && (
        <div className="key-findings-section">
          <div className="section-label">
            <Sparkles size={14} />
            <span>Key Takeaways (In Simple Words)</span>
          </div>
          <ul className="findings-list">
            {key_findings.map((finding, idx) => (
              <li key={idx} className="finding-bullet">
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation && (
        <div className="explanation-section">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', fontSize: '0.78rem', fontWeight: 600, color: '#38bdf8' }}>
            <Info size={13} />
            <span>What this means</span>
          </div>
          <p>{explanation}</p>
        </div>
      )}
    </>
  );
}

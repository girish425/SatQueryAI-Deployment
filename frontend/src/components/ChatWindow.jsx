import React, { useRef, useEffect } from 'react';
import { Satellite, AlertCircle } from 'lucide-react';
import ChatMessage from './ChatMessage';

export default function ChatWindow({
  messages,
  isLoading,
  error,
  onQuickQuery,
  hasAttachedImages
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  const samplePrompts = [
    "What is visible in this image?",
    "Is there water in this image?",
    "Where is the river?",
    "Are there buildings?",
    "Describe the image.",
    "What changed between these images?"
  ];

  return (
    <div className="messages-container">
      {messages.length === 0 ? (
        <div className="empty-state-welcome">
          <div className="welcome-icon-bubble">
            <Satellite size={32} />
          </div>
          <h2 className="welcome-title">SatQuery AI Assistant</h2>
          <p className="welcome-desc">
            An interactive vision-language assistant for multimodal remote sensing and satellite image analysis.
            Upload or retrieve a GeoTIFF raster (.tif), then ask any question.
          </p>

          <div className="sample-queries-box">
            <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
              Example Exploration Queries
            </span>
            {samplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                className="sample-query-btn"
                onClick={() => onQuickQuery(prompt)}
              >
                "{prompt}"
              </button>
            ))}
          </div>
        </div>
      ) : (
        messages.map((msg, index) => (
          <ChatMessage key={msg.id || index} message={msg} />
        ))
      )}

      {isLoading && (
        <div className="assistant-message-row">
          <div className="assistant-avatar">
            <Satellite size={18} className="animate-spin" />
          </div>
          <div className="assistant-card" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#94a3b8', fontSize: '0.9rem' }}>
              <span>AI Agent analyzing query, classifying intent & running selected remote sensing model...</span>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="assistant-message-row">
          <div className="assistant-card" style={{ borderLeft: '3px solid #ef4444', backgroundColor: 'rgba(239, 68, 68, 0.08)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontSize: '0.9rem' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

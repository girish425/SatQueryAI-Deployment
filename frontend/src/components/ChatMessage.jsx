import React from 'react';
import { Bot, User, Compass, Server, FileImage } from 'lucide-react';
import AnalysisResult from './AnalysisResult';
import EvidenceViewer from './EvidenceViewer';
import ConfidenceScore from './ConfidenceScore';
import TechnicalDetails from './TechnicalDetails';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="user-message-row">
        <div className="user-message-bubble">
          <div className="user-message-text">{message.message}</div>
          {message.image_ids && message.image_ids.length > 0 && (
            <div className="user-message-attachments">
              {message.image_ids.map((img, idx) => (
                <span key={idx} className="user-attachment-tag">
                  <FileImage size={11} />
                  <span>{img}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Assistant response card
  const intent = message.intent || 'image_understanding';
  const modelUsed = message.model_used || 'Remote Sensing Model';
  const confidence = message.confidence !== undefined
    ? message.confidence
    : (message.technical_details?.intent_confidence || 0.85);

  const answerObj = typeof message.answer === 'object' && message.answer !== null
    ? message.answer
    : { summary: message.message, key_findings: [], explanation: '' };

  return (
    <div className="assistant-message-row">
      <div className="assistant-avatar">
        <Bot size={18} />
      </div>

      <div className="assistant-card">
        {/* Meta Header */}
        <div className="agent-meta-header">
          <div className="meta-badges">
            <span className="meta-badge meta-badge-intent" title="Agent Classified Intent">
              <Compass size={12} />
              <span>{intent}</span>
            </span>
            <span className="meta-badge meta-badge-model" title="Dedicated Model Executed">
              <Server size={12} />
              <span>{modelUsed}</span>
            </span>
          </div>

          <ConfidenceScore confidence={confidence} label="Confidence" />
        </div>

        {/* Structured Result */}
        <AnalysisResult answer={answerObj} />

        {/* Visual Evidence */}
        {message.evidence && <EvidenceViewer evidence={message.evidence} />}

        {/* Collapsible Technical Details */}
        {message.technical_details && <TechnicalDetails details={message.technical_details} />}
      </div>
    </div>
  );
}

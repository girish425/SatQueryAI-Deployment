import React from 'react';
import ChatWindow from '../components/ChatWindow';
import ChatInput from '../components/ChatInput';
import DownloadButton from '../components/DownloadButton';

export default function Chat({
  sessionId,
  sessionTitle,
  messages,
  isLoading,
  error,
  attachedImages,
  onSendMessage,
  onRemoveImage,
  onOpenUpload,
  onOpenRetrieve,
  onQuickQuery
}) {
  return (
    <div className="main-chat-area">
      {/* Top Header */}
      <header className="top-header">
        <div className="header-session-title">
          <span>{sessionTitle || "New Satellite Analysis"}</span>
          <div className="header-status-badge">
            <span className="header-status-dot" />
            <span>Agentic Pipeline Active</span>
          </div>
        </div>

        <div className="header-actions">
          <DownloadButton sessionId={sessionId} disabled={messages.length === 0} />
        </div>
      </header>

      {/* Main Conversation Stream */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        error={error}
        onQuickQuery={onQuickQuery}
        hasAttachedImages={attachedImages.length > 0}
      />

      {/* Message Input Bar */}
      <ChatInput
        onSendMessage={onSendMessage}
        attachedImages={attachedImages}
        onRemoveImage={onRemoveImage}
        onOpenUpload={onOpenUpload}
        onOpenRetrieve={onOpenRetrieve}
        isLoading={isLoading}
      />
    </div>
  );
}

import React from 'react';
import { Plus, Globe, UploadCloud, Satellite, Database } from 'lucide-react';
import HistoryList from './HistoryList';

export default function Sidebar({
  conversations,
  activeSessionId,
  dbStatus,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onOpenUpload,
  onOpenRetrieve
}) {
  const isConnected = dbStatus?.status === 'connected';

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-icon">
          <Satellite size={18} />
        </div>
        <div>
          <h1 className="brand-title" style={{ fontSize: '1.1rem', margin: 0 }}>SatQuery AI</h1>
          <p style={{ fontSize: '0.68rem', color: '#64748b' }}>Remote Sensing Assistant</p>
        </div>
      </div>

      {/* Primary Actions */}
      <div className="sidebar-actions">
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus size={16} />
          <span>New Chat</span>
        </button>

        <div style={{ marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <button className="feature-nav-btn" onClick={onOpenUpload}>
            <UploadCloud size={15} color="#06b6d4" />
            <span>Upload GeoTIFF</span>
          </button>
          <button className="feature-nav-btn" onClick={onOpenRetrieve}>
            <Globe size={15} color="#3b82f6" />
            <span>Image Retrieval</span>
          </button>
        </div>
      </div>

      {/* History Section */}
      <div className="sidebar-history-section">
        <HistoryList
          conversations={conversations}
          activeSessionId={activeSessionId}
          onSelectSession={onSelectSession}
          onDeleteSession={onDeleteSession}
        />
      </div>

      {/* Database Connection Status */}
      <div style={{
        padding: '10px 14px',
        borderTop: '1px solid var(--border-subtle)',
        background: 'rgba(15, 23, 42, 0.85)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Database size={13} color={isConnected ? '#10b981' : '#f59e0b'} />
            <span style={{ fontSize: '0.74rem', fontWeight: 600, color: '#cbd5e1' }}>
              {isConnected ? 'MongoDB Atlas' : 'MongoDB Offline'}
            </span>
          </div>
          <span style={{
            fontSize: '0.66rem',
            padding: '1px 6px',
            borderRadius: '4px',
            background: isConnected ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            color: isConnected ? '#34d399' : '#fbbf24',
            border: isConnected ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)'
          }}>
            {isConnected ? 'Connected' : 'Fallback Active'}
          </span>
        </div>
        {!isConnected && (
          <p style={{
            fontSize: '0.67rem',
            color: '#f59e0b',
            margin: '6px 0 0',
            lineHeight: 1.35,
            wordBreak: 'break-word'
          }} title={dbStatus?.error || dbStatus?.message}>
            ⚠️ {dbStatus?.message || "MongoDB not connected. Local fallback store is active."}
          </p>
        )}
      </div>
    </aside>
  );
}

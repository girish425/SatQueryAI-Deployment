import React from 'react';
import { MessageSquare, Trash2 } from 'lucide-react';

export default function HistoryList({ conversations, activeSessionId, onSelectSession, onDeleteSession }) {
  if (!conversations || conversations.length === 0) {
    return (
      <div style={{ padding: '20px 10px', textAlign: 'center', color: '#64748b', fontSize: '0.8rem' }}>
        No past conversations.
      </div>
    );
  }

  // Group conversations by date: Today, Yesterday, Older
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const groups = {
    today: [],
    yesterday: [],
    older: []
  };

  conversations.forEach((conv) => {
    const d = new Date(conv.updated_at || conv.created_at || Date.now());
    if (d.toDateString() === today.toDateString()) {
      groups.today.push(conv);
    } else if (d.toDateString() === yesterday.toDateString()) {
      groups.yesterday.push(conv);
    } else {
      groups.older.push(conv);
    }
  });

  const renderGroup = (title, items) => {
    if (items.length === 0) return null;
    return (
      <div key={title} style={{ marginBottom: '12px' }}>
        <div className="history-group-title">{title}</div>
        {items.map((conv) => {
          const isActive = conv.session_id === activeSessionId;
          return (
            <div
              key={conv.session_id}
              className={`history-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectSession(conv.session_id)}
            >
              <MessageSquare size={13} style={{ marginRight: '8px', flexShrink: 0 }} />
              <span className="history-item-title" title={conv.title}>
                {conv.title || 'Satellite Analysis'}
              </span>
              <button
                className="history-delete-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(conv.session_id);
                }}
                title="Delete session"
              >
                <Trash2 size={13} />
              </button>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <>
      {renderGroup('Today', groups.today)}
      {renderGroup('Yesterday', groups.yesterday)}
      {renderGroup('Previous', groups.older)}
    </>
  );
}

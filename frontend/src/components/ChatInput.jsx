import React, { useState, useRef, useEffect } from 'react';
import { Plus, ArrowUp, UploadCloud, Globe, Loader2 } from 'lucide-react';
import ImagePreview from './ImagePreview';

export default function ChatInput({
  onSendMessage,
  attachedImages,
  onRemoveImage,
  onOpenUpload,
  onOpenRetrieve,
  isLoading
}) {
  const [text, setText] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const textareaRef = useRef(null);
  const menuRef = useRef(null);

  // Close menu on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Auto resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (!text.trim() || isLoading) return;
    onSendMessage(text);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-wrapper">
      <div className="input-container">
        {/* Attached image preview chips */}
        {attachedImages && attachedImages.length > 0 && (
          <ImagePreview images={attachedImages} onRemove={onRemoveImage} />
        )}

        {/* Input Row */}
        <div className="input-row">
          <div style={{ position: 'relative' }} ref={menuRef}>
            <button
              type="button"
              className="attach-menu-btn"
              onClick={() => setMenuOpen(!menuOpen)}
              title="Add Satellite Imagery"
            >
              <Plus size={18} />
            </button>

            {menuOpen && (
              <div className="attach-menu-dropdown">
                <button
                  type="button"
                  className="attach-menu-item"
                  onClick={() => {
                    setMenuOpen(false);
                    onOpenUpload();
                  }}
                >
                  <UploadCloud size={16} color="#06b6d4" />
                  <span>Upload GeoTIFF (.tif)</span>
                </button>
                <button
                  type="button"
                  className="attach-menu-item"
                  onClick={() => {
                    setMenuOpen(false);
                    onOpenRetrieve();
                  }}
                >
                  <Globe size={16} color="#3b82f6" />
                  <span>Retrieve Satellite Image</span>
                </button>
              </div>
            )}
          </div>

          <textarea
            ref={textareaRef}
            className="chat-textarea"
            placeholder={
              attachedImages.length > 0
                ? "Ask a question about your satellite image... (e.g. 'Is there water?', 'Where is the river?')"
                : "Attach or retrieve a GeoTIFF image, then ask a question..."
            }
            value={text}
            rows={1}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />

          <button
            type="button"
            className="send-btn"
            onClick={handleSend}
            disabled={!text.trim() || isLoading}
            title="Send query"
          >
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <ArrowUp size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
}

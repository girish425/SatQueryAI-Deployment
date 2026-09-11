import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Chat from './pages/Chat';
import ImageUpload from './components/ImageUpload';
import RetrievalModal from './components/RetrievalModal';
import LoginGate from './components/LoginGate';
import { chatApi, authApi } from './services/api';

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState('');
  const [sessionTitle, setSessionTitle] = useState('New Satellite Analysis');
  const [messages, setMessages] = useState([]);
  const [attachedImages, setAttachedImages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [retrieveModalOpen, setRetrieveModalOpen] = useState(false);
  const [dbStatus, setDbStatus] = useState(null);
  const [currentUser, setCurrentUser] = useState(() => authApi.getCurrentUser());

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Load conversation history and DB status on mount or user login
  useEffect(() => {
    if (currentUser) {
      loadHistory();
      fetchDbStatus();
    }
    // Default attach sample optical image so user can immediately test without finding a GeoTIFF
    setAttachedImages([
      {
        file_id: 'sample_optical_hyderabad.tif',
        filename: 'sample_optical_hyderabad.tif',
        preview_url: '/evidence/sample_optical_hyderabad_preview.png',
        dimensions: '512 x 512',
        bands: 3
      }
    ]);
  }, [currentUser]);

  const handleLogout = () => {
    authApi.logout();
    setCurrentUser(null);
    setConversations([]);
    setMessages([]);
    setActiveSessionId('');
    showToast('Signed out of private workspace.', 'info');
  };

  const fetchDbStatus = async () => {
    try {
      const res = await chatApi.getDatabaseHealth();
      setDbStatus(res);
    } catch (err) {
      setDbStatus({
        status: 'disconnected',
        message: 'Could not connect to backend database service.',
        error: err.message
      });
    }
  };

  const loadHistory = async () => {
    try {
      const res = await chatApi.getHistory();
      if (res.conversations && res.conversations.length > 0) {
        setConversations(res.conversations);
        // Load the most recent conversation if no active session
        if (!activeSessionId) {
          selectSession(res.conversations[0].session_id);
        }
      } else {
        startNewChat();
      }
    } catch (err) {
      console.warn("Could not load history on mount:", err);
      startNewChat();
    }
  };

  const startNewChat = async () => {
    try {
      const res = await chatApi.createNewSession();
      setActiveSessionId(res.session_id);
      setSessionTitle(res.conversation.title || 'New Satellite Analysis');
      setMessages([]);
      setError(null);
    } catch (err) {
      // Fallback client session id
      const tempId = 'session_' + Math.random().toString(36).substring(2, 9);
      setActiveSessionId(tempId);
      setSessionTitle('New Satellite Analysis');
      setMessages([]);
    }
  };

  const selectSession = async (sessionId) => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await chatApi.getConversation(sessionId);
      setActiveSessionId(sessionId);
      setSessionTitle(res.conversation?.title || 'Satellite Analysis');
      setMessages(res.conversation?.messages || []);
      setIsLoading(false);
    } catch (err) {
      setIsLoading(false);
      console.error("Failed to fetch session:", err);
      showToast("Failed to load conversation.", "error");
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      await chatApi.deleteSession(sessionId);
      showToast("Conversation deleted.", "info");
      const updated = conversations.filter(c => c.session_id !== sessionId);
      setConversations(updated);
      if (sessionId === activeSessionId) {
        if (updated.length > 0) {
          selectSession(updated[0].session_id);
        } else {
          startNewChat();
        }
      }
    } catch (err) {
      showToast("Could not delete conversation.", "error");
    }
  };

  const handleSendMessage = async (queryText) => {
    if (!queryText.trim()) return;

    if (attachedImages.length === 0) {
      setError("Please attach or retrieve a GeoTIFF satellite image first.");
      showToast("No satellite image attached.", "error");
      return;
    }

    setError(null);
    const imageIds = attachedImages.map(img => img.saved_filename || img.file_id || img.filename);

    // Optimistically append user message
    const userMsg = {
      role: 'user',
      message: queryText,
      image_ids: imageIds,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await chatApi.sendMessage(activeSessionId, queryText, imageIds);
      setIsLoading(false);

      // Assistant message
      const asstMsg = {
        role: 'assistant',
        message: res.answer?.summary || '',
        answer: res.answer,
        intent: res.intent,
        intent_confidence: res.intent_confidence,
        model_used: res.model_used,
        evidence: res.evidence,
        technical_details: res.technical_details,
        confidence: res.confidence,
        timestamp: res.timestamp
      };
      setMessages(prev => [...prev, asstMsg]);

      // Update active session ID if server returned new one
      if (res.session_id && res.session_id !== activeSessionId) {
        setActiveSessionId(res.session_id);
      }

      // Refresh sidebar list
      const histRes = await chatApi.getHistory();
      if (histRes.conversations) {
        setConversations(histRes.conversations);
        const cur = histRes.conversations.find(c => c.session_id === (res.session_id || activeSessionId));
        if (cur) setSessionTitle(cur.title);
      }
    } catch (err) {
      setIsLoading(false);
      const errMsg = err.response?.data?.detail || err.message || "Failed to process query.";
      setError(errMsg);
      showToast(errMsg, "error");
    }
  };

  const handleUploadSuccess = (uploadData) => {
    setAttachedImages(prev => [...prev, uploadData]);
    showToast(`Uploaded ${uploadData.filename} successfully.`, "success");
  };

  const handleSelectRetrievedImage = (imageData) => {
    setAttachedImages(prev => [...prev, imageData]);
    showToast(`Added ${imageData.filename} to session.`, "success");
  };

  const handleRemoveImage = (imgToRemove) => {
    setAttachedImages(prev => prev.filter(img =>
      (img.file_id || img.filename) !== (imgToRemove.file_id || imgToRemove.filename)
    ));
  };

  if (!currentUser) {
    return (
      <LoginGate
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          showToast(`Welcome back, ${user.full_name || user.email}!`, 'success');
        }}
      />
    );
  }

  return (
    <div className="app-container">
      {/* Left Sidebar with strictly isolated private sessions & profile */}
      <Sidebar
        conversations={conversations}
        activeSessionId={activeSessionId}
        dbStatus={dbStatus}
        currentUser={currentUser}
        onLogout={handleLogout}
        onNewChat={startNewChat}
        onSelectSession={selectSession}
        onDeleteSession={deleteSession}
        onOpenUpload={() => setUploadModalOpen(true)}
        onOpenRetrieve={() => setRetrieveModalOpen(true)}
      />

      {/* Main Chat Interface */}
      <Chat
        sessionId={activeSessionId}
        sessionTitle={sessionTitle}
        messages={messages}
        isLoading={isLoading}
        error={error}
        attachedImages={attachedImages}
        onSendMessage={handleSendMessage}
        onRemoveImage={handleRemoveImage}
        onOpenUpload={() => setUploadModalOpen(true)}
        onOpenRetrieve={() => setRetrieveModalOpen(true)}
        onQuickQuery={(prompt) => handleSendMessage(prompt)}
      />

      {/* Modals */}
      <ImageUpload
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      <RetrievalModal
        isOpen={retrieveModalOpen}
        onClose={() => setRetrieveModalOpen(false)}
        onSelectImage={handleSelectRetrievedImage}
        onApplyQuestion={(questionText) => handleSendMessage(questionText)}
      />

      {/* Notification Toasts */}
      {toast && (
        <div className={`toast-alert ${toast.type}`}>
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

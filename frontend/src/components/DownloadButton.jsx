import React from 'react';
import { Download, FileText } from 'lucide-react';
import { chatApi } from '../services/api';

export default function DownloadButton({ sessionId, disabled }) {
  const handleDownload = () => {
    if (!sessionId || disabled) return;
    const downloadUrl = chatApi.getPDFDownloadUrl(sessionId);
    window.open(downloadUrl, '_blank');
  };

  return (
    <button
      className="download-pdf-btn"
      onClick={handleDownload}
      disabled={disabled || !sessionId}
      title="Download complete conversation as PDF"
    >
      <Download size={14} />
      <span>Download PDF</span>
    </button>
  );
}

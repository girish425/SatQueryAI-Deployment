import React, { useRef, useState } from 'react';
import { UploadCloud, X, AlertCircle, Loader2 } from 'lucide-react';
import { validateSatelliteFile } from '../utils/fileValidation';
import { chatApi } from '../services/api';

export default function ImageUpload({ isOpen, onClose, onUploadSuccess }) {
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleFile = async (file) => {
    setErrorMessage('');
    const validation = validateSatelliteFile(file);
    if (!validation.valid) {
      setErrorMessage(validation.error);
      return;
    }

    try {
      setIsUploading(true);
      setUploadProgress(0);
      const res = await chatApi.uploadGeoTIFF(file, (pct) => setUploadProgress(pct));
      setIsUploading(false);
      onUploadSuccess(res);
      onClose();
    } catch (err) {
      setIsUploading(false);
      const msg = err.response?.data?.detail || err.message || 'Failed to upload satellite image.';
      setErrorMessage(msg);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span className="modal-title">
            <UploadCloud size={18} color="#06b6d4" />
            <span>Upload Satellite GeoTIFF</span>
          </span>
          <button className="modal-close-btn" onClick={onClose} disabled={isUploading}>
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <input
            type="file"
            ref={fileInputRef}
            accept=".tif,.tiff"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFile(e.target.files[0]);
              }
            }}
          />

          <div
            className="dropzone-box"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => !isUploading && fileInputRef.current?.click()}
          >
            {isUploading ? (
              <>
                <Loader2 size={36} color="#06b6d4" className="animate-spin" />
                <p style={{ fontSize: '0.9rem', color: '#94a3b8' }}>
                  Uploading & preprocessing GeoTIFF raster... ({uploadProgress}%)
                </p>
              </>
            ) : (
              <>
                <UploadCloud size={40} color="#06b6d4" />
                <div>
                  <p style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                    Click to select or drag and drop satellite image
                  </p>
                  <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>
                    Supports GeoTIFF format (<strong>.tif, .tiff</strong> up to 1GB)
                  </p>
                </div>
              </>
            )}
          </div>

          {errorMessage && (
            <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171', fontSize: '0.84rem' }}>
              <AlertCircle size={16} />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

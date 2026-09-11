import React from 'react';
import { Check, X, FileCheck } from 'lucide-react';
import { resolveAssetUrl } from '../services/api';

export default function ImagePreview({ images, onRemove }) {
  if (!images || images.length === 0) return null;

  return (
    <div className="attached-images-preview">
      {images.map((img) => (
        <div key={img.file_id || img.filename} className="image-preview-card">
          {img.preview_url ? (
            <img src={resolveAssetUrl(img.preview_url)} alt={img.filename} className="image-preview-thumb" />
          ) : (
            <div className="image-preview-thumb" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#334155' }}>
              <FileCheck size={20} color="#38bdf8" />
            </div>
          )}

          <div className="image-preview-info">
            <span className="image-preview-name" title={img.filename}>
              {img.filename}
            </span>
            <span className="image-preview-status">
              <Check size={12} />
              <span>Ready for analysis</span>
            </span>
          </div>

          <button
            type="button"
            className="image-preview-remove"
            onClick={() => onRemove(img)}
            title="Remove attachment"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

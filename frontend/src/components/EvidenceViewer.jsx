import React, { useState } from 'react';
import { Layers, Eye, X } from 'lucide-react';
import { resolveAssetUrl } from '../services/api';

export default function EvidenceViewer({ evidence }) {
  const [fullscreenImage, setFullscreenImage] = useState(null);

  if (!evidence) return null;

  const { original_image, overlay_image, difference_image } = evidence;

  // Determine available cards
  const cards = [];

  if (original_image) {
    cards.push({
      key: 'orig',
      title: 'Original GeoTIFF Preview',
      url: resolveAssetUrl(original_image)
    });
  }

  if (overlay_image) {
    cards.push({
      key: 'overlay',
      title: 'Analytical Overlay / Grounding',
      url: resolveAssetUrl(overlay_image)
    });
  }

  if (difference_image) {
    cards.push({
      key: 'diff',
      title: 'Difference Heatmap / Fusion',
      url: resolveAssetUrl(difference_image)
    });
  }

  if (cards.length === 0) return null;

  return (
    <div className="evidence-section">
      <div className="section-label">
        <Layers size={14} />
        <span>Visual Evidence</span>
      </div>

      <div className="evidence-grid">
        {cards.map((card) => (
          <div key={card.key} className="evidence-card">
            <div className="evidence-label">
              <span>{card.title}</span>
              <Eye size={12} style={{ opacity: 0.6 }} />
            </div>
            <img
              src={card.url}
              alt={card.title}
              className="evidence-image"
              onClick={() => setFullscreenImage(card)}
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          </div>
        ))}
      </div>

      {fullscreenImage && (
        <div className="modal-overlay" onClick={() => setFullscreenImage(null)}>
          <div className="modal-content" style={{ maxWidth: '800px' }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">{fullscreenImage.title}</span>
              <button className="modal-close-btn" onClick={() => setFullscreenImage(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body" style={{ display: 'flex', justifyContent: 'center' }}>
              <img
                src={fullscreenImage.url}
                alt={fullscreenImage.title}
                style={{ maxWidth: '100%', maxHeight: '70vh', borderRadius: '8px', objectFit: 'contain' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

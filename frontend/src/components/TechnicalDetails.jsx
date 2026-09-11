import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Cpu } from 'lucide-react';

export default function TechnicalDetails({ details }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!details) return null;

  return (
    <div className="tech-details-container">
      <button
        className="tech-details-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Cpu size={13} />
          <span>Technical Pipeline & Raster Metadata</span>
        </span>
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>

      {isOpen && (
        <div className="tech-details-body">
          {details.selected_intent && (
            <div>
              <span className="tech-item-label">Intent: </span>
              <span>{details.selected_intent}</span>
            </div>
          )}
          {details.model_selected && (
            <div>
              <span className="tech-item-label">Engine: </span>
              <span>{details.model_selected}</span>
            </div>
          )}
          {details.dimensions && (
            <div>
              <span className="tech-item-label">Dimensions: </span>
              <span>{details.dimensions}</span>
            </div>
          )}
          {details.bands !== undefined && (
            <div>
              <span className="tech-item-label">Bands: </span>
              <span>{details.bands}</span>
            </div>
          )}
          {details.crs && (
            <div>
              <span className="tech-item-label">CRS: </span>
              <span>{details.crs}</span>
            </div>
          )}
          {details.processing_time_sec !== undefined && (
            <div>
              <span className="tech-item-label">Compute Time: </span>
              <span>{details.processing_time_sec}s</span>
            </div>
          )}
          {details.preprocessing_info && (
            <div style={{ gridColumn: '1 / -1' }}>
              <span className="tech-item-label">Preprocessing: </span>
              <span>{details.preprocessing_info}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

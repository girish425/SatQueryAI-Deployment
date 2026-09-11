import React, { useState, useEffect } from 'react';
import { Search, Globe, X, Calendar, MapPin, Radio, Loader2, Layers, BookOpen, Sparkles, HelpCircle } from 'lucide-react';
import { chatApi, resolveAssetUrl } from '../services/api';

export default function RetrievalModal({ isOpen, onClose, onSelectImage, onApplyQuestion }) {
  const [activeTab, setActiveTab] = useState('bigearthnet'); // 'bigearthnet' | 'stac'
  const [queryText, setQueryText] = useState('');
  const [labelFilter, setLabelFilter] = useState('');
  const [satelliteFilter, setSatelliteFilter] = useState('');
  const [cloudCover, setCloudCover] = useState(30);

  const [benItems, setBenItems] = useState([]);
  const [stacItems, setStacItems] = useState([]);
  const [stacMessage, setStacMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectingId, setSelectingId] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadBigEarthNet('', '');
      loadStac(queryText || 'Mumbai', satelliteFilter, cloudCover);
    }
  }, [isOpen]);

  const loadBigEarthNet = async (q, lbl) => {
    try {
      setIsLoading(true);
      const res = await chatApi.getBigEarthNetCatalog(q, lbl || null);
      setBenItems(res.results || []);
    } catch (err) {
      console.error("Failed to load BigEarthNet catalog:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStac = async (q, sat, cc = cloudCover) => {
    try {
      setIsLoading(true);
      const res = await chatApi.getCatalogImagery(q || 'Mumbai', sat || null, cc);
      setStacItems(res.results || []);
      setStacMessage(res.message || '');
    } catch (err) {
      console.error("Failed to load STAC catalog:", err);
      setStacItems([]);
      setStacMessage("Failed to query live satellite STAC service. Please verify network connectivity.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (activeTab === 'bigearthnet') {
      loadBigEarthNet(queryText, labelFilter);
    } else {
      loadStac(queryText, satelliteFilter, cloudCover);
    }
  };

  const handleSelectBigEarthNet = async (patch, mode) => {
    try {
      setSelectingId(`${patch.id}_${mode}`);
      const res = await chatApi.selectBigEarthNetPatch(patch.id, mode);
      // Add staged items to images
      if (res.staged_items) {
        res.staged_items.forEach(item => onSelectImage(item));
      }
      onClose();
    } catch (err) {
      console.error("Error staging BigEarthNet patch:", err);
      alert("Failed to stage BigEarthNet imagery.");
    } finally {
      setSelectingId(null);
    }
  };

  const handleSelectStac = async (item) => {
    try {
      setSelectingId(item.id);
      const res = await chatApi.selectLiveSTACImage(
        item.id,
        item.thumbnail_url,
        item.title,
        item.satellite || item.platform
      );
      onSelectImage(res);
      onClose();
    } catch (err) {
      console.error("Error selecting image:", err);
      alert("Failed to stage selected satellite image.");
    } finally {
      setSelectingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '860px', height: '88vh' }} onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <span className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={19} color="#06b6d4" />
              <span>Satellite Imagery & BigEarthNet.txt Retrieval</span>
            </span>
            <p style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '3px' }}>
              Co-registered Sentinel-1 SAR & Sentinel-2 Multispectral benchmarks with rich text annotations (arXiv:2603.29630)
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div style={{ display: 'flex', gap: '10px', padding: '12px 20px 0', borderBottom: '1px solid var(--border-subtle)' }}>
          <button
            type="button"
            onClick={() => setActiveTab('bigearthnet')}
            style={{
              padding: '8px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'bigearthnet' ? '2px solid #06b6d4' : '2px solid transparent',
              color: activeTab === 'bigearthnet' ? '#06b6d4' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Sparkles size={14} />
            <span>BigEarthNet.txt (arXiv:2603.29630)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('stac')}
            style={{
              padding: '8px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'stac' ? '2px solid #06b6d4' : '2px solid transparent',
              color: activeTab === 'stac' ? '#06b6d4' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Globe size={14} />
            <span>Global STAC Search</span>
          </button>
        </div>

        {/* Search Bar & Filter Controls */}
        <div style={{ padding: '14px 20px 6px' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <input
                type="text"
                placeholder={
                  activeTab === 'bigearthnet'
                    ? "Search BigEarthNet captions, LULC classes (e.g. 'forest', 'water course', 'olive groves')..."
                    : "Search location or region (e.g. 'Hyderabad', 'Sentinel-2')..."
                }
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px 9px 36px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)',
                  fontSize: '0.86rem',
                  outline: 'none'
                }}
              />
              <Search size={15} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '11px' }} />
            </div>

            {activeTab === 'bigearthnet' ? (
              <select
                value={labelFilter}
                onChange={(e) => {
                  setLabelFilter(e.target.value);
                  loadBigEarthNet(queryText, e.target.value);
                }}
                style={{
                  padding: '0 12px',
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)',
                  fontSize: '0.84rem'
                }}
              >
                <option value="">All Land-Cover Classes</option>
                <option value="Forest">Forest (Broad-leaved / Coniferous)</option>
                <option value="Water">Water courses & Water bodies</option>
                <option value="Crops">Permanent crops & Cultivation</option>
                <option value="Urban">Urban fabric & Industrial</option>
              </select>
            ) : (
              <>
                <select
                  value={satelliteFilter}
                  onChange={(e) => {
                    setSatelliteFilter(e.target.value);
                    loadStac(queryText, e.target.value, cloudCover);
                  }}
                  style={{
                    padding: '0 12px',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    fontSize: '0.84rem'
                  }}
                >
                  <option value="">All Sensors</option>
                  <option value="Sentinel-2">Sentinel-2 (MSI)</option>
                  <option value="Sentinel-1">Sentinel-1 (SAR)</option>
                  <option value="Landsat">Landsat-8/9</option>
                </select>

                <select
                  value={cloudCover}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setCloudCover(val);
                    loadStac(queryText, satelliteFilter, val);
                  }}
                  title="Filter maximum cloud coverage for optical satellites"
                  style={{
                    padding: '0 12px',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--text-primary)',
                    fontSize: '0.84rem'
                  }}
                >
                  <option value={10}>Max Cloud: &lt;10%</option>
                  <option value={20}>Max Cloud: &lt;20%</option>
                  <option value={30}>Max Cloud: &lt;30%</option>
                  <option value={50}>Max Cloud: &lt;50%</option>
                  <option value={100}>Max Cloud: &lt;100%</option>
                </select>
              </>
            )}

            <button
              type="submit"
              className="catalog-select-btn"
              style={{ marginTop: 0, padding: '0 16px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <Search size={14} />
              <span>Search</span>
            </button>
          </form>
        </div>

        {/* Modal Body */}
        <div className="modal-body" style={{ flex: 1, overflowY: 'auto', padding: '12px 20px 24px' }}>
          {isLoading ? (
            <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>
              <Loader2 size={36} color="#06b6d4" className="animate-spin" style={{ margin: '0 auto 12px' }} />
              <p>Fetching remote sensing products...</p>
            </div>
          ) : activeTab === 'bigearthnet' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {benItems.map((patch) => (
                <div
                  key={patch.id}
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                  }}
                >
                  {/* Card Title & Badges */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                    <div>
                      <h4 style={{ fontSize: '0.98rem', fontWeight: 600, color: '#f8fafc', margin: 0 }}>
                        {patch.title}
                      </h4>
                      <span style={{ fontSize: '0.74rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                        <MapPin size={11} color="#06b6d4" />
                        <span>{patch.location} ({patch.country})</span>
                        <span style={{ margin: '0 6px' }}>•</span>
                        <span>Co-registered Sentinel-1 SAR + Sentinel-2 MSI (10m)</span>
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(6, 182, 212, 0.15)', color: '#06b6d4', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
                        Optical S2
                      </span>
                      <span style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                        Radar S1 (VV)
                      </span>
                    </div>
                  </div>

                  {/* Dual Thumbnails & Caption */}
                  <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <div style={{ position: 'relative' }}>
                        <img
                          src={resolveAssetUrl(patch.s2_thumbnail)}
                          alt="Sentinel-2 Optical"
                          style={{ width: '110px', height: '110px', borderRadius: '6px', objectFit: 'cover', border: '1px solid var(--border-subtle)' }}
                        />
                        <span style={{ position: 'absolute', bottom: '4px', left: '4px', fontSize: '0.65rem', background: 'rgba(0,0,0,0.7)', padding: '1px 5px', borderRadius: '3px' }}>
                          S2 Optical
                        </span>
                      </div>
                      <div style={{ position: 'relative' }}>
                        <img
                          src={resolveAssetUrl(patch.s1_thumbnail)}
                          alt="Sentinel-1 SAR"
                          style={{ width: '110px', height: '110px', borderRadius: '6px', objectFit: 'cover', border: '1px solid var(--border-subtle)' }}
                        />
                        <span style={{ position: 'absolute', bottom: '4px', left: '4px', fontSize: '0.65rem', background: 'rgba(0,0,0,0.7)', padding: '1px 5px', borderRadius: '3px' }}>
                          S1 SAR
                        </span>
                      </div>
                    </div>

                    <div style={{ flex: 1, minWidth: '240px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <span style={{ fontSize: '0.74rem', fontWeight: 600, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          BigEarthNet.txt Ground-Truth Caption:
                        </span>
                        <p style={{ fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.45, marginTop: '4px' }}>
                          "{patch.caption}"
                        </p>
                      </div>

                      {/* CORINE Multi-Labels */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '8px' }}>
                        {patch.corine_labels.map((lbl, idx) => (
                          <span key={idx} style={{ fontSize: '0.7rem', background: 'rgba(30, 41, 59, 0.8)', padding: '2px 7px', borderRadius: '4px', color: '#94a3b8', border: '1px solid var(--border-subtle)' }}>
                            {lbl}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Sample VQA Questions */}
                  {patch.vqa_pairs && patch.vqa_pairs.length > 0 && (
                    <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                      <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <HelpCircle size={11} />
                        <span>Annotated BigEarthNet VQA Questions (Click to Ask):</span>
                      </span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                        {patch.vqa_pairs.map((qa, qidx) => (
                          <button
                            key={qidx}
                            type="button"
                            onClick={async () => {
                              await handleSelectBigEarthNet(patch, 's2');
                              if (onApplyQuestion) {
                                onApplyQuestion(qa.question);
                              }
                            }}
                            style={{
                              fontSize: '0.75rem',
                              color: '#93c5fd',
                              background: 'rgba(59, 130, 246, 0.15)',
                              border: '1px solid rgba(59, 130, 246, 0.25)',
                              padding: '3px 9px',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              textAlign: 'left',
                              transition: 'all 0.15s ease'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = 'rgba(59, 130, 246, 0.3)';
                              e.currentTarget.style.color = '#ffffff';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = 'rgba(59, 130, 246, 0.15)';
                              e.currentTarget.style.color = '#93c5fd';
                            }}
                            title="Click to stage this patch and ask this question"
                          >
                            "{qa.question}"
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Staging Action Buttons */}
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                    <button
                      type="button"
                      className="catalog-select-btn"
                      style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)' }}
                      disabled={selectingId === `${patch.id}_pair`}
                      onClick={() => handleSelectBigEarthNet(patch, 'pair')}
                    >
                      {selectingId === `${patch.id}_pair` ? 'Staging Pair...' : '⚡ Stage Both S1+S2 (Co-registered Pair)'}
                    </button>
                    <button
                      type="button"
                      className="catalog-select-btn"
                      style={{ background: 'rgba(30, 41, 59, 0.8)', border: '1px solid var(--border-subtle)' }}
                      disabled={selectingId === `${patch.id}_s2`}
                      onClick={() => handleSelectBigEarthNet(patch, 's2')}
                    >
                      Stage Optical S2 Only
                    </button>
                    <button
                      type="button"
                      className="catalog-select-btn"
                      style={{ background: 'rgba(30, 41, 59, 0.8)', border: '1px solid var(--border-subtle)' }}
                      disabled={selectingId === `${patch.id}_s1`}
                      onClick={() => handleSelectBigEarthNet(patch, 's1')}
                    >
                      Stage SAR S1 Only
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* Standard STAC Results Grid */
            stacItems.length === 0 ? (
              <div style={{ padding: '60px 20px', textAlign: 'center', color: '#94a3b8' }}>
                <Globe size={44} color="#06b6d4" style={{ margin: '0 auto 16px', opacity: 0.7 }} />
                <h3 style={{ color: '#f8fafc', fontSize: '1.1rem', marginBottom: '8px' }}>
                  No Live Satellite Imagery Found
                </h3>
                <p style={{ maxWidth: '520px', margin: '0 auto', fontSize: '0.85rem', lineHeight: 1.5, color: '#cbd5e1' }}>
                  {stacMessage || `No satellite scenes matched query "${queryText || 'Mumbai'}" with current sensor and cloud cover constraints.`}
                </p>
                <p style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '14px' }}>
                  💡 Tip: Try increasing the max cloud cover threshold, selecting "All Sensors", or searching for a major location (e.g., Mumbai, Hyderabad, Delhi, London, Tokyo).
                </p>
              </div>
            ) : (
              <div className="retrieval-catalog-grid">
                {stacItems.map((item) => (
                  <div key={item.id} className="catalog-item-card">
                    <div style={{ position: 'relative' }}>
                      <img src={resolveAssetUrl(item.thumbnail_url)} alt={item.title} className="catalog-thumb" />
                      {item.cloud_cover !== undefined && item.cloud_cover !== null && (
                        <span style={{
                          position: 'absolute',
                          top: '6px',
                          right: '6px',
                          fontSize: '0.68rem',
                          fontWeight: 600,
                          padding: '2px 7px',
                          borderRadius: '4px',
                          background: 'rgba(15, 23, 42, 0.85)',
                          color: item.cloud_cover < 15 ? '#4ade80' : item.cloud_cover < 40 ? '#facc15' : '#f87171',
                          border: '1px solid rgba(255,255,255,0.1)'
                        }}>
                          ☁️ {Math.round(item.cloud_cover)}% Cloud
                        </span>
                      )}
                    </div>
                    <div className="catalog-info">
                      <span className="catalog-item-title" title={item.title}>{item.title}</span>
                      <div className="catalog-metadata-row">
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Radio size={11} color="#06b6d4" />
                          <span>{item.satellite}</span>
                        </span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Calendar size={11} />
                          <span>{item.date}</span>
                        </span>
                      </div>
                      <div className="catalog-metadata-row">
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <MapPin size={11} />
                          <span>{item.location}</span>
                        </span>
                        <span>{item.resolution}</span>
                      </div>

                      <button
                        className="catalog-select-btn"
                        onClick={() => handleSelectStac(item)}
                        disabled={selectingId === item.id}
                      >
                        {selectingId === item.id ? 'Downloading & Staging...' : 'Select & Add to Chat'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

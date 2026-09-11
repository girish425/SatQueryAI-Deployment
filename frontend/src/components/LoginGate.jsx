import React, { useState } from 'react';
import { authApi } from '../services/api';

export default function LoginGate({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let res;
      if (isRegister) {
        if (!fullName.trim()) {
          throw new Error('Please enter your full name.');
        }
        res = await authApi.register(fullName, email, password);
      } else {
        res = await authApi.login(email, password);
      }

      if (res && res.user) {
        onLoginSuccess(res.user);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Authentication failed. Please check credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoFill = () => {
    setEmail('researcher@satquery.ai');
    setPassword('satellite2026');
    setFullName('Satellite Researcher');
  };

  return (
    <div className="login-gate-container">
      <div className="login-gate-backdrop">
        <div className="radial-glow-1" />
        <div className="radial-glow-2" />
      </div>

      <div className="login-gate-card">
        {/* Brand Header */}
        <div className="login-brand-header">
          <div className="brand-icon-wrapper">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="brand-svg-icon">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
              <path d="M2 12h20" />
            </svg>
          </div>
          <h1 className="login-brand-title">SatQuery AI</h1>
          <p className="login-brand-subtitle">Multimodal Vision-Language Satellite Intelligence</p>
        </div>

        {/* Security Notice */}
        <div className="security-notice-badge">
          <span className="lock-icon">🔒</span>
          <span>Private Workspace Gate &middot; Individual User Isolation</span>
        </div>

        {/* Auth Mode Tabs */}
        <div className="auth-tab-group">
          <button
            type="button"
            className={`auth-tab-btn ${!isRegister ? 'active' : ''}`}
            onClick={() => { setIsRegister(false); setError(null); }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab-btn ${isRegister ? 'active' : ''}`}
            onClick={() => { setIsRegister(true); setError(null); }}
          >
            Create Account
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="auth-error-banner">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          {isRegister && (
            <div className="form-field">
              <label htmlFor="fullNameInput">Full Name</label>
              <input
                id="fullNameInput"
                type="text"
                placeholder="e.g. Dr. Alex Vance"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-field">
            <label htmlFor="emailInput">Email Address</label>
            <input
              id="emailInput"
              type="email"
              placeholder="user@organization.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="passwordInput">Password</label>
            <input
              id="passwordInput"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={loading}
          >
            {loading ? (
              <span className="auth-spinner-label">Authenticating...</span>
            ) : (
              <span>{isRegister ? 'Create Private Account' : 'Sign In to Workspace'}</span>
            )}
          </button>
        </form>

        {/* Privacy Footnote */}
        <div className="auth-footer-notes">
          <p>
            Your satellite analyses, conversation logs, and uploaded rasters are securely encrypted and isolated to your account.
          </p>
          <button type="button" onClick={handleDemoFill} className="quick-fill-link">
            Quick Fill Demo Account
          </button>
        </div>
      </div>
    </div>
  );
}

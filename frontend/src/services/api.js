import axios from 'axios';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

export function resolveAssetUrl(url) {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:') || url.startsWith('blob:')) {
    return url;
  }
  const cleanPath = url.startsWith('/') ? url : `/${url}`;
  return `${API_BASE_URL}${cleanPath}`;
}

// Configurable API client supporting both unified server and decoupled Render deployment
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically attach Bearer token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('satquery_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  async register(fullName, email, password) {
    const response = await api.post('/api/auth/register', {
      full_name: fullName,
      email,
      password,
    });
    if (response.data.token) {
      localStorage.setItem('satquery_token', response.data.token);
      localStorage.setItem('satquery_user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  async login(email, password) {
    const response = await api.post('/api/auth/login', {
      email,
      password,
    });
    if (response.data.token) {
      localStorage.setItem('satquery_token', response.data.token);
      localStorage.setItem('satquery_user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  async getMe() {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  logout() {
    localStorage.removeItem('satquery_token');
    localStorage.removeItem('satquery_user');
  },

  getCurrentUser() {
    try {
      const stored = localStorage.getItem('satquery_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  },
};

export const chatApi = {
  async sendMessage(sessionId, query, imageIds = []) {
    const response = await api.post('/chat/', {
      session_id: sessionId,
      query,
      image_ids: imageIds,
    });
    return response.data;
  },

  async uploadGeoTIFF(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return response.data;
  },

  async searchImagery(query, satellite = null) {
    const response = await api.post('/retrieve/', {
      query,
      satellite,
    });
    return response.data;
  },

  async getCatalogImagery(query = '', satellite = null, cloudCover = 30.0, limit = 8) {
    const params = {};
    if (query) params.query = query;
    if (satellite) params.satellite = satellite;
    if (cloudCover !== null && cloudCover !== undefined) params.cloud_cover = cloudCover;
    if (limit) params.limit = limit;
    const response = await api.get('/retrieve/results', { params });
    return response.data;
  },

  async selectLiveSTACImage(itemId, previewUrl, title, platform) {
    const response = await api.post('/retrieve/select-stac', null, {
      params: {
        item_id: itemId,
        preview_url: previewUrl,
        title: title || 'Live STAC Satellite Scene',
        platform: platform || 'Sentinel-2',
      },
    });
    return response.data;
  },

  async getBigEarthNetCatalog(query = '', label = null) {
    const params = {};
    if (query) params.query = query;
    if (label) params.label = label;
    const response = await api.get('/retrieve/bigearthnet', { params });
    return response.data;
  },

  async selectBigEarthNetPatch(patchId, mode = 'pair') {
    const response = await api.post(`/retrieve/select-bigearthnet/${patchId}`, null, {
      params: { mode }
    });
    return response.data;
  },

  async getHistory() {
    const response = await api.get('/history/');
    return response.data;
  },

  async getConversation(sessionId) {
    const response = await api.get(`/history/${sessionId}`);
    return response.data;
  },

  async createNewSession() {
    const response = await api.post('/history/new');
    return response.data;
  },

  async saveConversation(sessionId, title, messages = null, selectedModel = null, imageReferences = null) {
    const response = await api.post('/history/save', {
      session_id: sessionId,
      title,
      messages,
      selected_model: selectedModel,
      image_references: imageReferences,
    });
    return response.data;
  },

  async getDatabaseHealth() {
    const response = await api.get('/health/db');
    return response.data;
  },

  async getHealth() {
    const response = await api.get('/health');
    return response.data;
  },

  getPDFDownloadUrl(sessionId) {
    return resolveAssetUrl(`/conversation/${sessionId}/pdf`);
  },
};

export default api;

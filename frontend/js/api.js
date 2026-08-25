/* ELEVATE AI - API layer. All backend calls are centralized here so pages
   render values returned by the server rather than hardcoding data. */
const API_BASE = (function () {
  // Allows the same frontend to be opened from file:// or served statically.
  const override = window.localStorage.getItem('elevate_api_base');
  if (override) return override;
  return 'http://localhost:8000';
})();

const Api = {
  token() { return localStorage.getItem('elevate_token'); },

  async request(path, { method = 'GET', body = null, isForm = false } = {}) {
    const headers = {};
    const token = this.token();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!isForm) headers['Content-Type'] = 'application/json';

    let resp;
    try {
      resp = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: isForm ? body : (body ? JSON.stringify(body) : undefined),
      });
    } catch (err) {
      throw { offline: true, message: 'Could not reach the ELEVATE AI server. Is the backend running on port 8000?' };
    }

    let data = null;
    try { data = await resp.json(); } catch (e) { /* no body */ }

    if (resp.status === 401) {
      localStorage.removeItem('elevate_token');
      localStorage.removeItem('elevate_user');
      if (!location.pathname.endsWith('login.html') && !location.pathname.endsWith('index.html') && location.pathname !== '/') {
        location.href = 'login.html';
      }
      throw { status: 401, message: (data && data.detail) || 'Session expired' };
    }
    if (!resp.ok) {
      throw { status: resp.status, message: (data && data.detail) || 'Something went wrong' };
    }
    return data;
  },

  get(path) { return this.request(path); },
  post(path, body) { return this.request(path, { method: 'POST', body }); },
  put(path, body) { return this.request(path, { method: 'PUT', body }); },
  postForm(path, formData) { return this.request(path, { method: 'POST', body: formData, isForm: true }); },
};

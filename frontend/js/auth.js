const Auth = {
  isLoggedIn() { return !!localStorage.getItem('elevate_token'); },
  getUser() {
    try { return JSON.parse(localStorage.getItem('elevate_user') || 'null'); } catch (e) { return null; }
  },
  setSession(token, user) {
    localStorage.setItem('elevate_token', token);
    localStorage.setItem('elevate_user', JSON.stringify(user));
  },
  clearSession() {
    localStorage.removeItem('elevate_token');
    localStorage.removeItem('elevate_user');
  },
  async logout() {
    try { await Api.post('/api/auth/logout'); } catch (e) { /* ignore */ }
    this.clearSession();
    location.href = 'login.html';
  },
  /** Call at the top of any protected page. Redirects if not authenticated
      or role mismatched. Returns the user object. */
  requireRole(role) {
    if (!this.isLoggedIn()) { location.href = 'login.html'; return null; }
    const user = this.getUser();
    if (role && user && user.role !== role) {
      location.href = user.role === 'teacher' ? 'teacher-dashboard.html' : 'dashboard.html';
      return null;
    }
    return user;
  },
};

// If already logged in, keep public login/signup pages from being re-visited awkwardly.
function redirectIfLoggedIn() {
  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    if (user && user.role === 'teacher') location.href = 'teacher-dashboard.html';
    else if (user && !user.onboarding_completed) location.href = 'onboarding.html';
    else location.href = 'dashboard.html';
  }
}

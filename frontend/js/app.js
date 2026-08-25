/* ============================================================
   ELEVATE AI - shared app shell, toasts, small icon set
   ============================================================ */
const Icons = {
  logo: `<span class="brand-mark">E</span>`,
  dashboard: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>`,
  path: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="6" r="2.5"/><circle cx="19" cy="18" r="2.5"/><path d="M7 7.5 17 16.5"/></svg>`,
  gaps: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2 3 7v6c0 5 4 8 9 9 5-1 9-4 9-9V7l-9-5Z"/><path d="M12 8v5"/><circle cx="12" cy="16.3" r="0.6" fill="currentColor"/></svg>`,
  tutor: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.4 8.4 0 0 1-8.8 8.4 8.9 8.9 0 0 1-3.6-.8L3 20l1-4.8A8.4 8.4 0 0 1 21 11.5Z"/></svg>`,
  quiz: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 9h8M8 13h5"/></svg>`,
  assess: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3h6l1 3H8l1-3Z"/><rect x="5" y="6" width="14" height="15" rx="2"/><path d="m9 12 2 2 4-4"/></svg>`,
  materials: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/><path d="M14 2v6h6"/></svg>`,
  graph: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8 7.2 10.5 16M16 7.2 13.5 16M8.5 6h7"/></svg>`,
  analytics: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/></svg>`,
  bell: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>`,
  profile: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4.5 5-6 8-6s6.5 1.5 8 6"/></svg>`,
  settings: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9c.2.6.7 1 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/></svg>`,
  logout: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>`,
  menu: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"/></svg>`,
  students: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 20v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 20v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  review: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>`,
  empty: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>`,
};

function toast(message, type = 'default') {
  let root = document.getElementById('toast-root');
  if (!root) {
    root = document.createElement('div');
    root.id = 'toast-root';
    document.body.appendChild(root);
  }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

function initials(name) {
  if (!name) return '?';
  const parts = name.trim().split(' ');
  return (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase();
}

const STUDENT_NAV = [
  { key: 'dashboard', href: 'dashboard.html', label: 'Dashboard', icon: 'dashboard' },
  { key: 'learning-path', href: 'learning-path.html', label: 'My Learning Path', icon: 'path' },
  { key: 'knowledge-gaps', href: 'knowledge-gaps.html', label: 'Knowledge Gaps', icon: 'gaps' },
  { key: 'ai-tutor', href: 'ai-tutor.html', label: 'AI Tutor', icon: 'tutor' },
  { key: 'quiz-practice', href: 'quiz-practice.html', label: 'Quiz Practice', icon: 'quiz' },
  { key: 'assessments', href: 'assessments.html', label: 'Assessments', icon: 'assess' },
  { key: 'study-materials', href: 'study-materials.html', label: 'Study Materials', icon: 'materials' },
  { key: 'knowledge-graph', href: 'knowledge-graph.html', label: 'Knowledge Graph', icon: 'graph' },
  { key: 'analytics', href: 'analytics.html', label: 'Analytics', icon: 'analytics' },
];
const STUDENT_NAV_BOTTOM = ['dashboard', 'learning-path', 'quiz-practice', 'ai-tutor', 'analytics'];

const TEACHER_NAV = [
  { key: 'teacher-dashboard', href: 'teacher-dashboard.html', label: 'Dashboard', icon: 'dashboard' },
  { key: 'teacher-students', href: 'teacher-students.html', label: 'Students', icon: 'students' },
  { key: 'teacher-analytics', href: 'teacher-analytics.html', label: 'Class Analytics', icon: 'analytics' },
  { key: 'teacher-recommendations', href: 'teacher-recommendations.html', label: 'AI Recommendations', icon: 'review' },
];

function initShell(activeKey) {
  const user = Auth.getUser();
  if (!user) return;
  const isTeacher = user.role === 'teacher';
  const nav = isTeacher ? TEACHER_NAV : STUDENT_NAV;

  const sidebarRoot = document.getElementById('sidebar-root');
  if (sidebarRoot) {
    sidebarRoot.innerHTML = `
      <div class="sidebar-brand"><span class="brand-mark">E</span><span style="font-weight:800">ELEVATE AI</span></div>
      <nav class="sidebar-nav">
        ${nav.map(item => `<a href="${item.href}" class="${item.key === activeKey ? 'active' : ''}">${Icons[item.icon]}<span>${item.label}</span></a>`).join('')}
        <div class="nav-section-label">Account</div>
        <a href="notifications.html" class="${activeKey === 'notifications' ? 'active' : ''}">${Icons.bell}<span>Notifications</span></a>
        <a href="profile.html" class="${activeKey === 'profile' ? 'active' : ''}">${Icons.profile}<span>Profile</span></a>
        <a href="settings.html" class="${activeKey === 'settings' ? 'active' : ''}">${Icons.settings}<span>Settings</span></a>
      </nav>
      <div class="sidebar-footer">
        <a href="#" id="logout-link" style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-radius:8px;color:var(--color-text-secondary);font-weight:600;font-size:14px;">${Icons.logout}<span>Logout</span></a>
      </div>`;
  }

  const topbarRoot = document.getElementById('topbar-root');
  if (topbarRoot) {
    topbarRoot.innerHTML = `
      <button class="hamburger-btn" id="hamburger-btn">${Icons.menu}</button>
      <div></div>
      <div class="topbar-actions">
        <button class="notif-btn" id="notif-bell">${Icons.bell}<span class="notif-dot hidden" id="notif-dot"></span></button>
        <div class="avatar-circle" title="${user.full_name}">${initials(user.full_name)}</div>
      </div>`;
  }

  const bottomRoot = document.getElementById('bottom-nav-root');
  if (bottomRoot && !isTeacher) {
    const items = nav.filter(n => STUDENT_NAV_BOTTOM.includes(n.key));
    bottomRoot.innerHTML = items.map(item => `<a href="${item.href}" class="${item.key === activeKey ? 'active' : ''}">${Icons[item.icon]}<span>${item.label.split(' ')[0]}</span></a>`).join('');
  }

  const overlay = document.getElementById('sidebar-overlay');
  const hamburger = document.getElementById('hamburger-btn');
  if (hamburger) {
    hamburger.addEventListener('click', () => {
      sidebarRoot.classList.toggle('open');
      overlay.classList.toggle('show');
    });
  }
  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebarRoot.classList.remove('open');
      overlay.classList.remove('show');
    });
  }

  const logoutLink = document.getElementById('logout-link');
  if (logoutLink) logoutLink.addEventListener('click', (e) => { e.preventDefault(); Auth.logout(); });

  const bell = document.getElementById('notif-bell');
  if (bell) {
    bell.addEventListener('click', () => { location.href = 'notifications.html'; });
    Api.get('/api/notifications').then(data => {
      const dot = document.getElementById('notif-dot');
      if (dot && data.unread_count > 0) dot.classList.remove('hidden');
    }).catch(() => {});
  }
}

function statusBadge(status) {
  const labelMap = {
    not_started: 'Not Started', in_progress: 'In Progress', developing: 'Developing',
    needs_revision: 'Needs Revision', completed: 'Completed', mastered: 'Mastered',
  };
  return `<span class="badge status-${status}">${labelMap[status] || status}</span>`;
}

function fmtPercent(v) {
  if (v === null || v === undefined) return 'Not enough data';
  return `${Math.round(v)}%`;
}

function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

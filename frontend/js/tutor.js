const urlParams = new URLSearchParams(location.search);
let currentSessionId = null;
let currentTopicId = urlParams.get('topic_id') ? parseInt(urlParams.get('topic_id')) : null;
let currentMaterialId = urlParams.get('material_id') ? parseInt(urlParams.get('material_id')) : null;

async function loadSessions() {
  const list = document.getElementById('sessions-list');
  try {
    const data = await Api.get('/api/tutor/sessions');
    if (!data.sessions.length) {
      list.innerHTML = `<p class="text-sm text-muted">No conversations yet.</p>`;
      return;
    }
    list.innerHTML = data.sessions.map(s => `
      <div class="tutor-session-item ${s.id === currentSessionId ? 'active' : ''}" onclick="openSession(${s.id})">${s.title}</div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<p class="text-sm text-muted">Could not load conversations.</p>`;
  }
}

async function openSession(id) {
  currentSessionId = id;
  loadSessions();
  const container = document.getElementById('messages');
  container.innerHTML = `<div class="skeleton" style="height:40px;margin-bottom:10px"></div>`;
  try {
    const data = await Api.get(`/api/tutor/sessions/${id}/messages`);
    renderMessages(data.messages);
  } catch (e) {
    toast(e.message || 'Could not load conversation', 'error');
  }
}

function newSession() {
  currentSessionId = null;
  document.getElementById('messages').innerHTML = `<div class="empty-state"><p>Ask a question about any topic, or upload study material and I'll ground my answers in it.</p></div>`;
  loadSessions();
}

function renderMessages(messages) {
  const container = document.getElementById('messages');
  if (!messages.length) {
    container.innerHTML = `<div class="empty-state"><p>Ask a question to get started.</p></div>`;
    return;
  }
  container.innerHTML = messages.map(m => `
    <div class="msg-row ${m.role}">
      <div>
        <div class="msg-bubble">${escapeHtml(m.content).replace(/\n/g, '<br>')}</div>
        ${m.grounded_in ? `<div class="grounded-tag">📎 Grounded in: ${m.grounded_in}</div>` : ''}
      </div>
    </div>`).join('');
  container.scrollTop = container.scrollHeight;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function appendMessage(role, content, groundedIn) {
  const container = document.getElementById('messages');
  if (container.querySelector('.empty-state')) container.innerHTML = '';
  const row = document.createElement('div');
  row.className = `msg-row ${role}`;
  row.innerHTML = `<div><div class="msg-bubble">${escapeHtml(content).replace(/\n/g, '<br>')}</div>${groundedIn ? `<div class="grounded-tag">📎 Grounded in: ${groundedIn}</div>` : ''}</div>`;
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

function appendTyping() {
  const container = document.getElementById('messages');
  const row = document.createElement('div');
  row.className = 'msg-row tutor';
  row.id = 'typing-row';
  row.innerHTML = `<div class="msg-bubble typing-dots"><span></span><span></span><span></span></div>`;
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}
function removeTyping() {
  const el = document.getElementById('typing-row');
  if (el) el.remove();
}

async function sendChat(message, actionType) {
  appendMessage('student', message);
  appendTyping();
  const input = document.getElementById('chat-input');
  input.disabled = true;
  try {
    const data = await Api.post('/api/tutor/chat', {
      session_id: currentSessionId, message, action_type: actionType,
      topic_id: currentTopicId, material_id: currentMaterialId,
    });
    currentSessionId = data.session_id;
    removeTyping();
    appendMessage('tutor', data.reply, data.grounded_in);
    loadSessions();
  } catch (e) {
    removeTyping();
    toast(e.message || 'AI Tutor could not respond', 'error');
  } finally {
    input.disabled = false;
    input.focus();
  }
}

function sendMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  sendChat(message, null);
}

function sendAction(actionType) {
  const labels = {
    hint: 'Can you give me a hint?', simpler: 'Can you explain this more simply?',
    example: 'Can you give me an example?', summary: 'Can you summarize this?',
    practice: 'I want to practice this concept.', quiz: 'Generate a quiz on this topic.',
  };
  sendChat(labels[actionType] || 'Help me with this', actionType);
}

loadSessions();

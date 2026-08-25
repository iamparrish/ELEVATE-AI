const canvas = document.getElementById('graph-canvas');
const ctx = canvas.getContext('2d');
const wrap = document.getElementById('graph-wrap');

let graphData = { nodes: [], edges: [] };
let positions = {};
let scale = 1, offsetX = 0, offsetY = 0;
let dragging = false, lastX = 0, lastY = 0;
let selectedNodeId = null;

const STATUS_COLOR = {
  not_started: '#C9C9C6', in_progress: '#3651E3', developing: '#7C5CE0',
  needs_revision: '#B7791F', completed: '#17875B', mastered: '#0E6B45',
};

function resizeCanvas() {
  canvas.width = wrap.clientWidth;
  canvas.height = wrap.clientHeight;
  draw();
}
window.addEventListener('resize', resizeCanvas);

function layoutNodes() {
  const n = graphData.nodes.length;
  const cx = canvas.width / 2, cy = canvas.height / 2;
  const radius = Math.min(cx, cy) - 80;
  graphData.nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / Math.max(1, n);
    positions[node.id] = { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) };
  });
}

function draw() {
  ctx.save();
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.translate(offsetX, offsetY);
  ctx.scale(scale, scale);

  // edges
  ctx.strokeStyle = '#D6D3D1';
  ctx.lineWidth = 1.5;
  graphData.edges.forEach(e => {
    const a = positions[e.source], b = positions[e.target];
    if (!a || !b) return;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  });

  // nodes
  graphData.nodes.forEach(node => {
    const p = positions[node.id];
    if (!p) return;
    const r = 26;
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.fillStyle = STATUS_COLOR[node.status] || '#C9C9C6';
    ctx.fill();
    if (node.id === selectedNodeId) {
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#14213D';
      ctx.stroke();
    }
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 12px Manrope, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(Math.round(node.mastery) + '%', p.x, p.y);

    ctx.fillStyle = '#14213D';
    ctx.font = '600 11px Manrope, sans-serif';
    ctx.fillText(truncate(node.label, 16), p.x, p.y + r + 14);
  });
  ctx.restore();
}

function truncate(s, n) { return s.length > n ? s.slice(0, n - 1) + '…' : s; }

function screenToWorld(sx, sy) {
  return { x: (sx - offsetX) / scale, y: (sy - offsetY) / scale };
}

canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const world = screenToWorld(e.clientX - rect.left, e.clientY - rect.top);
  const hit = graphData.nodes.find(node => {
    const p = positions[node.id];
    return p && Math.hypot(p.x - world.x, p.y - world.y) < 26;
  });
  if (hit) { openNode(hit.id); return; }
  dragging = true; lastX = e.clientX; lastY = e.clientY;
  canvas.style.cursor = 'grabbing';
});
window.addEventListener('mouseup', () => { dragging = false; canvas.style.cursor = 'grab'; });
window.addEventListener('mousemove', (e) => {
  if (!dragging) return;
  offsetX += e.clientX - lastX;
  offsetY += e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  draw();
});
canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  zoomGraph(e.deltaY < 0 ? 1.1 : 0.9);
}, { passive: false });

// touch support
let lastTouchDist = null;
canvas.addEventListener('touchstart', (e) => {
  if (e.touches.length === 1) { dragging = true; lastX = e.touches[0].clientX; lastY = e.touches[0].clientY; }
});
canvas.addEventListener('touchmove', (e) => {
  e.preventDefault();
  if (e.touches.length === 1 && dragging) {
    offsetX += e.touches[0].clientX - lastX;
    offsetY += e.touches[0].clientY - lastY;
    lastX = e.touches[0].clientX; lastY = e.touches[0].clientY;
    draw();
  }
}, { passive: false });
canvas.addEventListener('touchend', () => { dragging = false; });

function zoomGraph(factor) { scale = Math.max(0.4, Math.min(2.5, scale * factor)); draw(); }
function resetGraph() { scale = 1; offsetX = 0; offsetY = 0; draw(); }

async function openNode(topicId) {
  selectedNodeId = topicId;
  draw();
  const panel = document.getElementById('node-panel');
  panel.classList.add('open');
  panel.innerHTML = `<div class="skeleton" style="height:100px"></div>`;
  try {
    const detail = await Api.get(`/api/knowledge-graph/node/${topicId}`);
    panel.innerHTML = `
      <button class="btn btn-ghost btn-sm" onclick="closeNodePanel()" style="margin-bottom:12px">✕ Close</button>
      <h3>${detail.topic}</h3>
      ${statusBadge(detail.status)}
      <p class="text-sm" style="margin-top:12px">${detail.description || ''}</p>
      <div class="card" style="padding:14px;margin:14px 0">
        <span class="text-xs text-muted font-bold">MASTERY ESTIMATE</span>
        <div class="font-bold" style="font-size:22px">${detail.has_data ? Math.round(detail.mastery) + '%' : 'Not started'}</div>
      </div>
      ${detail.prerequisites.length ? `<div style="margin-bottom:12px"><span class="text-xs text-muted font-bold">PREREQUISITES</span><br>${detail.prerequisites.map(p => `<span class="badge badge-neutral" style="margin:4px 4px 0 0">${p}</span>`).join('')}</div>` : ''}
      ${detail.related_concepts.length ? `<div style="margin-bottom:12px"><span class="text-xs text-muted font-bold">RELATED CONCEPTS</span><br>${detail.related_concepts.map(p => `<span class="badge badge-violet" style="margin:4px 4px 0 0">${p}</span>`).join('')}</div>` : ''}
      ${detail.common_mistakes.length ? `<div style="margin-bottom:12px"><span class="text-xs text-muted font-bold">COMMON MISTAKES</span>${detail.common_mistakes.map(m => `<p class="text-sm">• ${m}</p>`).join('')}</div>` : ''}
      <div style="margin-bottom:14px"><span class="text-xs text-muted font-bold">RECOMMENDED PRACTICE</span>${detail.recommended_actions.map(a => `<p class="text-sm">✓ ${a}</p>`).join('')}</div>
      <a href="quiz-practice.html?mode=custom&topic_id=${topicId}" class="btn btn-primary btn-block btn-sm">Practice This Topic</a>
    `;
  } catch (e) {
    panel.innerHTML = `<p class="text-muted">Could not load topic details.</p>`;
  }
}
function closeNodePanel() { document.getElementById('node-panel').classList.remove('open'); selectedNodeId = null; draw(); }

async function loadGraph() {
  try {
    graphData = await Api.get('/api/knowledge-graph');
    resizeCanvas();
    if (!graphData.nodes.length) {
      wrap.innerHTML = `<div class="empty-state" style="padding-top:100px">${Icons.empty}<h4>No knowledge graph yet</h4><p>Complete onboarding to build your personalized knowledge graph.</p></div>`;
      return;
    }
    layoutNodes();
    draw();
  } catch (e) {
    wrap.innerHTML = `<div class="empty-state" style="padding-top:100px">${Icons.empty}<p>Could not load knowledge graph.</p></div>`;
  }
}

loadGraph();

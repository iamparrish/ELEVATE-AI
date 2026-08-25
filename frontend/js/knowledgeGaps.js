async function loadGaps() {
  const content = document.getElementById('page-content');
  let data;
  try {
    data = await Api.get('/api/student/knowledge-gaps');
  } catch (e) {
    content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>Could not load knowledge gaps</h4><p>${e.message}</p></div>`;
    return;
  }

  const gaps = data.gaps.filter(g => g.status !== 'resolved');
  const resolved = data.gaps.filter(g => g.status === 'resolved');

  const header = `<h2>Knowledge Gaps</h2><p class="text-muted" style="margin-bottom:20px">Topics where your recent performance suggests extra attention is needed - detected automatically from your quiz and assessment history.</p>`;

  if (!gaps.length) {
    content.innerHTML = header + `<div class="empty-state">${Icons.empty}<h4>No active knowledge gaps</h4><p>${resolved.length ? 'Great work - your previous gaps have been resolved through practice.' : 'Keep practicing to build a picture of your strengths and weak spots.'}</p></div>`;
    return;
  }

  const trendIcon = { improving: '↑ Improving', declining: '↓ Declining', stable: '→ Stable' };
  const trendClass = { improving: 'trend-up', declining: 'trend-down', stable: 'trend-flat' };

  content.innerHTML = header + gaps.map(g => `
    <div class="card gap-card">
      <div class="flex justify-between items-center" style="margin-bottom:10px">
        <div>
          <h3 style="margin-bottom:4px">${g.topic_name}</h3>
          <span class="badge ${g.status === 'gap' ? 'badge-danger' : 'badge-warning'}">${g.status === 'gap' ? 'Knowledge Gap' : 'Watch'}</span>
          <span class="${trendClass[g.trend]} text-sm" style="margin-left:8px;font-weight:700">${trendIcon[g.trend]}</span>
        </div>
        <div style="text-align:right">
          <div class="font-bold" style="font-size:22px">${Math.round(g.mastery)}%</div>
          <span class="text-xs text-muted">mastery estimate</span>
        </div>
      </div>
      <div class="progress-track" style="margin-bottom:14px"><div class="progress-fill warning" style="width:${g.mastery}%"></div></div>
      ${g.common_mistakes.length ? `<div style="margin-bottom:12px"><span class="text-xs text-muted font-bold">RECENT MISTAKES</span><br>${g.common_mistakes.map(m => `<span class="mistake-tag">${m}</span>`).join('')}</div>` : ''}
      <div style="margin-bottom:14px">
        <span class="text-xs text-muted font-bold">RECOMMENDED NEXT ACTIONS</span>
        ${g.recommended_actions.map(a => `<div class="action-item">✓ ${a}</div>`).join('')}
      </div>
      <div class="flex gap-12">
        <a href="quiz-practice.html?mode=weak_area&topic_id=${g.topic_id}" class="btn btn-primary btn-sm">Practice This Topic</a>
        <a href="ai-tutor.html?topic_id=${g.topic_id}" class="btn btn-secondary btn-sm">Ask AI Tutor</a>
      </div>
    </div>`).join('');
}

loadGaps();

function drawBarChart(canvas, labels, values, color) {
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = w * dpr; canvas.height = h * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  const max = Math.max(1, ...values);
  const padBottom = 24, padTop = 10;
  const barW = (w / values.length) * 0.55;
  const gap = (w / values.length) * 0.45;
  values.forEach((v, i) => {
    const barH = ((h - padBottom - padTop) * v) / max;
    const x = i * (barW + gap) + gap / 2;
    const y = h - padBottom - barH;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(x, y, barW, barH, 4) : ctx.rect(x, y, barW, barH);
    ctx.fill();
    ctx.fillStyle = '#8B8B93';
    ctx.font = '10px Manrope, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(labels[i], x + barW / 2, h - 8);
  });
}

function drawLineChart(canvas, labels, values, color) {
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = w * dpr; canvas.height = h * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  const max = 100, padBottom = 24, padTop = 14, padX = 20;
  const stepX = values.length > 1 ? (w - padX * 2) / (values.length - 1) : 0;

  ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.beginPath();
  values.forEach((v, i) => {
    const x = padX + i * stepX;
    const y = padTop + ((h - padTop - padBottom) * (max - v)) / max;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();

  values.forEach((v, i) => {
    const x = padX + i * stepX;
    const y = padTop + ((h - padTop - padBottom) * (max - v)) / max;
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill();
  });
}

async function loadAnalytics() {
  const content = document.getElementById('page-content');
  let data;
  try {
    data = await Api.get('/api/analytics');
  } catch (e) {
    content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>Could not load analytics</h4><p>${e.message}</p></div>`;
    return;
  }

  if (!data.has_data) {
    content.innerHTML = `
      <h2>Progress & Analytics</h2>
      <div class="empty-state">${Icons.empty}<h4>Keep learning to unlock your progress insights</h4><p>${data.message}</p>
      <a href="quiz-practice.html" class="btn btn-primary">Start Practicing</a></div>`;
    return;
  }

  content.innerHTML = `
    <h2>Progress & Analytics</h2>
    <p class="text-muted" style="margin-bottom:20px">Every chart is calculated from your real activity - never hardcoded.</p>

    <div class="stat-grid" style="margin-bottom:20px">
      <div class="card stat-card"><div class="stat-label">Overall Progress</div><div class="stat-value">${Math.round(data.overall_progress)}%</div></div>
      <div class="card stat-card"><div class="stat-label">Overall Mastery</div><div class="stat-value">${Math.round(data.overall_mastery)}%</div></div>
      <div class="card stat-card"><div class="stat-label">Total Quizzes</div><div class="stat-value">${data.total_quizzes}</div></div>
      <div class="card stat-card"><div class="stat-label">Improvement</div><div class="stat-value">${data.improvement_vs_earlier === null ? '—' : (data.improvement_vs_earlier >= 0 ? '+' : '') + data.improvement_vs_earlier + '%'}</div></div>
    </div>

    <div class="two-col" style="margin-bottom:20px">
      <div class="card chart-card">
        <h3>Weekly Activity</h3>
        <canvas class="chart-canvas" id="weekly-chart"></canvas>
      </div>
      <div class="card chart-card">
        <h3>Quiz Accuracy Trend</h3>
        ${data.quiz_accuracy_trend.length ? `<canvas class="chart-canvas" id="accuracy-chart"></canvas>` : `<div class="empty-state" style="padding:30px">${Icons.empty}<p>Take a few quizzes to see your trend.</p></div>`}
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom:20px">
      <h3>Topic Mastery</h3>
      ${data.topic_mastery.length ? data.topic_mastery.map(t => `
        <div style="margin-bottom:10px">
          <div class="flex justify-between text-sm" style="margin-bottom:4px"><span>${t.topic}</span><span class="font-bold">${t.mastery}%</span></div>
          <div class="progress-track"><div class="progress-fill ${t.status === 'needs_revision' ? 'warning' : (t.status === 'mastered' || t.status === 'completed') ? 'success' : ''}" style="width:${t.mastery}%"></div></div>
        </div>`).join('') : `<p class="text-muted text-sm">No topic data yet.</p>`}
    </div>

    <div class="card card-pad">
      <h3>Weak Areas</h3>
      ${data.weak_areas.length ? data.weak_areas.map(t => `<div class="topic-result-row"><span>${t.topic}</span><span class="badge badge-warning">${t.mastery}%</span></div>`).join('') : `<p class="text-muted text-sm">No weak areas detected right now.</p>`}
    </div>
  `;

  const weeklyCanvas = document.getElementById('weekly-chart');
  if (weeklyCanvas) {
    const labels = data.weekly_activity.map(d => new Date(d.date).toLocaleDateString(undefined, { weekday: 'short' }));
    drawBarChart(weeklyCanvas, labels, data.weekly_activity.map(d => d.activity_count), '#3651E3');
  }
  const accCanvas = document.getElementById('accuracy-chart');
  if (accCanvas) {
    drawLineChart(accCanvas, data.quiz_accuracy_trend.map(d => `#${d.attempt}`), data.quiz_accuracy_trend.map(d => d.accuracy), '#7C5CE0');
  }
}

loadAnalytics();

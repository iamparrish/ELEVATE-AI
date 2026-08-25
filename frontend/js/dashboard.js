async function loadDashboard() {
  const content = document.getElementById('page-content');
  let data;
  try {
    data = await Api.get('/api/student/dashboard');
  } catch (e) {
    content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>Could not load your dashboard</h4><p>${e.message || 'Please check your connection and try again.'}</p><button class="btn btn-primary" onclick="loadDashboard()">Retry</button></div>`;
    return;
  }

  const masteryText = data.overall_mastery === null ? 'Not enough data yet' : `${Math.round(data.overall_mastery)}%`;
  const progressText = data.overall_progress === null ? '0%' : `${Math.round(data.overall_progress)}%`;

  content.innerHTML = `
    <div class="greeting-bar">
      <h2>${data.greeting} 👋</h2>
      <p class="text-muted">${data.has_learning_path ? `You have ${data.topics_total} topics in your personalized path.` : 'Your learning path will appear here once you complete onboarding.'}</p>
    </div>

    <div class="stat-grid" style="margin-bottom:24px">
      <div class="card stat-card">
        <div class="stat-label">${Icons.analytics} Overall Mastery</div>
        <div class="stat-value">${masteryText}</div>
        <div class="progress-track"><div class="progress-fill" style="width:${data.overall_mastery || 0}%"></div></div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">${Icons.path} Learning Progress</div>
        <div class="stat-value">${progressText}</div>
        <div class="progress-track"><div class="progress-fill success" style="width:${data.overall_progress || 0}%"></div></div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">🔥 Learning Streak</div>
        <div class="stat-value">${data.current_streak} day${data.current_streak === 1 ? '' : 's'}</div>
        <span class="text-xs text-muted">${data.current_streak > 0 ? 'Keep it going!' : 'Complete an activity today to start your streak'}</span>
      </div>
      <div class="card stat-card">
        <div class="stat-label">${Icons.assess} Topics Completed</div>
        <div class="stat-value">${data.topics_completed}/${data.topics_total}</div>
        <span class="text-xs text-muted">${data.active_knowledge_gaps} topic(s) need attention</span>
      </div>
    </div>

    ${data.continue_learning ? `
    <div class="card continue-card" style="margin-bottom:24px">
      <div>
        <div class="text-xs text-muted font-bold" style="margin-bottom:4px">CONTINUE LEARNING</div>
        <h3 style="margin-bottom:4px">${data.continue_learning.topic_name}</h3>
        ${statusBadge(data.continue_learning.status)}
      </div>
      <a class="btn btn-primary" href="learning-path.html">Continue</a>
    </div>` : ''}

    <div class="two-col" style="margin-bottom:24px">
      <div class="card card-pad">
        <div class="section-title"><h3>${Icons.tutor} AI Recommendations</h3><a href="learning-path.html" class="text-sm" style="color:var(--color-primary);font-weight:600">View path →</a></div>
        ${data.recommendations.length ? data.recommendations.map(r => `
          <div class="rec-item">
            <div class="icon-circle ${r.type === 'revision' ? 'warning' : r.type === 'advance' ? 'success' : 'primary'}" style="width:34px;height:34px">${Icons.gaps}</div>
            <div class="rec-body"><strong>${r.title}</strong><span>${r.reason}</span></div>
          </div>`).join('') : `<div class="empty-state" style="padding:24px">${Icons.empty}<p>Keep learning to unlock personalized recommendations.</p></div>`}
      </div>
      <div class="card card-pad">
        <div class="section-title"><h3>Recent Activity</h3></div>
        ${data.recent_activity.length ? data.recent_activity.map(a => `
          <div class="activity-item"><span class="badge badge-neutral">${a.type.replace(/_/g, ' ')}</span><span class="text-muted">${timeAgo(a.at)}</span></div>
        `).join('') : `<p class="text-muted text-sm">No activity yet. Start a quiz or open a topic to see it here.</p>`}
      </div>
    </div>

    <div class="card card-pad">
      <div class="section-title"><h3>Recent Quiz Performance</h3><a href="quiz-practice.html" class="text-sm" style="color:var(--color-primary);font-weight:600">Practice more →</a></div>
      ${data.recent_quizzes.length ? `
        <div class="flex gap-16" style="flex-wrap:wrap">
          ${data.recent_quizzes.map(q => `
            <div class="card" style="padding:14px 18px;min-width:120px">
              <div class="text-xs text-muted">${timeAgo(q.at)}</div>
              <div class="font-bold" style="font-size:20px">${q.accuracy}%</div>
            </div>`).join('')}
        </div>` : `<div class="empty-state" style="padding:24px">${Icons.empty}<h4>No quizzes yet</h4><p>Take your first quiz to see performance trends here.</p><a href="quiz-practice.html" class="btn btn-primary btn-sm">Start Quiz Practice</a></div>`}
    </div>
  `;
}

loadDashboard();

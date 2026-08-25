async function loadPath() {
  const content = document.getElementById('page-content');
  let data;
  try {
    data = await Api.get('/api/student/learning-path');
  } catch (e) {
    content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>Could not load your learning path</h4><p>${e.message}</p></div>`;
    return;
  }

  if (!data.path.length) {
    content.innerHTML = `
      <h2>My Learning Path</h2>
      <div class="empty-state">${Icons.empty}<h4>No learning path yet</h4><p>Complete onboarding to generate your personalized roadmap.</p>
      <a href="onboarding.html" class="btn btn-primary">Start Onboarding</a></div>`;
    return;
  }

  const bySubject = {};
  data.path.forEach(node => {
    bySubject[node.subject_name] = bySubject[node.subject_name] || [];
    bySubject[node.subject_name].push(node);
  });

  content.innerHTML = `
    <h2>My Learning Path</h2>
    <p class="text-muted" style="margin-bottom:24px">Your roadmap adapts automatically based on quizzes, assessments and knowledge gaps.</p>
    ${Object.entries(bySubject).map(([subject, nodes]) => `
      <div class="card card-pad" style="margin-bottom:20px">
        <h3 style="margin-bottom:16px">${subject}</h3>
        <div class="path-track">
          ${nodes.map(n => `
            <div class="path-node ${n.status}">
              <div class="card path-card card-hover">
                <div class="flex justify-between items-center" style="margin-bottom:8px">
                  <strong>${n.topic_name}</strong>
                  ${statusBadge(n.status)}
                </div>
                <div class="progress-track" style="margin-bottom:10px"><div class="progress-fill ${n.status === 'needs_revision' ? 'warning' : (n.status === 'mastered' || n.status === 'completed') ? 'success' : ''}" style="width:${n.mastery}%"></div></div>
                <div class="flex justify-between items-center">
                  <span class="text-xs text-muted">${n.has_data ? `${n.mastery}% mastery estimate · ${n.attempts} attempt(s)` : 'Not started yet'}</span>
                  <a href="quiz-practice.html?topic_id=${n.topic_id}" class="btn btn-secondary btn-sm">Practice</a>
                </div>
              </div>
            </div>`).join('')}
        </div>
      </div>`).join('')}
  `;
}

loadPath();

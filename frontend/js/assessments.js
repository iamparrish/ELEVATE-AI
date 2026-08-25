let assessTopics = [];
let pendingType = null;

async function loadTopicsForBuilder() {
  try {
    const path = await Api.get('/api/student/learning-path');
    assessTopics = path.path;
    const subjectSelect = document.getElementById('tb-subject');
    const subjects = [...new Set(assessTopics.map(t => t.subject_name))];
    subjectSelect.innerHTML = subjects.map(s => `<option>${s}</option>`).join('');
    populateAssessTopics();
    subjectSelect.addEventListener('change', populateAssessTopics);
  } catch (e) { /* ignore, builder just won't populate */ }
}
function populateAssessTopics() {
  const subject = document.getElementById('tb-subject').value;
  const topicSelect = document.getElementById('tb-topic');
  const topics = assessTopics.filter(t => t.subject_name === subject);
  topicSelect.innerHTML = topics.map(t => `<option value="${t.topic_id}">${t.topic_name}</option>`).join('');
}

function showTopicBuilder(type) {
  pendingType = type;
  document.getElementById('topic-builder-panel').style.display = 'block';
  document.getElementById('topic-builder-panel').scrollIntoView({ behavior: 'smooth' });
}

async function buildTopicAssessment() {
  const topicId = parseInt(document.getElementById('tb-topic').value);
  const num = parseInt(document.getElementById('tb-num').value) || 8;
  await createAssessment(pendingType || 'topic_test', { topic_id: topicId, num_questions: num });
}

async function buildAssessment(type) {
  await createAssessment(type, { num_questions: 8 });
}

async function createAssessment(type, extra) {
  try {
    const data = await Api.post('/api/assessments/build', { assessment_type: type, ...extra });
    location.href = `assessment.html?assessment_id=${data.assessment_id}`;
  } catch (e) {
    toast(e.message || 'Could not build assessment', 'error');
  }
}

async function loadAssessments() {
  const container = document.getElementById('assessments-list');
  try {
    const data = await Api.get('/api/assessments');
    if (!data.assessments.length) {
      container.innerHTML = `<div class="empty-state">${Icons.empty}<p>No assessments taken yet.</p></div>`;
      return;
    }
    container.innerHTML = data.assessments.map(a => `
      <div class="card" style="padding:14px 18px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center">
        <div><strong>${a.title}</strong><div class="text-xs text-muted">${a.num_questions} questions · ${new Date(a.created_at).toLocaleDateString()}</div></div>
        <div>${a.completed ? `<span class="badge badge-primary">${a.score}%</span>` : `<a href="assessment.html?assessment_id=${a.id}" class="btn btn-secondary btn-sm">Resume</a>`}</div>
      </div>`).join('');
  } catch (e) {
    container.innerHTML = `<p class="text-muted text-sm">Could not load assessments.</p>`;
  }
}

loadTopicsForBuilder();
loadAssessments();

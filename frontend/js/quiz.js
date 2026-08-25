let subjectsCatalogCache = null;
let allTopics = [];

const urlP = new URLSearchParams(location.search);

async function loadCatalogForCustom() {
  try {
    const data = await Api.get('/api/student/subjects-catalog');
    subjectsCatalogCache = data;
    const path = await Api.get('/api/student/learning-path');
    allTopics = path.path;

    const subjectSelect = document.getElementById('cq-subject');
    const subjectNames = [...new Set(allTopics.map(t => t.subject_name))];
    subjectSelect.innerHTML = subjectNames.map(s => `<option>${s}</option>`).join('');
    populateTopics();
    subjectSelect.addEventListener('change', populateTopics);
  } catch (e) {
    toast('Could not load subjects', 'error');
  }
}

function populateTopics() {
  const subject = document.getElementById('cq-subject').value;
  const topicSelect = document.getElementById('cq-topic');
  const topics = allTopics.filter(t => t.subject_name === subject);
  topicSelect.innerHTML = topics.map(t => `<option value="${t.topic_id}">${t.topic_name}</option>`).join('');
}

async function startCustomQuiz() {
  const topicId = parseInt(document.getElementById('cq-topic').value);
  const difficulty = document.getElementById('cq-difficulty').value;
  const num = parseInt(document.getElementById('cq-num').value) || 5;
  await launchQuiz({ quiz_mode: 'custom', topic_id: topicId, difficulty, num_questions: num });
}

async function openCustomQuiz(mode) {
  await launchQuiz({ quiz_mode: mode, difficulty: 'medium', num_questions: 5 });
}

function showTopicPicker() {
  document.getElementById('custom-quiz-panel').scrollIntoView({ behavior: 'smooth' });
}

async function openMistakes() {
  await launchQuiz({ quiz_mode: 'mistakes', num_questions: 10 });
}

async function launchQuiz(body) {
  try {
    const data = await Api.post('/api/quizzes/generate', body);
    location.href = `quiz.html?quiz_id=${data.quiz_id}`;
  } catch (e) {
    toast(e.message || 'Could not generate quiz', 'error');
  }
}

async function loadRecentQuizzes() {
  const container = document.getElementById('recent-quizzes');
  try {
    const data = await Api.get('/api/quizzes');
    if (!data.quizzes.length) {
      container.innerHTML = `<div class="empty-state">${Icons.empty}<p>No quizzes taken yet.</p></div>`;
      return;
    }
    container.innerHTML = data.quizzes.map(q => `
      <div class="card" style="padding:14px 18px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center">
        <div><strong>${q.title}</strong><div class="text-xs text-muted">${new Date(q.created_at).toLocaleDateString()} · ${q.difficulty}</div></div>
        <div>${q.status === 'completed' ? `<span class="badge badge-primary">${q.accuracy}%</span>` : `<a href="quiz.html?quiz_id=${q.id}" class="btn btn-secondary btn-sm">Resume</a>`}</div>
      </div>`).join('');
  } catch (e) {
    container.innerHTML = `<p class="text-muted text-sm">Could not load recent quizzes.</p>`;
  }
}

if (urlP.get('mode') && urlP.get('topic_id')) {
  launchQuiz({ quiz_mode: urlP.get('mode'), topic_id: parseInt(urlP.get('topic_id')), difficulty: 'easy', num_questions: 5 });
} else {
  loadCatalogForCustom();
  loadRecentQuizzes();
}

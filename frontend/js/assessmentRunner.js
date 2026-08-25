const ap = new URLSearchParams(location.search);
const assessmentId = ap.get('assessment_id');

let aTitle = '';
let aQuestions = [];
let aIndex = 0;
const aSelections = {};
const aMarked = {};
let timeLimitSeconds = 20 * 60;
let remainingSeconds = timeLimitSeconds;
let timerInterval = null;

async function loadAssessment() {
  const content = document.getElementById('page-content');
  try {
    const data = await Api.get(`/api/assessments/${assessmentId}`);
    aTitle = data.title;
    aQuestions = data.questions;
    timeLimitSeconds = data.time_limit_minutes * 60;
    remainingSeconds = timeLimitSeconds;
    if (!aQuestions.length) {
      content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>No questions available</h4><a href="assessments.html" class="btn btn-primary">Back to Assessments</a></div>`;
      return;
    }
    startTimer();
    renderAssessment();
  } catch (e) {
    content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>Could not load assessment</h4><p>${e.message}</p></div>`;
  }
}

function startTimer() {
  timerInterval = setInterval(() => {
    remainingSeconds--;
    const el = document.getElementById('assess-timer');
    if (el) el.textContent = formatTime(remainingSeconds);
    if (remainingSeconds <= 0) {
      clearInterval(timerInterval);
      submitAssessment();
    }
  }, 1000);
}
function formatTime(s) {
  const m = Math.floor(s / 60), sec = s % 60;
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

function renderAssessment() {
  const content = document.getElementById('page-content');
  const q = aQuestions[aIndex];
  const selected = aSelections[q.question_id];

  content.innerHTML = `
    <div class="quiz-header">
      <div><strong>${aTitle}</strong><div class="text-xs text-muted">Question ${aIndex + 1} of ${aQuestions.length}</div></div>
      <span class="quiz-timer" id="assess-timer">${formatTime(remainingSeconds)}</span>
    </div>

    <div class="flex gap-8" style="flex-wrap:wrap;margin-bottom:18px">
      ${aQuestions.map((qq, i) => `
        <div class="q-nav-dot ${i === aIndex ? 'current' : ''} ${aMarked[qq.question_id] ? 'review' : aSelections[qq.question_id] !== undefined ? 'answered' : ''}" onclick="jumpTo(${i})">${i + 1}</div>
      `).join('')}
    </div>

    <div class="card question-card">
      <span class="badge badge-neutral" style="margin-bottom:10px">${q.difficulty}</span>
      <h3>${q.question_text}</h3>
      <div>
        ${q.options.map((opt, i) => `
          <div class="option-row ${selected === i ? 'selected' : ''}" onclick="selectAssessOption(${q.question_id}, ${i})">
            <span class="option-letter">${String.fromCharCode(65 + i)}</span><span>${opt}</span>
          </div>`).join('')}
      </div>
      <button class="btn btn-ghost btn-sm" style="margin-top:10px" onclick="toggleMark(${q.question_id})">
        ${aMarked[q.question_id] ? '✓ Marked for Review' : '🚩 Mark for Review'}
      </button>
    </div>

    <div class="quiz-nav-row">
      <button class="btn btn-secondary" onclick="prevAssess()" ${aIndex === 0 ? 'disabled' : ''}>Previous</button>
      ${aIndex === aQuestions.length - 1
        ? `<button class="btn btn-primary" onclick="submitAssessment()">Submit</button>`
        : `<button class="btn btn-primary" onclick="nextAssess()">Next</button>`}
    </div>
  `;
}

function selectAssessOption(qid, idx) { aSelections[qid] = idx; renderAssessment(); }
function toggleMark(qid) { aMarked[qid] = !aMarked[qid]; renderAssessment(); }
function jumpTo(i) { aIndex = i; renderAssessment(); }
function nextAssess() { aIndex++; renderAssessment(); }
function prevAssess() { aIndex--; renderAssessment(); }

async function submitAssessment() {
  clearInterval(timerInterval);
  const answers = aQuestions.map(q => ({
    question_id: q.question_id,
    selected_index: aSelections[q.question_id] !== undefined ? aSelections[q.question_id] : null,
    topic_id: q.topic_id,
    marked_for_review: !!aMarked[q.question_id],
  }));
  const content = document.getElementById('page-content');
  content.innerHTML = `<div class="card card-pad" style="text-align:center"><p class="text-muted">Scoring your assessment...</p></div>`;
  try {
    const result = await Api.post(`/api/assessments/${assessmentId}/submit`, { answers });
    sessionStorage.setItem('elevate_last_result', JSON.stringify({ ...result, title: aTitle, type: 'assessment' }));
    location.href = 'results.html';
  } catch (e) {
    toast(e.message || 'Could not submit assessment', 'error');
  }
}

loadAssessment();

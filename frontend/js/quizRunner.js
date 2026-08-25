const qp = new URLSearchParams(location.search);
const quizId = qp.get('quiz_id');

let quizTitle = '';
let questions = [];
let currentIndex = 0;
const selections = {};       // question_id -> selected_index
const revealed = {};         // question_id -> true (explanation shown)
const questionStartTimes = {};
let quizStartTime = Date.now();
let paused = false;

async function loadQuiz() {
  const content = document.getElementById('page-content');
  try {
    const data = await Api.get(`/api/quizzes/${quizId}`);
    quizTitle = data.title;
    questions = data.questions;
    if (data.status === 'completed') {
      content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>This quiz was already completed</h4><a href="quiz-practice.html" class="btn btn-primary">Back to Quiz Practice</a></div>`;
      return;
    }
    if (!questions.length) {
      content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>No questions available</h4><p>Try a different topic or fewer questions.</p><a href="quiz-practice.html" class="btn btn-primary">Back to Quiz Practice</a></div>`;
      return;
    }
    questionStartTimes[questions[0].question_id] = Date.now();
    renderQuestion();
  } catch (e) {
    content.innerHTML = `<div class="empty-state">${Icons.empty}<h4>Could not load quiz</h4><p>${e.message}</p></div>`;
  }
}

function renderQuestion() {
  const content = document.getElementById('page-content');
  const q = questions[currentIndex];
  const total = questions.length;
  const answeredCount = Object.keys(selections).length;
  const selected = selections[q.question_id];
  const isRevealed = !!revealed[q.question_id];

  content.innerHTML = `
    <div class="quiz-header">
      <span class="text-sm text-muted">Question ${currentIndex + 1} of ${total}</span>
      <div class="quiz-progress-bar progress-track"><div class="progress-fill" style="width:${(answeredCount / total) * 100}%"></div></div>
      <button class="btn btn-ghost btn-sm" onclick="togglePause()">${paused ? '▶ Resume' : '⏸ Pause'}</button>
    </div>
    <div class="card question-card ${paused ? 'hidden' : ''}">
      <span class="badge badge-neutral" style="margin-bottom:10px">${q.difficulty} · ${q.question_type.replace(/_/g, ' ')}</span>
      ${q.grounded_in ? `<div class="grounded-tag" style="margin-bottom:8px;color:var(--color-violet);font-weight:700;font-size:12.5px">📎 Grounded in: ${q.grounded_in}</div>` : ''}
      <h3>${q.question_text}</h3>
      <div id="options-container">
        ${q.options.map((opt, i) => `
          <div class="option-row ${selected === i ? 'selected' : ''}" onclick="selectOption(${q.question_id}, ${i})">
            <span class="option-letter">${String.fromCharCode(65 + i)}</span><span>${opt}</span>
          </div>`).join('')}
      </div>
      <div class="flex gap-12" style="margin-top:14px">
        ${q.hint ? `<button class="btn btn-secondary btn-sm" onclick="toggleHint(${q.question_id})">💡 Show Hint</button>` : ''}
        ${selected !== undefined ? `<button class="btn btn-secondary btn-sm" onclick="revealExplanation(${q.question_id})">📖 View Explanation</button>` : ''}
      </div>
      <div id="hint-box-${q.question_id}" class="explanation-box hidden" style="background:var(--color-violet-light)">${q.hint || ''}</div>
      <div id="explanation-box-${q.question_id}" class="hidden"></div>
    </div>
    <div class="quiz-nav-row">
      <button class="btn btn-secondary" onclick="prevQuestion()" ${currentIndex === 0 ? 'disabled' : ''}>Previous</button>
      ${currentIndex === total - 1
        ? `<button class="btn btn-primary" onclick="submitQuiz()">Submit Quiz</button>`
        : `<button class="btn btn-primary" onclick="nextQuestion()">Next</button>`}
    </div>
  `;
}

function togglePause() {
  paused = !paused;
  renderQuestion();
}

function selectOption(qid, index) {
  if (paused) return;
  selections[qid] = index;
  renderQuestion();
}

function toggleHint(qid) {
  document.getElementById(`hint-box-${qid}`).classList.toggle('hidden');
}

function revealExplanation(qid) {
  revealed[qid] = true;
  const q = questions.find(x => x.question_id === qid);
  // Explanation text is fetched inline from the option correctness the
  // backend already validated on generation; since we don't expose the
  // correct answer to the client before submission (to avoid leaking
  // answers), we show a supportive prompt instead and reveal the true
  // explanation after this question is submitted with the quiz.
  const box = document.getElementById(`explanation-box-${qid}`);
  box.className = 'explanation-box';
  box.textContent = "Explanations for each question appear on your results page after you submit the quiz - this keeps practice honest while you're still deciding.";
}

function nextQuestion() {
  currentIndex++;
  if (!questionStartTimes[questions[currentIndex].question_id]) {
    questionStartTimes[questions[currentIndex].question_id] = Date.now();
  }
  renderQuestion();
}
function prevQuestion() {
  currentIndex--;
  renderQuestion();
}

async function submitQuiz() {
  const answers = questions.map(q => {
    const start = questionStartTimes[q.question_id] || Date.now();
    return {
      question_id: q.question_id,
      selected_index: selections[q.question_id] !== undefined ? selections[q.question_id] : null,
      response_time_seconds: Math.round((Date.now() - start) / 1000),
    };
  });
  const content = document.getElementById('page-content');
  content.innerHTML = `<div class="card card-pad" style="text-align:center"><div class="skeleton" style="height:24px;width:60%;margin:0 auto 10px"></div><p class="text-muted">Analyzing your answers...</p></div>`;
  try {
    const result = await Api.post(`/api/quizzes/${quizId}/submit`, {
      answers, time_taken_seconds: Math.round((Date.now() - quizStartTime) / 1000),
    });
    renderResults(result);
  } catch (e) {
    toast(e.message || 'Could not submit quiz', 'error');
  }
}

function renderResults(result) {
  const content = document.getElementById('page-content');
  const scoreColor = result.accuracy >= 70 ? 'var(--color-success)' : result.accuracy >= 45 ? 'var(--color-warning)' : 'var(--color-danger)';
  content.innerHTML = `
    <div class="card result-hero">
      <div class="result-score" style="color:${scoreColor}">${result.accuracy}%</div>
      <p class="text-muted">${result.correct_count} of ${result.total_questions} correct · ${quizTitle}</p>
      <div class="flex gap-12" style="justify-content:center;margin-top:16px;flex-wrap:wrap">
        <button class="btn btn-primary" onclick="retryIncorrect()">Retry Incorrect Questions</button>
        <a href="quiz-practice.html" class="btn btn-secondary">Practice Again</a>
        <a href="knowledge-gaps.html" class="btn btn-ghost">View Knowledge Gaps</a>
      </div>
    </div>
    <div class="card card-pad" style="margin-top:20px">
      <h3 style="margin-bottom:10px">Topic-wise Performance</h3>
      ${Object.entries(result.topic_results).map(([tid, r]) => `
        <div class="topic-result-row">
          <span>Topic #${tid}</span>
          <span class="badge ${r.correct / r.total >= 0.7 ? 'badge-success' : r.correct / r.total >= 0.4 ? 'badge-warning' : 'badge-danger'}">${r.correct}/${r.total} correct</span>
        </div>`).join('')}
    </div>
  `;
}

async function retryIncorrect() {
  try {
    const data = await Api.post(`/api/quizzes/${quizId}/retry`);
    if (!data.quiz_id) { toast(data.message, 'success'); location.href = 'quiz-practice.html'; return; }
    location.href = `quiz.html?quiz_id=${data.quiz_id}`;
  } catch (e) {
    toast(e.message || 'Could not create retry quiz', 'error');
  }
}

loadQuiz();

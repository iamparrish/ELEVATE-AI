Auth.requireRole('student');

let currentStep = 0;
const steps = ['step-academic', 'step-subjects', 'step-goals', 'step-prefs', 'step-diagnostic', 'step-done'];
let catalog = { subjects: [], goals: [], preferences: [] };
let selectedSubjects = [];
let selectedGoals = [];
let selectedPrefs = [];
let diagnosticQuestions = [];
let diagnosticAnswers = {};

function renderStepIndicator() {
  const el = document.getElementById('step-indicator');
  el.innerHTML = steps.slice(0, 5).map((_, i) => `<div class="dot ${i <= currentStep ? 'done' : ''}"></div>`).join('');
}

function showStep(index) {
  steps.forEach((id, i) => {
    document.getElementById(id).classList.toggle('hidden', i !== index);
  });
  renderStepIndicator();
}

function goStep(delta) {
  if (delta > 0 && currentStep === 0) {
    // save academic info implicitly read at submit time
  }
  currentStep = Math.max(0, Math.min(steps.length - 1, currentStep + delta));
  showStep(currentStep);
}

async function loadCatalog() {
  try {
    catalog = await Api.get('/api/student/subjects-catalog');
  } catch (e) {
    toast(e.message || 'Could not load catalog', 'error');
    return;
  }
  document.getElementById('subjects-grid').innerHTML = catalog.subjects.map(s => `
    <div class="choice-card" data-code="${s.code}" onclick="toggleSubject('${s.code}')">
      <strong>${s.name}</strong><span class="text-sm text-muted">${s.description}</span>
    </div>`).join('');
  document.getElementById('goals-grid').innerHTML = catalog.goals.map(g => `
    <div class="choice-card" data-code="${g.code}" onclick="toggleGoal('${g.code}')"><strong>${g.label}</strong></div>`).join('');
  document.getElementById('prefs-grid').innerHTML = catalog.preferences.map(p => `
    <div class="choice-card" data-code="${p.code}" onclick="togglePref('${p.code}')"><strong>${p.label}</strong></div>`).join('');
}

function toggleSubject(code) {
  selectedSubjects = selectedSubjects.includes(code) ? selectedSubjects.filter(c => c !== code) : [...selectedSubjects, code];
  document.querySelector(`#subjects-grid [data-code="${code}"]`).classList.toggle('selected');
  document.getElementById('subjects-next').disabled = selectedSubjects.length === 0;
}
function toggleGoal(code) {
  selectedGoals = selectedGoals.includes(code) ? selectedGoals.filter(c => c !== code) : [...selectedGoals, code];
  document.querySelector(`#goals-grid [data-code="${code}"]`).classList.toggle('selected');
  document.getElementById('goals-next').disabled = selectedGoals.length === 0;
}
function togglePref(code) {
  selectedPrefs = selectedPrefs.includes(code) ? selectedPrefs.filter(c => c !== code) : [...selectedPrefs, code];
  document.querySelector(`#prefs-grid [data-code="${code}"]`).classList.toggle('selected');
}

async function loadDiagnostic() {
  currentStep = 4;
  showStep(currentStep);
  const container = document.getElementById('diagnostic-questions');
  container.innerHTML = `<div class="skeleton" style="height:60px;margin-bottom:12px"></div><div class="skeleton" style="height:60px"></div>`;
  try {
    const data = await Api.get(`/api/student/diagnostic-questions?subjects=${selectedSubjects.join(',')}`);
    diagnosticQuestions = data.questions;
  } catch (e) {
    container.innerHTML = `<p class="text-muted">Could not load diagnostic questions - you can still continue, ELEVATE AI will calibrate as you learn.</p>`;
    return;
  }
  if (!diagnosticQuestions.length) {
    container.innerHTML = `<p class="text-muted">No diagnostic questions available yet for these subjects - you can still continue.</p>`;
    return;
  }
  container.innerHTML = diagnosticQuestions.map((q, qi) => `
    <div class="diag-q">
      <p style="font-weight:600;color:var(--color-text)">${qi + 1}. ${q.question_text}</p>
      ${q.options.map((opt, oi) => `
        <div class="diag-opt" data-qid="${q.question_id}" data-oi="${oi}" onclick="selectDiagAnswer(${q.question_id}, ${oi})">
          <span>${String.fromCharCode(65 + oi)}.</span><span>${opt}</span>
        </div>`).join('')}
    </div>`).join('');
}

function selectDiagAnswer(qid, oi) {
  diagnosticAnswers[qid] = oi;
  document.querySelectorAll(`.diag-opt[data-qid="${qid}"]`).forEach(el => el.classList.remove('selected'));
  document.querySelector(`.diag-opt[data-qid="${qid}"][data-oi="${oi}"]`).classList.add('selected');
}

async function finishOnboarding() {
  const btn = document.getElementById('finish-btn');
  btn.disabled = true;
  btn.textContent = 'Building your learning path...';

  const answers = Object.entries(diagnosticAnswers).map(([qid, oi]) => ({ question_id: parseInt(qid), selected_index: oi }));

  try {
    const result = await Api.post('/api/student/onboarding', {
      academic_level: document.getElementById('academic_level').value,
      institution: document.getElementById('institution').value.trim(),
      subjects: selectedSubjects,
      goals: selectedGoals,
      preferences: { style: selectedPrefs },
      diagnostic_answers: answers,
    });

    const user = Auth.getUser();
    user.onboarding_completed = true;
    localStorage.setItem('elevate_user', JSON.stringify(user));

    if (result.diagnostic_result) {
      document.getElementById('diag-result-text').textContent =
        `You answered ${result.diagnostic_result.correct} of ${result.diagnostic_result.total} correctly on your diagnostic. ELEVATE AI has built your personalized path starting from your real level - not an inflated one.`;
    }
    currentStep = 5;
    showStep(currentStep);
  } catch (e) {
    toast(e.message || 'Could not complete onboarding', 'error');
    btn.disabled = false;
    btn.textContent = 'Finish & Build My Path';
  }
}

loadCatalog();
showStep(0);

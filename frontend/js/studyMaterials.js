const PIPELINE_STAGES = ['uploaded', 'extracting', 'extracted', 'concepts_identified', 'topics_structured', 'graph_built', 'questions_generated', 'ready'];
const PIPELINE_LABELS = {
  uploaded: 'File Uploaded', extracting: 'Extracting Text', extracted: 'Text Extracted',
  concepts_identified: 'Concepts Identified', topics_structured: 'Topics Structured',
  graph_built: 'Knowledge Graph Built', questions_generated: 'Quiz Questions Generated', ready: 'Ready',
};

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => { if (fileInput.files.length) uploadFile(fileInput.files[0]); });

function renderPipeline(currentStatus, filename) {
  const progressBox = document.getElementById('upload-progress');
  progressBox.classList.remove('hidden');
  document.getElementById('upload-filename').textContent = filename;
  const currentIdx = PIPELINE_STAGES.indexOf(currentStatus);
  document.getElementById('pipeline-steps').innerHTML = PIPELINE_STAGES.map((stage, i) => `
    <span class="pipeline-step ${i < currentIdx ? 'done' : i === currentIdx ? 'active' : ''}">${i <= currentIdx ? '✓ ' : ''}${PIPELINE_LABELS[stage]}</span>
  `).join('');
}

async function uploadFile(file) {
  if (!/\.(pdf|txt|md)$/i.test(file.name)) {
    toast('Only PDF, TXT or MD files are supported', 'error');
    return;
  }
  renderPipeline('uploaded', file.name);
  // Simulated staged reveal while the (synchronous) backend pipeline runs,
  // so the real pipeline stages are visibly communicated to the student.
  let stageIdx = 0;
  const stageTimer = setInterval(() => {
    stageIdx = Math.min(stageIdx + 1, PIPELINE_STAGES.length - 2);
    renderPipeline(PIPELINE_STAGES[stageIdx], file.name);
  }, 500);

  const formData = new FormData();
  formData.append('file', file);
  try {
    const resource = await Api.postForm('/api/materials/upload', formData);
    clearInterval(stageTimer);
    renderPipeline(resource.status, file.name);
    toast('Material processed successfully', 'success');
    setTimeout(() => { document.getElementById('upload-progress').classList.add('hidden'); loadMaterials(); }, 1200);
  } catch (e) {
    clearInterval(stageTimer);
    toast(e.message || 'Upload failed', 'error');
    document.getElementById('upload-progress').classList.add('hidden');
  }
}

async function loadMaterials() {
  const container = document.getElementById('materials-list');
  try {
    const data = await Api.get('/api/materials');
    if (!data.materials.length) {
      container.innerHTML = `<div class="empty-state">${Icons.empty}<p>No study materials uploaded yet.</p></div>`;
      return;
    }
    container.innerHTML = data.materials.map(m => `
      <div class="card material-card">
        <div class="flex justify-between items-center" style="margin-bottom:8px">
          <strong>${m.filename}</strong>
          <span class="badge ${m.status === 'ready' ? 'badge-success' : 'badge-primary'}">${PIPELINE_LABELS[m.status] || m.status}</span>
        </div>
        ${m.summary ? `<p class="text-sm">${m.summary}</p>` : ''}
        <div class="text-xs text-muted" style="margin-bottom:8px">${m.concepts_count} concept(s) identified · opened ${m.open_count} time(s) · ${Math.round(m.progress_percent)}% engaged</div>
        <div class="flex gap-8">
          <a href="ai-tutor.html?material_id=${m.id}" class="btn btn-secondary btn-sm">Use with AI Tutor</a>
          ${m.status === 'ready' ? `<button class="btn btn-secondary btn-sm" onclick="generateFromMaterial(${m.id})">Generate Quiz From This</button>` : ''}
          <button class="btn btn-ghost btn-sm" onclick="markViewed(${m.id})">Mark as Studied (5 min)</button>
        </div>
      </div>`).join('');
  } catch (e) {
    container.innerHTML = `<p class="text-muted text-sm">Could not load materials.</p>`;
  }
}

async function generateFromMaterial(materialId) {
  try {
    const data = await Api.post('/api/quizzes/generate', { quiz_mode: 'material', material_id: materialId, num_questions: 5, difficulty: 'medium' });
    location.href = `quiz.html?quiz_id=${data.quiz_id}`;
  } catch (e) {
    toast(e.message || 'Could not generate quiz from this material', 'error');
  }
}

async function markViewed(materialId) {
  try {
    await Api.post(`/api/materials/${materialId}/mark-viewed?seconds=300`);
    toast('Study session recorded', 'success');
    loadMaterials();
  } catch (e) {
    toast(e.message || 'Could not record study session', 'error');
  }
}

loadMaterials();

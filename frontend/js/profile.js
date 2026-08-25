let catalogCache = null;

async function loadProfile() {
  const content = document.getElementById('page-content');
  let profile, catalog;
  try {
    [profile, catalog] = await Promise.all([
      Api.get('/api/student/profile'),
      Api.get('/api/student/subjects-catalog'),
    ]);
    catalogCache = catalog;
  } catch (e) {
    content.innerHTML = `<h2>Profile</h2><div class="empty-state">${Icons.empty}<p>${e.message}</p></div>`;
    return;
  }

  content.innerHTML = `
    <h2>Profile</h2>
    <p class="text-muted" style="margin-bottom:20px">Update your personal and academic information, subjects and goals.</p>
    <div class="card card-pad" style="margin-bottom:20px">
      <h3>Personal Information</h3>
      <div class="field"><label>Full Name</label><input class="input" id="p-name" value="${profile.full_name}"></div>
      <div class="field"><label>Email</label><input class="input" value="${profile.email}" disabled></div>
      <div class="field"><label>Academic Level</label>
        <select class="input" id="p-level">
          ${['Grade 8','Grade 9','Grade 10','Grade 11','Grade 12','Undergraduate'].map(l => `<option ${l === profile.academic_level ? 'selected' : ''}>${l}</option>`).join('')}
        </select>
      </div>
      <div class="field"><label>Institution</label><input class="input" id="p-institution" value="${profile.institution || ''}"></div>
    </div>

    <div class="card card-pad" style="margin-bottom:20px">
      <h3>Subjects</h3>
      <div class="choice-grid" id="p-subjects" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        ${catalog.subjects.map(s => `<div class="choice-card ${profile.subjects.includes(s.code) ? 'selected' : ''}" data-code="${s.code}" onclick="toggleChoice(this,'subjects')" style="border:1.5px solid var(--color-border-strong);border-radius:8px;padding:12px;cursor:pointer"><strong>${s.name}</strong></div>`).join('')}
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom:20px">
      <h3>Learning Goals</h3>
      <div id="p-goals" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        ${catalog.goals.map(g => `<div class="choice-card ${profile.goals.includes(g.code) ? 'selected' : ''}" data-code="${g.code}" onclick="toggleChoice(this,'goals')" style="border:1.5px solid var(--color-border-strong);border-radius:8px;padding:12px;cursor:pointer"><strong>${g.label}</strong></div>`).join('')}
      </div>
    </div>

    <div class="card card-pad" style="margin-bottom:20px">
      <h3>Streak</h3>
      <p class="text-sm">Current streak: <strong>${profile.current_streak} day(s)</strong> · Longest: <strong>${profile.longest_streak} day(s)</strong></p>
    </div>

    <button class="btn btn-primary" onclick="saveProfile()">Save Changes</button>
  `;

  document.querySelectorAll('.choice-card.selected').forEach(el => el.style.cssText += 'border-color:var(--color-primary);background:var(--color-primary-light)');
}

function toggleChoice(el, group) {
  el.classList.toggle('selected');
  if (el.classList.contains('selected')) el.style.cssText += 'border-color:var(--color-primary);background:var(--color-primary-light)';
  else el.style.cssText = 'border:1.5px solid var(--color-border-strong);border-radius:8px;padding:12px;cursor:pointer';
}

async function saveProfile() {
  const subjects = [...document.querySelectorAll('#p-subjects .selected')].map(el => el.dataset.code);
  const goals = [...document.querySelectorAll('#p-goals .selected')].map(el => el.dataset.code);
  try {
    await Api.put('/api/student/profile', {
      full_name: document.getElementById('p-name').value.trim(),
      academic_level: document.getElementById('p-level').value,
      institution: document.getElementById('p-institution').value.trim(),
      subjects, goals,
    });
    toast('Profile updated', 'success');
    const user = Auth.getUser();
    user.full_name = document.getElementById('p-name').value.trim();
    localStorage.setItem('elevate_user', JSON.stringify(user));
  } catch (e) {
    toast(e.message || 'Could not save profile', 'error');
  }
}

loadProfile();

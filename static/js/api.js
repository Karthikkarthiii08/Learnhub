const API = 'http://127.0.0.1:5000';

function getToken() { return localStorage.getItem('token'); }
function getUser() { return JSON.parse(localStorage.getItem('user') || 'null'); }
function isAdmin() { const u = getUser(); return u && u.role === 'admin'; }
function isLoggedIn() { return !!getToken(); }

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = '/login.html';
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json();
  if (!res.ok) throw data;
  return data;
}

function showAlert(containerId, msg, type = 'error') {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert alert-${type}">${type === 'error' ? '⚠️' : '✅'} ${msg}</div>`;
  setTimeout(() => { el.innerHTML = ''; }, 4000);
}

function starsHtml(rating) {
  const r = Math.round(rating * 2) / 2;
  const full = Math.floor(r);
  const half = r % 1 !== 0;
  let s = '';
  for (let i = 0; i < full; i++) s += '★';
  if (half) s += '½';
  return s;
}

function courseCardHtml(c, showProgress = false) {
  const thumb = c.thumbnail || `https://placehold.co/480x270/4F46E5/ffffff?text=${encodeURIComponent(c.title)}`;
  const pct = c.percent || 0;
  const level = c.level || 'Beginner';
  const category = c.category || 'Course';
  const isEnrolled = showProgress && pct > 0;

  return `
    <div class="course-card" onclick="location.href='/course.html?id=${c.id}'">
      <div class="course-thumb">
        <img src="${thumb}" alt="${c.title}" loading="lazy" onerror="this.src='https://placehold.co/480x270/4F46E5/ffffff?text=${encodeURIComponent(c.title)}'"/>
        <span class="lesson-badge">☰ ${c.lesson_count} Lessons</span>
        ${c.is_premium ? '<span class="lesson-badge" style="left:10px;right:auto;background:#7C3AED">⭐ Premium</span>' : ''}
      </div>
      <div class="course-body">
        <span class="course-tag">${category}</span>
        <h3>${c.title}</h3>
        <div class="course-instructor">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
          ${c.instructor || 'Admin'}
        </div>
        <div class="stars">
          <span class="star-icons">${starsHtml(c.rating || 4.5)}</span>
          <span class="rating-num">${(c.rating || 4.5).toFixed(1)}</span>
          <span class="level-badge level-${level.toLowerCase()}">${level}</span>
        </div>
        ${isEnrolled ? `
          <div class="progress-mini">
            <div class="bar-wrap"><div class="bar" style="width:${pct}%"></div></div>
            <div class="pct">${pct}% complete</div>
          </div>` : ''}
        <div class="course-footer">
          <div class="course-duration">🕐 ${c.duration_weeks || 4} weeks</div>
          <button class="enroll-btn ${isEnrolled ? 'enrolled' : ''}"
            onclick="event.stopPropagation(); handleEnroll(${c.id}, this)">
            ${isEnrolled ? '▶ Continue' : '+ Enroll'}
          </button>
        </div>
      </div>
    </div>`;
}

async function handleEnroll(courseId, btn) {
  if (!isLoggedIn()) {
    window.location.href = '/login.html?enroll=' + courseId;
    return;
  }
  if (isAdmin()) { window.location.href = '/lesson.html?course=' + courseId; return; }
  const orig = btn.textContent;
  btn.textContent = '...'; btn.disabled = true;
  try {
    await apiFetch('/api/enroll', { method: 'POST', body: JSON.stringify({ course_id: courseId }) });
    btn.textContent = '▶ Continue';
    btn.classList.add('enrolled');
    setTimeout(() => window.location.href = '/lesson.html?course=' + courseId, 300);
  } catch {
    // Already enrolled or error — just go to lesson
    window.location.href = '/lesson.html?course=' + courseId;
  }
}

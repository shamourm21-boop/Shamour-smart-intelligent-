/* Shredded — shared utilities */

// ── Toast notifications ───────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  const c = document.getElementById('toast-container') || (() => {
    const el = document.createElement('div');
    el.id = 'toast-container';
    document.body.appendChild(el);
    return el;
  })();
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.3s'; }, 2500);
  setTimeout(() => t.remove(), 2900);
}

// ── Fetch helpers ─────────────────────────────────────────────────────────────
async function api(method, url, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

// ── Workout timer ─────────────────────────────────────────────────────────────
let _timerInterval = null;

function startTimer(startedAt) {
  const el = document.getElementById('session-timer');
  if (!el) return;
  const start = startedAt ? new Date(startedAt) : new Date();
  clearInterval(_timerInterval);
  _timerInterval = setInterval(() => {
    const secs = Math.floor((Date.now() - start) / 1000);
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    el.textContent = h > 0
      ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
      : `${m}:${String(s).padStart(2,'0')}`;
  }, 1000);
}

// ── Autocomplete helper ────────────────────────────────────────────────────────
function initAutocomplete(inputId, listId, onSelect) {
  const input = document.getElementById(inputId);
  const list  = document.getElementById(listId);
  if (!input || !list) return;

  let idx = -1;
  let items = [];

  async function refresh(q) {
    const data = await fetch(`/api/exercises?q=${encodeURIComponent(q)}`).then(r => r.json());
    items = data.slice(0, 10);
    idx = -1;
    list.innerHTML = '';
    if (!items.length) { list.classList.add('hidden'); return; }
    items.forEach((name, i) => {
      const div = document.createElement('div');
      div.className = 'autocomplete-item';
      div.textContent = name;
      div.addEventListener('mousedown', e => { e.preventDefault(); pick(name); });
      list.appendChild(div);
    });
    list.classList.remove('hidden');
  }

  function pick(name) {
    input.value = name;
    list.classList.add('hidden');
    if (onSelect) onSelect(name);
  }

  input.addEventListener('input', () => refresh(input.value));
  input.addEventListener('keydown', e => {
    const rows = list.querySelectorAll('.autocomplete-item');
    if (e.key === 'ArrowDown')  { e.preventDefault(); idx = Math.min(idx+1, rows.length-1); }
    if (e.key === 'ArrowUp')    { e.preventDefault(); idx = Math.max(idx-1, 0); }
    if (e.key === 'Enter' && idx >= 0) { e.preventDefault(); pick(items[idx]); return; }
    if (e.key === 'Escape') { list.classList.add('hidden'); idx = -1; }
    rows.forEach((r, i) => r.classList.toggle('selected', i === idx));
  });
  input.addEventListener('blur', () => setTimeout(() => list.classList.add('hidden'), 150));
  input.addEventListener('focus', () => { if (input.value) refresh(input.value); });
}

// ── Epley 1RM estimate ────────────────────────────────────────────────────────
function epley(weight, reps) {
  if (!weight || !reps) return null;
  return Math.round(weight * (1 + reps / 30) * 10) / 10;
}

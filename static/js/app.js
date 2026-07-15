/**
 * CareGuard AI — Client-Side JavaScript
 * Theme management, toast notifications, markdown renderer,
 * live vitals refresh, and chat UI helpers.
 */

// ── Theme ──────────────────────────────────────────────────────────────────
const THEME_KEY = 'careguard-theme';

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const btn = document.getElementById('theme-toggle-btn');
  if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next    = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

(function initTheme() {
  const saved = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(saved);
})();

// ── Toast notifications ────────────────────────────────────────────────────
function showToast(message, type = 'success', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    toast.style.transition = '0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Simple Markdown → HTML renderer ───────────────────────────────────────
function renderMarkdown(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    .replace(/`(.+?)`/g,       '<code>$1</code>')
    .replace(/^#{3} (.+)$/gm,  '<h3>$1</h3>')
    .replace(/^#{2} (.+)$/gm,  '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,     '<h1>$1</h1>')
    .replace(/^\s*[-*] (.+)$/gm,'<li>$1</li>')
    .replace(/(<li>[\s\S]+?<\/li>)/g, '<ul>$1</ul>')
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/\n/g,     '<br>')
    .replace(/^(.+)$/gm, (line) => line.startsWith('<') ? line : `<p>${line}</p>`);
}

// ── Chat UI ────────────────────────────────────────────────────────────────
function appendMessage(role, content, timestamp) {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  const isUser = role === 'user';
  const msg = document.createElement('div');
  msg.className = `message ${role}`;

  const html = isUser ? content.replace(/</g,'&lt;').replace(/>/g,'&gt;') : renderMarkdown(content);

  msg.innerHTML = `
    <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
    <div>
      <div class="message-bubble">${html}</div>
      <span class="message-time">${timestamp || new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</span>
    </div>`;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function setTypingIndicator(visible) {
  let el = document.getElementById('typing-indicator');
  if (visible && !el) {
    const container = document.getElementById('chat-messages');
    el = document.createElement('div');
    el.id = 'typing-indicator';
    el.className = 'message assistant';
    el.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-bubble" style="padding:14px 18px;">
        <span class="spinner"></span>&nbsp;&nbsp;CareGuard AI is thinking…
      </div>`;
    if (container) container.appendChild(el);
  } else if (!visible && el) {
    el.remove();
  }
}

// ── Send chat message ──────────────────────────────────────────────────────
async function sendChat() {
  const input   = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  if (!input) return;

  const message = input.value.trim();
  if (!message) return;

  input.value = '';
  input.style.height = 'auto';
  sendBtn.disabled = true;

  appendMessage('user', message);
  setTypingIndicator(true);

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    const data = await resp.json();
    setTypingIndicator(false);
    if (data.reply) {
      appendMessage('assistant', data.reply, data.timestamp);
      if (data.reading) updateMiniVitals(data.reading);
    } else {
      showToast(data.error || 'Unknown error', 'error');
    }
  } catch (err) {
    setTypingIndicator(false);
    showToast('Network error: ' + err.message, 'error');
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

// ── Mini vitals update (chat sidebar) ─────────────────────────────────────
function updateMiniVitals(reading) {
  const map = {
    'mini-hr':      reading.heart_rate   + ' bpm',
    'mini-bp':      reading.systolic_bp  + '/' + reading.diastolic_bp,
    'mini-glucose': reading.blood_glucose + ' mg/dL',
    'mini-spo2':    reading.spo2         + '%',
  };
  for (const [id, val] of Object.entries(map)) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }
}

// ── Live vitals refresh (dashboard) ───────────────────────────────────────
async function refreshVitals() {
  try {
    const resp = await fetch('/api/health-reading');
    const data = await resp.json();
    if (!data.reading) return;
    const r = data.reading;
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setVal('live-hr',      r.heart_rate);
    setVal('live-bp',      `${r.systolic_bp}/${r.diastolic_bp}`);
    setVal('live-glucose', r.blood_glucose);
    setVal('live-spo2',    r.spo2);
    setVal('live-temp',    r.temperature + '°C');
    setVal('live-steps',   r.steps.toLocaleString());
    setVal('live-sleep',   r.sleep_hours + 'h');
    setVal('live-stress',  r.stress_index);
    // Risk badge
    if (data.risk) {
      const badge = document.getElementById('risk-badge');
      if (badge) {
        badge.className = `risk-badge risk-${data.risk.label}`;
        badge.innerHTML = `● ${data.risk.label} — ${data.risk.score}/100`;
      }
    }
  } catch (e) { /* silent */ }
}

// ── Full AI analysis ──────────────────────────────────────────────────────
async function triggerAnalysis() {
  const btn = document.getElementById('analyze-btn');
  const out  = document.getElementById('analysis-output');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Analyzing…'; }
  if (out)  { out.innerHTML = ''; }
  try {
    const resp = await fetch('/api/analyze', { method: 'POST' });
    const data = await resp.json();
    if (data.analysis && out) {
      out.innerHTML = renderMarkdown(data.analysis);
      showToast('AI analysis complete ✅', 'success');
    }
  } catch (err) {
    showToast('Analysis failed: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '🔍 Run AI Analysis'; }
  }
}

// ── Medication advice ─────────────────────────────────────────────────────
async function getMedAdvice() {
  const btn = document.getElementById('med-advice-btn');
  const out  = document.getElementById('med-advice-output');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Loading…'; }
  try {
    const resp = await fetch('/api/medication-reminder', { method: 'POST' });
    const data = await resp.json();
    if (data.advice && out) out.innerHTML = renderMarkdown(data.advice);
  } catch (err) {
    showToast('Failed to get advice: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '💊 Get AI Medication Advice'; }
  }
}

// ── Patient profile save ──────────────────────────────────────────────────
async function saveProfile(event) {
  event.preventDefault();
  const form   = event.target;
  const btn    = form.querySelector('[type=submit]');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Saving…';

  const payload = {
    name:   form.name.value,
    age:    parseInt(form.age.value),
    gender: form.gender.value,
    weight_kg: parseFloat(form.weight_kg.value),
    height_cm: parseFloat(form.height_cm.value),
    blood_group: form.blood_group.value,
    allergies: form.allergies.value,
    current_medications: form.current_medications.value,
    existing_conditions: form.existing_conditions.value,
    family_history: form.family_history.value,
    emergency_contact: {
      name:     form.ec_name.value,
      relation: form.ec_relation.value,
      phone:    form.ec_phone.value,
    },
  };

  try {
    const resp = await fetch('/api/patient', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (data.status === 'saved') showToast('Profile saved successfully! ✅', 'success');
    else showToast('Save failed', 'error');
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '💾 Save Profile';
  }
}

// ── Auto-resize textarea ─────────────────────────────────────────────────
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Enter key in chat input
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
    });
    chatInput.addEventListener('input', () => autoResize(chatInput));
  }

  // Auto-scroll chat to bottom
  const messages = document.getElementById('chat-messages');
  if (messages) messages.scrollTop = messages.scrollHeight;

  // Live vitals refresh every 30 seconds
  if (document.getElementById('live-hr')) {
    setInterval(refreshVitals, 30000);
  }
});

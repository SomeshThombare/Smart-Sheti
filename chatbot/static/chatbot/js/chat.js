/* ═══════════════════════════════════════════════════════════
   Smart Sheti — AI Krishi Sahayak
   chat.js
   ═══════════════════════════════════════════════════════════ */

// ════════════════════════════════════════════════════════
// STATE
// ════════════════════════════════════════════════════════
let currentLang      = 'en';
let pendingImageB64  = null;
let pendingImageMime = null;
let pendingPdfB64    = null;
let isRecording      = false;
let recognition      = null;
let currentSessionId = Date.now();

// ════════════════════════════════════════════════════════
// SEND MESSAGE
// ════════════════════════════════════════════════════════
async function sendMessage() {
  const input   = document.getElementById('user-input');
  const message = input.value.trim();

  if (!message && !pendingImageB64 && !pendingPdfB64) return;

  // Remove welcome screen on first message
  const welcome = document.getElementById('welcome-screen');
  if (welcome) welcome.remove();

  // Build display text for user bubble
  let displayText = '';
  if (pendingImageB64) displayText += `<span class="attach-badge">📷 Image attached</span><br>`;
  if (pendingPdfB64)   displayText += `<span class="attach-badge">📄 PDF attached</span><br>`;
  if (message)         displayText += escapeHtml(message);

  addBubble('user', displayText);
  input.value = '';
  autoResize(input);

  // Snapshot pending files then clear UI
  const imgB64  = pendingImageB64;
  const imgMime = pendingImageMime;
  const pdfB64  = pendingPdfB64;
  clearImage();
  clearPdf();

  // Show typing indicator
  const typingRow = addTyping();

  try {
    const payload = { message };
    if (imgB64) { payload.image = imgB64; payload.image_mime = imgMime; }
    if (pdfB64) { payload.pdf   = pdfB64; }

    const res  = await fetch('/chatbot/api/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload)
    });

    const data = await res.json();
    typingRow.remove();

    if (data.status === 'success') {
      addBubble('bot', formatBotText(data.response));
      saveHistory(message || '[file]', data.response);
    } else {
      addBubble('bot', '⚠️ ' + (data.response || 'Something went wrong.'));
    }
  } catch (err) {
    typingRow.remove();
    addBubble('bot', '❌ Connection error. Please check your internet and try again.');
  }
}

// ════════════════════════════════════════════════════════
// BUBBLE HELPERS
// ════════════════════════════════════════════════════════
function addBubble(sender, html) {
  const area = document.getElementById('chat-area');
  const row  = document.createElement('div');
  row.className = `msg-row ${sender}`;

  const avatarIcon  = sender === 'bot' ? '🌾' : '👤';
  const avatarClass = sender === 'bot' ? 'bot-av' : 'user-av';

  row.innerHTML = `
    <div class="msg-avatar ${avatarClass}">${avatarIcon}</div>
    <div class="msg-bubble">${html}</div>
  `;
  area.appendChild(row);
  area.scrollTop = area.scrollHeight;
  return row;
}

function addTyping() {
  const area = document.getElementById('chat-area');
  const row  = document.createElement('div');
  row.className = 'msg-row bot';
  row.innerHTML = `
    <div class="msg-avatar bot-av">🌾</div>
    <div class="msg-bubble typing-bubble">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
  `;
  area.appendChild(row);
  area.scrollTop = area.scrollHeight;
  return row;
}

function formatBotText(text) {
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ════════════════════════════════════════════════════════
// SUGGESTION CARDS
// ════════════════════════════════════════════════════════
function askSuggestion(el) {
  const text = el.querySelector('.suggestion-text').textContent;
  document.getElementById('user-input').value = text;
  sendMessage();
}

// ════════════════════════════════════════════════════════
// NEW CHAT
// ════════════════════════════════════════════════════════
function newChat() {
  currentSessionId = Date.now();
  document.getElementById('chat-area').innerHTML = `
    <div class="welcome-screen" id="welcome-screen">
      <div class="welcome-avatar">🤖</div>
      <div class="welcome-title">Hello Farmer! 👋</div>
      <div class="welcome-sub">New conversation started. Ask me anything!</div>
      <div class="suggestion-grid">
        <div class="suggestion-card" onclick="askSuggestion(this)">
          <span class="suggestion-icon">🌱</span>
          <div class="suggestion-text">Which crop should I plant this Kharif season?</div>
        </div>
        <div class="suggestion-card" onclick="askSuggestion(this)">
          <span class="suggestion-icon">🍃</span>
          <div class="suggestion-text">My tomato leaves are turning yellow. What disease?</div>
        </div>
        <div class="suggestion-card" onclick="askSuggestion(this)">
          <span class="suggestion-icon">💧</span>
          <div class="suggestion-text">Best fertilizer for black cotton soil in Vidarbha</div>
        </div>
        <div class="suggestion-card" onclick="askSuggestion(this)">
          <span class="suggestion-icon">🏛️</span>
          <div class="suggestion-text">Tell me about PM-Kisan yojana benefits</div>
        </div>
      </div>
    </div>`;
}

// ════════════════════════════════════════════════════════
// IMAGE UPLOAD
// ════════════════════════════════════════════════════════
function triggerImage() { document.getElementById('img-input').click(); }

function handleImageSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    pendingImageB64  = reader.result.split(',')[1];
    pendingImageMime = file.type;
    document.getElementById('image-name').textContent = file.name;
    document.getElementById('image-pill').style.display = 'inline-flex';
    document.getElementById('attachment-strip').classList.add('has-files');
  };
  reader.readAsDataURL(file);
  e.target.value = '';
}

function clearImage() {
  pendingImageB64 = null; pendingImageMime = null;
  document.getElementById('image-pill').style.display = 'none';
  checkStrip();
}

// ════════════════════════════════════════════════════════
// PDF UPLOAD
// ════════════════════════════════════════════════════════
function triggerPdf() { document.getElementById('pdf-input').click(); }

function handlePdfSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    pendingPdfB64 = reader.result.split(',')[1];
    document.getElementById('pdf-name').textContent = file.name;
    document.getElementById('pdf-pill').style.display = 'inline-flex';
    document.getElementById('attachment-strip').classList.add('has-files');
  };
  reader.readAsDataURL(file);
  e.target.value = '';
}

function clearPdf() {
  pendingPdfB64 = null;
  document.getElementById('pdf-pill').style.display = 'none';
  checkStrip();
}

function checkStrip() {
  const anyVisible = ['image-pill', 'pdf-pill'].some(
    id => document.getElementById(id).style.display !== 'none'
  );
  if (!anyVisible) {
    document.getElementById('attachment-strip').classList.remove('has-files');
  }
}

// ════════════════════════════════════════════════════════
// VOICE INPUT
// ════════════════════════════════════════════════════════
function toggleVoice() {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    alert('Voice input is not supported in your browser. Please use Chrome.');
    return;
  }

  if (isRecording) {
    recognition && recognition.stop();
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang            = currentLang === 'mr' ? 'mr-IN' : 'en-IN';
  recognition.continuous      = false;
  recognition.interimResults  = false;

  recognition.onstart = () => {
    isRecording = true;
    document.getElementById('voice-btn').textContent = '🔴';
    document.getElementById('voice-btn').title = 'Recording… click to stop';
  };

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    const input = document.getElementById('user-input');
    input.value = transcript;
    autoResize(input);
  };

  recognition.onend = () => {
    isRecording = false;
    document.getElementById('voice-btn').textContent = '🎤';
    document.getElementById('voice-btn').title = 'Voice input';
  };

  recognition.onerror = () => {
    isRecording = false;
    document.getElementById('voice-btn').textContent = '🎤';
  };

  recognition.start();
}

// ════════════════════════════════════════════════════════
// LANGUAGE TOGGLE
// ════════════════════════════════════════════════════════
function setLang(lang) {
  currentLang = lang;
  document.getElementById('lang-en').classList.toggle('active', lang === 'en');
  document.getElementById('lang-mr').classList.toggle('active', lang === 'mr');
  document.getElementById('user-input').placeholder =
    lang === 'mr'
      ? 'शेतीविषयी प्रश्न विचारा…'
      : 'Ask about crops, disease, fertilizer, govt schemes…';
}

// ════════════════════════════════════════════════════════
// CHAT HISTORY (localStorage)
// ════════════════════════════════════════════════════════
function saveHistory(question) {
  let sessions = JSON.parse(localStorage.getItem('sheti_history') || '[]');
  const existing = sessions.find(s => s.id === currentSessionId);
  if (existing) {
    existing.preview = question.slice(0, 40);
  } else {
    sessions.unshift({ id: currentSessionId, preview: question.slice(0, 40) });
    if (sessions.length > 20) sessions = sessions.slice(0, 20);
  }
  localStorage.setItem('sheti_history', JSON.stringify(sessions));
  renderHistory();
}

function renderHistory() {
  const list     = document.getElementById('history-list');
  const sessions = JSON.parse(localStorage.getItem('sheti_history') || '[]');
  list.innerHTML = sessions.map(s => `
    <div class="history-item" title="${escapeHtml(s.preview)}">
      💬 ${escapeHtml(s.preview)}…
    </div>
  `).join('');
}

// ════════════════════════════════════════════════════════
// UTILS
// ════════════════════════════════════════════════════════
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ════════════════════════════════════════════════════════
// INIT
// ════════════════════════════════════════════════════════
window.onload = () => {
  document.getElementById('user-input').focus();
  renderHistory();
};
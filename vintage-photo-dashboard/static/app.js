// VintageAI Studio — Dashboard Application
// Real-time 90s Photography Analysis via Gemini API

const STATE = {
  selectedFile: null,
  selectedStyle: 'polaroid',
  isProcessing: false,
  clientId: null,
  history: [],
  photoCount: 0,
  styleCount: 0,
  usedStyles: new Set(),
};

// ===== DOM ELEMENTS =====
const els = {
  apiKey: document.getElementById('apiKey'),
  toggleApiKey: document.getElementById('toggleApiKey'),
  styleCards: document.querySelectorAll('.style-card'),
  uploadZone: document.getElementById('uploadZone'),
  photoInput: document.getElementById('photoInput'),
  photoPreviewArea: document.getElementById('photoPreviewArea'),
  photoPreview: document.getElementById('photoPreview'),
  photoName: document.getElementById('photoName'),
  removePhoto: document.getElementById('removePhoto'),
  processBtn: document.getElementById('processBtn'),
  toggleTextMode: document.getElementById('toggleTextMode'),
  textModePanel: document.getElementById('textModePanel'),
  modelSelect: document.getElementById('modelSelect'),
  sceneDescription: document.getElementById('sceneDescription'),
  processTextBtn: document.getElementById('processTextBtn'),
  welcomeState: document.getElementById('welcomeState'),
  processingState: document.getElementById('processingState'),
  resultsState: document.getElementById('resultsState'),
  progressFill: document.getElementById('progressFill'),
  progressStage: document.getElementById('progressStage'),
  progressPct: document.getElementById('progressPct'),
  processingLog: document.getElementById('processingLog'),
  photoDisplay: document.getElementById('photoDisplay'),
  resultHeader: document.getElementById('resultHeader'),
  resultGrid: document.getElementById('resultGrid'),
  editingTipsSection: document.getElementById('editingTipsSection'),
  newSessionBtn: document.getElementById('newSessionBtn'),
  historyList: document.getElementById('historyList'),
  statPhotos: document.getElementById('statPhotos'),
  statStyles: document.getElementById('statStyles'),
  clock: document.getElementById('clock'),
};

// ===== CLOCK =====
function updateClock() {
  const now = new Date();
  els.clock.textContent = now.toLocaleTimeString('en-US', {
    hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}
setInterval(updateClock, 1000);
updateClock();

// ===== API KEY TOGGLE =====
els.toggleApiKey.addEventListener('click', () => {
  const isPassword = els.apiKey.type === 'password';
  els.apiKey.type = isPassword ? 'text' : 'password';
  els.toggleApiKey.textContent = isPassword ? '🙈' : '👁';
});

// ===== STYLE SELECTION =====
els.styleCards.forEach(card => {
  card.addEventListener('click', () => {
    els.styleCards.forEach(c => c.classList.remove('active'));
    card.classList.add('active');
    STATE.selectedStyle = card.dataset.style;
  });
});

// ===== FILE UPLOAD =====
els.uploadZone.addEventListener('click', () => els.photoInput.click());

els.uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  els.uploadZone.classList.add('dragover');
});

els.uploadZone.addEventListener('dragleave', () => {
  els.uploadZone.classList.remove('dragover');
});

els.uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  els.uploadZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    loadPhoto(file);
  } else {
    showToast('Please drop an image file', 'error');
  }
});

els.photoInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) loadPhoto(file);
});

els.removePhoto.addEventListener('click', () => {
  STATE.selectedFile = null;
  els.photoPreviewArea.hidden = true;
  els.uploadZone.hidden = false;
  els.photoInput.value = '';
  updateProcessBtn();
});

function loadPhoto(file) {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
  if (!allowedTypes.includes(file.type)) {
    showToast('Unsupported file type. Use JPG, PNG, WEBP or GIF.', 'error');
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    showToast('File too large. Maximum 16MB.', 'error');
    return;
  }

  STATE.selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    els.photoPreview.src = e.target.result;
    els.photoName.textContent = file.name;
    els.uploadZone.hidden = true;
    els.photoPreviewArea.hidden = false;
    updateProcessBtn();
  };
  reader.readAsDataURL(file);
}

function updateProcessBtn() {
  const hasKey = els.apiKey.value.trim().length > 10;
  const hasFile = STATE.selectedFile !== null;
  els.processBtn.disabled = !hasKey || !hasFile || STATE.isProcessing;
}

els.apiKey.addEventListener('input', updateProcessBtn);

// ===== TEXT MODE =====
els.toggleTextMode.addEventListener('click', () => {
  const hidden = els.textModePanel.hidden;
  els.textModePanel.hidden = !hidden;
  els.toggleTextMode.textContent = hidden
    ? '✕ Close text mode'
    : '✍️ Generate from scene description';
});

els.processTextBtn.addEventListener('click', async () => {
  const apiKey = els.apiKey.value.trim();
  const scene = els.sceneDescription.value.trim();

  if (!apiKey) { showToast('Enter your Google AI Studio API key', 'error'); return; }
  if (!scene) { showToast('Describe a scene first', 'error'); return; }

  els.processTextBtn.disabled = true;
  els.processTextBtn.textContent = '⏳ Generating...';

  try {
    const res = await fetch('/api/analyze-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        style: STATE.selectedStyle,
        scene: scene,
        model: els.modelSelect ? els.modelSelect.value : 'gemini-2.0-flash-exp',
      }),
    });

    const data = await res.json();
    if (data.error) { showToast(data.error, 'error'); return; }

    showTextResults(data.result);

  } catch (e) {
    showToast('Request failed: ' + e.message, 'error');
  } finally {
    els.processTextBtn.disabled = false;
    els.processTextBtn.textContent = '🎨 Generate Style Guide';
  }
});

function showTextResults(result) {
  showState('results');

  els.photoDisplay.innerHTML = `
    <div style="font-size:3rem; text-align:center; padding: 1rem; opacity:0.5;">🎞️</div>
  `;

  renderResults(result, null);
  addToHistory(null, STATE.selectedStyle, result);
}

// ===== MAIN PROCESS =====
els.processBtn.addEventListener('click', startProcessing);

async function startProcessing() {
  const apiKey = els.apiKey.value.trim();
  if (!apiKey || !STATE.selectedFile || STATE.isProcessing) return;

  STATE.isProcessing = true;
  STATE.clientId = 'client_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
  updateProcessBtn();

  showState('processing');
  setProgress(5, 'Connecting to darkroom...');

  // Start SSE stream
  const evtSource = new EventSource(`/stream/${STATE.clientId}`);

  evtSource.addEventListener('connected', () => {
    setProgress(10, 'Darkroom connected. Loading photo...');
    // Now send the form data
    uploadAndProcess(apiKey, evtSource);
  });

  evtSource.addEventListener('progress', (e) => {
    const data = JSON.parse(e.data);
    setProgress(data.progress, data.message);
    appendLog(data.message);
  });

  evtSource.addEventListener('complete', (e) => {
    evtSource.close();
    const data = JSON.parse(e.data);
    setProgress(100, 'Development complete!');

    setTimeout(() => {
      showResults(data);
      STATE.isProcessing = false;
      updateProcessBtn();
    }, 500);
  });

  evtSource.addEventListener('error_event', (e) => {
    evtSource.close();
    const data = JSON.parse(e.data);
    showToast('Error: ' + data.message, 'error');
    showState('welcome');
    STATE.isProcessing = false;
    updateProcessBtn();
  });

  evtSource.onerror = () => {
    if (STATE.isProcessing) {
      evtSource.close();
      showToast('Connection lost. Please try again.', 'error');
      showState('welcome');
      STATE.isProcessing = false;
      updateProcessBtn();
    }
  };
}

async function uploadAndProcess(apiKey, evtSource) {
  const formData = new FormData();
  formData.append('api_key', apiKey);
  formData.append('style', STATE.selectedStyle);
  formData.append('client_id', STATE.clientId);
  formData.append('model', els.modelSelect ? els.modelSelect.value : 'gemini-2.0-flash-exp');
  formData.append('photo', STATE.selectedFile);

  try {
    const res = await fetch('/api/process', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      evtSource.close();
      showToast(err.error || 'Upload failed', 'error');
      showState('welcome');
      STATE.isProcessing = false;
      updateProcessBtn();
    }
  } catch (e) {
    evtSource.close();
    showToast('Upload failed: ' + e.message, 'error');
    showState('welcome');
    STATE.isProcessing = false;
    updateProcessBtn();
  }
}

// ===== STATE MANAGEMENT =====
function showState(state) {
  els.welcomeState.hidden = state !== 'welcome';
  els.processingState.hidden = state !== 'processing';
  els.resultsState.hidden = state !== 'results';
}

function setProgress(pct, message) {
  els.progressFill.style.width = pct + '%';
  els.progressStage.textContent = message;
  els.progressPct.textContent = pct + '%';
}

function appendLog(msg) {
  els.processingLog.textContent = '> ' + msg;
}

// ===== RESULTS =====
function showResults(data) {
  showState('results');

  // Original photo
  if (data.original_preview) {
    els.photoDisplay.innerHTML = `<img src="${data.original_preview}" alt="Original photo">`;
  }

  renderResults(data.result, data);
  addToHistory(data.original_preview, data.style, data.result);

  STATE.photoCount++;
  if (!STATE.usedStyles.has(data.style)) {
    STATE.usedStyles.add(data.style);
    STATE.styleCount++;
  }
  els.statPhotos.textContent = STATE.photoCount;
  els.statStyles.textContent = STATE.styleCount;
}

function renderResults(result, data) {
  // Header badge
  const icon = data ? data.style_icon : '🎞️';
  const styleName = result.style_name || (data ? data.style_name : 'Vintage');
  els.resultHeader.innerHTML = `
    <div class="result-badge">
      <span>${icon}</span>
      <span>${styleName}</span>
    </div>
    <div class="result-meta">
      <span>📅 ${result.era || '1990s'}</span>
      <span>🎞️ ${result.film_type || styleName}</span>
    </div>
  `;

  // Main result cards
  const cards = [];

  // Mood card
  if (result.mood) {
    cards.push(`
      <div class="result-card">
        <div class="result-card-title">✨ Mood & Atmosphere</div>
        <p class="mood-text">${result.mood}</p>
        ${result.lighting_advice ? `<p class="mood-text" style="margin-top:0.5rem">${result.lighting_advice}</p>` : ''}
      </div>
    `);
  }

  // Color palette
  const palette = result.color_palette || result.colors || [];
  if (palette.length) {
    cards.push(`
      <div class="result-card">
        <div class="result-card-title">🎨 Color Palette</div>
        <div class="color-swatches">
          ${palette.map(c => `<span class="color-swatch">${c}</span>`).join('')}
        </div>
      </div>
    `);
  }

  // Characteristics
  const chars = result.characteristics || result.composition_tips || [];
  if (chars.length) {
    cards.push(`
      <div class="result-card">
        <div class="result-card-title">📐 Key Characteristics</div>
        <ul class="characteristics-list">
          ${chars.map(c => `<li>${c}</li>`).join('')}
        </ul>
      </div>
    `);
  }

  // Camera settings (text mode)
  if (result.camera_settings) {
    const cs = result.camera_settings;
    cards.push(`
      <div class="result-card">
        <div class="result-card-title">⚙️ Camera Settings</div>
        <ul class="characteristics-list">
          ${Object.entries(cs).map(([k, v]) => `<li><strong style="color:var(--accent-gold)">${k}:</strong> ${v}</li>`).join('')}
        </ul>
      </div>
    `);
  }

  // Era context
  if (result.era_context) {
    cards.push(`
      <div class="result-card">
        <div class="result-card-title">📚 Era Context</div>
        <p class="mood-text">${result.era_context}</p>
      </div>
    `);
  }

  els.resultGrid.innerHTML = cards.join('');

  // Editing tips
  const tips = result.editing_tips || result.post_processing || [];
  if (tips.length) {
    els.editingTipsSection.innerHTML = `
      <div class="result-card" style="background:var(--bg-card)">
        <div class="tips-title">🔬 Darkroom Techniques & Editing Tips</div>
        <div class="tips-grid">
          ${tips.map((tip, i) => `
            <div class="tip-item">
              <span class="tip-num">0${i + 1}</span>
              <p class="tip-text">${tip}</p>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } else {
    els.editingTipsSection.innerHTML = '';
  }
}

// ===== HISTORY =====
function addToHistory(previewUrl, style, result) {
  const item = { previewUrl, style, result, time: new Date() };
  STATE.history.unshift(item);

  const historyEl = document.querySelector('.history-empty');
  if (historyEl) historyEl.remove();

  const timeStr = item.time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const styleIcons = { polaroid: '📷', film_grain: '🎞️', vhs_aesthetic: '📼', disposable_camera: '📸', slide_film: '🎨' };
  const icon = styleIcons[style] || '📷';

  const histItem = document.createElement('div');
  histItem.className = 'history-item';
  histItem.innerHTML = `
    ${previewUrl ? `<img class="history-thumb" src="${previewUrl}" alt="">` : `<div style="width:36px;height:36px;background:var(--bg-card);border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:1.2rem">${icon}</div>`}
    <div class="history-info">
      <div class="history-style">${icon} ${result.style_name || style}</div>
      <div class="history-time">${timeStr} • ${result.era || '1990s'}</div>
    </div>
  `;
  histItem.addEventListener('click', () => restoreFromHistory(item));
  els.historyList.prepend(histItem);
}

function restoreFromHistory(item) {
  showState('results');
  if (item.previewUrl) {
    els.photoDisplay.innerHTML = `<img src="${item.previewUrl}" alt="Photo">`;
  } else {
    els.photoDisplay.innerHTML = `<div style="font-size:3rem;text-align:center;padding:1rem;opacity:0.5">🎞️</div>`;
  }
  renderResults(item.result, { style: item.style, style_name: item.result.style_name, style_icon: '📷' });
}

// ===== NEW SESSION =====
els.newSessionBtn.addEventListener('click', () => {
  showState('welcome');
  STATE.selectedFile = null;
  els.photoPreviewArea.hidden = true;
  els.uploadZone.hidden = false;
  els.photoInput.value = '';
  updateProcessBtn();
  els.progressFill.style.width = '0%';
  els.processingLog.textContent = '';
});

// ===== TOAST NOTIFICATIONS =====
function showToast(msg, type = 'info') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ===== INIT =====
showState('welcome');
updateProcessBtn();

// --- Upload ---
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');
const progressBar = document.getElementById('progress-bar');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
  if (!file.name.endsWith('.pdf')) {
    setStatus('upload-status', 'Only PDF files are supported.', 'error');
    return;
  }

  setStatus('upload-status', `Uploading ${file.name}...`, 'info');
  progressBar.style.display = 'block';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/document/upload', { method: 'POST', body: formData });
    const data = await res.json();
    progressBar.style.display = 'none';
    if (res.ok) {
      setStatus('upload-status', `Uploaded successfully — ${data.chunks} chunks indexed.`, 'success');
      loadFiles();
    } else {
      setStatus('upload-status', 'Upload failed.', 'error');
    }
  } catch {
    progressBar.style.display = 'none';
    setStatus('upload-status', 'Upload failed — server error.', 'error');
  }

  fileInput.value = '';
}

// --- Query ---
const queryInput = document.getElementById('query-input');
const queryBtn = document.getElementById('query-btn');
const answerBox = document.getElementById('answer-box');

queryInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') submitQuery();
});

async function submitQuery() {
  const question = queryInput.value.trim();
  if (!question) return;

  queryBtn.disabled = true;
  queryBtn.innerHTML = '<span class="spinner"></span>Thinking...';
  answerBox.style.display = 'block';
  answerBox.textContent = '';

  try {
    const res = await fetch('/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: question })
    });
    const answer = await res.json();
    answerBox.innerHTML = marked.parse(answer);
  } catch {
    answerBox.textContent = 'Error — could not get an answer.';
  }

  queryBtn.disabled = false;
  queryBtn.textContent = 'Ask';
}

// --- File list ---
async function loadFiles() {
  const list = document.getElementById('file-list');
  try {
    const res = await fetch('/document/list');
    const data = await res.json();
    const files = data.files;

    if (!files.length) {
      list.innerHTML = '<div class="empty-state">No documents uploaded yet.</div>';
      return;
    }

    list.innerHTML = files.map(f => `
      <div class="file-item">
        <span class="file-name">${f}</span>
        <div class="file-actions">
          <button class="btn-view" onclick="viewFile('${f}')">View</button>
          <button class="btn-delete" onclick="deleteFile('${f}', this)">Delete</button>
        </div>
      </div>
    `).join('');
  } catch {
    list.innerHTML = '<div class="empty-state error">Failed to load files.</div>';
  }
}

async function deleteFile(filename, btn) {
  if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;
  btn.disabled = true;
  btn.textContent = '...';
  try {
    await fetch(`/document/delete?filename=${encodeURIComponent(filename)}`, { method: 'DELETE' });
    loadFiles();
  } catch {
    btn.disabled = false;
    btn.textContent = 'Delete';
  }
}

function viewFile(filename) {
  const viewer = document.getElementById('pdf-viewer');
  const card = document.getElementById('viewer-card');
  const title = document.getElementById('viewer-title');
  viewer.src = `/document/read?filename=${encodeURIComponent(filename)}`;
  viewer.style.display = 'block';
  card.style.display = 'block';
  title.textContent = `Viewing: ${filename}`;
  card.scrollIntoView({ behavior: 'smooth' });
}

// --- Helpers ---
function setStatus(id, message, type) {
  const el = document.getElementById(id);
  el.className = `upload-status ${type}`;
  el.textContent = message;
}

loadFiles();

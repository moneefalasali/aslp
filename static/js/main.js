function safeStorageGet(key, defaultValue = null) {
    try {
        return localStorage.getItem(key);
    } catch (e) {
        return defaultValue;
    }
}

function safeStorageSet(key, value) {
    try {
        localStorage.setItem(key, value);
    } catch (e) {
        // ignore storage access issues
    }
}

function safeStorageRemove(key) {
    try {
        localStorage.removeItem(key);
    } catch (e) {
        // ignore storage access issues
    }
}

// Application State
let state = {
    currentPage: 'home',
    file: null,
    isProcessing: false,
    progress: 0,
    analysisResult: null,
    history: [],
    selectedAnswers: {},
    darkMode: safeStorageGet('darkMode') === 'true',
    user: JSON.parse(safeStorageGet('user') || 'null'),
    token: safeStorageGet('access_token')
};

// Initialize
function init() {
    lucide.createIcons();
    applyDarkMode();
    updateAuthUI();
    if (state.token) loadHistory();
    
    // Setup Drag & Drop
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        dropZone.onclick = () => document.getElementById('file-input').click();
        dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add('dragging'); };
        dropZone.ondragleave = () => dropZone.classList.remove('dragging');
        dropZone.ondrop = (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragging');
            if (e.dataTransfer.files.length > 0) handleFileSelect(e.dataTransfer.files[0]);
        };
    }

    document.getElementById('file-input').onchange = (e) => {
        if (e.target.files.length > 0) handleFileSelect(e.target.files[0]);
    };
}

// Navigation
function navigate(page) {
    state.currentPage = page;
    if (page !== 'home' && !state.token) {
        window.location.href = '/login';
        return;
    }

    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.getElementById(`page-${page}`).classList.remove('hidden');
    
    // Update Bottom Nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('onclick').includes(page)) item.classList.add('active');
    });

    if (page === 'history') renderHistory();
    if (page === 'profile') renderProfile();
    window.scrollTo(0, 0);
    lucide.createIcons();
}

// File Handling
function handleFileSelect(file) {
    if (!state.token) {
        window.location.href = '/login';
        return;
    }

    const allowed = ['.pdf', '.docx', '.doc', '.mp3', '.wav', '.m4a'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowed.includes(ext)) {
        showNotification('صيغة الملف غير مدعومة', 'error');
        return;
    }

    state.file = file;
    document.getElementById('file-info').classList.remove('hidden');
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-size').textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
    document.getElementById('upload-btn').disabled = false;
    
    const icon = file.type.startsWith('audio/') ? 'mic' : 'file-text';
    document.getElementById('file-icon').setAttribute('data-lucide', icon);
    lucide.createIcons();
}

function resetUploadState() {
    state.file = null;
    document.getElementById('file-info').classList.add('hidden');
    document.getElementById('upload-btn').disabled = true;
    document.getElementById('file-input').value = '';
}

// API Integration
async function handleUpload() {
    if (!state.file || state.isProcessing) return;
    if (!state.token) {
        window.location.href = '/login';
        return;
    }

    state.isProcessing = true;
    document.getElementById('upload-btn').disabled = true;
    document.getElementById('progress-section').classList.remove('hidden');
    
    try {
        const formData = new FormData();
        formData.append('file', state.file);

        // 1. Upload
        updateProgress(20, 'جاري رفع الملف...');
        const uploadRes = await fetch('/api/upload', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` },
            body: formData
        });
        const uploadData = await uploadRes.json();
        if (!uploadRes.ok) {
            throw new Error(uploadData.detail || 'فشل الرفع');
        }
        const { file_url, file_id } = uploadData;

        // 2. Process
        updateProgress(50, 'جاري استخراج النصوص...');
        const type = state.file.type.startsWith('audio/') ? 'audio' : 'pdf';
        const processRes = await fetch(type === 'audio' ? '/api/process-audio' : '/api/process-pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ file_url })
        });
        const processData = await processRes.json();
        if (!processRes.ok) {
            throw new Error(processData.detail || 'فشل استخراج النصوص');
        }
        const { text } = processData;

        // 3. Analyze
        updateProgress(80, 'جاري التحليل بالذكاء الاصطناعي...');
        const mode = document.querySelector('input[name="analysis-type"]:checked').value;
        const lang = document.querySelector('input[name="analysis-language"]:checked').value;
        
        const analyzeRes = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                text, file_id, file_name: state.file.name,
                analysis_type: mode, target_language: lang
            })
        });
        const analyzeData = await analyzeRes.json();
        if (!analyzeRes.ok) {
            throw new Error(analyzeData.detail || 'فشل في تحليل النص');
        }
        const result = analyzeData;
        
        updateProgress(100, 'اكتمل التحليل!');
        state.analysisResult = { ...result, fileName: state.file.name, id: file_id };
        
        setTimeout(() => {
            displayResults(state.analysisResult);
            navigate('results');
            state.isProcessing = false;
            document.getElementById('progress-section').classList.add('hidden');
        }, 800);

    } catch (err) {
        showNotification(err.message, 'error');
        state.isProcessing = false;
        document.getElementById('upload-btn').disabled = false;
    }
}

function updateProgress(val, status) {
    document.getElementById('progress-fill').style.width = val + '%';
    document.getElementById('progress-text').textContent = val + '%';
    document.getElementById('progress-status').textContent = status;
}

// UI Rendering
function displayResults(res) {
    document.getElementById('res-file-name').textContent = res.fileName;
    document.getElementById('res-summary').textContent = res.summary || 'لا يوجد ملخص';
    
    const pointsList = document.getElementById('res-key-points');
    pointsList.innerHTML = (res.key_points || []).map(p => `<li>• ${p}</li>`).join('');
    
    const quizContainer = document.getElementById('res-quizzes');
    quizContainer.innerHTML = (res.quizzes || []).map((q, i) => `
        <div class="quiz-card mb-6">
            <p class="font-semibold mb-3">${i+1}. ${q.question}</p>
            <div class="space-y-2">
                ${q.options.map((opt, oi) => `
                    <button class="option-btn" onclick="checkAnswer(${i}, ${oi}, ${q.correct_answer}, this)">
                        ${opt}
                    </button>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function checkAnswer(qIdx, sIdx, cIdx, btn) {
    const card = btn.closest('.quiz-card');
    const buttons = card.querySelectorAll('.option-btn');
    buttons.forEach(b => b.disabled = true);
    
    if (sIdx === cIdx) {
        btn.classList.add('correct');
        showNotification('إجابة صحيحة!', 'success');
    } else {
        btn.classList.add('incorrect');
        buttons[cIdx].classList.add('correct');
        showNotification('إجابة خاطئة، حاول في السؤال القادم', 'error');
    }
}

function downloadSummary() {
    if (!state.analysisResult || !state.analysisResult.id) {
        showNotification('لا يوجد تقرير للتنزيل بعد.', 'error');
        return;
    }
    if (!state.token) {
        window.location.href = '/login';
        return;
    }
    const url = `/api/download-summary/${state.analysisResult.id}`;
    window.open(url, '_blank');
}

// Dark Mode
function toggleDarkMode() {
    state.darkMode = !state.darkMode;
    safeStorageSet('darkMode', state.darkMode);
    applyDarkMode();
}

function applyDarkMode() {
    document.body.classList.toggle('dark-mode', state.darkMode);
    const icon = document.querySelector('#dark-mode-toggle i');
    if (icon) icon.setAttribute('data-lucide', state.darkMode ? 'sun' : 'moon');
    lucide.createIcons();
}

// Notifications
function showNotification(msg, type = 'info') {
    const n = document.getElementById('notification');
    n.textContent = msg;
    n.className = `notification show notification-${type}`;
    setTimeout(() => n.classList.remove('show'), 3000);
}

// History
async function loadHistory() {
    if (!state.token) {
        state.history = [];
        return [];
    }

    try {
        const res = await fetch('/api/history', {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'فشل تحميل السجل');
        }
        state.history = data;
        return data;
    } catch (err) {
        showNotification(err.message, 'error');
        state.history = [];
        return [];
    }
}

function renderHistory() {
    const historyList = document.getElementById('history-list');
    if (!historyList) return;

    if (!state.history || state.history.length === 0) {
        historyList.innerHTML = '<div class="card"><p class="text-muted">لا يوجد سجل حتى الآن.</p></div>';
        return;
    }

    historyList.innerHTML = state.history.map(item => `
        <div class="card">
            <div class="flex justify-between items-start gap-4">
                <div>
                    <h4>${item.file_name || 'ملف غير معروف'}</h4>
                    <p class="text-muted">${item.created_at ? new Date(item.created_at).toLocaleString('ar-EG') : ''}</p>
                    <p class="text-muted">${item.file_type ? item.file_type.toUpperCase() : 'نوع غير معروف'}</p>
                    <p class="text-muted mt-2">${item.summary || 'لا يوجد ملخص'}</p>
                </div>
                <div class="flex flex-col gap-2">
                    <button class="btn btn-primary" onclick="viewHistoryItem('${item.file_id}')">عرض النتائج</button>
                    <button class="btn btn-outline" onclick="window.open('/api/download-summary/${item.file_id}', '_blank')">تحميل الملخص</button>
                </div>
            </div>
        </div>
    `).join('');
}

async function viewHistoryItem(fileId) {
    if (!state.token) {
        window.location.href = '/login';
        return;
    }

    try {
        const res = await fetch(`/api/results/${fileId}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'فشل جلب النتائج');
        }

        state.analysisResult = {
            ...data,
            fileName: data.file_name || 'النتائج'
        };
        displayResults(state.analysisResult);
        navigate('results');
    } catch (err) {
        showNotification(err.message, 'error');
    }
}

// Auth UI
function updateAuthUI() {
    if (state.user && state.token) {
        document.getElementById('auth-buttons').classList.add('hidden');
        document.getElementById('user-profile').classList.remove('hidden');
        document.getElementById('user-name').textContent = state.user.username;
    } else {
        document.getElementById('auth-buttons').classList.remove('hidden');
        document.getElementById('user-profile').classList.add('hidden');
    }
}

function renderProfile() {
    if (!state.user) return;
    document.getElementById('profile-username').textContent = state.user.username || '-';
    document.getElementById('profile-fullname').textContent = state.user.full_name || '-';
    document.getElementById('profile-email').textContent = state.user.email || '-';
}

function logout() {
    safeStorageRemove('access_token');
    safeStorageRemove('user');
    state.token = null;
    state.user = null;
    updateAuthUI();
    window.location.href = '/login';
}

function selectOption(name, value, el) {
    document.getElementsByName(name).forEach(i => i.checked = false);
    const input = el.querySelector('input');
    input.checked = true;
    
    // Visual feedback
    el.parentElement.querySelectorAll('div').forEach(d => d.style.borderColor = 'var(--border)');
    el.style.borderColor = 'var(--primary)';
}

window.onload = init;

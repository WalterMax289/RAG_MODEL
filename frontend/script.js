// ─── CONFIG ───
const CONFIG = {
    title: "AI-PERSONAL BRAIN",
    pathCount: 20
};

// ─── SIMPLE MARKDOWN RENDERER ───
function renderMarkdown(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.1);padding:2px 5px;border-radius:4px;font-size:0.9em;">$1</code>')
        .replace(/\n/g, '<br>');
}

// ─── FLOATING PATHS (KokonutUI style) ───
function createFloatingPaths(position, container) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'w-full h-full absolute inset-0');
    svg.setAttribute('viewBox', '0 0 696 316');
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('fill', 'none');
    
    const allPaths = [];
    for (let i = 0; i < 36; i++) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const d = `M-${380 - i * 5 * position} -${189 + i * 6}C-${380 - i * 5 * position} -${189 + i * 6} -${312 - i * 5 * position} ${216 - i * 6} ${152 - i * 5 * position} ${343 - i * 6}C${616 - i * 5 * position} ${470 - i * 6} ${684 - i * 5 * position} ${875 - i * 6} ${684 - i * 5 * position} ${875 - i * 6}`;
        
        path.setAttribute('d', d);
        path.setAttribute('stroke', 'currentColor');
        path.setAttribute('stroke-width', (0.5 + i * 0.03).toString());
        path.setAttribute('stroke-opacity', '0.7');
        path.setAttribute('stroke-linecap', 'round');
        
        svg.appendChild(path);
        allPaths.push(path);
    }
    
    container.appendChild(svg);
    return allPaths;
}

function animatePath(path) {
    const length = path.getTotalLength();
    if (!length) return;
    
    const duration = 20000 + Math.random() * 10000;
    const startTime = performance.now();
    
    function step(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = (elapsed % duration) / duration;
        
        // Offset and length smoothly loop: 0 -> 1 -> 0
        const t = progress < 0.5 ? progress * 2 : 2 - progress * 2;
        
        const dashLength = length * 0.3 + (length * 0.7 * t);
        const offset = -length * t;
        const opacity = 0.7; // Set to 0.7 as requested
        
        path.style.strokeDasharray = `${dashLength} ${length}`;
        path.style.strokeDashoffset = offset;
        path.style.opacity = opacity;
        
        requestAnimationFrame(step);
    }
    
    requestAnimationFrame(step);
}

function animateTitle() {
    const titleEl = document.getElementById('title');
    if (titleEl.dataset.animated === '1') return;
    titleEl.dataset.animated = '1';
    titleEl.innerHTML = '';
    const words = CONFIG.title.split(' ');
    words.forEach((word, wordIndex) => {
        const ws = document.createElement('span');
        ws.className = 'word';
        word.split('').forEach((letter, letterIndex) => {
            const ls = document.createElement('span');
            ls.className = 'letter';
            ls.textContent = letter;
            const delay = (wordIndex * 0.1 + letterIndex * 0.03) * 1000;
            setTimeout(() => {
                ls.style.transition = 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)';
                ls.style.transform = 'translateY(0)';
                ls.style.opacity = '1';
            }, delay);
            ws.appendChild(ls);
        });
        titleEl.appendChild(ws);
    });
}

function resetTitle() {
    const titleEl = document.getElementById('title');
    titleEl.dataset.animated = '0';
    titleEl.innerHTML = '';
}

function initBackground() {
    const container = document.getElementById('paths-container');
    if (!container) return;
    container.innerHTML = ''; // clear any existing content

    const p1 = createFloatingPaths(1, container);
    const p2 = createFloatingPaths(-1, container);
    [...p1, ...p2].forEach(p => animatePath(p));
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBackground);
} else {
    initBackground();
}

// ─── CONNECTION TOGGLE (Online / Offline) ───
(function initConnectionToggle() {
    const toggle = document.getElementById('connectionToggle');
    const checkbox = document.getElementById('connectionCheckbox');
    const label = document.getElementById('connectionLabel');
    const statusDot = document.querySelector('.chat-header .status-dot');
    const knobLeft = toggle.querySelector('.knob-left');
    const knobRight = toggle.querySelector('.knob-right');

    function applyState(checked) {
        knobLeft.style.transformOrigin = '16px 16px';
        knobRight.style.transformOrigin = '36px 36px';

        if (checked) {
            knobLeft.style.transform = 'translateX(12px) scale(0)';
            knobRight.style.transform = 'translateX(0px) scale(1)';
            label.textContent = 'Online';
            label.classList.add('online');
            if (statusDot) {
                statusDot.classList.remove('offline');
                statusDot.classList.add('online');
            }
        } else {
            knobLeft.style.transform = 'translateX(0px) scale(1)';
            knobRight.style.transform = 'translateX(-12px) scale(0)';
            label.textContent = 'Offline';
            label.classList.remove('online');
            if (statusDot) {
                statusDot.classList.remove('online');
                statusDot.classList.add('offline');
            }
        }

        toggle.classList.toggle('checked', checked);
    }

    knobLeft.style.transition = 'none';
    knobRight.style.transition = 'none';

    const saved = localStorage.getItem('ragConnectionMode');
    const isOnline = saved === 'online';
    checkbox.checked = isOnline;
    applyState(isOnline);

    requestAnimationFrame(() => requestAnimationFrame(() => {
        knobLeft.style.transition = '';
        knobRight.style.transition = '';
    }));

    toggle.addEventListener('click', (e) => {
        e.preventDefault();
        checkbox.checked = !checkbox.checked;
        applyState(checkbox.checked);
        localStorage.setItem('ragConnectionMode', checkbox.checked ? 'online' : 'offline');
    });

    checkbox.addEventListener('change', () => applyState(checkbox.checked));
})();

// ─── THEME TOGGLE (Dark / Light) ───
function toggleTheme() {
    const btn = document.getElementById('themeToggleBtn');
    const icon = document.getElementById('themeIcon');
    const isLight = document.body.classList.toggle('light');

    if (icon) icon.src = isLight ? 'assets/sun.svg' : 'assets/moon.svg';
    localStorage.setItem('ragTheme', isLight ? 'light' : 'dark');

    btn.classList.remove('spinning');
    void btn.offsetWidth; // force reflow to restart animation
    btn.classList.add('spinning');
    btn.addEventListener('animationend', () => btn.classList.remove('spinning'), { once: true });
}

function initTheme() {
    const saved = localStorage.getItem('ragTheme');
    const icon = document.getElementById('themeIcon');
    if (saved === 'light') {
        document.body.classList.add('light');
        if (icon) icon.src = 'assets/sun.svg';
    } else {
        document.body.classList.remove('light');
        if (icon) icon.src = 'assets/moon.svg';
    }
}

// ─── INTERACTIVE MARQUEE ───
(function initTechMarquee() {
    const track = document.getElementById('techMarqueeTrack');
    const tags = [
        { icon: '🗄️', label: 'Vector DB' },
        { icon: '🔗', label: 'LangChain' },
        { icon: '🐍', label: 'Python' },
        { icon: '🌐', label: 'HTML' },
        { icon: '🎨', label: 'CSS' },
        { icon: '⚛️', label: 'React' },
        { icon: '🦙', label: 'LlamaIndex' },
        { icon: '🧠', label: 'Embeddings' },
        { icon: '📦', label: 'Chunking' },
        { icon: '🔍', label: 'Semantic Search' },
        { icon: '📄', label: 'Document Parsing' },
        { icon: '🧪', label: 'Reranking' },
        { icon: '⚡', label: 'FastAPI' },
        { icon: '🗣️', label: 'LLM' },
        { icon: '🔒', label: 'Private & Local' },
        { icon: '🧠', label: 'Vector Search' },
        { icon: '⚡', label: 'LLM Synthesis' },
    ];

    function buildPills() {
        track.innerHTML = '';
        const triple = [...tags, ...tags, ...tags];
        triple.forEach(t => {
            const pill = document.createElement('div');
            pill.className = 'tech-pill';
            pill.innerHTML = `<span class="pill-icon">${t.icon}</span>${t.label}`;
            track.appendChild(pill);
        });
    }
    buildPills();

    let isDown = false;
    let startX = 0;
    let scrollLeft = 0;
    let rafId = null;
    let momentum = 0;
    let lastMoveX = 0;
    let lastMoveTime = 0;

    const wrap = document.getElementById('techMarquee');

    function stopMomentum() {
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }
        momentum = 0;
    }

    wrap.addEventListener('mousedown', e => {
        isDown = true;
        wrap.classList.add('active');
        startX = e.pageX - wrap.offsetLeft;
        scrollLeft = parseFloat(track.dataset.x) || 0;
        lastMoveX = e.pageX;
        lastMoveTime = Date.now();
        stopMomentum();
        track.style.transition = 'none';
    });

    wrap.addEventListener('mousemove', e => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - wrap.offsetLeft;
        const walk = (x - startX) * 1;
        const now = Date.now();
        const dt = now - lastMoveTime;
        if (dt > 0) {
            momentum = (e.pageX - lastMoveX) * 0.6;
        }
        lastMoveX = e.pageX;
        lastMoveTime = now;
        track.dataset.x = scrollLeft + walk;
        track.style.transform = `translateX(${scrollLeft + walk}px)`;
    });

    function onUp() {
        if (!isDown) return;
        isDown = false;
        wrap.classList.remove('active');
        if (Math.abs(momentum) > 0.5) {
            applyMomentum();
        }
    }

    wrap.addEventListener('mouseup', onUp);
    wrap.addEventListener('mouseleave', onUp);

    function applyMomentum() {
        const current = parseFloat(track.dataset.x) || 0;
        momentum *= 0.92;
        const next = current + momentum;
        track.dataset.x = next;
        track.style.transition = 'none';
        track.style.transform = `translateX(${next}px)`;
        if (Math.abs(momentum) > 0.3) {
            rafId = requestAnimationFrame(applyMomentum);
        } else {
            stopMomentum();
        }
    }

    let autoScrollId = null;
    let autoPos = 0;

    function startAutoScroll() {
        function step() {
            if (!isDown) {
                autoPos -= 0.25;
                const tagW = 120;
                const totalW = tags.length * (tagW + 10);
                if (Math.abs(autoPos) >= totalW) autoPos = 0;
                track.dataset.x = autoPos;
                track.style.transition = 'none';
                track.style.transform = `translateX(${autoPos}px)`;
            }
            autoScrollId = requestAnimationFrame(step);
        }
        autoScrollId = requestAnimationFrame(step);
    }

    wrap.addEventListener('mousedown', () => { stopMomentum(); });
    startAutoScroll();
})();

// ─── SCROLL REVEAL ANIMATIONS (both directions) ───
function initScrollReveal() {
    const revealEls = Array.from(document.querySelectorAll('.reveal'));
    const chatWrapper = document.getElementById('chatWrapper');
    if (chatWrapper) revealEls.push(chatWrapper);
    const titleEl = document.getElementById('title');
    if (titleEl) revealEls.push(titleEl);

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                if (entry.target === titleEl) animateTitle();
            } else {
                entry.target.classList.remove('visible');
                if (entry.target === titleEl) resetTitle();
            }
        });
    }, { threshold: 0.15 });

    revealEls.forEach(el => observer.observe(el));
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScrollReveal);
} else {
    initScrollReveal();
}

// ─── FILE UPLOAD ───
let selectedFiles = [];
let serverDocs = [];

async function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    if (!files.length) return;
    for (const file of files) {
        if (!selectedFiles.find(f => f.name === file.name)) {
            selectedFiles.push(file);
            await uploadFileToServer(file);
        }
    }
    renderFilePills();
    await loadServerDocs();
    event.target.value = '';
}

async function uploadFileToServer(file) {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await fetch('http://localhost:8000/api/upload', {
            method: 'POST',
            body: formData,
        });
        if (!res.ok) {
            const err = await res.json();
            console.error('Upload error:', err.detail);
        }
    } catch (e) {
        console.error('Upload failed:', e);
    }
}

function renderFilePills() {
    const area = document.getElementById('file-pill-area');
    area.innerHTML = selectedFiles.map((f, i) => `
        <div class="file-pill">
            📄 <span title="${f.name}">${f.name.length > 20 ? f.name.slice(0, 18) + '…' : f.name}</span>
            <span class="file-pill-remove" onclick="removeFile(${i})">×</span>
        </div>
    `).join('');
}

async function removeFile(index) {
    const file = selectedFiles[index];
    selectedFiles.splice(index, 1);
    renderFilePills();
    try {
        await fetch(`http://localhost:8000/api/documents/${encodeURIComponent(file.name)}`, {
            method: 'DELETE',
        });
    } catch (e) { /* ignore */ }
    await loadServerDocs();
}

async function loadServerDocs() {
    try {
        const res = await fetch('http://localhost:8000/api/documents');
        if (res.ok) {
            const data = await res.json();
            serverDocs = data.documents || [];
            renderDocPanel();
        }
    } catch (e) { /* ignore */ }
}

// ─── CHAT ───
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const suggestionsDiv = document.getElementById('suggestions');



function checkEnter(e) {
    if (e.key === 'Enter') sendMessage();
}

function fillInput(el) {
    chatInput.value = el.innerText;
    sendMessage();
}

function addMessage(text, type, name) {
    const div = document.createElement('div');
    div.className = `message ${type}`;

    const avatarEl = document.createElement('div');
    avatarEl.className = `avatar ${type}`;
    avatarEl.textContent = type === 'ai' ? 'V' : 'U';

    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'bubble';
    bubbleEl.innerHTML = type === 'ai' ? renderMarkdown(text) : text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

    if (type === 'ai') {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = '📋';
        copyBtn.dataset.copyText = text;
        copyBtn.onclick = function() { copyMessage(this); };
        bubbleEl.appendChild(copyBtn);
    }

    div.appendChild(avatarEl);
    div.appendChild(bubbleEl);
    chatMessages.appendChild(div);
    chatHistory.push({ type, text, name });
    saveChat();
    setTimeout(() => chatMessages.scrollTop = chatMessages.scrollHeight, 50);
}

function showTyping() {
    const div = document.createElement('div');
    div.className = 'message ai';
    div.id = 'typing-indicator';
    div.innerHTML = `
        <div class="avatar ai">V</div>
        <div class="bubble typing-wave">
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
            <div class="wave-bar"></div>
        </div>
    `;
    chatMessages.appendChild(div);
    setTimeout(() => chatMessages.scrollTop = chatMessages.scrollHeight, 50);
}

function removeTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

async function sendMessage() {
    const val = chatInput.value.trim();
    if (!val) return;

    addMessage(val, 'user', 'Me');
    chatInput.value = '';

    suggestionsDiv.style.opacity = '0';
    suggestionsDiv.style.pointerEvents = 'none';

    showTyping();

    try {
        const isOnline = document.getElementById('connectionCheckbox').checked;
        const selectedModel = isOnline ? 'online' : 'offline';
        const res = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: val, model: selectedModel })
        });

        if (!res.ok) {
            throw new Error('Network response was not ok');
        }

        const response = await res.json();

        const delay = 600 + Math.random() * 400;

        setTimeout(() => {
            removeTyping();
            addMessage(response.text, 'ai', 'V');

            setTimeout(() => {
                suggestionsDiv.innerHTML = response.followups
                    .map(f => `<div class="sugg-pill" onclick="fillInput(this)">${f}</div>`)
                    .join('');
                suggestionsDiv.style.opacity = '1';
                suggestionsDiv.style.pointerEvents = 'auto';
            }, 400);
        }, delay);

    } catch (error) {
        console.error("Error:", error);
        removeTyping();
        addMessage("Sorry, I'm having trouble connecting to the server.", 'ai', 'V');
    }
}

// ─── CHAT HISTORY ───
let chatHistory = [];

function saveChat() {
    try {
        const data = { history: chatHistory, files: selectedFiles.map(f => f.name) };
        localStorage.setItem('ragChatHistory', JSON.stringify(data));
    } catch (e) { /* storage full */ }
}

function loadChat() {
    try {
        const raw = localStorage.getItem('ragChatHistory');
        if (!raw) return;
        const data = JSON.parse(raw);
        if (data.history && data.history.length) {
            chatHistory = data.history;
            chatMessages.innerHTML = '';
            chatHistory.forEach(msg => {
                const div = document.createElement('div');
                div.className = `message ${msg.type}`;

                const avatarEl = document.createElement('div');
                avatarEl.className = `avatar ${msg.type}`;
                avatarEl.textContent = msg.type === 'ai' ? 'V' : 'U';

                const bubbleEl = document.createElement('div');
                bubbleEl.className = 'bubble';
                bubbleEl.innerHTML = msg.type === 'ai'
                    ? renderMarkdown(msg.text)
                    : msg.text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

                if (msg.type === 'ai') {
                    const copyBtn = document.createElement('button');
                    copyBtn.className = 'copy-btn';
                    copyBtn.textContent = '📋';
                    copyBtn.dataset.copyText = msg.text;
                    copyBtn.onclick = function() { copyMessage(this); };
                    bubbleEl.appendChild(copyBtn);
                }

                div.appendChild(avatarEl);
                div.appendChild(bubbleEl);
                chatMessages.appendChild(div);
            });
            setTimeout(() => chatMessages.scrollTop = chatMessages.scrollHeight, 100);
            suggestionsDiv.style.opacity = '0';
            suggestionsDiv.style.pointerEvents = 'none';
        }
    } catch (e) { /* ignore corrupt data */ }
}

function clearChat() {
    if (!confirm('Clear all chat messages?')) return;
    chatHistory = [];
    chatMessages.innerHTML = `
        <div class="message ai">
            <div class="avatar ai">V</div>
            <div class="bubble">
                I've analyzed your documents and mapped your local vectors. What would you like to know about
                your data?
            </div>
        </div>
    `;
    suggestionsDiv.style.opacity = '1';
    suggestionsDiv.style.pointerEvents = 'auto';
    localStorage.removeItem('ragChatHistory');
}

function exportChat() {
    if (!chatHistory.length) {
        alert('No chat messages to export.');
        return;
    }
    const format = confirm('Click OK for JSON format, Cancel for plain text.');
    let content, filename, mime;
    if (format) {
        content = JSON.stringify(chatHistory, null, 2);
        filename = `chat-export-${Date.now()}.json`;
        mime = 'application/json';
    } else {
        content = chatHistory.map(m => `[${m.type.toUpperCase()}] ${m.text}`).join('\n\n---\n\n');
        filename = `chat-export-${Date.now()}.txt`;
        mime = 'text/plain';
    }
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ─── COPY MESSAGE ───
function copyMessage(btn) {
    const text = btn.dataset.copyText || '';
    const finish = () => {
        btn.textContent = '✓';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = '📋'; btn.classList.remove('copied'); }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(finish).catch(() => fallbackCopy(text, finish));
    } else {
        fallbackCopy(text, finish);
    }
}

function fallbackCopy(text, callback) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    if (callback) callback();
}

// ─── DOCUMENT PANEL ───
let docPanelOpen = false;

function toggleDocPanel() {
    docPanelOpen = !docPanelOpen;
    document.getElementById('docPanel').classList.toggle('open', docPanelOpen);
    document.getElementById('docPanelBackdrop').classList.toggle('open', docPanelOpen);
    document.getElementById('docPanelToggle').classList.toggle('hidden', docPanelOpen);
}

function renderDocPanel() {
    const list = document.getElementById('docList');
    const docs = serverDocs.length ? serverDocs : selectedFiles.map(f => ({
        filename: f.name,
        size: f.size,
        chunks: 0,
    }));
    if (!docs.length) {
        list.innerHTML = `
            <div class="doc-empty">
                <div class="doc-empty-icon">📄</div>
                No documents uploaded yet.<br>Upload files to see them here.
            </div>
        `;
        return;
    }
    list.innerHTML = docs.map((d, i) => {
        const ext = d.filename.split('.').pop().toLowerCase();
        const icon = ext === 'pdf' ? '📕' : ext === 'png' || ext === 'jpg' || ext === 'jpeg' ? '🖼️' : '📄';
        const size = d.size > 1024 * 1024 ? (d.size / (1024 * 1024)).toFixed(1) + ' MB' : (d.size / 1024).toFixed(1) + ' KB';
        const safeFilename = d.filename.replace(/'/g, '&#39;');
        const localIdx = selectedFiles.findIndex(f => f.name === d.filename);
        const previewBtn = localIdx !== -1
            ? `<button class="doc-item-btn" onclick="previewFile(${localIdx})" title="Preview">👁️</button>`
            : '';
        return `
            <div class="doc-item">
                <div class="doc-item-icon">${icon}</div>
                <div class="doc-item-info">
                    <div class="doc-item-name" title="${safeFilename}">${d.filename.length > 22 ? d.filename.slice(0, 20) + '…' : d.filename}</div>
                    <div class="doc-item-size">${size}</div>
                </div>
                <div class="doc-item-actions">
                    ${previewBtn}
                    <button class="doc-item-btn" onclick="removeDocFromServer('${safeFilename}')" title="Remove">🗑️</button>
                </div>
            </div>
        `;
    }).join('');
}

async function removeDocFromServer(filename) {
    selectedFiles = selectedFiles.filter(f => f.name !== filename);
    renderFilePills();
    try {
        await fetch(`http://localhost:8000/api/documents/${encodeURIComponent(filename)}`, {
            method: 'DELETE',
        });
    } catch (e) { /* ignore */ }
    await loadServerDocs();
}

// ─── FILE PREVIEW ───
let previewFileIndex = -1;
let previewBlobUrl = null;

function previewFile(index) {
    const file = selectedFiles[index];
    if (!file) return;
    const modal = document.getElementById('previewModal');
    const content = document.getElementById('previewContent');
    const name = document.getElementById('previewName');
    name.textContent = file.name;

    if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
        previewBlobUrl = null;
    }

    if (file.type.startsWith('image/')) {
        previewBlobUrl = URL.createObjectURL(file);
        content.innerHTML = `<img src="${previewBlobUrl}" alt="${file.name}" style="max-width:100%;max-height:85vh;">`;
    } else if (file.type === 'application/pdf') {
        previewBlobUrl = URL.createObjectURL(file);
        content.innerHTML = `<iframe src="${previewBlobUrl}" style="width:80vw;height:80vh;border:none;"></iframe>`;
    } else {
        const reader = new FileReader();
        reader.onload = function(e) {
            const text = e.target.result;
            content.innerHTML = `<pre style="color:#e2e8f0;background:rgba(0,0,0,0.3);padding:20px;border-radius:12px;overflow:auto;max-height:80vh;max-width:80vw;font-size:13px;line-height:1.6;white-space:pre-wrap;word-break:break-word;margin:0;">${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>`;
        };
        reader.readAsText(file);
    }
    modal.classList.add('open');
}

function closePreview(event) {
    if (event && event.target !== event.currentTarget) return;
    const modal = document.getElementById('previewModal');
    modal.classList.remove('open');
    document.getElementById('previewContent').innerHTML = '';
    document.getElementById('previewName').textContent = '';
    if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
        previewBlobUrl = null;
    }
}

// ─── TOAST NOTIFICATION ───
function showToast(msg) {
    let toast = document.getElementById('toast-notification');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast-notification';
        toast.style.cssText = 'position:fixed;bottom:32px;left:50%;transform:translateX(-50%) translateY(20px);background:rgba(30,30,30,0.95);color:#e2e8f0;padding:10px 20px;border-radius:10px;font-size:13px;font-weight:500;border:1px solid rgba(255,255,255,0.1);z-index:999;opacity:0;transition:opacity 0.3s,transform 0.3s;pointer-events:none;backdrop-filter:blur(8px);';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    });
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(20px)';
    }, 2500);
}

// ─── MODEL SELECTION ───
function loadModel() {
    const saved = localStorage.getItem('ragSelectedModel');
    if (saved) {
        document.getElementById('modelSelect').value = saved;
    }
}

function saveModel() {
    const val = document.getElementById('modelSelect').value;
    localStorage.setItem('ragSelectedModel', val);
    showToast(`Model switched to ${val}`);
}

// ─── INIT ───
function initFeatures() {
    initTheme();
    loadChat();
    loadServerDocs();
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        loadModel();
        modelSelect.addEventListener('change', saveModel);
    }
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closePreview();
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFeatures);
} else {
    initFeatures();
}

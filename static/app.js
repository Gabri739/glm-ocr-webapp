
/**
 * GLM OCR PDF Converter - Frontend Logic
 */

// Stato dell'applicazione
const state = {
    images: [],           // Array di immagini base64
    markdowns: [],       // Array di markdown per ogni pagina
    currentPage: 0,      // Pagina corrente (0-indexed)
    totalPages: 0,       // Numero totale di pagine
    isProcessing: false, // Stato elaborazione
    filename: '',        // Nome del file caricato
    editMode: false      // Modalità edit
};

// Elementi DOM
const elements = {
    fileInput: document.getElementById('fileInput'),
    status: document.getElementById('status'),
    progressBar: document.getElementById('progressBar'),
    pdfPanel: document.getElementById('pdfPanel'),
    markdownPanel: document.getElementById('markdownPanel'),
    pageNav: document.getElementById('pageNav'),
    pageInfo: document.getElementById('pageInfo'),
    prevPage: document.getElementById('prevPage'),
    nextPage: document.getElementById('nextPage'),
    processAll: document.getElementById('processAll'),
    exportBtn: document.getElementById('exportBtn'),
    exportDropdown: document.getElementById('exportDropdown'),
    editToggle: document.getElementById('editToggle'),
    ocrStatus: document.getElementById('ocrStatus')
};

// API Endpoints
const API_BASE = window.location.origin;

// Inizializzazione
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkHealth();
});

function setupEventListeners() {
    // Upload file
    elements.fileInput.addEventListener('change', handleFileUpload);

    // Navigazione pagine
    elements.prevPage.addEventListener('click', () => navigatePage(-1));
    elements.nextPage.addEventListener('click', () => navigatePage(1));

    // Elaborazione
    elements.processAll.addEventListener('click', processAllPages);

    // Export
    elements.exportBtn.addEventListener('click', toggleExportMenu);
    document.querySelectorAll('.export-item').forEach(item => {
        item.addEventListener('click', (e) => exportFile(e.target.dataset.format));
    });

    // Chiudi menu export cliccando fuori
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.export-menu')) {
            elements.exportDropdown.classList.remove('show');
        }
    });

    // Toggle edit mode
    elements.editToggle.addEventListener('click', toggleEditMode);

    // Tastiera
    document.addEventListener('keydown', handleKeyboard);
}

// Controlla se Ollama è disponibile
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();

        if (!data.ollama_connected) {
            setStatus('⚠️ Ollama non raggiungibile su localhost:11434', 'error');
        } else if (!data.glm_ocr_available) {
            setStatus('⚠️ Modello glm-ocr non trovato. Esegui: ollama pull glm-ocr', 'error');
        } else {
            setStatus('Pronto - Ollama connesso', 'success');
        }
    } catch (e) {
        setStatus('⚠️ Backend non raggiungibile', 'error');
    }
}

// Gestione upload file
async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file || !file.name.endsWith('.pdf')) {
        setStatus('Seleziona un file PDF valido', 'error');
        return;
    }

    state.filename = file.name.replace('.pdf', '');
    setStatus('Caricamento...', 'processing');
    showProgress(10);

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Errore ${response.status}`);
        }

        const data = await response.json();

        // Inizializza stato
        state.images = data.images;
        state.totalPages = data.total_pages;
        state.currentPage = 0;
        state.markdowns = new Array(state.totalPages).fill('');

        showProgress(100);
        setStatus(`PDF caricato: ${state.totalPages} pagine`, 'success');

        // Abilita controlli
        elements.pageNav.style.display = 'flex';
        elements.processAll.disabled = false;
        elements.exportBtn.disabled = false;
        elements.editToggle.style.display = 'inline-block';

        // Mostra prima pagina
        renderPDFPage(0);
        renderMarkdownPanel(0);
        updatePageInfo();

    } catch (error) {
        console.error('Upload error:', error);
        setStatus(`Errore caricamento: ${error.message}`, 'error');
        showProgress(0);
    }
}

// Render pagina PDF
function renderPDFPage(index) {
    if (index < 0 || index >= state.totalPages) return;

    const imgData = state.images[index];

    elements.pdfPanel.innerHTML = `
        <div class="pdf-container">
            <div class="pdf-page" style="position: relative;">
                <img src="data:image/png;base64,${imgData}" alt="Pagina ${index + 1}">
                <span class="page-number">Pagina ${index + 1}</span>
            </div>
        </div>
    `;
}

// Render pannello markdown
function renderMarkdownPanel(index) {
    const markdown = state.markdowns[index];

    if (state.editMode) {
        // Modalità edit
        elements.markdownPanel.innerHTML = `
            <textarea class="markdown-editor" data-page="${index}"
                placeholder="Inserisci markdown...">${markdown || ''}</textarea>
        `;

        const textarea = elements.markdownPanel.querySelector('.markdown-editor');
        textarea.addEventListener('input', (e) => {
            state.markdowns[index] = e.target.value;
        });
        textarea.focus();
    } else {
        // Modalità preview
        if (markdown) {
            const html = marked.parse(markdown);
            elements.markdownPanel.innerHTML = `<div class="markdown-content">${html}</div>`;
        } else {
            elements.markdownPanel.innerHTML = `
                <div class="empty-state">
                    <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <h3>Pagina non ancora elaborata</h3>
                    <p>Clicca "Processa tutto" o attendi l'elaborazione automatica.</p>
                </div>
            `;
        }
    }
}

// Navigazione pagine
function navigatePage(direction) {
    const newPage = state.currentPage + direction;
    if (newPage >= 0 && newPage < state.totalPages) {
        state.currentPage = newPage;
        renderPDFPage(newPage);
        renderMarkdownPanel(newPage);
        updatePageInfo();
    }
}

function updatePageInfo() {
    elements.pageInfo.textContent = `Pagina ${state.currentPage + 1}/${state.totalPages}`;
    elements.prevPage.disabled = state.currentPage === 0;
    elements.nextPage.disabled = state.currentPage === state.totalPages - 1;
}

// Toggle edit mode
function toggleEditMode() {
    state.editMode = !state.editMode;
    elements.editToggle.textContent = state.editMode ? 'Anteprima' : 'Modifica';
    renderMarkdownPanel(state.currentPage);
}

// Processa tutte le pagine
async function processAllPages() {
    if (state.isProcessing || state.totalPages === 0) return;

    state.isProcessing = true;
    elements.processAll.disabled = true;
    setStatus('Elaborazione OCR in corso...', 'processing');

    // Processa pagine in sequenza con batch di 3 per non sovraccaricare
    const BATCH_SIZE = 3;

    for (let i = 0; i < state.totalPages; i += BATCH_SIZE) {
        const batch = [];
        for (let j = i; j < Math.min(i + BATCH_SIZE, state.totalPages); j++) {
            batch.push(processPageOCR(j));
        }

        await Promise.all(batch);

        // Aggiorna progresso
        const progress = ((i + batch.length) / state.totalPages) * 100;
        showProgress(progress);

        // Se la pagina corrente è stata elaborata, aggiorna la view
        if (i <= state.currentPage && state.currentPage < i + BATCH_SIZE) {
            renderMarkdownPanel(state.currentPage);
        }
    }

    showProgress(100);
    state.isProcessing = false;
    elements.processAll.disabled = false;
    setStatus(`OCR completato per ${state.totalPages} pagine`, 'success');

    // Torna alla prima pagina per revisione
    state.currentPage = 0;
    renderPDFPage(0);
    renderMarkdownPanel(0);
    updatePageInfo();
}

// Processa singola pagina OCR
async function processPageOCR(pageIndex) {
    const imgData = state.images[pageIndex];

    try {
        setOCRStatus(true, `Elaborazione pagina ${pageIndex + 1}...`);

        const response = await fetch(`${API_BASE}/api/ocr/${pageIndex}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: imgData })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        state.markdowns[pageIndex] = data.markdown;

        setOCRStatus(false, 'Completato');

    } catch (error) {
        console.error(`OCR error for page ${pageIndex + 1}:`, error);
        state.markdowns[pageIndex] = `*Errore OCR: ${error.message}*`;
        setOCRStatus(false, 'Errore', true);
    }
}

// Toggle menu export
function toggleExportMenu() {
    elements.exportDropdown.classList.toggle('show');
}

// Esporta file
function exportFile(format) {
    const content = state.markdowns.join('\n\n---\n\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.filename}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(url);
    elements.exportDropdown.classList.remove('show');
}

// Utility: aggiorna stato
function setStatus(message, type = '') {
    elements.status.textContent = message;
    elements.status.className = 'status ' + type;
}

// Utility: mostra progresso
function showProgress(percent) {
    elements.progressBar.style.width = `${percent}%`;
}

// Utility: stato OCR
function setOCRStatus(loading, text, isError = false) {
    const spinner = elements.ocrStatus.querySelector('.spinner');
    const syncText = elements.ocrStatus.querySelector('.sync-text');

    spinner.style.display = loading ? 'inline-block' : 'none';
    syncText.textContent = text;
    elements.ocrStatus.className = 'sync-indicator' + (isError ? '' : (loading ? ' active' : ''));
}

// Gestione tastiera
function handleKeyboard(e) {
    // Navigazione con frecce
    if (e.key === 'ArrowLeft' && !elements.prevPage.disabled) {
        navigatePage(-1);
    } else if (e.key === 'ArrowRight' && !elements.nextPage.disabled) {
        navigatePage(1);
    }

    // Ctrl/Cmd + S per salvare
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (state.markdowns.some(m => m)) {
            exportFile('md');
        }
    }
}

// Auto-process dopo upload (opzionale)
// Scommenta se vuoi che l'OCR parta automaticamente
/*
elements.fileInput.addEventListener('change', () => {
    setTimeout(() => {
        if (state.totalPages > 0 && !state.isProcessing) {
            processAllPages();
        }
    }, 500);
});
*/
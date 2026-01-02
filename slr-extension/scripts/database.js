// Database Tab Logic - Curation & Management

let currentPapers = [];
let currentQueryHistory = [];

async function initDatabase() {
    await loadPapers();
    await loadQueryHistory();

    // Paper search
    document.getElementById('paper-search').addEventListener('input', (e) => {
        filterPapers(e.target.value);
    });
}

async function loadPapers() {
    const projectId = document.getElementById('project-select').value;

    try {
        const response = await fetch(`http://localhost:8000/extension/papers?project_id=${projectId}`);
        if (response.ok) {
            currentPapers = await response.json();
        } else {
            currentPapers = [];
        }
    } catch (e) {
        console.error('Failed to load papers:', e);
        // Fallback to local storage
        const { savedPapers = [] } = await chrome.storage.local.get('savedPapers');
        currentPapers = savedPapers;
    }

    renderPapers(currentPapers);
    updateProjectStats();
}

function filterPapers(searchTerm) {
    const term = searchTerm.toLowerCase();
    const filtered = currentPapers.filter(p =>
        p.title.toLowerCase().includes(term) ||
        (p.authors && p.authors.toLowerCase().includes(term))
    );
    renderPapers(filtered);
}

function renderPapers(papers) {
    const container = document.getElementById('papers-list');

    if (!papers || papers.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No papers found.</p>
                <p class="hint">Add papers from Google Scholar using the checkmarks.</p>
            </div>`;
        return;
    }

    container.innerHTML = papers.map(paper => `
        <div class="paper-card" data-id="${paper.id}">
            <div class="paper-header">
                <span class="paper-status ${paper.status || 'unread'}">${paper.status === 'reviewed' ? '✓' : '○'}</span>
                <div class="paper-title" title="${paper.title}">${paper.title}</div>
            </div>
            <div class="paper-meta">${paper.authors || 'Unknown authors'}</div>
            <div class="paper-actions">
                ${paper.pdfUrl ? `<a href="${paper.pdfUrl}" target="_blank" class="btn-small">📄 PDF</a>` : ''}
                <a href="${paper.url}" target="_blank" class="btn-small">🔗 Link</a>
                <button class="btn-small toggle-status" data-id="${paper.id}" data-status="${paper.status || 'unread'}">
                    ${paper.status === 'reviewed' ? 'Mark Unread' : 'Mark Reviewed'}
                </button>
                <button class="btn-small btn-danger remove-paper" data-id="${paper.id}">🗑️</button>
            </div>
        </div>
    `).join('');

    // Attach handlers
    container.querySelectorAll('.toggle-status').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = e.target.dataset.id;
            const currentStatus = e.target.dataset.status;
            const newStatus = currentStatus === 'reviewed' ? 'unread' : 'reviewed';
            await updatePaperStatus(id, newStatus);
        });
    });

    container.querySelectorAll('.remove-paper').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = e.target.dataset.id;
            await removePaper(id);
        });
    });
}

async function updatePaperStatus(paperId, status) {
    try {
        await fetch(`http://localhost:8000/extension/papers/${paperId}/status?status=${status}`, {
            method: 'PATCH'
        });
        await loadPapers();
    } catch (e) {
        console.error('Failed to update status:', e);
    }
}

async function removePaper(paperId) {
    try {
        await fetch(`http://localhost:8000/extension/papers/${paperId}`, {
            method: 'DELETE'
        });

        // Also remove from local storage
        const { savedPapers = [] } = await chrome.storage.local.get('savedPapers');
        const updated = savedPapers.filter(p => p.id !== paperId);
        await chrome.storage.local.set({ savedPapers: updated });

        await loadPapers();
        showNotification('Paper removed', 'success');
    } catch (e) {
        console.error('Failed to remove paper:', e);
    }
}

async function loadQueryHistory() {
    const projectId = document.getElementById('project-select').value;

    try {
        const response = await fetch(`http://localhost:8000/extension/query-history?project_id=${projectId}`);
        if (response.ok) {
            currentQueryHistory = await response.json();
        } else {
            currentQueryHistory = [];
        }
    } catch (e) {
        console.error('Failed to load query history:', e);
        currentQueryHistory = [];
    }

    renderQueryHistory();
}

function renderQueryHistory() {
    const container = document.getElementById('query-history-list');

    if (!currentQueryHistory || currentQueryHistory.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No query history yet.</p>
                <p class="hint">Queries you execute from the Assistant tab will appear here.</p>
            </div>`;
        return;
    }

    container.innerHTML = currentQueryHistory.map(entry => `
        <div class="history-item">
            <div class="history-query">${entry.query}</div>
            <div class="history-meta">${new Date(entry.timestamp).toLocaleString()}</div>
            <button class="btn-small rerun-query" data-query="${encodeURIComponent(entry.query)}">🔍 Re-run</button>
        </div>
    `).join('');

    container.querySelectorAll('.rerun-query').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const query = decodeURIComponent(e.target.dataset.query);
            const url = `https://scholar.google.com/scholar?q=${encodeURIComponent(query)}`;
            chrome.tabs.create({ url });
        });
    });
}

function updateProjectStats() {
    const statsEl = document.getElementById('project-stats');
    const total = currentPapers.length;
    const reviewed = currentPapers.filter(p => p.status === 'reviewed').length;
    statsEl.textContent = `${total} papers | ${reviewed} reviewed`;
}

// Export
window.initDatabase = initDatabase;
window.loadPapers = loadPapers;
window.loadQueryHistory = loadQueryHistory;

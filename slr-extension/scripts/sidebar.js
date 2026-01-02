// Sidebar Logic

// Import API if we were using modules, but in basic chrome ext we might just include it in HTML before this script
// validation: ensure api is available
if (typeof api === 'undefined') {
    console.error('API module not loaded');
}

// State
let currentProject = 'default';
let papers = [];

document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    await checkConnection();
    await loadPapers();

    // Listen for updates from background/content scripts
    chrome.runtime.onMessage.addListener((message) => {
        if (message.type === 'PAPERS_UPDATED') {
            loadPapers();
        }
    });

    // Reconnect button
    document.getElementById('reconnect-btn').addEventListener('click', async () => {
        const statusEl = document.getElementById('connection-status');
        const btn = document.getElementById('reconnect-btn');

        statusEl.textContent = 'Connecting...';
        statusEl.classList.remove('connected');

        // Add rotation animation
        btn.style.transition = 'transform 0.5s';
        btn.style.transform = 'rotate(360deg)';

        await checkConnection();

        // Reset rotation
        setTimeout(() => {
            btn.style.transition = 'none';
            btn.style.transform = 'none';
        }, 500);
    });
});

function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            // Add active to clicked
            tab.classList.add('active');
            const targetId = tab.dataset.tab + '-panel';
            document.getElementById(targetId).classList.add('active');
        });
    });
}

async function checkConnection() {
    const statusEl = document.getElementById('connection-status');
    const isConnected = await api.healthCheck();

    if (isConnected) {
        statusEl.textContent = 'Connected';
        statusEl.classList.add('connected');
    } else {
        statusEl.textContent = 'Backend Offline';
        statusEl.classList.remove('connected');
    }
}

async function loadPapers() {
    // Try to load from API, fallback to local storage
    try {
        // First check local storage for unsaved papers
        const { savedPapers = [] } = await chrome.storage.local.get('savedPapers');
        papers = savedPapers;

        // Also try to sync with backend if connected
        try {
            // For now, let's just display what's in local storage as that's what content script saves to via background
            // In full impl, we would sync these.

            // TODO: Fetch from backend and merge
            const remotePapers = await api.getPapers(currentProject);
            // Merge logic... for now just replace if remote has data
            if (remotePapers.length > 0) {
                // Simple merge logic needed
            }
        } catch (e) {
            console.log('Backend sync failed, showing local data');
        }

        renderPapers();
    } catch (e) {
        console.error('Error loading papers:', e);
    }
}

function renderPapers() {
    const listEl = document.getElementById('papers-list');
    const countEl = document.getElementById('paper-count');

    countEl.textContent = `${papers.length} papers`;

    if (papers.length === 0) {
        listEl.innerHTML = `
        <div class="empty-state">
          <p>No papers selected.</p>
          <p class="hint">Search on Google Scholar and click checkmarks to add.</p>
        </div>`;
        return;
    }

    listEl.innerHTML = papers.map(paper => `
        <div class="paper-card" id="card-${paper.id}">
            <div class="paper-title" title="${paper.title}">${paper.title}</div>
            <div class="paper-authors">${paper.authors}</div>
            <div class="actions">
                ${paper.pdfUrl ? `<a href="${paper.pdfUrl}" target="_blank" class="icon-btn" title="Open PDF">📄</a>` : ''}
                <a href="${paper.url}" target="_blank" class="icon-btn" title="View Link">🔗</a>
                <button class="icon-btn remove-btn" onclick="removePaper('${paper.id}')" title="Remove">✕</button>
            </div>
        </div>
    `).join('');

    // Attach event listeners for dynamic buttons if needed, or use delegation
    // Using inline onclick for simplicity in template, but need to expose function
    window.removePaper = removePaper;
}

async function removePaper(id) {
    // Remove from local storage
    const index = papers.findIndex(p => p.id === id);
    if (index !== -1) {
        papers.splice(index, 1);
        await chrome.storage.local.set({ savedPapers: papers });
        renderPapers();

        // Also try to delete from backend
        // await api.deletePaper(id);
    }
}

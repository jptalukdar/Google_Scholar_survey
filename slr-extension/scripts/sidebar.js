// Main Sidebar Logic - Tab switching, project management, connection

document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    initProjectManagement();
    await checkConnection();
    await loadProjects();

    // Initialize tab modules
    if (typeof initAssistant === 'function') initAssistant();
    if (typeof initDatabase === 'function') initDatabase();

    // Reconnect button
    document.getElementById('reconnect-btn').addEventListener('click', async () => {
        const statusEl = document.getElementById('connection-status');
        statusEl.textContent = 'Connecting...';
        statusEl.classList.remove('connected');
        await checkConnection();
    });

    // Listen for updates from content/background
    chrome.runtime.onMessage.addListener((message) => {
        if (message.type === 'PAPERS_UPDATED') {
            if (typeof loadPapers === 'function') loadPapers();
        }
    });
});

// Main tab switching
function initTabs() {
    // Main tabs (Assistant / Database)
    document.querySelectorAll('.main-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.main-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.main-tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`${btn.dataset.tab}-panel`).classList.add('active');
        });
    });

    // Sub-tabs in Database
    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.sub-tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(`${btn.dataset.subtab}-subtab`).classList.add('active');
        });
    });
}

// Project management
function initProjectManagement() {
    const modal = document.getElementById('new-project-modal');
    const newBtn = document.getElementById('new-project-btn');
    const cancelBtn = document.getElementById('cancel-project-btn');
    const createBtn = document.getElementById('create-project-btn');
    const projectSelect = document.getElementById('project-select');

    newBtn.addEventListener('click', () => {
        modal.classList.add('show');
    });

    cancelBtn.addEventListener('click', () => {
        modal.classList.remove('show');
    });

    createBtn.addEventListener('click', async () => {
        const id = document.getElementById('new-project-id').value.trim();
        const name = document.getElementById('new-project-name').value.trim();

        if (!id || !name) {
            showNotification('Please fill in both fields', 'warning');
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/extension/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, name, description: '' })
            });

            if (response.ok) {
                await loadProjects();
                projectSelect.value = id;
                modal.classList.remove('show');
                document.getElementById('new-project-id').value = '';
                document.getElementById('new-project-name').value = '';
                showNotification('Project created!', 'success');

                // Reload data for new project
                if (typeof loadPapers === 'function') loadPapers();
                if (typeof loadQueryHistory === 'function') loadQueryHistory();
            } else {
                const error = await response.json();
                showNotification(error.detail || 'Failed to create project', 'error');
            }
        } catch (e) {
            showNotification('Failed to create project', 'error');
        }
    });

    // Project switch
    projectSelect.addEventListener('change', async () => {
        if (typeof loadPapers === 'function') await loadPapers();
        if (typeof loadQueryHistory === 'function') await loadQueryHistory();
    });
}

async function loadProjects() {
    const select = document.getElementById('project-select');

    try {
        const response = await fetch('http://localhost:8000/extension/projects');
        if (response.ok) {
            const projects = await response.json();

            // Preserve current selection
            const current = select.value;

            select.innerHTML = projects.map(p =>
                `<option value="${p.id}">${p.name}</option>`
            ).join('');

            // Restore selection if possible
            if (current && [...select.options].some(o => o.value === current)) {
                select.value = current;
            }
        }
    } catch (e) {
        console.error('Failed to load projects:', e);
    }
}

async function checkConnection() {
    const statusEl = document.getElementById('connection-status');

    try {
        const response = await fetch('http://localhost:8000/extension/health');
        if (response.ok) {
            statusEl.textContent = 'Connected';
            statusEl.classList.add('connected');
            return true;
        }
    } catch (e) {
        console.error('Connection check failed:', e);
    }

    statusEl.textContent = 'Offline';
    statusEl.classList.remove('connected');
    return false;
}

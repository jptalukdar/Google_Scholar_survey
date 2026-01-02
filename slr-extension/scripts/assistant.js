// Assistant Tab Logic - Discovery Engine

async function initAssistant() {
    const generateBtn = document.getElementById('generate-btn');
    const abstractInput = document.getElementById('abstract-input');
    const strategySelect = document.getElementById('strategy-select');
    const queryResults = document.getElementById('query-results');
    const apiKeyInput = document.getElementById('api-key-input');

    // Load saved API key
    const { geminiApiKey } = await chrome.storage.local.get('geminiApiKey');
    if (geminiApiKey) {
        apiKeyInput.value = geminiApiKey;
    }

    // Save API key on change
    apiKeyInput.addEventListener('change', async () => {
        await chrome.storage.local.set({ geminiApiKey: apiKeyInput.value });
    });

    generateBtn.addEventListener('click', async () => {
        const abstract = abstractInput.value.trim();
        const strategy = strategySelect.value;
        const apiKey = apiKeyInput.value.trim();

        if (!abstract) {
            showNotification('Please enter an idea or abstract', 'warning');
            return;
        }

        if (!apiKey) {
            showNotification('Please enter your Gemini API key', 'warning');
            return;
        }

        // Get selected sites
        const siteCheckboxes = document.querySelectorAll('.checkbox-group input:checked');
        const sites = Array.from(siteCheckboxes).map(cb => cb.value);

        generateBtn.disabled = true;
        generateBtn.textContent = '⏳ Generating...';
        queryResults.innerHTML = '<div class="loading">Generating search strategies...</div>';

        try {
            const response = await fetch('http://localhost:8000/extension/generate-queries', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    abstract,
                    strategy,
                    sites,
                    api_key: apiKey
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to generate queries');
            }

            const data = await response.json();
            renderQueryCards(data.queries);

        } catch (e) {
            console.error('Query generation failed:', e);
            queryResults.innerHTML = `<div class="error">Error: ${e.message}</div>`;
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = '✨ Generate Search Strategies';
        }
    });
}

function renderQueryCards(queries) {
    const container = document.getElementById('query-results');

    if (!queries || queries.length === 0) {
        container.innerHTML = '<div class="empty-state">No queries generated. Try a different abstract.</div>';
        return;
    }

    container.innerHTML = queries.map((q, i) => `
        <div class="query-card" data-query="${encodeURIComponent(q.query)}">
            <div class="query-text">${q.query}</div>
            <div class="query-meta">${q.description || ''}</div>
            <div class="query-actions">
                <button class="btn-small search-scholar" title="Search Google Scholar">🔍 Scholar</button>
                <button class="btn-small copy-query" title="Copy Query">📋 Copy</button>
            </div>
        </div>
    `).join('');

    // Attach click handlers
    container.querySelectorAll('.search-scholar').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const card = e.target.closest('.query-card');
            const query = decodeURIComponent(card.dataset.query);
            const url = `https://scholar.google.com/scholar?q=${encodeURIComponent(query)}`;
            chrome.tabs.create({ url });

            // Log to history
            logQueryToHistory(query);
        });
    });

    container.querySelectorAll('.copy-query').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const card = e.target.closest('.query-card');
            const query = decodeURIComponent(card.dataset.query);
            navigator.clipboard.writeText(query);
            showNotification('Query copied!', 'success');
        });
    });
}

async function logQueryToHistory(query) {
    try {
        const projectId = document.getElementById('project-select').value;
        await fetch(`http://localhost:8000/extension/query-history?query=${encodeURIComponent(query)}&project_id=${projectId}`, {
            method: 'POST'
        });
    } catch (e) {
        console.error('Failed to log query:', e);
    }
}

function showNotification(message, type = 'info') {
    // Simple notification - could be enhanced
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const notif = document.createElement('div');
    notif.className = `notification ${type}`;
    notif.textContent = message;
    document.body.appendChild(notif);

    setTimeout(() => notif.remove(), 3000);
}

// Export for sidebar.js to call
window.initAssistant = initAssistant;
window.showNotification = showNotification;

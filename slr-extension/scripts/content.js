// Content Script for Google Scholar - Simplified (no duplicate check)

const API_BASE = 'http://localhost:8000';
let currentProjectId = 'default';

async function init() {
    console.log('SLR Partner: Content script loaded');

    // Get current project from storage
    const { currentProject } = await chrome.storage.local.get('currentProject');
    currentProjectId = currentProject || 'default';

    // Inject buttons
    injectAddButtons();

    // Observer for pagination/dynamic content
    const observer = new MutationObserver(() => {
        injectAddButtons();
    });

    const mainContent = document.getElementById('gs_res_ccl_mid');
    if (mainContent) {
        observer.observe(mainContent, { childList: true, subtree: true });
    }
}

function injectAddButtons() {
    const results = document.querySelectorAll('.gs_r.gs_or.gs_scl');

    results.forEach(result => {
        if (result.querySelector('.slr-add-btn')) return;

        const paperData = extractPaperData(result);
        if (!paperData) return;

        const btn = document.createElement('button');
        btn.className = 'slr-add-btn new';
        btn.innerHTML = '+ Add';

        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            handleButtonClick(btn, paperData);
        });

        // Insert after the links row
        const linksRow = result.querySelector('.gs_fl');
        if (linksRow) {
            linksRow.appendChild(btn);
        }
    });
}

function extractPaperData(element) {
    try {
        const titleLink = element.querySelector('.gs_rt a');
        const title = titleLink ? titleLink.innerText : element.querySelector('.gs_rt')?.innerText || '';
        const url = titleLink ? titleLink.href : '';
        const id = element.getAttribute('data-cid') || element.getAttribute('data-rp') || url || title;

        if (!title) return null;

        // Authors and venue
        const metaDiv = element.querySelector('.gs_a');
        let authors = '';
        let year = '';
        if (metaDiv) {
            const metaText = metaDiv.innerText;
            const parts = metaText.split(' - ');
            authors = parts[0]?.trim() || '';
            const yearMatch = metaText.match(/\b(19|20)\d{2}\b/);
            if (yearMatch) year = yearMatch[0];
        }

        // Abstract snippet
        const snippetDiv = element.querySelector('.gs_rs');
        const abstract = snippetDiv ? snippetDiv.innerText : '';

        // PDF link
        const pdfLink = element.querySelector('.gs_or_ggsm a');
        const pdfUrl = pdfLink ? pdfLink.href : null;

        return {
            id: id.toString(),
            title,
            url,
            authors,
            year,
            abstract,
            pdfUrl,
            source: 'Google Scholar'
        };
    } catch (e) {
        console.error('Error extracting paper data:', e);
        return null;
    }
}

async function handleButtonClick(btn, paperData) {
    // If already saved, handle removal
    if (btn.classList.contains('saved')) {
        btn.classList.remove('saved');
        btn.classList.add('saving');
        btn.innerHTML = '<span class="spinner"></span>';

        try {
            await fetch(`${API_BASE}/extension/papers/${encodeURIComponent(paperData.id)}`, {
                method: 'DELETE'
            });

            btn.classList.remove('saving');
            btn.classList.add('new');
            btn.innerHTML = '+ Add';

            chrome.runtime.sendMessage({ type: 'PAPERS_UPDATED' }).catch(() => { });
        } catch (e) {
            console.error('Failed to remove paper:', e);
            btn.classList.remove('saving');
            btn.classList.add('saved');
            btn.innerHTML = '✓ Saved';
        }
        return;
    }

    // Add new paper
    btn.classList.remove('new');
    btn.classList.add('saving');
    btn.innerHTML = '<span class="spinner"></span> Saving...';

    try {
        const response = await fetch(`${API_BASE}/extension/papers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: paperData.id,
                title: paperData.title,
                url: paperData.url,
                authors: paperData.authors || '',
                abstract: paperData.abstract || '',
                pdfUrl: paperData.pdfUrl || null,
                source: paperData.source || 'Google Scholar',
                project_id: currentProjectId,
                status: 'unread'
            })
        });

        if (response.ok) {
            btn.classList.remove('saving');
            btn.classList.add('saved');
            btn.innerHTML = '✓ Saved';

            // Update local storage too
            const { savedPapers = [] } = await chrome.storage.local.get('savedPapers');
            if (!savedPapers.find(p => p.id === paperData.id)) {
                savedPapers.push({ ...paperData, savedAt: new Date().toISOString() });
                await chrome.storage.local.set({ savedPapers });
            }

            chrome.runtime.sendMessage({ type: 'PAPERS_UPDATED' }).catch(() => { });
        } else {
            throw new Error('Save failed');
        }
    } catch (e) {
        console.error('Failed to save paper:', e);
        btn.classList.remove('saving');
        btn.classList.add('new');
        btn.innerHTML = '+ Add';
    }
}

// Run init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

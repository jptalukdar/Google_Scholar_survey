// Background Service Worker

// Open sidebar when extension icon is clicked
// Open sidebar when extension icon is clicked
// chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }); is persistent
// calling it once is enough, but safest to just allow the click listener which works universally
// OR use the new API exclusively. Let's use the click listener as it is already there and works if popup is gone.
// Actually, setPanelBehavior is better for "Sidebar by default" UX (keeps it open across tabs potentially).
// Let's use the explicit click handler -> open logic which is robust.
// Wait, the previous code was:
// chrome.action.onClicked.addListener((tab) => {
//    chrome.sidePanel.open({ tabId: tab.id });
// });
// This code is actually CORRECT and works fine once default_popup is gone.
// However, I'll update it to use setPanelBehavior for best practice if available.

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
    .catch((error) => console.error(error));

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'PAPER_SELECTED') {
        handlePaperSelection(message.payload);
    }
    return true; // Keep channel open for async response
});

async function handlePaperSelection(paper) {
    console.log('Paper selected:', paper);

    // Save to local storage as buffer
    const { savedPapers = [] } = await chrome.storage.local.get('savedPapers');

    // Check if exists locally
    if (!savedPapers.find(p => p.id === paper.id)) {
        savedPapers.push({ ...paper, savedAt: new Date().toISOString() });
        await chrome.storage.local.set({ savedPapers });

        // Notify sidebar to refresh
        chrome.runtime.sendMessage({ type: 'PAPERS_UPDATED' }).catch(() => { });
    }

    // Also save to backend API
    try {
        const response = await fetch('http://localhost:8000/extension/papers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: paper.id,
                title: paper.title,
                url: paper.url,
                authors: paper.authors || '',
                abstract: paper.abstract || '',
                pdfUrl: paper.pdfUrl || null,
                source: paper.source || 'Google Scholar',
                project_id: 'default'
            })
        });

        if (response.ok) {
            console.log('Paper saved to backend');
        } else {
            console.error('Backend save failed:', response.status);
        }
    } catch (e) {
        console.error('Failed to save to backend:', e);
    }
}

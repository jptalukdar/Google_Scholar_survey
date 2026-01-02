// Content Script for Google Scholar

function init() {
    console.log('SLR Partner: Content script loaded');
    injectCheckmarks();

    // Observer for pagination/dynamic content
    const observer = new MutationObserver((mutations) => {
        injectCheckmarks();
    });

    const mainContent = document.getElementById('gs_res_ccl_mid');
    if (mainContent) {
        observer.observe(mainContent, { childList: true, subtree: true });
    }
}

function injectCheckmarks() {
    const results = document.querySelectorAll('.gs_r.gs_or.gs_scl');

    results.forEach(result => {
        if (result.querySelector('.slr-checkmark')) return;

        const paperData = extractPaperData(result);
        if (!paperData) return;

        const checkmark = document.createElement('div');
        checkmark.className = 'slr-checkmark';
        checkmark.title = 'Add to Literature Review';
        checkmark.innerHTML = '&#10003;'; // Checkmark symbol

        // Check if already saved (sync state needs async check)
        // For now, just click handler

        checkmark.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            toggleSelection(checkmark, paperData);
        });

        // Insert before the title
        const titleHeader = result.querySelector('.gs_ri');
        if (titleHeader) {
            titleHeader.style.position = 'relative';
            // Prepend to the result item body (gs_ri)
            titleHeader.insertBefore(checkmark, titleHeader.firstChild);
        }
    });
}

function extractPaperData(element) {
    try {
        const titleLink = element.querySelector('.gs_rt a');
        const title = titleLink ? titleLink.innerText : element.querySelector('.gs_rt').innerText;
        const url = titleLink ? titleLink.href : '';
        const id = element.getAttribute('data-cid') || element.getAttribute('data-rp') || url;

        // Authors and snippet
        const metaDiv = element.querySelector('.gs_a');
        const authors = metaDiv ? metaDiv.innerText.split('-')[0].trim() : '';

        const snippetDiv = element.querySelector('.gs_rs');
        const abstract = snippetDiv ? snippetDiv.innerText : '';

        // PDF link
        const pdfLink = element.querySelector('.gs_or_ggsm a');
        const pdfUrl = pdfLink ? pdfLink.href : null;

        return {
            id,
            title,
            url,
            authors,
            abstract,
            pdfUrl,
            source: 'Google Scholar'
        };
    } catch (e) {
        console.error('Error extracting paper data:', e);
        return null;
    }
}

function toggleSelection(element, paperData) {
    element.classList.toggle('selected');
    const isSelected = element.classList.contains('selected');

    chrome.runtime.sendMessage({
        type: isSelected ? 'PAPER_SELECTED' : 'PAPER_REMOVED',
        payload: paperData
    });
}

// Run init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

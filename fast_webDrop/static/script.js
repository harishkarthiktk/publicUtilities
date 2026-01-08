// DOM Elements
const dropZone = document.getElementById('drop-zone');
const linkList = document.getElementById('link-list');
const urlInput = document.getElementById('manual-url-input');
const addButton = document.getElementById('add-button');
const themeToggle = document.getElementById('theme-toggle');
const toastContainer = document.getElementById('toast-container');
const emptyState = document.getElementById('empty-state');
const searchContainer = document.getElementById('search-container');
const searchInput = document.getElementById('search-input');
const modalOverlay = document.getElementById('modal-overlay');
const cancelButton = document.getElementById('cancel-button');
const confirmDelete = document.getElementById('confirm-delete');
const resultCount = document.getElementById('result-count');
const modalUrl = document.getElementById('modal-url');

// State
let allLinks = [];
let filteredLinks = [];
let deleteTarget = null;
let isLoading = false;

// === Theme Management ===
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark');
        themeToggle.textContent = '🌙';
    } else {
        themeToggle.textContent = '☀️';
    }
}

themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    const isDark = document.body.classList.contains('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    themeToggle.textContent = isDark ? '🌙' : '☀️';
});

// === Utilities ===

/**
 * Get emoji for domain based on URL
 */
function getDomainEmoji(url) {
    try {
        const domain = new URL(url).hostname;
        const domainLower = domain.toLowerCase();

        if (domainLower.includes('youtube')) return '🎥';
        if (domainLower.includes('github')) return '💻';
        if (domainLower.includes('twitter') || domainLower.includes('x.com')) return '𝕏';
        if (domainLower.includes('linkedin')) return '💼';
        if (domainLower.includes('reddit')) return '🤖';
        if (domainLower.includes('wikipedia')) return '📚';
        if (domainLower.includes('news')) return '📰';
        if (domainLower.includes('stackoverflow')) return '📖';
        if (domainLower.includes('medium')) return '📝';
        if (domainLower.includes('dribbble')) return '🎨';
        if (domainLower.includes('figma')) return '✨';
        if (domainLower.includes('slack')) return '💬';
        if (domainLower.includes('discord')) return '🎮';
        return '🔗';
    } catch {
        return '🔗';
    }
}

/**
 * Format URL for display (extract domain)
 */
function formatUrl(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.hostname;
    } catch {
        return url;
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Add icon based on type
    const icon = type === 'success' ? '✓' : '✕';
    toast.textContent = `${icon} ${message}`;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

/**
 * Update UI state based on links
 */
function updateUI() {
    const hasLinks = filteredLinks.length > 0;
    emptyState.style.display = hasLinks ? 'none' : 'block';
    searchContainer.style.display = hasLinks || allLinks.length > 0 ? 'block' : 'none';

    // Update result count if searching
    if (searchInput.value.trim()) {
        resultCount.textContent = `${filteredLinks.length} link${filteredLinks.length !== 1 ? 's' : ''} found`;
    } else {
        resultCount.textContent = '';
    }
}

// === Data Loading ===

/**
 * Parse links from existing template
 */
function loadLinksFromTemplate() {
    const items = document.querySelectorAll('ol#link-list > li.link-item');
    allLinks = [];

    items.forEach((item) => {
        const url = item.getAttribute('data-url');
        const metadataItems = item.querySelectorAll('.link-meta-item');
        let timestamp = 'N/A';
        let ip = 'N/A';

        metadataItems.forEach(meta => {
            const label = meta.querySelector('.link-meta-label')?.textContent || '';
            const content = meta.textContent.replace(label, '').trim();

            if (label.includes('Added')) {
                timestamp = content;
            } else if (label.includes('IP')) {
                ip = content;
            }
        });

        if (url) {
            allLinks.push({ url, timestamp, ip });
        }
    });

    filteredLinks = [...allLinks];
    renderLinks();
    updateUI();
}

/**
 * Render links to DOM
 */
function renderLinks() {
    linkList.innerHTML = '';

    filteredLinks.forEach((link, index) => {
        const li = document.createElement('li');
        li.className = 'link-item';
        li.setAttribute('data-url', link.url);

        const emoji = getDomainEmoji(link.url);
        const domain = formatUrl(link.url);
        const metaId = `meta-${index}`;

        li.innerHTML = `
            <div class="link-favicon" data-url="${link.url}">${emoji}</div>
            <div class="link-content">
                <a href="${link.url}" target="_blank" rel="noopener" class="link-url">${link.url}</a>
                <div class="link-domain">${domain}</div>
                <div class="link-metadata" id="${metaId}">
                    <div class="link-meta-item">
                        <span class="link-meta-label">Added:</span>
                        ${link.timestamp}
                    </div>
                    <div class="link-meta-item">
                        <span class="link-meta-label">IP:</span>
                        ${link.ip}
                    </div>
                </div>
            </div>
            <div class="link-actions">
                <button type="button" class="link-action-btn info" data-action="info" title="More info">ℹ️</button>
                <button type="button" class="link-action-btn copy" data-action="copy" title="Copy URL">📋</button>
                <button type="button" class="link-action-btn delete" data-action="delete" data-url="${link.url}" title="Delete">🗑️</button>
            </div>
        `;

        linkList.appendChild(li);
    });

    attachLinkEventHandlers();
}

/**
 * Attach event handlers to link items
 */
function attachLinkEventHandlers() {
    // Info button (expand metadata)
    linkList.addEventListener('click', (e) => {
        if (e.target.closest('.link-action-btn.info')) {
            const item = e.target.closest('.link-item');
            const metadata = item.querySelector('.link-metadata');
            metadata.classList.toggle('expanded');
        }
    });

    // Copy button
    linkList.addEventListener('click', (e) => {
        if (e.target.closest('.link-action-btn.copy')) {
            const item = e.target.closest('.link-item');
            const url = item.getAttribute('data-url');
            const btn = e.target.closest('.link-action-btn.copy');

            navigator.clipboard.writeText(url).then(() => {
                showToast('Copied to clipboard!', 'success');

                // Visual feedback
                const originalText = btn.textContent;
                btn.textContent = '✓';
                btn.style.color = 'var(--success)';

                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.color = '';
                }, 1500);
            }).catch(() => {
                showToast('Failed to copy', 'error');
            });
        }
    });

    // Delete button
    linkList.addEventListener('click', (e) => {
        if (e.target.closest('.link-action-btn.delete')) {
            const item = e.target.closest('.link-item');
            const url = item.getAttribute('data-url');
            deleteTarget = url;
            modalUrl.textContent = url;
            modalOverlay.classList.add('active');
        }
    });
}

// === API Operations ===

/**
 * Add a link via API
 */
async function addLink() {
    const url = urlInput.value.trim();
    if (!url) {
        showToast('Please enter a URL', 'error');
        return;
    }

    // Validate URL format
    let validUrl = url;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        validUrl = 'https://' + url;
    }

    // Check for duplicates
    const isDuplicate = allLinks.some(link => link.url === validUrl);
    if (isDuplicate) {
        showToast('This link already exists', 'error');
        return;
    }

    // Set loading state
    isLoading = true;
    addButton.classList.add('loading');
    addButton.disabled = true;
    document.getElementById('add-button-text').innerHTML = '<span class="spinner"></span>';

    try {
        const response = await fetch('/add-link', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: validUrl })
        });

        if (response.ok) {
            showToast('Link added successfully!', 'success');
            urlInput.value = '';
            urlInput.focus();

            // Add to local list
            const now = new Date().toISOString();
            const newLink = { url: validUrl, timestamp: now, ip: 'You' };
            allLinks.unshift(newLink);
            filteredLinks = [...allLinks];
            renderLinks();
            updateUI();
        } else {
            showToast('Failed to add link', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error: ' + error.message, 'error');
    } finally {
        isLoading = false;
        addButton.classList.remove('loading');
        addButton.disabled = false;
        document.getElementById('add-button-text').textContent = 'Add Link';
    }
}

/**
 * Delete a link via API
 */
async function deleteLink(url) {
    try {
        const response = await fetch('/delete-link', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (response.ok) {
            showToast('Link deleted', 'success');

            // Remove from local list
            allLinks = allLinks.filter(link => link.url !== url);
            filteredLinks = filteredLinks.filter(link => link.url !== url);
            renderLinks();
            updateUI();
        } else {
            showToast('Failed to delete link', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error: ' + error.message, 'error');
    }
}

// === Event Handlers ===

// Add button click
addButton.addEventListener('click', addLink);

// Enter key in input
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !isLoading) {
        addLink();
    }
});

// Search/filter
searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();

    if (query === '') {
        filteredLinks = [...allLinks];
    } else {
        filteredLinks = allLinks.filter(link =>
            link.url.toLowerCase().includes(query) ||
            formatUrl(link.url).toLowerCase().includes(query)
        );
    }

    renderLinks();
    updateUI();
});

// Modal cancel
cancelButton.addEventListener('click', () => {
    modalOverlay.classList.remove('active');
    deleteTarget = null;
});

// Modal confirm delete
confirmDelete.addEventListener('click', () => {
    if (deleteTarget) {
        deleteLink(deleteTarget);
        modalOverlay.classList.remove('active');
        deleteTarget = null;
    }
});

// Modal overlay close (click outside)
modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
        modalOverlay.classList.remove('active');
        deleteTarget = null;
    }
});

// === Drag and Drop ===

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.add('drag-over');
    });
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.remove('drag-over');
    });
});

dropZone.addEventListener('drop', async (e) => {
    const text = e.dataTransfer.getData('text') || e.dataTransfer.getData('URL');
    if (text) {
        urlInput.value = text;
        await addLink();
    }
});

// === Initialization ===

function init() {
    loadTheme();
    loadLinksFromTemplate();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

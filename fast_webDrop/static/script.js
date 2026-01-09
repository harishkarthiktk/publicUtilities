// DOM Elements
const dropZone = document.getElementById('drop-zone');
const linkListWorking = document.getElementById('link-list-working');
const linkListArchived = document.getElementById('link-list-archived');
const linkListTemporary = document.getElementById('link-list-temporary');
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
const sortSelect = document.getElementById('sort-select');
const exportImportSelect = document.getElementById('export-import-select');
const importFile = document.getElementById('import-file');

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
 * Apply filters and sort
 */
function applyFiltersAndSort() {
    let temp = [...allLinks];

    // Search filter
    const searchQuery = searchInput.value.toLowerCase().trim();
    if (searchQuery) {
        temp = temp.filter(link =>
            link.url.toLowerCase().includes(searchQuery) ||
            formatUrl(link.url).toLowerCase().includes(searchQuery)
        );
    }

    // Sort
    const sortType = sortSelect.value;
    temp.sort((a, b) => {
        if (sortType === 'newest') {
            return new Date(b.timestamp) - new Date(a.timestamp);
        } else if (sortType === 'oldest') {
            return new Date(a.timestamp) - new Date(b.timestamp);
        } else if (sortType === 'alpha') {
            return a.url.localeCompare(b.url);
        } else if (sortType === 'domain') {
            const da = formatUrl(a.url).toLowerCase();
            const db = formatUrl(b.url).toLowerCase();
            return da.localeCompare(db);
        }
        return 0;
    });

    filteredLinks = temp;
    renderLinks();
    updateUI();
}

/**
 * Update UI state based on links
 */
function updateUI() {
    const hasLinks = filteredLinks.length > 0;
    emptyState.style.display = hasLinks ? 'none' : 'block';
    searchContainer.style.display = allLinks.length > 0 ? 'block' : 'none';

    // Update result count if searching
    const searchQuery = searchInput.value.trim();
    if (searchQuery) {
        resultCount.textContent = `${filteredLinks.length} link${filteredLinks.length !== 1 ? 's' : ''} found`;
    } else {
        resultCount.textContent = '';
    }
}

// === Data Loading ===

/**
 * Load initial links from backend (passed via INITIAL_LINKS global)
 */
function loadLinksFromTemplate() {
    // Load from backend data embedded in template
    if (typeof INITIAL_LINKS !== 'undefined' && Array.isArray(INITIAL_LINKS)) {
        allLinks = INITIAL_LINKS.map(link => ({
            url: link.url,
            timestamp: link.timestamp || 'N/A',
            ip: link.ip || 'N/A',
            category: link.category || 'working'
        }));
    } else {
        allLinks = [];
    }
    filteredLinks = [...allLinks];
}

/**
 * Render links to kanban board (grouped by category)
 */
function renderLinks() {
    // Clear all lists
    linkListWorking.innerHTML = '';
    linkListArchived.innerHTML = '';
    linkListTemporary.innerHTML = '';

    // Group links by category
    const byCategory = {
        working: [],
        archived: [],
        temporary: []
    };

    filteredLinks.forEach(link => {
        const category = link.category || 'working';
        if (byCategory[category]) {
            byCategory[category].push(link);
        }
    });

    // Render each category
    const categories = [
        { key: 'working', list: linkListWorking },
        { key: 'archived', list: linkListArchived },
        { key: 'temporary', list: linkListTemporary }
    ];

    categories.forEach(({ key, list }) => {
        const links = byCategory[key];

        links.forEach((link, index) => {
            const li = createLinkItem(link, index);
            list.appendChild(li);
        });

        // Update count
        const column = document.querySelector(`[data-category="${key}"]`);
        if (column) {
            column.querySelector('.kanban-count').textContent = links.length;
        }
    });
}

/**
 * Create a single link item element with category selector
 */
function createLinkItem(link, index) {
    const li = document.createElement('li');
    li.className = 'link-item';
    li.setAttribute('data-url', link.url);

    const emoji = getDomainEmoji(link.url);
    const domain = formatUrl(link.url);
    const metaId = `meta-${link.url.replace(/[^a-z0-9]/gi, '')}`;

    const linkContent = document.createElement('div');
    linkContent.className = 'link-content';

    const a = document.createElement('a');
    a.href = link.url;
    a.target = '_blank';
    a.rel = 'noopener';
    a.className = 'link-url';
    a.textContent = link.url;
    linkContent.appendChild(a);

    const domainDiv = document.createElement('div');
    domainDiv.className = 'link-domain';
    domainDiv.textContent = domain;
    linkContent.appendChild(domainDiv);

    // Category selector
    const categorySelector = document.createElement('select');
    categorySelector.className = 'link-category-select';
    categorySelector.setAttribute('data-url', link.url);
    categorySelector.innerHTML = `
        <option value="working" ${link.category === 'working' ? 'selected' : ''}>Working</option>
        <option value="archived" ${link.category === 'archived' ? 'selected' : ''}>Archived</option>
        <option value="temporary" ${link.category === 'temporary' ? 'selected' : ''}>Temporary</option>
    `;
    linkContent.appendChild(categorySelector);

    // Metadata
    const metadata = document.createElement('div');
    metadata.className = 'link-metadata';
    metadata.id = metaId;
    metadata.innerHTML = `
        <div class="link-meta-item">
            <span class="link-meta-label">Added:</span>
            ${link.timestamp}
        </div>
        <div class="link-meta-item">
            <span class="link-meta-label">IP:</span>
            ${link.ip}
        </div>
    `;
    linkContent.appendChild(metadata);

    li.appendChild(document.createElement('div')).className = 'link-favicon';
    li.querySelector('.link-favicon').setAttribute('data-url', link.url);
    li.querySelector('.link-favicon').textContent = emoji;

    li.appendChild(linkContent);

    const actions = document.createElement('div');
    actions.className = 'link-actions';
    actions.innerHTML = `
        <button type="button" class="link-action-btn info" data-action="info" title="More info">ℹ️</button>
        <button type="button" class="link-action-btn copy" data-action="copy" title="Copy URL">📋</button>
        <button type="button" class="link-action-btn delete" data-action="delete" data-url="${link.url}" title="Delete">🗑️</button>
    `;
    li.appendChild(actions);

    return li;
}

/**
 * Attach event handlers to link items (use event delegation)
 */
function attachLinkEventHandlers() {
    const lists = [linkListWorking, linkListArchived, linkListTemporary];

    lists.forEach(list => {
        // Info button (expand metadata)
        list.addEventListener('click', (e) => {
            if (e.target.closest('.link-action-btn.info')) {
                const item = e.target.closest('.link-item');
                const metadata = item.querySelector('.link-metadata');
                metadata.classList.toggle('expanded');
            }
        });

        // Copy button
        list.addEventListener('click', (e) => {
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
        list.addEventListener('click', (e) => {
            if (e.target.closest('.link-action-btn.delete')) {
                const item = e.target.closest('.link-item');
                const url = item.getAttribute('data-url');
                deleteTarget = url;
                modalUrl.textContent = url;
                modalOverlay.classList.add('active');
            }
        });

        // Category change
        list.addEventListener('change', (e) => {
            if (e.target.classList.contains('link-category-select')) {
                const url = e.target.getAttribute('data-url');
                const newCategory = e.target.value;
                changeLinkCategory(url, newCategory);
            }
        });
    });
}

/**
 * Change link category and re-render
 */
function changeLinkCategory(url, newCategory) {
    const link = allLinks.find(l => l.url === url);
    if (link) {
        link.category = newCategory;
        applyFiltersAndSort();
    }
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

    // Add protocol if missing
    let validUrl = url;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        validUrl = 'https://' + url;
    }

    // Validate URL
    try {
        new URL(validUrl);
    } catch {
        showToast('Invalid URL format', 'error');
        return;
    }

    // Check for duplicates locally
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

        const data = await response.json();

        if (data.status === 'success') {
            showToast('Link added successfully!', 'success');
            urlInput.value = '';
            urlInput.focus();

            // Add to local list
            const now = new Date().toISOString();
            const newLink = { url: validUrl, timestamp: now, ip: 'You', category: 'working' };
            allLinks.unshift(newLink);
            applyFiltersAndSort();
        } else if (data.status === 'duplicate') {
            showToast('This link already exists', 'error');
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
            applyFiltersAndSort();
        } else {
            showToast('Failed to delete link', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error: ' + error.message, 'error');
    }
}

/**
 * Export data
 */
async function exportData(type) {
    try {
        const response = await fetch(`/export-${type}`);
        if (!response.ok) throw new Error('Export failed');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `links.${type}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(`Exported as ${type.toUpperCase()}`, 'success');
    } catch (error) {
        console.error('Export error:', error);
        showToast('Export failed', 'error');
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

// Search input
searchInput.addEventListener('input', applyFiltersAndSort);

// Sort change
sortSelect.addEventListener('change', () => {
    localStorage.setItem('sort', sortSelect.value);
    applyFiltersAndSort();
});

// Export / Import select
exportImportSelect.addEventListener('change', (e) => {
    const value = e.target.value;

    if (value.startsWith('export-')) {
        const type = value.split('-')[1];
        exportData(type);
    } else if (value === 'import') {
        importFile.click();
    }

    // Reset select to default
    e.target.value = '';
});

importFile.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/import-links', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.status === 'success') {
            showToast(`Imported ${data.added || 0} links`, 'success');
            // Reload to fetch new links
            location.reload();
        } else {
            showToast(data.message || 'Import failed', 'error');
        }
    } catch (error) {
        console.error('Import error:', error);
        showToast('Import error', 'error');
    }
    e.target.value = '';
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
    const savedSort = localStorage.getItem('sort') || 'newest';
    sortSelect.value = savedSort;
    attachLinkEventHandlers();
    applyFiltersAndSort();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

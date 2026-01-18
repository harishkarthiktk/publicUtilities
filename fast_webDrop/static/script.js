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

// === Authentication ===

// Authentication state
let authCredentials = null;

// Load credentials from localStorage
function loadStoredCredentials() {
    const stored = localStorage.getItem('authCredentials');
    if (stored) {
        try {
            const creds = JSON.parse(stored);
            // Check if credentials are older than 24 hours
            const age = Date.now() - (creds.timestamp || 0);
            if (age > 24 * 60 * 60 * 1000) {
                localStorage.removeItem('authCredentials');
                return false;
            }
            authCredentials = creds;
            return true;
        } catch (e) {
            localStorage.removeItem('authCredentials');
            return false;
        }
    }
    return false;
}

// Save credentials to localStorage
function saveCredentials(username, password) {
    authCredentials = {
        username,
        password,
        token: btoa(`${username}:${password}`),
        timestamp: Date.now()
    };
    localStorage.setItem('authCredentials', JSON.stringify(authCredentials));
}

// Clear credentials
function clearCredentials() {
    authCredentials = null;
    localStorage.removeItem('authCredentials');
}

// Get authorization header
function getAuthHeader() {
    if (!authCredentials) {
        return {};
    }
    return {
        'Authorization': `Basic ${authCredentials.token}`
    };
}

// Enhanced fetch wrapper
async function authenticatedFetch(url, options = {}) {
    const authHeaders = getAuthHeader();
    const headers = {
        ...authHeaders,
        ...(options.headers || {})
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    // Handle 401 - clear credentials and show login
    if (response.status === 401) {
        clearCredentials();
        document.getElementById('login-overlay').style.display = 'flex';
        throw new Error('Authentication required');
    }

    return response;
}

// Check authentication on page load
function checkAuthentication() {
    if (!loadStoredCredentials()) {
        // No credentials - show login modal
        document.getElementById('login-overlay').style.display = 'flex';
        return false;
    }
    // Has credentials - hide login modal
    document.getElementById('login-overlay').style.display = 'none';
    return true;
}

// Login form handler
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const loginButton = document.getElementById('login-button');
    const loginError = document.getElementById('login-error');

    // Disable button during login
    loginButton.disabled = true;
    document.getElementById('login-button-text').textContent = 'Logging in...';
    loginError.style.display = 'none';

    try {
        // Test credentials by attempting to fetch homepage
        const response = await fetch('/', {
            headers: {
                'Authorization': `Basic ${btoa(`${username}:${password}`)}`
            }
        });

        if (response.ok) {
            // Success - save credentials and reload page
            saveCredentials(username, password);
            document.getElementById('login-overlay').style.display = 'none';
            location.reload();
        } else {
            // Failed authentication
            loginError.textContent = 'Invalid username or password';
            loginError.style.display = 'block';
            loginButton.disabled = false;
            document.getElementById('login-button-text').textContent = 'Login';
        }
    } catch (error) {
        loginError.textContent = 'Connection error. Please try again.';
        loginError.style.display = 'block';
        loginButton.disabled = false;
        document.getElementById('login-button-text').textContent = 'Login';
    }
});

// State
let allLinks = [];
let filteredLinks = [];
let deleteTarget = null;
let isLoading = false;
let isExporting = false;
let isImporting = false;

// Category name customization
const DEFAULT_CATEGORY_NAMES = {
    working: 'Working',
    archived: 'Archived',
    temporary: 'Temporary'
};
let categoryNames = { ...DEFAULT_CATEGORY_NAMES };

function loadCategoryNames() {
    const stored = localStorage.getItem('categoryNames');
    if (stored) {
        try {
            const names = JSON.parse(stored);
            categoryNames = { ...DEFAULT_CATEGORY_NAMES, ...names };
        } catch (e) {
            categoryNames = { ...DEFAULT_CATEGORY_NAMES };
        }
    } else {
        categoryNames = { ...DEFAULT_CATEGORY_NAMES };
    }
}

function saveCategoryNames() {
    localStorage.setItem('categoryNames', JSON.stringify(categoryNames));
}

function resetCategoryNames() {
    categoryNames = { ...DEFAULT_CATEGORY_NAMES };
    saveCategoryNames();
    renderLinks();
    updateCategoryDisplays();
}

function updateCategoryDisplays() {
    Object.keys(categoryNames).forEach(key => {
        const column = document.querySelector(`[data-category="${key}"]`);
        if (column) {
            const titleEl = column.querySelector('.kanban-title');
            if (titleEl) {
                titleEl.textContent = categoryNames[key];
            }
        }
    });
}

function enableCategoryEditing() {
    const titleElements = document.querySelectorAll('.kanban-title');
    titleElements.forEach(titleEl => {
        const column = titleEl.closest('.kanban-column');
        if (!column) return;
        const category = column.getAttribute('data-category');

        // Add dblclick listener
        titleEl.addEventListener('dblclick', () => {
            startEditingCategory(titleEl, category);
        });

        // Add edit button listener
        const editBtn = column.querySelector('.kanban-edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                startEditingCategory(titleEl, category);
            });
        }
    });
}

function startEditingCategory(titleEl, category) {
    // Don't allow editing if already editing
    if (titleEl.parentElement.querySelector('.kanban-title-edit')) {
        return;
    }

    // Create input element
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'kanban-title-edit';
    input.value = categoryNames[category];
    input.maxLength = 30;

    // Replace title with input
    titleEl.style.display = 'none';
    titleEl.parentElement.insertBefore(input, titleEl);
    input.focus();
    input.select();

    // Handle save/cancel
    const handleSave = () => saveCategory(input, titleEl, category);
    const handleCancel = () => cancelEdit(input, titleEl);

    input.addEventListener('blur', handleSave);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            handleSave();
        } else if (e.key === 'Escape') {
            handleCancel();
        }
    });
}

function saveCategory(input, titleEl, category) {
    const newName = input.value.trim();

    // Validate: not empty and not just whitespace
    if (newName === '' || newName.length === 0) {
        showToast('Category name cannot be empty', 'error');
        input.remove();
        titleEl.style.display = '';
        return;
    }

    // Update state and save
    categoryNames[category] = newName;
    saveCategoryNames();

    // Update display
    titleEl.textContent = newName;
    input.remove();
    titleEl.style.display = '';

    // Re-render links to update dropdowns
    renderLinks();
    attachLinkEventHandlers();

    showToast(`Updated to "${newName}"`, 'success');
}

function cancelEdit(input, titleEl) {
    input.remove();
    titleEl.style.display = '';
}

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
    searchContainer.style.display = 'block';

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

        // Update count and title with custom names
        const column = document.querySelector(`[data-category="${key}"]`);
        if (column) {
            const titleEl = column.querySelector('.kanban-title');
            if (titleEl) {
                titleEl.textContent = categoryNames[key];
            }
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

    const categories = ['working', 'archived', 'temporary'];
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.textContent = categoryNames[cat];
        if (link.category === cat) {
            option.selected = true;
        }
        categorySelector.appendChild(option);
    });

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

                // Prevent multiple animations while one is running
                if (btn.classList.contains('success-animation')) {
                    return;
                }

                navigator.clipboard.writeText(url).then(() => {
                    showToast('Copied to clipboard!', 'success');

                    // Add animation class
                    btn.classList.add('success-animation');

                    // Visual feedback
                    const originalText = btn.textContent;
                    btn.textContent = '✓';
                    btn.style.color = 'var(--success)';

                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.style.color = '';
                        btn.classList.remove('success-animation');
                    }, 600);
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
 * Change link category and persist to backend
 */
async function changeLinkCategory(url, newCategory) {
    try {
        const response = await authenticatedFetch('/update-category', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, category: newCategory })
        });

        if (response.ok) {
            // Update local state after successful API call
            const link = allLinks.find(l => l.url === url);
            if (link) {
                link.category = newCategory;
                applyFiltersAndSort();
            }
            showToast(`Moved to ${newCategory}`, 'success');
        } else {
            showToast('Failed to update category', 'error');
        }
    } catch (error) {
        console.error('Error updating category:', error);
        showToast('Error: ' + error.message, 'error');
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
        const response = await authenticatedFetch('/add-link', {
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
        const response = await authenticatedFetch('/delete-link', {
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
    if (isExporting) return;

    isExporting = true;
    exportImportSelect.disabled = true;
    exportImportSelect.classList.add('loading');

    // Save original options and create temporary "Exporting..." option
    const originalOptions = Array.from(exportImportSelect.options);
    const tempOption = document.createElement('option');
    tempOption.textContent = `Exporting ${type.toUpperCase()}...`;
    tempOption.selected = true;
    tempOption.disabled = true;

    // Clear and add temp option
    while (exportImportSelect.options.length > 0) {
        exportImportSelect.remove(0);
    }
    exportImportSelect.appendChild(tempOption);

    try {
        const response = await authenticatedFetch(`/export-${type}`);
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
    } finally {
        isExporting = false;
        exportImportSelect.disabled = false;
        exportImportSelect.classList.remove('loading');

        // Restore original options
        while (exportImportSelect.options.length > 0) {
            exportImportSelect.remove(0);
        }
        originalOptions.forEach(option => {
            exportImportSelect.appendChild(option.cloneNode(true));
        });
        exportImportSelect.value = '';
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

    // Show import overlay
    const importOverlay = document.getElementById('import-overlay');
    importOverlay.classList.add('active');
    isImporting = true;

    try {
        const response = await authenticatedFetch('/import-links', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.status === 'success') {
            showToast(`Imported ${data.added || 0} links`, 'success');
            // Keep overlay visible during reload
            location.reload();
        } else {
            showToast(data.message || 'Import failed', 'error');
            importOverlay.classList.remove('active');
            isImporting = false;
        }
    } catch (error) {
        console.error('Import error:', error);
        showToast('Import error', 'error');
        importOverlay.classList.remove('active');
        isImporting = false;
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

// Reset categories button
document.getElementById('reset-categories-btn').addEventListener('click', () => {
    resetCategoryNames();
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
        // Remove drag-over, add drop-success
        dropZone.classList.remove('drag-over');
        dropZone.classList.add('drop-success');

        // Change icon to checkmark
        const iconEl = dropZone.querySelector('.drop-zone__icon');
        const originalIcon = iconEl.textContent;
        iconEl.textContent = '✓';
        iconEl.style.color = 'var(--success)';

        // Add link
        urlInput.value = text;
        await addLink();

        // Reset after 600ms
        setTimeout(() => {
            dropZone.classList.remove('drop-success');
            iconEl.textContent = originalIcon;
            iconEl.style.color = '';
        }, 600);
    }
});

// === Initialization ===

function init() {
    // Initialize authentication before anything else
    if (checkAuthentication()) {
        // User is authenticated - load and render links
        loadTheme();
        loadCategoryNames();
        loadLinksFromTemplate();
        const savedSort = localStorage.getItem('sort') || 'newest';
        sortSelect.value = savedSort;
        attachLinkEventHandlers();
        enableCategoryEditing();
        applyFiltersAndSort();
    } else {
        // User not authenticated - login modal is already shown by checkAuthentication
        loadTheme();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

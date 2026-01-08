const dropZone = document.getElementById('drop-zone');
const linkList = document.getElementById('link-list');
const manualInput = document.getElementById('manual-url-input');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop zone when dragging over it
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.add('drag-over');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.classList.remove('drag-over');
    }, false);
});

// Handle dropped content
dropZone.addEventListener('drop', async (e) => {
    const text = e.dataTransfer.getData('text');
    const url = e.dataTransfer.getData('URL') || text;

    if (url) {
        await addLink(url);
    }
});

// Also handle paste events in drop zone
dropZone.addEventListener('paste', async (e) => {
    const text = e.clipboardData.getData('text');
    if (text) {
        await addLink(text);
    }
});

// Manual link addition (mobile-friendly)
async function addManualLink() {
    const url = manualInput.value.trim();
    if (url) {
        await addLink(url);
        manualInput.value = '';
    }
}

// Allow Enter key in manual input
manualInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        addManualLink();
    }
});

async function addLink(url) {
    // Simple URL validation
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }

    try {

        const response = await fetch('/add-link', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (response.ok) {
            location.reload();
        }
    } catch (error) {
        alert('Invalid URL');
    }
}

async function deleteLink(url) {
    const response = await fetch('/delete-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    });

    if (response.ok) {
        location.reload();
    }
}

// Theme toggle functionality
function toggleTheme() {
    document.body.classList.toggle('dark');
    // Optionally save to localStorage
    const isDark = document.body.classList.contains('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Load saved theme on page load, default to dark
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        // Do nothing, dark is default
    } else {
        document.body.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }
});
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FastWebDrop** is a modern, minimalist link management application with a kanban-style organization system. It allows users to quickly save, organize, and manage links across three categories: Working, Archived, and Temporary. The app features a polished UI with drag-and-drop support, search functionality, export/import capabilities, and a dark/light theme toggle.

### Tech Stack
- **Backend:** FastAPI (Python)
- **Frontend:** Vanilla JavaScript, HTML, CSS
- **Data Storage:** JSON file-based (links.json)
- **Styling:** OKLch color space with CSS custom properties
- **Fonts:** Plus Jakarta Sans (body), IBM Plex Mono (code)

---

## Development Commands

### Running the Application
```bash
# Start the FastAPI server
python fast_api_main.py

# Server runs on http://localhost:8000
```

### Building / Linting
- No build step required (vanilla frontend, no bundler)
- No linting configured (consider adding if expanding codebase)

### File Organization
```
fast_webDrop/
├── fast_api_main.py          # FastAPI backend (API routes, data persistence)
├── links.json                 # Data storage (links with metadata)
├── templates/
│   └── index.html            # HTML template (Jinja2 templated)
├── static/
│   ├── script.js             # Frontend logic (19KB, well-organized)
│   └── styles.css            # Styling (24KB, OKLch color system)
└── UI_UX_IMPROVEMENT_PLAN.md # Design documentation
```

---

## Architecture Overview

### Frontend Architecture (Client-Side)

**script.js** implements a state-based UI system:

1. **State Management**
   - `allLinks`: All links loaded from backend
   - `filteredLinks`: Links after search/sort filtering
   - `deleteTarget`: Currently targeted link for deletion
   - `isLoading`: Global loading flag for async operations

2. **Core Data Flow**
   - Links load from backend via `INITIAL_LINKS` global (passed via Jinja2)
   - All user actions (add, delete, category change) immediately update local state
   - AJAX requests sync changes to backend without page reload
   - UI re-renders reactively when state changes

3. **Key Functions** (in order of importance)
   - `applyFiltersAndSort()` - Central rendering function; runs after any state change
   - `renderLinks()` - Groups links by category (working/archived/temporary) and renders kanban layout
   - `addLink()` - Validates, deduplicates, POSTs to `/add-link`
   - `deleteLink()` - POSTs to `/delete-link`
   - `changeLinkCategory()` - POSTs to `/update-category` (kanban column drag behavior)
   - `attachLinkEventHandlers()` - Event delegation for all link items

4. **UI Patterns**
   - **Optimistic updates**: Local state updates before API confirmation
   - **Event delegation**: Single listener per category list (not per item)
   - **Toast notifications**: Auto-dismissing feedback (3s duration)
   - **Modal confirmation**: Delete confirmation prevents accidental data loss
   - **Search/filter**: Real-time filtering by URL and domain
   - **Sort options**: Newest/oldest/A-Z/by domain (preference saved to localStorage)

### Backend Architecture (Server-Side)

**fast_api_main.py** handles:

1. **Data Persistence**
   - `load_links()` / `save_links()` - Simple file I/O to links.json
   - Links stored with: `url`, `timestamp` (ISO), `ip` (client IP), `category` (working/archived/temporary)

2. **API Endpoints**
   - `GET /` - Serves index.html with embedded links (Jinja2)
   - `POST /add-link` - Validates, deduplicates, saves
   - `POST /delete-link` - Removes link from list
   - `POST /update-category` - Updates link category for kanban
   - `GET /export-json`, `/export-csv`, `/export-html` - Data export
   - `POST /import-links` - File upload (JSON/CSV), deduplicates on import
   - `GET /favicon.svg` - SVG favicon

3. **Key Implementation Details**
   - **Duplicate prevention**: Both frontend and backend check for duplicates
   - **Client IP tracking**: `request.client.host` captures user IP on add
   - **Timestamp**: ISO format timestamp on link creation
   - **File-based storage**: No database; simple JSON for portability

### Styling System (CSS)

**styles.css** uses a design system approach:

1. **Color System** (OKLch perceptually uniform colors)
   - Light theme: Light backgrounds, dark text
   - Dark theme: Dark backgrounds, light text
   - Automatic switching via `.dark` class on body
   - Accent colors: Primary (blue), success (green), error (red)

2. **Spacing System** (CSS custom properties)
   - `--spacing-xs` through `--spacing-2xl` (0.5rem to 3rem)
   - Consistent padding/margins across components

3. **Typography**
   - Display/body: Plus Jakarta Sans (modern, readable)
   - Monospace: IBM Plex Mono (URLs, metadata)
   - Line height: 1.6 for readability

4. **Shadows** (depth system)
   - `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-xl`
   - Hardware-accelerated transforms for performance

5. **Kanban Layout**
   - Three-column grid layout (`display: grid; grid-template-columns: repeat(3, 1fr)`)
   - Responsive: Stacks to 2 columns at 768px, 1 column at 480px
   - Each column renders links with category selector and actions

6. **Component Patterns**
   - Cards with hover elevation (`scale`, `box-shadow`)
   - Smooth transitions (0.2s, 0.3s durations)
   - Modal with backdrop blur and overlay
   - Toast notifications slide in from right
   - Input focus states with accent color

---

## Common Development Tasks

### Adding a New Link Field
1. Update `UpdateCategory` Pydantic model in `fast_api_main.py` if needed
2. Modify `/add-link` endpoint to capture and store the field
3. Update `link` object in `script.js` when creating new links
4. Update `createLinkItem()` to render the new field in HTML
5. Update localStorage/export functions if persistence needed

### Changing the Kanban Categories
1. Update the three `data-category` values in `templates/index.html` (currently: working, archived, temporary)
2. Update the `byCategory` object in `renderLinks()` in `script.js`
3. Update the category selector options in `createLinkItem()`
4. Update backend if category validation needed

### Adding an Export Format
1. Create new endpoint in `fast_api_main.py` (e.g., `/export-xml`)
2. Add option to the select element in `templates/index.html`
3. Modify export case in `script.js` (line 537)
4. Update `exportData()` to handle new type

### Improving Performance
- Current bottleneck: DOM rendering for large lists (1000+ links)
- Solution: Implement virtual scrolling or paginate links in `renderLinks()`
- Frontend is already optimized: CSS animations only, event delegation, debounced search

---

## Design System Reference

### Key Color Tokens (OKLch format)
- **Light theme backgrounds:** oklch(0.98 0.01 228.79) → oklch(0.95 0.02 225.66)
- **Dark theme backgrounds:** oklch(0.18 0.02 271.27) → oklch(0.22 0.02 271.67)
- **Primary accent:** oklch(0.71 0.15 239.15) (blue, used for buttons, links)
- **Success:** oklch(0.65 0.15 159.03) (green, for confirmations)
- **Error:** oklch(0.61 0.24 20.96) (red, for errors)

### Responsive Breakpoints
- Mobile (< 480px): Single column kanban, adjusted spacing
- Tablet (480px - 768px): Two-column kanban
- Desktop (> 768px): Three-column kanban

---

## Testing & Debugging

### Manual Testing Checklist
- Add link via input field and via drag-and-drop
- Test duplicate detection (should show error toast)
- Switch between kanban categories (should persist on refresh)
- Search/filter by URL and domain name
- Test sort options (newest, oldest, A-Z, by domain)
- Export to JSON/CSV/HTML and verify file format
- Import previously exported file
- Toggle theme (dark/light) and verify localStorage persistence
- Test on mobile (responsive design)

### Browser DevTools Tips
- **Console:** Check for errors during add/delete operations
- **Network:** Verify AJAX requests to backend (should be JSON content-type)
- **Storage:** Check localStorage for `theme` and `sort` preferences
- **Application:** View links.json in Network tab if needed

---

## Known Patterns & Conventions

1. **Naming**: Use kebab-case for CSS classes (`.link-item`), camelCase for JavaScript variables (`isLoading`)
2. **Color system**: Always use CSS custom properties (e.g., `color: var(--text-primary)`) for theme switching
3. **Animations**: CSS-only for performance; use `transition` property
4. **Accessibility**: All buttons have `type="button"` and `title` attributes; inputs have `aria-label`
5. **Data format**: Links always include `url`, `timestamp`, `ip`, `category` (required for consistency)

---

## Important Notes

- **No Build Step**: This is vanilla JavaScript/CSS, not a framework project. Changes are live without compilation.
- **File-Based Storage**: Scaling beyond 10k+ links may require moving to a database (currently fine for personal use).
- **Jinja2 Templating**: Links are embedded in HTML via `{{ links | tojson }}` for initial page load; any new template variables must be passed from the backend.
- **CORS**: Not configured; assumes same-origin requests (frontend and backend on same domain).
- **Security**: Client IPs are logged; sanitize user input if expanding features (currently safe; no user-generated content in rendered HTML).

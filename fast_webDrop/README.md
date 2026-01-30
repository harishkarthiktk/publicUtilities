# FastWebDrop

A modern, minimalist link management application with kanban-style organization, HTTP Basic Authentication, and comprehensive data export/import capabilities.

## Features

- **Kanban-style organization** - Organize links across Working, Archived, and Temporary categories
- **Drag-and-drop** - Move links between columns
- **Search & filter** - Real-time filtering by URL and domain
- **Sorting** - Sort by newest, oldest, A-Z, or by domain
- **Export/Import** - Export to JSON/CSV/HTML; import from JSON/CSV with deduplication
- **Theme toggle** - Dark/light mode with localStorage persistence
- **Authentication** - HTTP Basic Auth with bcrypt password hashing
- **Audit logging** - Comprehensive authentication logging
- **File-based storage** - Portable JSON file storage (no database required)

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Data Storage**: JSON file-based (links.json)
- **Authentication**: HTTP Basic Auth + bcrypt
- **Styling**: OKLch color space with CSS custom properties
- **Fonts**: Plus Jakarta Sans (body), IBM Plex Mono (code)

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

### Running the Application

```bash
# Activate virtual environment
source ~/.venv_gen/bin/activate

# Start FastAPI server
python fast_api_main.py

# Open browser
# http://localhost:8000
```

Default test users (see `users.yaml`):
- Username: `admin` / Password: `admin123`
- Username: `user1` / Password: `user123`
- Username: `developer` / Password: `dev@secure!`

## Project Structure

```
fast_webDrop/
├── fast_api_main.py          # FastAPI backend with API routes
├── links.json                # JSON data storage
├── users.yaml                # User configuration with bcrypt hashes
├── manage_users.py           # CLI utility for user management
├── templates/
│   └── index.html            # HTML template with Jinja2
├── static/
│   ├── script.js             # Frontend logic (19KB)
│   └── styles.css            # Styling system (24KB)
├── authService/              # Authentication module
│   ├── authservice.py        # AuthManager, AuthConfig, AuthLogger
│   └── requirements.txt       # Auth service dependencies
├── logs/
│   └── auth.log              # Authentication audit log
├── test_fast_api_main.py     # Backend test suite (10 tests)
├── requirements.txt          # Main dependencies
└── requirements-dev.txt      # Development dependencies
```

## API Endpoints

### Protected Endpoints (Require HTTP Basic Auth)

- `POST /add-link` - Add new link
- `POST /delete-link` - Delete link
- `POST /update-category` - Update link category
- `GET /export-json` - Export links as JSON
- `GET /export-csv` - Export links as CSV
- `GET /export-html` - Export links as HTML
- `POST /import-links` - Import links from file

### Public Endpoints

- `GET /` - Home page with embedded links
- `GET /favicon.svg` - Favicon

### Example API Calls

```bash
# Add a link
curl -u admin:admin123 -X POST http://localhost:8000/add-link \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Export links as JSON
curl -u admin:admin123 http://localhost:8000/export-json

# Export links as CSV
curl -u admin:admin123 http://localhost:8000/export-csv
```

## Authentication

FastWebDrop uses HTTP Basic Authentication with bcrypt password hashing.

### User Configuration Format

The `users.yaml` file stores user credentials and metadata:

```yaml
users:
  admin:
    password: $2b$12$...bcrypt_hash...
    is_active: true
    roles:
      - admin
      - manager
    email: admin@example.com
    metadata:
      department: IT
```

Fields:
- `password` - Bcrypt hash (starts with `$2b$`)
- `is_active` - Boolean, enables/disables user
- `roles` - List of role strings
- `email` - User email address
- `metadata` - Free-form metadata dictionary

### User Management

```bash
# Add a new user
python manage_users.py add alice mypass123 --email alice@example.com --role user

# Change password
python manage_users.py change-password alice newpassword

# Remove user
python manage_users.py remove alice

# List all users
python manage_users.py list

# View user details
python manage_users.py info alice
```

### Authentication Flow

1. Client navigates to `/`
2. Frontend checks localStorage for stored credentials
3. If no/expired credentials: Show login modal
4. User submits username/password
5. Frontend creates Basic Auth header and sends request
6. AuthManager verifies credentials against `users.yaml`
7. On success: credentials stored in localStorage (24-hour expiration)
8. All subsequent API calls include Authorization header

### Production Security

- **Use HTTPS**: Never use HTTP with Basic Auth in production
- **Environment variables**: Store credentials in env vars, not config files
- **Keep users.yaml in .gitignore**: Never commit user passwords
- **Rotate credentials**: Regularly update user passwords
- **Audit logs**: Monitor `logs/auth.log` for suspicious activity

## Frontend Architecture

**script.js** implements a state-based UI system:

### State Management
- `allLinks` - All links loaded from backend
- `filteredLinks` - Links after search/sort filtering
- `deleteTarget` - Currently targeted link for deletion
- `isLoading` - Global loading flag

### Core Data Flow
1. Links load from backend via Jinja2 templating
2. All user actions immediately update local state
3. AJAX requests sync changes to backend
4. UI re-renders reactively when state changes

### Key Functions
- `applyFiltersAndSort()` - Central rendering function
- `renderLinks()` - Groups by category and renders kanban layout
- `addLink()` - Validates, deduplicates, posts to `/add-link`
- `deleteLink()` - Posts to `/delete-link`
- `changeLinkCategory()` - Handles kanban drag/drop
- `attachLinkEventHandlers()` - Event delegation for link items

### UI Patterns
- **Optimistic updates**: Local state updates before API confirmation
- **Event delegation**: Single listener per category list
- **Toast notifications**: 3-second auto-dismissing feedback
- **Modal confirmation**: Prevents accidental data loss
- **Real-time search**: Instant filtering by URL/domain
- **Sort preferences**: Saved to localStorage

## Backend Architecture

**fast_api_main.py** implements:

### Data Persistence
- `load_links()` / `save_links()` - File I/O to links.json
- Links stored with: `url`, `timestamp` (ISO), `ip`, `category`

### Key Features
- **Duplicate prevention**: Both frontend and backend validation
- **Client IP tracking**: IP logged with each link
- **Timestamps**: ISO format on link creation
- **Deduplication**: Import/add operations check for duplicates

## Development & Testing

### Run Tests

```bash
pytest tests/ -v
```

### Test Coverage

10 tests covering critical operations:
1. Add link successfully
2. Prevent duplicate links
3. Delete link
4. Update link category
5. Export JSON
6. Export CSV
7. Import JSON
8. Import CSV
9. Load links from file
10. Save links to file

All tests pass with mocked authentication for isolation.

### Manual Testing Checklist

- Add/delete links via input field
- Test duplicate detection
- Switch between kanban categories
- Search/filter by URL and domain
- Test sort options (newest, oldest, A-Z, by domain)
- Export to JSON/CSV/HTML
- Import previously exported file
- Toggle dark/light theme
- Test on mobile (responsive design)

## Design System

### Color System (OKLch format)

- **Light theme**: Light backgrounds with dark text
- **Dark theme**: Dark backgrounds with light text
- **Primary**: Blue (oklch(0.71 0.15 239.15))
- **Success**: Green (oklch(0.65 0.15 159.03))
- **Error**: Red (oklch(0.61 0.24 20.96))

### Responsive Breakpoints

- Mobile (< 480px): Single column kanban
- Tablet (480px - 768px): Two-column kanban
- Desktop (> 768px): Three-column kanban

## Common Tasks

### Adding a New Link Field

1. Update `Link` Pydantic model in `fast_api_main.py`
2. Modify `/add-link` endpoint to capture field
3. Update `createLinkItem()` in `script.js` to render field
4. Update export/import functions if needed

### Changing Kanban Categories

1. Update `data-category` values in `templates/index.html`
2. Update `byCategory` object in `renderLinks()` in `script.js`
3. Update category selector options in `createLinkItem()`
4. Update backend if category validation needed

### Adding a New Export Format

1. Create endpoint in `fast_api_main.py` (e.g., `/export-xml`)
2. Add option to select element in `templates/index.html`
3. Modify export handler in `script.js`

## Performance

- **Current bottleneck**: DOM rendering for 1000+ links
- **Solution**: Implement virtual scrolling or pagination
- **Frontend**: Already optimized with CSS animations, event delegation, debounced search

## Logging

Authentication events logged to `logs/auth.log`:
- Max file size: 5MB
- Backups: 5 files retained
- Level: INFO

Log entries:
```
[2024-01-22 15:30:45] AUTH_ATTEMPT username=admin ip=127.0.0.1 success=True
[2024-01-22 15:35:12] INVALID_CREDENTIALS username=baduser ip=192.168.1.100
```

## Troubleshooting

### Login modal stays open

1. Check browser console for errors
2. Verify FastAPI server is running: `python fast_api_main.py`
3. Clear browser localStorage and try again

### "Invalid credentials" error

1. Verify username exists: `python manage_users.py list`
2. Verify password is correct (passwords are case-sensitive)
3. Check auth log: `tail -f logs/auth.log`

### User account disabled

1. Check `users.yaml` - ensure `is_active: true`
2. Update if needed: `python manage_users.py info <username>`

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [authService Documentation](./authService/README.md)
- [authService Technical Details](./authService/TECHNICAL.md)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/http-basic-auth/)

## License

MIT

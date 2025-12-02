# Modularization Plan for app.py: Minimal Split for Auth, Routes, and Entrypoint

This document outlines a minimal, low-risk approach to split the monolithic `app.py` into three files for better modularity:
- `core_auth.py`: Centralized authentication logic (YAML/env loading, HTTPBasicAuth).
- `routes.py`: All route definitions and app logic (file serving, uploads, zipping), using a Flask Blueprint.
- `app.py`: Slimmed-down entrypoint for wiring components, configuration, logging, and startup.

**Goals**:
- Preserve template-based HTML rendering (e.g., `browser.html`, `error.html`) unchanged.
- Keep core auth logic isolated but accessible.
- Separate routes for easier maintenance without over-engineering.
- No changes to templates, static files, or external dependencies.
- Ignore testing (`test_app.py`) for now—handle manually later.

**Assumptions**:
- Flask app runs as before (`python app.py`).
- Constants (e.g., `SERVE_FOLDER`) remain in `app.py`.
- Logging uses `app.logger` (accessible via `current_app` in modules).
- No further splits (e.g., no `utils.py`) unless the codebase expands.

## Step-by-Step Implementation Checklist

### 1. Create `core_auth.py` (New File)
   - [ ] Add imports: `flask_httpauth.HTTPBasicAuth`, `os`, `yaml`, `pathlib.Path`, `logging`.
   - [ ] Define global `auth = HTTPBasicAuth()`.
   - [ ] Implement `load_yaml_users()`:
     - Load from `users.yaml` (or `BASIC_AUTH_USERS_FILE` env var).
     - Handle file existence, YAML parsing, dict extraction (support `'users'` key or direct dict).
     - Cache results in a simple module-level dict (or use `current_app` if needed).
     - Log debug/info/warnings/errors using `logging.getLogger(__name__)`.
     - Return dict of `username: password` or `None` on failure.
   - [ ] Implement `@auth.verify_password def verify_password(username, password)`:
     - Call `load_yaml_users()` first; check if username/password match.
     - Fallback to env vars (`BASIC_AUTH_USER`, `BASIC_AUTH_PASSWORD`).
     - Log success/failure.
     - Return `username` on success, `None` on failure.
   - [ ] Add docstrings for functions.
   - [ ] Verify: Import and test auth independently (e.g., in a temp script).

### 2. Create `routes.py` (New File)
   - [ ] Add imports:
     - Flask: `Flask`, `send_file`, `abort`, `render_template`, `request`, `jsonify`, `after_this_request`, `Blueprint`.
     - Others: `os`, `pathlib.Path`, `zipfile`, `shutil`, `tempfile`, `werkzeug.utils.secure_filename`, `markupsafe.escape`.
     - From `core_auth`: `auth`.
   - [ ] Define Blueprint: `bp = Blueprint('main', __name__, template_folder='templates')`.
   - [ ] Move helper functions from `app.py`:
     - [ ] `zip_folder(folder_path, zip_path)`: ZIP logic with relative paths.
     - [ ] `get_file_tree(base_path, current_path=None, depth=0)`: Recursive file listing with sizes.
     - [ ] `is_allowed_file(filename)`: Extension check against `ALLOWED_EXTENSIONS`.
     - [ ] `safe_resolve_join(base: Path, *parts) -> Path`: Secure path resolution.
   - [ ] Move and adapt routes to Blueprint (`@bp.route`):
     - [ ] `/` (`list_files`): `@auth.login_required`, build tree, `render_template('browser.html', files=file_tree, root_path=SERVE_FOLDER.name)`; handle errors with `error.html`.
     - [ ] `/files/<path:filename>` (`serve_file`): `@auth.login_required`, secure resolve, send file or abort (403/404/500).
     - [ ] `/download-folder/<path:foldername>` (`download_folder`): `@auth.login_required`, ZIP folder, send as attachment, cleanup with `@after_this_request`.
     - [ ] `/upload` (POST, `handle_upload`): `@auth.login_required`, validate path/files, secure upload with temp files/atomic moves, return JSON (success/warning/error).
   - [ ] Expose registration: `def register_routes(app): app.register_blueprint(bp); app.config['ALLOWED_EXTENSIONS'] = {'.txt', ...}` (pass constants if needed).
   - [ ] Update logging: Use `current_app.logger` for consistency.
   - [ ] Verify: No changes to template rendering or JSON responses.

### 3. Modify `app.py` (Existing File, Slim Down)
   - [ ] Keep unchanged:
     - [ ] App creation: `app = Flask(__name__); app.config['MAX_CONTENT_LENGTH'] = ...`.
     - [ ] Constants: `SERVE_FOLDER`, `TEMP_DIR`, `UPLOAD_FOLDER`, `ALLOWED_EXTENSIONS`.
     - [ ] Directory creation: For `SERVE_FOLDER`, `TEMP_DIR`.
     - [ ] Logging setup: RotatingFileHandler, console handler, initial logs.
     - [ ] Cleanup: `atexit.register(...)` for `TEMP_DIR`.
     - [ ] Run block: `if __name__ == '__main__': app.run(...)`.
   - [ ] Remove:
     - [ ] Auth block: `auth = HTTPBasicAuth()`, `load_yaml_users()`, `verify_password` (full impl).
     - [ ] All helper functions (`zip_folder`, etc.).
     - [ ] All route definitions.
   - [ ] Add/Modify:
     - [ ] Import: `from core_auth import auth`.
     - [ ] Thin auth wrapper: `@auth.verify_password def verify_password(username, password): return core_verify_password(username, password)` (if direct import not possible; else use module's decorator).
     - [ ] Import and register: `from routes import register_routes; register_routes(app)`.
     - [ ] Pass globals if needed: E.g., set `app.config['SERVE_FOLDER'] = SERVE_FOLDER` for access in routes.
   - [ ] Clean up unused imports: Remove `yaml`, auth-related if fully moved.
   - [ ] Verify: App starts, logs show startup, no syntax errors.

### 4. Post-Implementation Verification
   - [ ] Run `python app.py` and test:
     - [ ] Auth: YAML and env login works.
     - [ ] Routes: File listing renders `browser.html`, downloads/serves files, uploads succeed (check JSON).
     - [ ] Errors: 403/404/500 handled with `error.html`.
     - [ ] Cleanup: Temp ZIPs removed after download.
   - [ ] Check file sizes: `app.py` reduced to ~100 lines; new files self-contained.
   - [ ] No regressions: Template styles unchanged, security (path traversal) intact.

### Potential Edge Cases
- **Logging in Modules**: Use `current_app.logger` in `routes.py`/`core_auth.py` during request context.
- **Constants Access**: If helpers need `SERVE_FOLDER`, pass via `app.config` or import from `app.py` (circular? Avoid by setting in entrypoint).
- **Dependencies**: Ensure `requirements.txt` covers all (no changes expected).
- **Further Splits**: If adding features (e.g., API), consider `utils.py` for shared helpers.
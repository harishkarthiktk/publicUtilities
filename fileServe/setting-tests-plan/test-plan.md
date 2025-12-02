# Critical Acceptance Criteria and Test Plan for File Server

## Project Overview
This is a Flask-based file server application that provides secure file management operations over HTTP. It supports basic authentication, file browsing, serving individual files, downloading folders as ZIP archives, and uploading files to a designated directory. The application is designed to work with Nginx for efficient static file serving via X-Accel-Redirect. Configuration is handled via YAML files, with fallbacks to environment variables.

The focus is solely on **critical operations**: authentication, file listing, file serving, folder downloading, and file uploading. Non-critical aspects (e.g., logging details, error page styling, deployment scripts) are excluded from testing.

## Critical Acceptance Criteria
These are the high-level requirements the application must satisfy for core functionality. Each criterion is derived from the key routes and authentication mechanisms in the codebase.

1. **Authentication (Basic HTTP Auth)**:
   - Users must authenticate using valid credentials (from `users.yaml` or environment variables `BASIC_AUTH_USER`/`BASIC_AUTH_PASSWORD`).
   - Invalid credentials must be rejected with a 401 Unauthorized response.
   - Authenticated requests must proceed to protected routes; unauthenticated requests must be blocked.
   - Authentication must log success/failure attempts for auditing.

2. **File Listing (Root Route: `/`)**:
   - Authenticated users must see a browsable directory tree of the `SERVE_FOLDER` (e.g., `serveFolder`).
   - The tree must include files and subdirectories with names, paths, types (file/directory), sizes (for files), and recursive children.
   - Invalid or inaccessible paths must return appropriate errors (404 for missing directory, 500 for exceptions).
   - The response must render the `browser.html` template with the file tree data.

3. **File Serving (`/files/<path:filename>`)**:
   - Authenticated users must be able to serve individual files from `SERVE_FOLDER`.
   - Path traversal attempts (e.g., `../`) must be blocked (403 Forbidden).
   - Non-existent files must return 404 Not Found.
   - Served files must use X-Accel-Redirect for Nginx integration, with correct MIME type, content disposition (attachment), and content length headers.
   - Only files with allowed extensions (e.g., .txt, .pdf, .jpg) are implicitly handled, but serving is not restricted by extension in the route.

4. **Folder Downloading (`/download-folder/<path:foldername>`)**:
   - Authenticated users must download an entire folder from `SERVE_FOLDER` as a ZIP archive.
   - The ZIP must include all files and subdirectories relative to `SERVE_FOLDER`, preserving structure.
   - Path traversal attempts must be blocked (403 Forbidden).
   - Non-existent folders must return 404 Not Found.
   - Temporary ZIP files must be created in `TEMP_DIR` and cleaned up after download.
   - The response must be a ZIP file attachment with correct MIME type (`application/zip`).

5. **File Uploading (`/upload` POST)**:
   - Authenticated users must upload one or more files to a target path within `UPLOAD_FOLDER` (defaults to `SERVE_FOLDER`).
   - Target paths must be validated to prevent traversal outside allowed directories (403 Forbidden).
   - Filenames must be secured (via `secure_filename`) and checked against allowed extensions; disallowed files must be skipped with warnings.
   - Uploads must handle multiple files, overwriting existing files if present.
   - Successful uploads must return JSON with file details (name, path, size); errors/warnings must be reported in JSON.
   - Large files (up to `MAX_CONTENT_LENGTH`, default 5GB) must be handled without truncation.
   - Temporary files must be used during upload for atomic moves to final location.

## Test Plan
This plan outlines manual and automated test cases for the critical acceptance criteria. Tests will be implemented post-confirmation, focusing on unit/integration tests using pytest and Flask's test client. No UI/end-to-end tests beyond API simulation. Tests will mock file system interactions where possible (e.g., using `tmp_path` fixture) to avoid modifying real files.

### General Test Setup
- Use Flask's test client for HTTP requests.
- Mock `SERVE_FOLDER`, `UPLOAD_FOLDER`, `TEMP_DIR` to temporary directories.
- Create sample files/subdirs in test fixtures (e.g., text files, images, nested folders).
- Test with valid/invalid credentials.
- Verify logs for auth attempts (via captured output).
- Edge cases: Empty directories, large files (>1MB simulated), special characters in filenames/paths.

### 1. Authentication Tests
- **Positive**: Send GET `/` with valid YAML creds → 200 OK, proceeds to file list.
- **Positive**: Send GET `/` with valid env creds → 200 OK.
- **Negative**: Send GET `/` without creds → 401 Unauthorized.
- **Negative**: Send GET `/` with invalid username/password → 401 Unauthorized.
- **Logging**: Verify success log entry on valid auth; warning on failure.
- **Edge**: Empty password field → 401.

### 2. File Listing Tests
- **Positive**: Authenticated GET `/` → 200, renders template with file tree JSON (includes files, dirs, sizes, recursion up to depth).
- **Negative**: Authenticated GET `/` with missing `SERVE_FOLDER` → 404, error template.
- **Negative**: Authenticated GET `/` with permission error on dir → 500, error template.
- **Edge**: Empty `SERVE_FOLDER` → 200, empty tree array.
- **Edge**: Deeply nested dirs (3+ levels) → Full recursion without stack overflow.

### 3. File Serving Tests
- **Positive**: Authenticated GET `/files/sample.txt` → 200, X-Accel-Redirect header set, correct Content-Type/Length/Disposition.
- **Negative**: Authenticated GET `/files/nonexistent.txt` → 404.
- **Negative**: Authenticated GET `/files/../../etc/passwd` → 403 (path traversal).
- **Negative**: Unauthenticated GET `/files/sample.txt` → 401.
- **Edge**: Large file (simulate 10MB) → Headers correct, no truncation.
- **Edge**: File with special chars in name (e.g., space, accent) → Serves correctly.

### 4. Folder Downloading Tests
- **Positive**: Authenticated GET `/download-folder/sample/` → 200, ZIP attachment with all contents (verify ZIP extraction post-download).
- **Negative**: Authenticated GET `/download-folder/nonexistent/` → 404.
- **Negative**: Authenticated GET `/download-folder/../../` → 403.
- **Negative**: Unauthenticated → 401.
- **Cleanup**: Verify temp ZIP deleted after response (check `TEMP_DIR` empty).
- **Edge**: Folder with subdirs/files → ZIP preserves structure.
- **Edge**: Empty folder → Valid empty ZIP.

### 5. File Uploading Tests
- **Positive**: Authenticated POST `/upload` with single file, no path → 200 JSON, file saved in `UPLOAD_FOLDER`, correct size/path.
- **Positive**: POST with multiple files → 200 JSON, all saved, results array.
- **Positive**: POST with target path `/sub/dir/` → Saves to nested dir (creates if missing).
- **Negative**: POST with disallowed extension (e.g., .exe) → 200 JSON, warning in errors, file skipped.
- **Negative**: POST with traversal path `../../../etc/` → 403 Forbidden.
- **Negative**: POST without files → 200 JSON, success message "No files provided".
- **Negative**: Unauthenticated POST → 401.
- **Edge**: Overwrite existing file → Success, old file replaced.
- **Edge**: Large file upload (simulate chunks) → Success, atomic move.
- **Edge**: Invalid filename (e.g., `<script>`) → Secured, saved if allowed.

## Next Steps After Confirmation
- Implement tests in a new `tests/` directory using pytest.
- Run tests via `pytest` to validate.
- No modifications to existing app files; tests only.

This plan ensures comprehensive coverage of critical operations without over-testing. Confirm or suggest changes before implementation.
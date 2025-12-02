# Nginx + X-Accel-Redirect Implementation Plan

This is a simple, step-by-step checklist for integrating Nginx as a reverse proxy with X-Accel-Redirect for efficient file serving in the Flask File Server project. The plan focuses on keeping Flask's Basic Auth intact while offloading large-file transfers to Nginx. Each step is straightforward, with estimated effort (low/medium) and dependencies.

Assumptions:
- macOS environment (from system info).
- Flask app (via Gunicorn) runs on internal port 8002.
- Nginx runs on external port 8000 (for LAN access).
- No changes to `core_auth.py` or templates; auth handled solely by Flask (YAML/env), with Nginx only sending files.
- Focus on single-file downloads (`/files/<path>`); folder zips (`/download-folder`) remain in Flask for now.
- Nginx installed system-wide via Homebrew; project-specific configs stored in ./nginx/ folder (gitignore if sensitive), with README.md for deployment instructions (copy to system path like /usr/local/etc/nginx/servers/file-serve.conf).
- Nginx will proxy all traffic; internal paths protected.
- No custom headers or caching needed.

## Checklist

### Preparation (Low Effort, ~5 min)
- [ ] Install Gunicorn: Add `gunicorn` to `requirements.txt` and run `pip install -r requirements.txt`. (Dependency for production Flask serving.)
- [ ] Install Nginx: Run `brew install nginx` (macOS). Verify with `nginx -v`.
- [ ] Create Nginx config directory: Ensure `/usr/local/etc/nginx/servers/` exists (default on macOS via Homebrew).
- [ ] Create ./nginx/ folder in project root for project-specific configs (add to .gitignore if containing sensitive info).

### Step 1: Update Flask Route for X-Accel-Redirect (Medium Effort, ~10 min)
- [ ] Add import in `routes.py`: `from flask import Response` and `import mimetypes` (for content-type guessing).
- [ ] Modify `serve_file` function in `routes.py` (lines ~106-129):
  - Keep `@auth.login_required` for Flask auth.
  - After validation, replace `return send_file(filepath)` with a `Response` object setting:
    - `X-Accel-Redirect: /internal-files/{filename}`
    - `Content-Type`: Guessed via `mimetypes.guess_type` or fallback to 'application/octet-stream'.
    - `Content-Disposition`: `attachment; filename="{filename}"`.
    - `Content-Length`: `filepath.stat().st_size`.
  - Log the redirect issuance.
- [ ] Test locally: Run `python app.py`, access `/files/example.txt` – should prompt auth and download (still via Flask for now).

### Step 2: Create Nginx Configuration (Medium Effort, ~15 min)
- [ ] Create project-specific `nginx.conf` in ./nginx/ (full server block):
  - Server block listening on 8000.
  - `location /`: Proxy to `http://127.0.0.1:8002`, pass auth headers (`proxy_pass_header Authorization; proxy_pass_header WWW-Authenticate;`).
  - `location /internal-files/`: `internal; alias /Users/harish-5102/Downloads/Programs/publicUtilities/fileServe/serveFolder/; sendfile on; tcp_nopush on; tcp_nodelay on; gzip off;`.
- [ ] Create ./nginx/README.md: Instructions to copy `nginx.conf` to `/usr/local/etc/nginx/servers/file-serve.conf` (or include in main nginx.conf), then `nginx -t && nginx -s reload`.
- [ ] Test config: Run `nginx -t` after copying to system path.
- [ ] Reload Nginx: `nginx -s reload` or `brew services restart nginx`.

### Step 3: Production Deployment Setup (Low Effort, ~10 min)
- [ ] Update `app.py`: Comment out `app.run()` to avoid dev server conflicts.
- [ ] Create `start_gunicorn.sh` in project root (executable: `chmod +x start_gunicorn.sh`):
  - Activate venv, run `gunicorn -w 4 -k gevent -b 127.0.0.1:8002 app:app`.
- [ ] Create `deploy.sh` (executable):
  - Copy ./nginx/nginx.conf to system path (e.g., /usr/local/etc/nginx/servers/file-serve.conf).
  - Start Gunicorn in background.
  - Reload Nginx (`nginx -t && nginx -s reload`).
  - Output PIDs and access URL (http://localhost:8000).
- [ ] Run: `./deploy.sh` to start stack.

### Step 4: Testing and Validation (Medium Effort, ~15 min)
- [ ] Auth test: `curl -u admin:password http://localhost:8000/files/example.txt` – Verify download after auth (Flask auth, Nginx serve).
- [ ] Unauthorized test: `curl -u wrong:wrong http://localhost:8000/files/example.txt` – Expect 401 from Flask.
- [ ] Throughput test: `curl -u admin:password -L -o /dev/null -w "Speed: %{speed_download} bytes/sec\n" http://localhost:8000/files/Evil.Dead.Rise.2023...mkv` – Compare speeds (expect >50MB/s on LAN via Nginx).
- [ ] Direct internal test: `curl http://localhost:8000/internal-files/example.txt` – Expect 404 (protected).
- [ ] Logs check: Verify Flask auth logs (app.log) and Nginx access/error logs (/usr/local/var/log/nginx/).

### Step 5: Optional Enhancements (Low Effort, ~10 min each)
- [ ] Add Nginx auth to `/internal-files/` (if desired): Use `auth_basic` with `.htpasswd` (migrate YAML users via `htpasswd` tool).
- [ ] HTTPS: Add SSL certs to Nginx server block.
- [ ] Rate limiting: Add `limit_req_zone` in Nginx for brute-force protection.
- [ ] Update README.md: Add deployment section with this plan.

## Total Estimated Time: ~55 min
- Risks: Path alias mismatches (test with small files first); permissions on `serveFolder` (ensure readable by Nginx user `_www`).
- Rollback: Revert `routes.py` to use `send_file`; stop Nginx/Gunicorn.

## Clarifying Questions
Before finalizing implementation:

1. **Nginx and Flask Ports**: Would Nginx and Flask use the same port for their operation? (Elaboration: No, best practice is Nginx on an external port like 80/443 for public access, proxying to Flask on an internal port like 8000. This separates concerns: Nginx handles static/termination, Flask dynamic logic. Using the same port would require running one behind the other without proxying, which defeats the purpose. Confirm if you want Nginx on 80 (may need sudo) or 8000 for testing.)
-- My Suggestion: run ngnix on port 8000, and let flask app run on 8002 internally for all operations.

2. **Nginx Deployment Location**: Nginx will be deployed within the same location itself in the ./ngnix folder but added to .gitignore to avoid everything being committed – is this acceptable practice? (Elaboration: For config files (e.g., nginx.conf), yes – store in project (./nginx/ folder) and .gitignore sensitive parts like .htpasswd. But Nginx binary/install is system-wide (via brew), not in project folder. Deploy configs via scripts (e.g., copy to /usr/local/etc/nginx/). Acceptable for dev, but for prod, use system configs or Docker for portability. Confirm if you mean configs/binary in ./nginx/ or just configs.)
-- My Suggestions: i will install ngnix using brew, but keep all required ngnix configurations under `./ngnix` folder and then use a `README.md` within this folder to show what configuration must be moved where.


Original Questions (for reference):
1. What port should Nginx listen on (80 for prod, 8000 for testing to avoid conflicts)?--anwwered above
2. Do you want to keep auth solely in Flask (recommended for YAML consistency) or add Nginx Basic Auth to `/internal-files/` (requires .htpasswd migration)? -- only user flask's auth with ngnix handling file send.
3. Specific Nginx config path (e.g., Homebrew default or custom) -- home brew, systemwide installation with project specific configs in the `./ngnix` folder.
4. Any custom headers or caching needs for files? -- not needed.
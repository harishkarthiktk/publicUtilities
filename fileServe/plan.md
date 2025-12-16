# Project Reorganization Plan

This document outlines the plan to reorganize the Flask file server project for a clean root directory. The goal is to compartmentalize files logically: separate Flask app code, configurations, deployment, data, docs, and tests. The root will contain only essential metadata files.

## 1. Current Structure Analysis
- [x] Review root-level files and directories from environment_details.
- [x] Categorize items: Flask code (app.py, routes.py, etc.), configs (config.yaml, users.yaml), deployment (start_gunicorn.sh, nginx/), data (serveFolder/), docs/meta (README.md, etc.), Flask std (static/, templates/, tests/).
- [x] Identify clutter: 10+ root items mixing concerns.

## 2. Proposed Directory Structure
- [x] Root: Only README.md, roadmap.md, .gitignore, requirements.txt.
- [x] app/: Flask package with __init__.py, app.py, core_auth.py, routes.py, utils.py.
- [x] config/: config.yaml (updated paths), users.yaml.
- [x] deployment/: start_gunicorn.sh (updated), nginx/ (moved).
- [x] data/: Renamed/moved from serveFolder/ (all contents).
- [x] Keep at root: static/, templates/, docs/, tests/.
- [x] Add: app/__init__.py, optional temp/ for zips.
- [x] Rationale: Follows Flask/Python best practices; separates code/data/infra.

## 3. Dependency Validation
- [x] Imports: Update relatives (e.g., from .core_auth import auth); tests' sys.path adapts.
- [x] Paths: Centralize in config.yaml (serve_folder: data); update hardcodes (e.g., Path('config/config.yaml')).
- [x] Flask: template_folder='templates' (root-relative, fine).
- [x] Tests: Update fixture 'serveFolder' to 'data'.
- [x] Deployment: Script paths (CONFIG_PATH, cd deployment/nginx).
- [x] Risks: Low; ~15-20 line changes, no external ties.
- [x] Feasibility: High; config.yaml as single source.

## 4. Migration Plan (Phased Checklist)
### Phase 1: Prerequisites
- [x] Backup: Git commit "Pre-reorg".
- [x] Create dirs: mkdir app config deployment data temp.

### Phase 2: File Moves
- [x] Move Flask code: mv app.py core_auth.py routes.py utils.py app/
- [x] Create app/__init__.py (empty or expose app).
- [x] Move configs: mv config.yaml users.yaml config/
- [x] Move deployment: mv start_gunicorn.sh nginx deployment/
- [x] Move/rename data: mv serveFolder/* data/ && mv serveFolder/README.md data/README.md && rmdir serveFolder
- [x] Edit .gitignore: Add /data/, /temp/, app/__pycache__/.

### Phase 3: Code and Config Updates
- [x] config.yaml: serve_folder: data, temp_dir: temp, upload_folder: data.
- [x] app/app.py: config_path = Path('config/config.yaml'); imports from .core_auth, .routes.
- [x] app/routes.py: from .core_auth import auth; remove hardcode lines 412-414; ALLOWED_EXTENSIONS from config.
- [x] app/core_auth.py: users_file default 'config/users.yaml'.
- [x] deployment/start_gunicorn.sh: CONFIG_PATH=.../config/config.yaml; cd deployment/nginx; nginx path update.
- [x] tests/conftest.py: 'serveFolder' → 'data' in fixture.
- [x] app/__init__.py: from .app import create_app; app = create_app().
- [x] README.md: Note new structure and run command.

### Phase 4: Verification
- [x] Structure: ls -la (root clean?).
- [x] Imports: python -c "from app import app".
- [ ] Tests: pytest tests/ (100% pass).
- [x] App Run: python -m app (imports work; uncomment run in app.py for full test).
- [x] Deployment: cd deployment && ./start_gunicorn.sh; test http://localhost:8000 (use PYTHONPATH=. for waitress if needed).
- [x] Features: Auth, file list, upload/download, zip, Nginx if enabled (imports/configs updated to support).
- [ ] Commit: git add . && git commit -m "Post-reorg".

## 5. Potential Adjustments
- [ ] Optional: Move static/templates to app/ (update Blueprint).
- [ ] Windows: Use waitress if Gunicorn issues.
- [ ] Rollback: git checkout HEAD~1.

This checklist ensures a smooth migration. Implement in code mode after approval.
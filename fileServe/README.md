# Flask File Server
A self-hosted Flask-based utility for quickly transferring files between machines without needing to set up FTP or SMB shares.

**Note**: This app now includes HTTP Basic Authentication for security. All endpoints require valid credentials (username/password) via the `Authorization: Basic <base64(username:password)>` header. Browsers will prompt for credentials; tools like curl use `-u user:pass`.

![Screenshot](https://raw.githubusercontent.com/harishkarthiktk/publicUtilities/refs/heads/master/fileServe/docs/Screenshot.png "File Serve with Upload Utility")

---

## Current Features
- **File Browser UI**: Explore folder structure starting from a configurable `serveFolder`
- **Folder Support**: Nested directories are rendered and navigable
- **File Download**: Any listed file can be downloaded via the web UI
- **Drag-and-Drop Upload**: Upload single files or entire folder structures
- **Basic Security**: Prevents directory traversal and unauthorized filesystem access
- **HTTP Basic Authentication**: All routes protected; requires username/password (configurable via env vars)
- **Temp Zip Cleanup**: Folders downloaded as ZIPs are auto-cleaned after delivery
- **File Filtering**: Only files with safe extensions (`.txt`, `.pdf`, `.jpg`, etc.) are accepted during upload

---

## Upcoming Features: Admin Info
> (Planned section to appear at bottom of UI)
- **Total file count**
- **Total storage used**
- **Lifespan indicators** for uploaded files (e.g., "uploaded 3 hours ago")

---

## Planned Security Features
- **Access Token in URL** (e.g. `/?token=abc123`)
- **Optional Upload Password**
- **Rate Limiting or Time-Boxed Access**
- **Access logs and audit trail** (optional)

---

## Planned Functional Features
- **Select and Download Multiple Files as a ZIP**
- **Unzip Uploaded ZIP Archives Automatically**
- **QR Code for easy access from mobile devices**
- **Auto-delete old files** (based on file age or max count)
- **Pagination** of the list when the files and folders in the served folder becomes lot.
- **Search** functionality of quickly finding the file/path being searched in the entire listing.

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/harishkarthiktk/flask-file-server.git
cd flask-file-server
```

2. Create environment & install dependencies:
```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

3. (Optional) Set up authentication credentials in a `.env` file or export as environment variables:
   ```
   BASIC_AUTH_USER=your_username
   BASIC_AUTH_PASSWORD=your_secure_password
   ```
   Defaults to `admin` / `password` if not set. Rotate credentials regularly by updating these values and restarting the app.

3. Run the app:
```bash
python app.py
```
Then open [http://localhost:8000](http://localhost:8000) in your browser. You'll be prompted for username/password.

**Usage with curl (example)**:
```bash
curl -u your_username:your_password http://localhost:8000/
```

---

## Configuration
Edit these in `app.py` if needed, or use environment variables:

| Variable                  | Purpose                                      | Default                  |
|---------------------------|----------------------------------------------|--------------------------|
| `SERVE_FOLDER`            | Root directory to serve files from           | `serveFolder`            |
| `UPLOAD_FOLDER`           | Where uploads get stored                     | Same as `SERVE_FOLDER`   |
| `TEMP_DIR`                | Folder used to store temp zips               | `temp_zips`              |
| `BASIC_AUTH_USER`         | Username for Basic Auth                      | `admin`                  |
| `BASIC_AUTH_PASSWORD`     | Password for Basic Auth (rotate regularly)   | `password`               |
| `port` (in `app.run()`)   | Port number (default `8000`)                 | `8000`                   |
| `host` (in `app.run()`)   | Set to `0.0.0.0` to allow LAN access         | `127.0.0.1`              |
| `BASIC_AUTH_USERS_FILE`   | Path to YAML file for multiple users (optional) | `users.yaml`             |

**Credential Rotation Plan**:
- Update `BASIC_AUTH_PASSWORD` in your `.env` file or environment.
- Restart the app (`python app.py`).
- Use a password manager; change every 90 days or after potential exposure.
- For production, consider hashing (but Basic Auth sends plaintext—use HTTPS!).
- Log failed attempts (already enabled) to monitor brute-force attacks.

### YAML-Based Multi-User Authentication (Optional)

For supporting multiple users, create a `users.yaml` file in the project root (or set `BASIC_AUTH_USERS_FILE` env var to a custom path). The YAML can be in one of two formats:

1. **With 'users' key** (recommended):
   ```yaml
   users:
     alice: secret1
     bob: secret2
     admin: adminpass
   ```

2. **Flat mapping**:
   ```yaml
   alice: secret1
   bob: secret2
   admin: adminpass
   ```

If the YAML file exists and is valid, authentication will use it first. If invalid or missing, it falls back to single-user env vars (`BASIC_AUTH_USER`/`BASIC_AUTH_PASSWORD`).

**Testing YAML Auth**:
- Set `BASIC_AUTH_USERS_FILE=users.yaml` (or your path).
- Restart the app.
- Test with curl: `curl -u alice:secret1 http://localhost:8000/`
- Invalid creds: `curl -u wrong:wrong http://localhost:8000/` (should return 401).
- Fallback test: Remove YAML, use env user: `curl -u admin:password http://localhost:8000/`.

**Security Notes**:
- Store YAML securely (e.g., gitignore it, use .env for path).
- Rotate passwords regularly.
- For production, consider hashed passwords (future enhancement) and HTTPS.

---

## API Endpoints
All endpoints require Basic Auth. Use `-u user:pass` with curl or equivalent.

| Method | Path                       | Description                      |
|--------|----------------------------|----------------------------------|
| GET    | `/`                        | Show browser UI with files       |
| GET    | `/files/<path>`           | Download single file             |
| GET    | `/download-folder/<path>` | Download folder as ZIP           |
| POST   | `/upload`                 | Upload files/folders             |

---

## Considerations
- This is a utility, not a hardened production tool
- Great for LAN use, secure behind firewall/VPN
- Always use HTTPS in production (e.g., via reverse proxy like Nginx/Apache)
- Authentication logs failed/successful attempts to `logs/app.log`
- Avoid exposing it directly to the internet without additional hardening (e.g., rate limiting, IP whitelisting)

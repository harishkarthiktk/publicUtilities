# Flask File Server
A self-hosted Flask-based utility for quickly transferring files between machines without needing to set up FTP or SMB shares.

![Screenshot](https://raw.githubusercontent.com/harishkarthiktk/publicUtilities/refs/heads/master/fileServe/docs/Screenshot.png "File Serve with Upload Utility")

---

## Current Features
- **File Browser UI**: Explore folder structure starting from a configurable `serveFolder`
- **Folder Support**: Nested directories are rendered and navigable
- **File Download**: Any listed file can be downloaded via the web UI
- **Drag-and-Drop Upload**: Upload single files or entire folder structures
- **Basic Security**: Prevents directory traversal and unauthorized filesystem access
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

3. Run the app:
```bash
python app.py
```
Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Configuration
Edit these in `app.py` if needed:

| Variable       | Purpose                        |
|----------------|---------------------------------|
| `SERVE_FOLDER` | Root directory to serve files from |
| `UPLOAD_FOLDER`| Where uploads get stored        |
| `TEMP_DIR`     | Folder used to store temp zips  |
| `port`         | Port number (default `8000`)     |
| `host`         | Set to `0.0.0.0` to allow LAN access |

---

## API Endpoints
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
- Avoid exposing it directly to the internet without hardening

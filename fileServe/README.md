# Flask File Server

A simple Flask-based file server that allows browsing and downloading files from a designated folder, with upcoming drag-and-drop upload functionality.

I have written this utility to quickly transfer files from and to my local machines, instead of accessing my ftp/smb networks.

## Features

- Browse files in the designated `serveFolder` directory
- Download files via web interface
- Basic security checks to prevent directory traversal
- Upcoming feature: Drag-and-drop file/folder upload

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/harishkarthiktk/flask-file-server.git
   cd flask-file-server
   ```

2. Setup env if needed, install dependencies:
   ```bash
   python3 -m venv env
   source activate env/bin/activate
   python -m pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```
Access the file server in your browser at http://localhost:8000

## Important Considerations
### Security Notes
- The application checks for directory traversal attempts
- Currently no authentication - anyone on your network can access files
- For production use, consider adding:
- Authentication
- Rate limiting
- HTTPS

### Configuration
- Modify these variables in app.py as needed:
- SERVE_FOLDER: Change to your preferred directory path
- host="0.0.0.0": Change if you want to restrict access
- port=8000: Change if you prefer a different port

### API Endpoints
- GET /: Lists all available files with download links
- GET /files/<filename>: Downloads the specified file
- POST /upload (Coming soon): Will handle file uploads

## Upcoming Features
- Drag-and-drop file/folder upload interface
- File upload endpoint
- Progress indicators for uploads/downloads
- Authentication options
- Folder navigation (currently only shows files in root directory)


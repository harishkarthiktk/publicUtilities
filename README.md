# Consolidated Information

Random utilities that I have written for various functions

# Flask File Server
A self-hosted Flask-based utility for quickly transferring files between machines without needing to set up FTP or SMB shares.

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
# Sansio

This folder contains code that can be used by alternative Flask
implementations, for example Quart. The code therefore cannot do any
IO, nor be part of a likely IO path. Finally this code cannot use the
Flask globals.
# parseContentGPT

## Purpose
I often need to clean and structure messy text content, like web-scraped data, for my knowledge base. 
While I could manually edit each file, why not have gpt do it for me?

This tool uses OpenAI's GPT-4 to intelligently parse text files, 
    removing garbage content and formatting the output as clean markdown.

## Usage
```
options:
  -h, --help            show this help message and exit
  -f FOLDER, --folder FOLDER
                        Input folder containing .txt/.md files (default: ./input)
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Folder to save processed files (default: ./outputs)
  -w WORKERS, --workers WORKERS
                        Maximum concurrent API requests (default: 3)
```

## Requirements
- Python 3.x
- OpenAI API key (stored in system keyring)
- Required packages: `openai`, `keyring`, `tqdm`

## Setup
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Store your OpenAI API key:
Obtain your API Key for ChatGPT.
```bash
python -c "import keyring; keyring.set_password('OpenAI', 'api_key', 'your-api-key-here')"
```

## Disclaimer
This tool uses the OpenAI API which may have content moderation policies and usage limits. The quality of output depends on GPT-4's capabilities and may require manual verification. Be mindful of:
- API costs (charged per request). The default model being used is gpt-4.1-nano, which I find to be extremely effective.
- You can change the model at your own risk and need, if the content size exceeds as what the nano model can work with.
- Content ownership of processed files.
- Potential hallucinations or errors in AI processing.

Use responsibly and verify critical outputs. The liability of tool usage lies with the user themselves.

---


# pageDownloads

## Purpose
I often need to save webpages locally to augment to my knowledge base.
The most straight forward way of doing it is by downloading it as html using the browser's save-as functionality.

But being a programmer, we will spend an hour building tools to do an activity that would have taken a few minutes.

## Usage
options:
```
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to a text file with URLs, one per line.
  -u URL, --url URL     A single URL to process.
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Folder to save the output files.
```

## Disclaimer
Web scrapping and downloading of files might be in breach of T&C of the targeted websites, and this tool is strictly for personal use.
Use with caution and ethical considerations, and the liability of the tool usage lies with the user themselves.

---



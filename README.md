-e # Consolidated Information

Random utilities that I have written for various functions

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



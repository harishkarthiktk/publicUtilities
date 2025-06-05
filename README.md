# Consolidated Information

Random utilities that I have written for various functions

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



import argparse
import os
from pathlib import Path
from openai import OpenAI
import keyring
import time
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def setup_logging():
    """Setup logging to logs.txt file"""
    log_file = "logs.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n\n=== New Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    return log_file

def log_message(log_file, message):
    """Append message to log file"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def get_api_client():
    """Initialize OpenAI client with API key from keyring"""
    key = keyring.get_password('OpenAI', 'api_key')
    if not key:
        raise ValueError("No API key found in keyring. Please set it with keyring.set_password('OpenAI', 'api_key', 'your-key')")
    return OpenAI(api_key=key)

def process_file(input_path, output_folder, client, log_file):
    """Process a single file with GPT-4 and save the result"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        messages = [
            {"role": "system", "content": "You are a helpful text parsing assistant capable of reading through the given text, and removing gibberish or unwanted html tags. You will extract just useful information and links if present and structure it as markdown."},
            {"role": "user", "content": content}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=messages,
            temperature=0.3
        )
        
        processed_content = response.choices[0].message.content
        
        output_path = Path(output_folder) / Path(input_path).name
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        success_msg = f"Successfully processed: {input_path} -> {output_path}"
        print(success_msg)
        log_message(log_file, success_msg)
        return True
    
    except Exception as e:
        error_msg = f"Error processing {input_path}: {str(e)}"
        print(error_msg)
        log_message(log_file, error_msg)
        return False

def process_files_in_folder(input_folder, output_folder, log_file, max_workers=3):
    """Process files with controlled concurrency while maintaining tqdm progress"""
    client = get_api_client()
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    
    output_folder.mkdir(parents=True, exist_ok=True)
    
    input_files = []
    for ext in ['*.txt', '*.md']:
        input_files.extend(input_folder.glob(ext))
    
    if not input_files:
        msg = f"No .txt or .md files found in {input_folder}"
        print(msg)
        log_message(log_file, msg)
        return 0
    
    total_files = len(input_files)
    msg = f"Found {total_files} files to process (using {max_workers} workers)..."
    print(msg)
    log_message(log_file, msg)
    
    success_count = 0
    with tqdm(total=total_files, desc="Processing files") as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    process_file, 
                    input_file, 
                    output_folder, 
                    client, 
                    log_file
                ): input_file for input_file in input_files
            }
            
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                pbar.update(1)
    
    summary_msg = f"\nProcessing complete. Success: {success_count}/{total_files}"
    print(summary_msg)
    log_message(log_file, summary_msg)
    return success_count

def main():
    log_file = setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Process text files within a folder to get clean and structured content. It is intended to be used for cleaning web-scrapped content."
    )

    parser.add_argument('-f', '--folder', default="./input", help='Input folder containing .txt/.md files')
    parser.add_argument('-o', '--output-folder', default="./outputs", help='Output folder for processed files')
    parser.add_argument('-w', '--workers', type=int, default=3, help='Maximum concurrent API requests (default: 3)')
    
    args = parser.parse_args()
    
    start_msg = f"Starting processing: {args.folder} -> {args.output_folder}"
    print(start_msg)
    log_message(log_file, start_msg)
    
    start_time = time.time()
    process_files_in_folder(args.folder, args.output_folder, log_file, args.workers)
    
    duration = time.time() - start_time
    end_msg = f"\nTotal processing time: {duration:.2f} seconds"
    print(end_msg)
    log_message(log_file, end_msg)

if __name__ == '__main__':
    main()

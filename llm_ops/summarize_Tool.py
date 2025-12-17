import argparse
import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

from dotenv import load_dotenv

from file_utils import scan_and_populate_processed, save_processed_json
from llm_client import CONFIG
from processor import process_folder, process_single_file

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Summarize .md files using Ollama or OpenRouter"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--input-file", help="Path to a single .md input file")
    group.add_argument(
        "-f", "--folder-input", help="Path to input folder containing .md files"
    )
    parser.add_argument(
        "-o", "--output-folder", default="./", help="Output folder (default: ./)"
    )

    parser.add_argument(
        "--persona",
        choices=list(CONFIG.get("PERSONAS", {}).keys()),
        default="summarizer",
        help="Persona to use (default: summarizer)",
    )
    parser.add_argument("--model", help="Model to use (default from config based on API)")
    parser.add_argument(
        "--instructions", default="", help="Specific instructions for the task"
    )
    parser.add_argument(
        "--api",
        choices=["ollama", "openrouter"],
        default="openrouter",
        help="API to use (default: ollama)",
    )
    parser.add_argument(
        "--api-key", help="OpenRouter API key (or use OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--openrouter-base-url",
        default=CONFIG["openrouter_base"],
        help="OpenRouter base URL (default from config)",
    )
    parser.add_argument(
        "--http-referer",
        default=os.getenv("OPENROUTER_HTTP_REFERER", ""),
        help=(
            "HTTP-Referer header for OpenRouter (optional, or use "
            "OPENROUTER_HTTP_REFERER env var)"
        ),
    )
    parser.add_argument(
        "--x-title",
        default=os.getenv("OPENROUTER_X_TITLE", ""),
        help=(
            "X-Title header for OpenRouter (optional, or use "
            "OPENROUTER_X_TITLE env var)"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help=(
            "Request timeout in seconds (default: 120 for Ollama, 300 for OpenRouter)"
        ),
    )
    parser.add_argument(
        "--save-interval",
        type=int,
        default=1,
        help="Save processed JSON every N files (default: 1 for immediate saves)",
    )

    args = parser.parse_args()

    # CLI Validation for input paths
    if args.input_file:
        input_path = Path(args.input_file)
        if not input_path.exists():
            parser.error(f"Input file '{args.input_file}' does not exist.")
        if input_path.is_dir():
            # We'll handle fallback later, but warn here if needed
            pass  # Fallback logic below

    api_type = args.api
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if api_type == "openrouter" and not api_key:
        parser.error(
            "OpenRouter API key is required. Provide --api-key or set the "
            "OPENROUTER_API_KEY environment variable."
        )
    model = args.model or CONFIG[f"{api_type}_model"]
    base_url_or_host = (
        CONFIG["ollama_host"]
        if api_type == "ollama"
        else (args.openrouter_base_url or CONFIG["openrouter_base"])
    )
    http_referer = args.http_referer
    x_title = args.x_title
    timeout = (
        args.timeout
        if args.timeout
        else (CONFIG["openrouter_timeout"] if api_type == "openrouter" else 120)
    )
    persona = args.persona
    instructions = args.instructions

    # Create output directory if it doesn't exist
    os.makedirs(args.output_folder, exist_ok=True)

    # Setup logging
    log_file = os.path.join(args.output_folder, "log.txt")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="a",
    )
    logger = logging.getLogger(__name__)

    if logger:
        logger.info(
            f"Script started - Output: {args.output_folder}, API: {api_type}, "
            f"Persona: {persona}, Model: {model}, Timeout: {timeout}s"
            + (f", Instructions: '{instructions}'" if instructions else "")
        )

    # Load or initialize processed files tracking
    processed_file_path = Path(args.output_folder) / "processedFiles.json"

    stop_event = Event()

    def signal_handler(sig, frame):
        stop_event.set()
        raise KeyboardInterrupt("User interrupt requested")

    signal.signal(signal.SIGINT, signal_handler)
    try:
        if processed_file_path.exists():
            with open(processed_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            processed_files = data.get("processed_files", [])
            metadata = data.get("metadata", {})
            metadata.setdefault("failed_attempts", [])  # Ensure key exists
        else:
            processed_files = []
            metadata = {"failed_attempts": []}
        processed_set = set(processed_files)
    except json.JSONDecodeError as e:
        if logger:
            logger.warning(f"Invalid processedFiles.json ({e}), starting fresh.")
        processed_files = []
        processed_set = set()
        metadata = {"failed_attempts": []}

    # Scan output folder and populate processed_files with valid outputs
    added = scan_and_populate_processed(
        args.output_folder, processed_files, processed_set, metadata, logger
    )
    if added > 0:
        save_processed_json(processed_file_path, processed_files, metadata, logger=logger)
        if logger:
            logger.info(f"Populated {added} existing valid files into processed tracking.")

    new_processed_total = 0
    skipped_total = 0
    save_interval = args.save_interval

    processing_error = None
    try:
        if args.input_file:
            input_path = Path(args.input_file)
            if input_path.is_dir():
                if logger:
                    logger.info(
                        f"Detected directory '{args.input_file}'; automatically switching to folder mode."
                    )
                print(f"Detected directory; processing as folder: {args.input_file}")
                np, s = process_folder(
                    input_path,
                    args.output_folder,
                    persona,
                    model,
                    base_url_or_host,
                    api_type,
                    api_key,
                    http_referer,
                    x_title,
                    instructions,
                    logger,
                    processed_files,
                    processed_set,
                    timeout,
                    CONFIG["max_retries"],
                    CONFIG["max_workers"],
                    processed_file_path,
                    metadata,
                    save_interval,
                    stop_event,
                )
            else:
                if logger:
                    logger.info(f"Processing single file: {args.input_file}")
                np, s, _ = process_single_file(
                    input_path,
                    args.output_folder,
                    persona,
                    model,
                    base_url_or_host,
                    api_type,
                    api_key,
                    http_referer,
                    x_title,
                    instructions,
                    logger,
                    processed_files,
                    processed_set,
                    None,
                    timeout,
                    CONFIG["max_retries"],
                    processed_file_path,
                    metadata,
                    save_interval,
                    1,
                    stop_event,
                )
                new_processed_total += np
                skipped_total += s
                # For single file, np and s are from tuple, but process_folder returns (np, s)
                # Adjust: for single, np is first, s second, ignore third
        elif args.folder_input:
            if logger:
                logger.info(f"Processing folder: {args.folder_input}")
            np, s = process_folder(
                args.folder_input,
                args.output_folder,
                persona,
                model,
                base_url_or_host,
                api_type,
                api_key,
                http_referer,
                x_title,
                instructions,
                logger,
                processed_files,
                processed_set,
                timeout,
                CONFIG["max_retries"],
                CONFIG["max_workers"],
                processed_file_path,
                metadata,
                save_interval,
                stop_event,
            )
            new_processed_total += np
            skipped_total += s
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving progress and exiting.")
        if logger:
            logger.info("Script interrupted by user.")
        # Save on interrupt (interrupted flag already set in process_folder if applicable)
        if "interrupted" not in metadata:
            metadata["last_run"] = datetime.now(timezone.utc).isoformat() + "Z"
            metadata["interrupted"] = True
            save_processed_json(
                processed_file_path, processed_files, metadata, logger=logger
            )
        sys.exit(0)
    except Exception as e:
        processing_error = e
        print(f"Error during processing: {e}")
        if logger:
            logger.error(f"Error during processing: {e}")

    # Final update and safe save
    metadata["last_run"] = datetime.now(timezone.utc).isoformat() + "Z"
    metadata["total_processed"] = len(processed_files)
    metadata["skipped_this_run"] = skipped_total  # per run
    if "interrupted" in metadata:
        del metadata["interrupted"]

    save_processed_json(processed_file_path, processed_files, metadata, logger=logger)

    if processing_error:
        print("Processing completed with errors, but processed files list updated.")
    else:
        print("Processing completed successfully.")
    if logger:
        logger.info(
            f"Run complete (API: {api_type}): {new_processed_total} new files processed, "
            f"{skipped_total} skipped. Total ever processed: {len(processed_files)}"
        )
        if metadata.get("failed_attempts"):
            logger.warning(
                f"{len(metadata['failed_attempts'])} failures tracked this run."
            )


if __name__ == "__main__":
    main()
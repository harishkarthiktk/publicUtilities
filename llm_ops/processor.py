import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from tqdm import tqdm

from llm_client import call_llm_api, build_prompt, CONFIG, PERSONAS
from file_utils import save_processed_json


def process_single_file(
    input_path,
    output_dir,
    persona,
    model,
    base_url_or_host,
    api_type,
    api_key=None,
    http_referer="",
    x_title="",
    instructions="",
    logger=None,
    processed_files=None,
    processed_set=None,
    lock=None,
    timeout=120,
    max_retries=3,
    processed_file_path=None,
    metadata=None,
    save_interval=1,
    file_count=0,
    stop_event=None,
):
    """
    Process a single .md file: read content, build prompt parts, call API, write output.
    Returns: (new_processed: int, skipped: int, updated_count: int) - 1 if newly processed,
    1 if skipped, updated_count for save triggering.
    """
    filename = input_path.name
    output_path = Path(output_dir) / filename

    if not input_path.exists():
        if logger:
            logger.warning(f"Input file missing, skipping: {filename}")
        return 0, 0, 0  # not processed, not skipped, no update

    if input_path.is_dir():
        raise ValueError(
            f"Input '{input_path}' is a directory. Use --folder-input for directories."
        )

    # Check if already processed and valid (thread-safe)
    output_exists = output_path.exists()
    output_valid = output_exists and (output_path.stat().st_size >= 256)
    is_processed = False
    if lock:
        with lock:
            is_processed = filename in processed_set and output_valid

    if is_processed:
        if logger:
            logger.info(f"Skipping already processed and valid: {filename}")
        return 0, 1, 0  # not new, skipped, no update

    # Process (reprocess if output exists but invalid or not tracked)
    if logger:
        logger.info(
            f"Starting to process (new or reprocess): {filename} with persona '{persona}'"
        )

    if input_path.is_file() and not input_path.suffix.lower() == '.md':
        if logger:
            logger.error(f"Invalid file type for {filename}, skipping")
        return 0, 0, 0

    content = input_path.read_text(encoding='utf-8')
    start_time = time.time()
    template = PERSONAS.get(persona, PERSONAS["summarizer"])
    system_part, user_part = build_prompt(template, content, instructions)

    try:
        summary = call_llm_api(
            api_type,
            model,
            base_url_or_host,
            system_part,
            user_part,
            api_key,
            http_referer,
            x_title,
            timeout,
            max_retries,
            stop_event,
        )
    except Exception as e:
        if logger:
            logger.error(f"API error for {filename}: {e}")
        # Track failure
        if processed_files is not None and metadata is not None and lock:
            with lock:
                metadata.setdefault("failed_attempts", []).append(
                    {
                        "filename": filename,
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                save_processed_json(
                    processed_file_path, processed_files, metadata, lock, logger
                )
        return 0, 0, 0

    output_path.write_text(summary, encoding='utf-8')
    end_time = time.time()
    duration = end_time - start_time

    # Validate output
    if output_path.stat().st_size < 1024:
        if logger:
            logger.error(
                f"Output too small for {filename} ({output_path.stat().st_size} bytes), "
                f"not marking as processed"
            )
        # Optionally delete invalid output: output_path.unlink(missing_ok=True)
        # Track validation failure
        if processed_files is not None and metadata is not None and lock:
            with lock:
                metadata.setdefault("failed_attempts", []).append(
                    {
                        "filename": filename,
                        "error": "Output too small",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                save_processed_json(
                    processed_file_path, processed_files, metadata, lock, logger
                )
        return 0, 0, 0

    # Mark as processed
    updated = False
    if processed_files is not None and filename not in processed_set:
        if lock:
            with lock:
                if filename not in processed_set:  # Double-check
                    processed_files.append(filename)
                    processed_set.add(filename)
                    updated = True
        else:
            if filename not in processed_set:
                processed_files.append(filename)
                processed_set.add(filename)
                updated = True

    if logger:
        logger.info(
            f"Completed {filename}: saved to {output_path}, processing time: "
            f"{duration:.2f} seconds"
        )
    print(f"Processed: {filename} -> {output_path} (took {duration:.2f}s)")

    # Trigger intermediate save if updated and interval allows
    if (
        updated
        and processed_file_path
        and metadata
        and (file_count % save_interval == 0 or save_interval == 1)
    ):
        if lock:
            with lock:
                save_processed_json(
                    processed_file_path, processed_files, metadata, lock, logger
                )
        else:
            save_processed_json(processed_file_path, processed_files, metadata)

    return 1, 0, 1 if updated else 0  # newly processed, update flag


def process_folder(
    folder_path,
    output_dir,
    persona,
    model,
    base_url_or_host,
    api_type,
    api_key=None,
    http_referer="",
    x_title="",
    instructions="",
    logger=None,
    processed_files=None,
    processed_set=None,
    timeout=120,
    max_retries=3,
    max_workers=5,
    processed_file_path=None,
    metadata=None,
    save_interval=1,
    stop_event=None,
):
    """
    Process all .md files in the folder (non-recursive, top-level only).
    Use tqdm for progress indication.
    Returns: (total_new_processed: int, total_skipped: int)
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError(f"{folder_path} is not a valid directory")

    md_files = list(folder.glob("*.md"))
    if not md_files:
        print("No .md files found in the folder.")
        if logger:
            logger.info("No .md files found in the folder.")
        return 0, 0

    # Filter files to process: exclude already processed and valid
    files_to_process = []
    skipped = 0
    lock = Lock()  # Ensure lock exists
    for input_path in md_files:
        filename = input_path.name
        output_path = Path(output_dir) / filename
        output_exists = output_path.exists()
        output_valid = output_exists and (output_path.stat().st_size >= 256)
        is_processed = False
        with lock:
            is_processed = filename in processed_set and output_valid
        if not is_processed:
            files_to_process.append(input_path)
        else:
            skipped += 1

    total_files = len(md_files)
    if logger:
        logger.info(
            f"Found {total_files} .md files in {folder_path}, will process "
            f"{len(files_to_process)}, skip {skipped}"
        )

    if not files_to_process:
        print(f"No files to process (all {skipped} skipped).")
        return 0, skipped

    new_processed = 0
    total_skipped = skipped
    skipped_from_errors = 0
    file_counter = 0

    effective_workers = min(max_workers, len(files_to_process))
    if logger:
        logger.info(
            f"Processing {len(files_to_process)} files with {effective_workers} "
            f"concurrent workers"
        )

    executor = ThreadPoolExecutor(max_workers=effective_workers)
    try:
        # Submit all tasks
        future_to_file = {
            executor.submit(
                process_single_file,
                input_path,
                output_dir,
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
                lock,
                timeout,
                max_retries,
                processed_file_path,
                metadata,
                save_interval,
                file_counter,
                stop_event,
            ): input_path
            for input_path in files_to_process
        }

        # Process as they complete
        with tqdm(total=len(files_to_process), desc="Processing files") as pbar:
            for future in as_completed(future_to_file):
                if stop_event and stop_event.is_set():
                    break
                input_path = future_to_file[future]
                try:
                    np, s, uc = future.result()
                    new_processed += np
                    total_skipped += s
                    file_counter += 1
                    # Intermediate save every save_interval
                    if (
                        uc > 0
                        and processed_file_path
                        and metadata
                        and (file_counter % save_interval == 0)
                    ):
                        with lock:
                            save_processed_json(
                                processed_file_path, processed_files, metadata, lock, logger
                            )
                    if logger:
                        logger.info(
                            f"Completed asynchronously: {input_path.name} "
                            f"(new: {np}, skip: {s}, updated: {uc})"
                        )
                    print(f"Async processed: {input_path.name} (new: {np}, skip: {s})")
                except Exception as e:
                    filename = input_path.name
                    if logger:
                        logger.error(f"Async processing error for {filename}: {e}")
                    print(f"Error processing {filename}: {e}")
                    skipped_from_errors += 1
                    # Track async error
                    if processed_files is not None and metadata is not None:
                        with lock:
                            metadata.setdefault("failed_attempts", []).append(
                                {
                                    "filename": filename,
                                    "error": f"Async error: {str(e)}",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                            )
                            save_processed_json(
                                processed_file_path, processed_files, metadata, lock, logger
                            )
                pbar.update(1)
    except KeyboardInterrupt:
        print(
            "\nInterrupted during folder processing. Shutting down executor without waiting "
            "and saving progress."
        )
        if logger:
            logger.info("Interrupted during folder processing.")
        executor.shutdown(wait=False)
        # Save current state
        if processed_file_path and metadata:
            with lock:
                metadata['last_run'] = datetime.now(timezone.utc).isoformat() + 'Z'
                metadata['interrupted'] = True
                save_processed_json(
                    processed_file_path, processed_files, metadata, lock, logger
                )
        raise  # Re-raise to main handler
    finally:
        executor.shutdown(wait=True)  # Ensure cleanup if not interrupted

    total_skipped += skipped_from_errors
    return new_processed, total_skipped
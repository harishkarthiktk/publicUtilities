import json
import os
from datetime import datetime, timezone
from pathlib import Path


def scan_and_populate_processed(
    output_dir,
    processed_files,
    processed_set,
    metadata,
    logger=None,
):
    """
    Scan the output directory recursively for existing .md files and populate processed_files
    if they meet validation criteria (size >= 256 bytes) and are not already tracked.
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        if logger:
            logger.info(
                f"Output directory {output_dir} does not exist yet, skipping scan."
            )
        return 0

    added_count = 0
    scanned_count = 0
    valid_count = 0

    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.lower().endswith('.md'):
                scanned_count += 1
                full_path = Path(os.path.join(root, file))
                try:
                    if full_path.stat().st_size >= 256:
                        filename = file  # Use basename as in processing logic
                        if filename not in processed_set:
                            processed_files.append(filename)
                            processed_set.add(filename)
                            added_count += 1
                        valid_count += 1
                    else:
                        if logger:
                            logger.debug(
                                f"Skipped invalid output (size < 256): {file}"
                            )
                except OSError as e:
                    if logger:
                        logger.warning(f"Could not access {full_path}: {e}")

    if logger:
        logger.info(
            f"Scan complete: {scanned_count} .md files found, {valid_count} valid, "
            f"{added_count} added to processed list."
        )

    # Update metadata
    metadata['scan_info'] = metadata.get('scan_info', [])
    metadata['scan_info'].append({
        'scanned_at': datetime.now(timezone.utc).isoformat() + 'Z',
        'scanned_count': scanned_count,
        'valid_count': valid_count,
        'added_count': added_count
    })

    return added_count


def save_processed_json(
    processed_file_path,
    processed_files,
    metadata,
    lock=None,
    logger=None,
):
    """
    Atomically save processed_files and metadata to JSON using a temporary file for safety.
    """
    data = {
        'processed_files': processed_files,
        'metadata': metadata
    }
    temp_path = processed_file_path.with_suffix('.tmp')
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if temp_path.exists():
            temp_path.rename(processed_file_path)
    except (OSError, ValueError) as e:
        # Fallback to backup
        backup_path = processed_file_path.with_suffix('.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if logger:
            logger.error(
                f"Failed to save to {processed_file_path}: {e}. Saved to backup: "
                f"{backup_path}"
            )
import os
from difflib import SequenceMatcher
from pathlib import Path


def calculate_similarity(file_path_1, file_path_2):
    """
    Calculate similarity ratio between two files (0.0 to 1.0).
    Compares file contents line by line.
    """
    try:
        with open(file_path_1, 'r', encoding='utf-8', errors='ignore') as f1:
            content1 = f1.readlines()
        with open(file_path_2, 'r', encoding='utf-8', errors='ignore') as f2:
            content2 = f2.readlines()

        matcher = SequenceMatcher(None, content1, content2)
        return matcher.ratio()
    except Exception:
        return 0.0


def detect_and_remove_duplicates(directory, logger=None, similarity_threshold=0.98):
    """
    Detect duplicate files in directory by content similarity and remove them.
    Keeps the first occurrence, removes subsequent duplicates matching threshold.
    similarity_threshold: float between 0.0 and 1.0 (default 0.98 = 98%)
    Returns a dict with similarity_groups -> list of files mapping and deleted files list.
    """
    if not os.path.exists(directory):
        if logger:
            logger.warning(f"Directory does not exist: {directory}")
        return {'similarity_groups': {}, 'deleted_files': []}

    deleted_files = []
    processed_files = set()
    similarity_groups = {}

    # Get all .md files in directory
    md_files = sorted(Path(directory).glob('*.md'))

    if not md_files:
        if logger:
            logger.info(f"No markdown files found in {directory}")
        return {'similarity_groups': {}, 'deleted_files': []}

    if logger:
        logger.info(f"Scanning {len(md_files)} files for duplicates (threshold: {similarity_threshold*100}%) in {directory}")

    # Compare each file with others to find duplicates
    for i, file_path_1 in enumerate(md_files):
        if str(file_path_1) in processed_files:
            continue

        group_key = str(file_path_1)
        similarity_groups[group_key] = [str(file_path_1)]
        processed_files.add(str(file_path_1))

        # Compare with remaining files
        for file_path_2 in md_files[i+1:]:
            if str(file_path_2) in processed_files:
                continue

            similarity = calculate_similarity(str(file_path_1), str(file_path_2))

            if similarity >= similarity_threshold:
                similarity_groups[group_key].append((str(file_path_2), similarity))
                processed_files.add(str(file_path_2))

    # Remove duplicates, keeping first occurrence
    # Safety check: ensure at least 1 file remains
    total_files_to_keep = len(md_files) - sum(len(files) - 1 for files in similarity_groups.values() if len(files) > 1)

    if total_files_to_keep < 1:
        if logger:
            logger.warning("Duplicate removal would delete all files. Aborting to preserve at least 1 file.")
        return {'similarity_groups': similarity_groups, 'deleted_files': []}

    for group_key, files in similarity_groups.items():
        if len(files) > 1:
            if logger:
                logger.info(f"Found {len(files)} similar files")
                logger.info(f"  Keeping: {os.path.basename(group_key)}")

            # Keep first, delete the rest
            for duplicate_entry in files[1:]:
                duplicate_file = duplicate_entry[0] if isinstance(duplicate_entry, tuple) else duplicate_entry
                similarity_score = duplicate_entry[1] if isinstance(duplicate_entry, tuple) else 1.0

                try:
                    os.remove(duplicate_file)
                    deleted_files.append(duplicate_file)
                    if logger:
                        logger.info(f"  Deleted: {os.path.basename(duplicate_file)} (similarity: {similarity_score*100:.1f}%)")
                except Exception as e:
                    if logger:
                        logger.error(f"Failed to delete {duplicate_file}: {e}")

    if logger:
        if deleted_files:
            logger.info(f"Duplicate removal complete. Deleted {len(deleted_files)} files")
        else:
            logger.info("No duplicates found")

    return {'similarity_groups': similarity_groups, 'deleted_files': deleted_files}

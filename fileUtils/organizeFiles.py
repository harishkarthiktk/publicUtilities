#!/c/Users/haris/.venv/Scripts/python
# -*- coding: utf-8 -*-
"""
organizeFiles.py

Usage examples:
  python organizeFiles.py -w /path/to/folder
  python organizeFiles.py -w /path/to/folder -V
  python organizeFiles.py -w /path/to/folder -P
"""

import argparse
import logging
import os
import shutil
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, List, Set, Tuple
from tqdm import tqdm

# Configuration
MAX_RECURSION = 20
FOLDER_THRESHOLD = 3
VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.3gp', '.m4v'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.heic', '.webp'}


def setup_logging():
    logger = logging.getLogger("organizeFiles")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    handler.setLevel(logging.ERROR)
    logger.addHandler(handler)
    # Optionally, INFO messages can go to stdout
    info_handler = logging.StreamHandler(sys.stdout)
    info_handler.setFormatter(logging.Formatter("%(message)s"))
    info_handler.setLevel(logging.INFO)
    logger.addHandler(info_handler)
    return logger


logger = setup_logging()


def parse_args():
    p = argparse.ArgumentParser(description="Move files in a working directory into Vid/Pic organization.")
    p.add_argument("-w", "--working-dir", required=True, type=Path,
                   help="Target folder to scan and operate upon.")
    p.add_argument("-R", "--recursive", default="yes", choices=["yes", "no"],
                   help='Whether to recurse subfolders. Accepts "yes" or "no". Default: yes.')
    p.add_argument("-V", "--vid", action="store_true",
                   help="Move videos to root; other files into a Pic folder. (default if no mode is chosen)")
    p.add_argument("-P", "--pic", action="store_true",
                   help="Move images to root; other files into a Vid folder. Overrides --vid if both are present.")
    p.add_argument("-f", "--force", action="store_true",
                   help="Force proceed without confirmation prompt.")
    return p.parse_args()


def gather_files(root: Path, recursive: bool, other_folder: str) -> List[Tuple[Path, str]]:
    """Walk the tree with os.scandir and return (path, lowercased_suffix) tuples.

    Only the current mode's destination subfolder (other_folder) is pruned at
    the top level — files already there are at their destination. The opposite
    folder (e.g. Pic in -P mode) is intentionally scanned so any primary-type
    files inside it can be moved to root.
    """
    excluded_top_level = {other_folder}
    out: List[Tuple[Path, str]] = []

    def walk(dir_path: Path, depth: int):
        if depth > MAX_RECURSION:
            return
        try:
            with os.scandir(dir_path) as it:
                entries = list(it)
        except OSError as e:
            logger.error(f"Cannot scan {dir_path}: {e}")
            return
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    if not recursive:
                        continue
                    if depth == 0 and entry.name in excluded_top_level:
                        continue
                    walk(Path(entry.path), depth + 1)
                elif entry.is_file():
                    # follow_symlinks=True (default) so symlinks to files are
                    # collected, matching os.walk's behaviour.
                    p = Path(entry.path)
                    out.append((p, p.suffix.lower()))
            except OSError:
                continue

    walk(root, 0)
    return out


def make_unique_path_provider() -> Callable[[Path], Path]:
    """Returns a thread-safe function that yields a non-conflicting destination
    path and reserves it so concurrent workers can't pick the same suffix (P6).

    Per-destination-directory locks keep contention tight; the in-memory
    `reserved` set short-circuits repeated `exists()` syscalls after the first
    conflict.
    """
    locks: dict = defaultdict(threading.Lock)
    reserved: dict = defaultdict(set)

    def provider(dest: Path) -> Path:
        parent = dest.parent
        stem, suffix = dest.stem, dest.suffix
        lock = locks[parent]
        with lock:
            r = reserved[parent]
            if dest.name not in r and not dest.exists():
                r.add(dest.name)
                return dest
            counter = 1
            while True:
                cand_name = f"{stem}_{counter}{suffix}"
                cand = parent / cand_name
                if cand_name not in r and not cand.exists():
                    r.add(cand_name)
                    return cand
                counter += 1

    return provider


def move_file(src: Path, dest_dir: Path, get_unique: Callable[[Path], Path]) -> Tuple[Path, Path, bool, str]:
    try:
        dest = dest_dir / src.name
        if src == dest:
            return src, dest, True, "skipped (already at destination)"
        dest = get_unique(dest)
        shutil.move(str(src), str(dest))
        return src, dest, True, "moved"
    except Exception as e:
        return src, dest_dir, False, f"error: {e}"


def remove_empty_folders_targeted(root_path: Path, source_dirs: Set[Path], other_folder: str):
    """Only check directories that had files moved out, plus their ancestors up
    to (but not including) root_path (P1). Replaces a full second os.walk over
    the working tree.

    Only the current mode's destination subfolder (other_folder) is protected
    from deletion — it is the canonical output location and should persist even
    when empty. The opposite folder is eligible for removal if emptied.
    """
    excluded = {root_path / other_folder}
    to_check: Set[Path] = set()
    for d in source_dirs:
        try:
            d.relative_to(root_path)
        except ValueError:
            continue
        cur = d
        while cur != root_path:
            to_check.add(cur)
            parent = cur.parent
            if parent == cur:
                break
            cur = parent

    for d in sorted(to_check, key=lambda p: len(p.parts), reverse=True):
        if d in excluded:
            continue
        try:
            if d.exists() and not any(d.iterdir()):
                d.rmdir()
                logger.info(f"Deleted empty folder: {d}")
        except OSError as e:
            logger.error(f"Error removing folder {d}: {e}")


def main():
    args = parse_args()
    working_dir: Path = args.working_dir.expanduser().resolve()

    if not working_dir.exists() or not working_dir.is_dir():
        logger.error(f"Working directory does not exist or is not a directory: {working_dir}")
        return

    recursive = args.recursive.lower() == "yes"

    # Determine mode and set extensions/folder names
    if args.pic:
        mode = "pic"
        primary_exts = IMAGE_EXTS
        other_folder_name = "Vid"
    else:
        mode = "vid"
        primary_exts = VIDEO_EXTS
        other_folder_name = "Pic"

    logger.info(f"Running in {mode.upper()} mode")

    files_with_ext = gather_files(working_dir, recursive, other_folder_name)
    logger.info(f"Found {len(files_with_ext)} files under {working_dir}")

    primary_dest_dir = working_dir
    other_dest_dir = working_dir / other_folder_name

    # Single-pass partition (validation #5) using cached suffix (validation #6).
    # Drop Path.resolve() in the hot path: gather built paths under the already-
    # resolved root, so a plain parent comparison is sufficient (P3).
    move_jobs: List[Tuple[Path, Path]] = []
    for fp, ext in files_with_ext:
        if ext in primary_exts:
            if fp.parent != primary_dest_dir:
                move_jobs.append((fp, primary_dest_dir))
        else:
            if fp.parent != other_dest_dir:
                move_jobs.append((fp, other_dest_dir))

    total_jobs = len(move_jobs)
    if total_jobs == 0:
        logger.info("No files need moving. Exiting.")
    else:
        # Count unique folders to be reorganized
        unique_folders = set(src.parent for src, _ in move_jobs)
        num_folders = len(unique_folders)
        logger.info(f"Found {num_folders} unique folders to reorganize.")

        if num_folders > FOLDER_THRESHOLD and not args.force:
            confirm = input(f"More than {FOLDER_THRESHOLD} folders ({num_folders}) will be affected. Proceed? (y/n): ").lower().strip()
            if confirm != 'y':
                logger.info("Operation cancelled by user.")
                return

        logger.info(f"Will operate on {total_jobs} files.")

        # Pre-create destination directories once instead of from every worker (P4).
        for dest in {primary_dest_dir, other_dest_dir}:
            dest.mkdir(parents=True, exist_ok=True)

        # Group by destination so the OS dir-entry cache stays warm (P7).
        move_jobs.sort(key=lambda j: str(j[1]))

        get_unique = make_unique_path_provider()

        # Worker count tuned for I/O bound moves: too high causes head thrashing
        # on HDDs and only marginal benefit on SSDs (validation #4).
        max_workers = min(16, (os.cpu_count() or 4) * 2)
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_job = {
                ex.submit(move_file, src, dest_dir, get_unique): (src, dest_dir)
                for src, dest_dir in move_jobs
            }
            for future in tqdm(as_completed(future_to_job), total=total_jobs, desc="Moving files"):
                try:
                    src, dest, success, message = future.result()
                    if not success:
                        logger.error(f"{src} -> {dest} failed: {message}")
                    results.append((src, dest, success, message))
                except Exception as e:
                    job = future_to_job.get(future)
                    logger.error(f"Unhandled exception processing {job}: {e}")
                    results.append((job[0], job[1], False, f"unhandled exception: {e}"))

        moved = sum(1 for r in results if r[2])
        failed = sum(1 for r in results if not r[2])
        logger.info(f"Operation complete. Success: {moved}. Failed: {failed}.")

        logger.info("Cleaning up empty folders...")
        # Targeted cleanup walks only directories that lost files plus their
        # ancestors, instead of re-walking the entire working tree (P1).
        remove_empty_folders_targeted(working_dir, unique_folders, other_folder_name)
        logger.info("Cleanup complete.")
    return


if __name__ == "__main__":
    main()

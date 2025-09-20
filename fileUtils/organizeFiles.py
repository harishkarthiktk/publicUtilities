#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
organizeFiles.py

Usage examples:
  python organizeFiles.py -W /path/to/folder
  python organizeFiles.py -W /path/to/folder -V
  python organizeFiles.py -W /path/to/folder -P
"""

import argparse
import logging
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple
from tqdm import tqdm

# Configuration
MAX_RECURSION = 20
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
    p.add_argument("-W", "--working-dir", required=True, type=Path,
                   help="Target folder to scan and operate upon.")
    p.add_argument("-R", "--recursive", default="yes", choices=["yes", "no"],
                   help='Whether to recurse subfolders. Accepts "yes" or "no". Default: yes.')
    p.add_argument("-V", "--vid", action="store_true",
                   help="Move videos to root; other files into a Pic folder. (default if no mode is chosen)")
    p.add_argument("-P", "--pic", action="store_true",
                   help="Move images to root; other files into a Vid folder. Overrides --vid if both are present.")
    return p.parse_args()


def is_subpath(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except Exception:
        return False


def gather_files(root: Path, recursive: bool) -> List[Path]:
    files = []
    root = root.resolve()
    root_parts = len(root.parts)

    pic_folder = root / "Pic"
    vid_folder = root / "Vid"

    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath).resolve()
        depth = len(current.parts) - root_parts
        if depth > MAX_RECURSION:
            dirnames[:] = []
            continue
        if not recursive and current != root:
            dirnames[:] = []
            continue
        if is_subpath(current, pic_folder) and current != root:
            dirnames[:] = []
            continue
        if is_subpath(current, vid_folder) and current != root:
            dirnames[:] = []
            continue
        for fn in filenames:
            fp = current / fn
            if is_subpath(fp, pic_folder) or is_subpath(fp, vid_folder):
                continue
            files.append(fp)
    return files


def unique_dest_path(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_file(src: Path, dest_dir: Path) -> Tuple[Path, Path, bool, str]:
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        try:
            if src.resolve() == dest.resolve():
                return src, dest, True, "skipped (already at destination)"
        except Exception:
            pass
        dest = unique_dest_path(dest)
        shutil.move(str(src), str(dest))
        return src, dest, True, "moved"
    except Exception as e:
        return src, dest_dir, False, f"error: {e}"


def remove_empty_folders(root_path: Path):
    """
    Recursively scans and removes empty folders starting from the root_path.
    """
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        current_dir = Path(dirpath)
        # Exclude main Pic and Vid folders
        if current_dir.name in ["Pic", "Vid"] and current_dir.parent == root_path:
            continue
        if not any(current_dir.iterdir()):
            try:
                current_dir.rmdir()
                logger.info(f"Deleted empty folder: {current_dir}")
            except OSError as e:
                logger.error(f"Error removing folder {current_dir}: {e}")


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

    files = gather_files(working_dir, recursive)
    logger.info(f"Found {len(files)} files under {working_dir}")

    primary_files = [f for f in files if f.suffix.lower() in primary_exts]
    other_files = [f for f in files if f.suffix.lower() not in primary_exts]

    primary_dest_dir = working_dir
    other_dest_dir = working_dir / other_folder_name

    def needs_move(fp: Path, destination_dir: Path) -> bool:
        try:
            return fp.resolve().parent != destination_dir.resolve()
        except Exception:
            return True

    move_jobs = []
    for pf in primary_files:
        if needs_move(pf, primary_dest_dir):
            move_jobs.append((pf, primary_dest_dir))
    for of in other_files:
        if needs_move(of, other_dest_dir):
            move_jobs.append((of, other_dest_dir))

    total_jobs = len(move_jobs)
    if total_jobs == 0:
        logger.info("No files need moving. Exiting.")
    else:
        logger.info(f"Will operate on {total_jobs} files.")
        max_workers = min(32, (os.cpu_count() or 4) * 4)
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_to_job = {ex.submit(move_file, src, dest_dir): (src, dest_dir) for src, dest_dir in move_jobs}
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
    remove_empty_folders(working_dir)
    logger.info("Cleanup complete.")


if __name__ == "__main__":
    main()

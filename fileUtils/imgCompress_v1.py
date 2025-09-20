#!/usr/bin/env python3
"""
convert_to_jpeg.py

Scan directories for image files and convert them to JPEG (.jpeg) with `_cmp` suffix.
Optional:
  -A / --auto-correct : analyze & apply corrections from config.py
  -D / --delete-flag  : move originals to img2delete folder after successful conversion
  --replace           : delete originals outright (overridden by --delete-flag if both used)

Example:
  python convert_to_jpeg.py -W /path/to/folder -R 2 -Q 80 -A -D
"""

from __future__ import annotations
import argparse
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import List, Tuple
import sys, shutil

from PIL import Image, ImageEnhance, UnidentifiedImageError
from tqdm import tqdm

# Import thresholds
import config

# Optional deps
try:
    import cv2
except Exception:
    cv2 = None
import numpy as np

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("convert_to_jpeg")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".heic", ".heif"}


# --- Args ---
def yes_no_arg(value: str) -> bool:
    """Convert 'yes'/'no' strings to boolean."""
    val = value.lower()
    if val in ("yes", "y", "true", "1"):
        return True
    elif val in ("no", "n", "false", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Must be 'yes' or 'no'")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scan folders for images and convert to .jpeg with _cmp suffix.")
    p.add_argument("-W", "--working-dir", required=True, help="Folder location to scan.")
    p.add_argument("-R", "--recursive-depth", type=int, default=5,
                   help="Recursion depth: 0 = only given dir. Default=5.")
    p.add_argument("-Q", "--quality", type=int, default=80, help="JPEG quality (1-95). Default=80.")
    
    # Changed to accept yes/no, default=yes
    p.add_argument("-A", "--auto-correct", type=yes_no_arg, default=True,
                   help="Analyze and apply adaptive corrections before saving (yes/no). Default=yes.")
    p.add_argument("-D", "--delete-flag", type=yes_no_arg, default=True,
                   help="Move originals to img2delete/ folder after successful conversion (yes/no). Default=yes.")
    
    p.add_argument("--replace", action="store_true",
                   help="Delete original after successful conversion (ignored if --delete-flag is used).")
    p.add_argument("--no-overwrite", action="store_true", help="Skip if target exists.")
    p.add_argument("--workers", type=int, default=max(1, multiprocessing.cpu_count() - 1),
                   help="Number of worker processes. Default = cpu_count()-1.")
    return p.parse_args()


# --- Scan ---
def gather_image_files(root: Path, depth: int) -> List[Path]:
    if depth < 0:
        raise ValueError("depth must be >= 0")
    root = root.resolve()
    files: List[Path] = []
    root_parts = len(root.parts)

    iterator = root.rglob("*") if depth > 0 else root.iterdir()
    for p in iterator:
        p = Path(p)
        if not p.is_file():
            continue
        try:
            rel_parts = len(p.parent.resolve().parts) - root_parts
        except Exception:
            rel_parts = 0
        if rel_parts > depth:
            continue
        if p.name.lower().endswith("_cmp.jpeg"):
            continue
        if p.suffix.lower() in IMAGE_EXTS:
            files.append(p)
    return sorted(files)


# --- Auto Enhance ---
def _cap_factor(f: float) -> float:
    return max(config.SAFETY["min_enhance"], min(config.SAFETY["max_enhance"], float(f)))


def _compute_basic_stats(im: Image.Image):
    rgb = im.convert("RGB")
    arr = np.array(rgb)

    gray = np.asarray(rgb.convert("L"), dtype=np.float32)
    mean_brightness = float(np.mean(gray))
    stddev = float(np.std(gray))

    hsv = np.array(rgb.convert("HSV"))
    mean_saturation = float(np.mean(hsv[:, :, 1]))

    if cv2 is not None:
        try:
            gray_cv = np.uint8(gray)
            lap = cv2.Laplacian(gray_cv, cv2.CV_64F)
            sharpness_metric = float(np.var(lap))
        except Exception:
            sharpness_metric = float(np.var(np.abs(np.diff(gray, axis=0))) + np.var(np.abs(np.diff(gray, axis=1))))
    else:
        gy, gx = np.gradient(gray)
        gradmag = np.sqrt(gx ** 2 + gy ** 2)
        sharpness_metric = float(np.var(gradmag))

    return mean_brightness, stddev, mean_saturation, sharpness_metric


def auto_enhance_image(im: Image.Image) -> Image.Image:
    mean_brightness, stddev, mean_saturation, sharpness_metric = _compute_basic_stats(im)

    # Brightness
    bcfg = config.BRIGHTNESS
    if mean_brightness < bcfg["dark_thresh"]:
        brightness_factor = bcfg["dark_factor"]
    elif mean_brightness > bcfg["bright_thresh"]:
        brightness_factor = bcfg["bright_factor"]
    else:
        brightness_factor = bcfg["neutral_factor"]
    brightness_factor = _cap_factor(brightness_factor)

    # Contrast
    ccfg = config.CONTRAST
    if stddev < ccfg["low_thresh"]:
        contrast_factor = ccfg["low_factor"]
    elif stddev > ccfg["high_thresh"]:
        contrast_factor = ccfg["high_factor"]
    else:
        contrast_factor = ccfg["neutral_factor"]
    contrast_factor = _cap_factor(contrast_factor)

    # Color
    colcfg = config.COLOR
    if mean_saturation < colcfg["low_saturation_thresh"]:
        color_factor = colcfg["boost_factor"]
    else:
        color_factor = colcfg["neutral_factor"]
    color_factor = _cap_factor(color_factor)

    # Sharpness
    scfg = config.SHARPNESS
    if sharpness_metric < scfg["blur_thresh"]:
        sharpness_factor = scfg["boost_factor"]
    else:
        sharpness_factor = scfg["neutral_factor"]
    sharpness_factor = _cap_factor(sharpness_factor)

    # Apply
    if brightness_factor != 1.0:
        im = ImageEnhance.Brightness(im).enhance(brightness_factor)
    if contrast_factor != 1.0:
        im = ImageEnhance.Contrast(im).enhance(contrast_factor)
    if color_factor != 1.0:
        im = ImageEnhance.Color(im).enhance(color_factor)
    if sharpness_factor != 1.0:
        im = ImageEnhance.Sharpness(im).enhance(sharpness_factor)

    return im


# --- Conversion Worker ---
def convert_image_to_jpeg(
    src: str,
    quality: int,
    replace: bool,
    no_overwrite: bool,
    auto_correct: bool,
    delete_flag: bool,
    delete_dir: str | None,
) -> Tuple[str, bool, str]:
    src_path = Path(src)
    try:
        dst = src_path.with_name(src_path.stem + "_cmp.jpeg")

        if no_overwrite and dst.exists():
            return (str(src_path), False, f"Target exists and --no-overwrite used: {dst}")

        with Image.open(src_path) as im:
            if auto_correct:
                im = auto_enhance_image(im)

            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            if im.mode == "L":
                im = im.convert("RGB")

            im.save(dst, format="JPEG", quality=quality, optimize=True)

        # handle delete/move of originals
        if delete_flag:
            try:
                delete_dir_path = Path(delete_dir)
                delete_dir_path.mkdir(exist_ok=True)
                target = delete_dir_path / src_path.name
                shutil.move(str(src_path), str(target))
            except Exception as e:
                return (str(src_path), True,
                        f"Converted to {dst}, but failed to move original to img2delete: {e}")
        elif replace:
            try:
                if src_path.resolve() != dst.resolve():
                    src_path.unlink()
            except Exception as e:
                return (str(src_path), True, f"Converted to {dst}, but failed to delete original: {e}")

        return (str(src_path), True, f"Converted to {dst}")
    except UnidentifiedImageError:
        return (str(src_path), False, "UnidentifiedImageError: file not recognized as an image")
    except OSError as e:
        return (str(src_path), False, f"OSError while processing: {e}")
    except Exception as e:
        return (str(src_path), False, f"Unexpected error: {e}")


# --- Main ---
def main():
    args = parse_args()
    working_dir = Path(args.working_dir)
    if not working_dir.exists() or not working_dir.is_dir():
        logger.error("Invalid working directory: %s", working_dir)
        sys.exit(2)

    quality = int(args.quality)
    if not (1 <= quality <= 95):
        logger.error("Quality must be between 1 and 95. Got: %s", quality)
        sys.exit(2)

    logger.info("Scanning %s (depth=%d)...", working_dir, args.recursive_depth)
    files = gather_image_files(working_dir, args.recursive_depth)
    total = len(files)
    if total == 0:
        logger.info("No image files found.")
        return

    delete_dir = None
    if args.delete_flag:
        delete_dir = str(working_dir / "img2delete")

    logger.info("Found %d images. Quality=%d, Workers=%d, Auto-correct=%s, Delete-flag=%s",
                total, quality, args.workers, args.auto_correct, args.delete_flag)

    convert_fn = partial(
        convert_image_to_jpeg,
        quality=quality,
        replace=args.replace,
        no_overwrite=args.no_overwrite,
        auto_correct=args.auto_correct,
        delete_flag=args.delete_flag,
        delete_dir=delete_dir,
    )

    success_count = 0
    failure_count = 0

    try:
        with ProcessPoolExecutor(max_workers=args.workers) as exe:
            futures = {exe.submit(convert_fn, str(fp)): fp for fp in files}
            with tqdm(total=total, desc="Converting", unit="file") as pbar:
                for fut in as_completed(futures):
                    src_fp = futures[fut]
                    try:
                        src, success, message = fut.result()
                    except Exception as e:
                        logger.exception("Worker error for %s: %s", src_fp, e)
                        success, message = False, f"Worker exception: {e}"

                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                    logger.debug("%s", message)
                    pbar.update(1)
    except KeyboardInterrupt:
        logger.error("Interrupted by user.")
        sys.exit(1)

    logger.info("Done. Success=%d, Failures=%d, Total=%d", success_count, failure_count, total)


if __name__ == "__main__":
    main()

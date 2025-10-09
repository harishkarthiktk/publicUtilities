# AGENTS.md

This file provides guidance to agents when working with code in this repository.

- The project uses a Python script (`organizeFiles.py`) for organizing files into "Vid" and "Pic" folders based on extensions.
- The script enforces a maximum directory recursion depth of 20 to prevent deep traversal.
- It distinguishes video and image files using specific extension sets (`.mp4`, `.mkv`, `.avi`, etc. for videos; `.jpg`, `.png`, `.gif`, etc. for images).
- Files are moved into "Vid" or "Pic" folders depending on the mode (`-V` for videos, `-P` for pictures). If no mode is specified, defaults to "vid".
- The script skips moving files already in the correct destination.
- Filename conflicts are resolved by appending an incremental counter (`_1`, `_2`, etc.).
- After moving files, it cleans up empty folders, excluding the main "Vid" and "Pic" folders.
- Logging is set up to report errors and info, with info messages printed to stdout and errors to stderr.
- Command-line arguments include:
  - `-W` or `--working-dir`: target directory (required)
  - `-R` or `--recursive`: whether to recurse (default "yes")
  - `-V` or `--vid`: mode for videos
  - `-P` or `--pic`: mode for images (overrides `-V`)
- The script is designed for safe operation, avoiding overwriting files and cleaning up empty directories.

No custom build, lint, or test commands are defined in this script. Standard Python environment setup and dependencies (like `tqdm`) are used.

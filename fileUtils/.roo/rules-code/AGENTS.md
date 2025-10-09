# Code Mode Rules (Non-Obvious Only)
- Always respect the MAX_RECURSION limit of 20 to prevent deep directory traversal.
- Use the `unique_dest_path()` function to avoid filename conflicts by appending counters.
- When moving files, skip if the source is already at the destination to prevent unnecessary operations.
- The script cleans up empty folders, excluding the main "Pic" and "Vid" folders, to maintain directory hygiene.
- The script distinguishes between video and image files using specific extension sets, which must be kept updated if new formats are added.
- Logging levels: INFO for operational messages, ERROR for issues; ensure logs are monitored for silent failures.
- The script defaults to "vid" mode if no mode is specified, but "pic" mode overrides it.
- Use `shutil.move()` for file operations to ensure atomic moves.
- Recursion is controlled via the `-R` argument, with "yes" or "no" options.
# Debug Mode Rules (Non-Obvious Only)
- The script uses `logging` with INFO and ERROR levels; ensure logs are monitored for silent failures.
- Debugging issues related to file conflicts should focus on the `unique_dest_path()` function to understand filename resolution.
- The cleanup process skips the main "Pic" and "Vid" folders; verify these are correctly identified to avoid accidental deletions.
- The script's operation depends on correct argument parsing; validate command-line inputs if issues arise.
- The maximum recursion depth (`MAX_RECURSION=20`) is critical; exceeding it may cause incomplete traversal.
- Use `ThreadPoolExecutor` with a max of 32 workers; monitor for thread-related issues or resource exhaustion.
- The script logs errors during folder removal; check logs for silent failures in cleanup.
- The script relies on `shutil.move()`; ensure source files are accessible and not locked by other processes.
- The script skips moving files already in the correct folder; verify source and destination paths resolve correctly.
# Modular Summarization Tool

This project refactors the original `summarize_Tool.py` into smaller, reusable modules for better maintainability and extensibility. The system processes Markdown files using LLMs (Ollama or OpenRouter) for summarization or analysis.

## Structure
- **llm_client.py**: Handles LLM API calls (Ollama/OpenRouter), prompt building, and configuration. Reusable for any LLM integration in chatbots, generators, or AI pipelines.
- **file_utils.py**: Manages file scanning, validation, and JSON state tracking for resumable processing. Useful for batch file operations in document tools.
- **processor.py**: Core logic for single-file and batch processing with threading and progress bars. Generalizable for tasks like analysis or extraction.
- **summarize_Tool.py**: Main CLI entry point, orchestrating arguments and workflow. (Original script refactored; use `python summarize_Tool.py` for execution.)

Dependencies: See `requirements.txt` (python-dotenv, requests, tqdm).

## Usage
The CLI supports processing single .md files or entire folders of .md files. Use `--input-file` (-i) for a single file or `--folder-input` (-f) for a directory. If a directory is provided to `--input-file`, the script automatically falls back to folder mode for convenience.

Run the CLI:
```
python summarize_Tool.py -f /path/to/input/folder -o /path/to/output --api openrouter --api-key YOUR_KEY --persona summarizer
```

Key arguments:
- `--input-file` (-i): Path to a single .md file. If a directory is provided, it automatically processes all .md files in it (fallback to folder mode).
- `--folder-input` (-f): Path to input folder containing .md files (non-recursive, top-level only).
- `--output-folder` (-o): Where to save processed summaries (.md files) and `processedFiles.json` (tracks progress for resuming).
- `--persona`: "summarizer" (default) or "analyzer".
- `--api`: "ollama" (local) or "openrouter" (cloud; requires `--api-key` or OPENROUTER_API_KEY env var).
- `--instructions`: Optional custom instructions for the LLM task.
- `--model`: Optional model override (defaults from config).
- Supports resuming interrupted runs via `processedFiles.json` in output folder.

Example for single file:
```
python summarize_Tool.py -i example.md -o ./summaries --api ollama
```

Example for folder (or fallback from -i):
```
python summarize_Tool.py -i /path/to/input_sample -o ./summaries --api openrouter --api-key YOUR_KEY
```
This will detect the directory and process all .md files inside.

If issues arise (e.g., invalid path), check `log.txt` in output for details.

## Reusability
- **LLM Client**: Import `call_llm_api` and `build_prompt` for custom LLM interactions (e.g., integrate into web apps or scripts).
- **File Utils**: Use `scan_and_populate_processed` for tracking processed files in ETL pipelines or data processors.
- **Processor**: Extend `process_single_file` for non-Markdown formats or different tasks (e.g., PDF summarization by adding loaders).
- **State Management**: JSON metadata for logging failures, scans, and runs – adaptable to any long-running CLI tool.

Benefits: Modular design allows unit testing (e.g., mock API calls), easy extension (add personas/APIs), and reuse in projects like document analyzers or content generators.

For architecture and implementation plan, see `plan.md`.
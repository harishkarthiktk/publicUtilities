# Markdown to DOCX Converter

## Overview

This enhanced script converts Markdown files to DOCX format using Pandoc, supporting comprehensive Markdown extensions, custom styling, batch processing, and validation features. It addresses all the issues from the original critique, providing a robust, testable, and user-friendly tool for document conversion.

## Features

- **Single and Batch Conversion**: Convert individual files or multiple files/directories using glob patterns or recursive search.
- **Custom Styling**: Override fonts, sizes, and heading styles via CLI flags, environment variables, or JSON/YAML config files.
- **Template Support**: Use custom DOCX templates with validation to ensure required styles are present.
- **Progress Indication**: Visual progress bar (with tqdm) or timed logging for conversions, with file size display and ETA.
- **Error Handling**: Specific exception handling with actionable messages and error codes.
- **Testability**: Abstract interfaces for file I/O and Pandoc operations with dependency injection for unit testing.
- **Compatibility Checks**: Verify Python version (>=3.7) and Pandoc version (>=2.0 recommended).
- **Logging**: Standardized logging levels (DEBUG for details, INFO for progress, WARNING for recoverable issues, ERROR for failures).

## Supported Markdown Features

- Headers, lists (ordered/unordered with bullets/numbers via styled template), blockquotes, task lists
- Tables (pipe, grid, multiline), fenced code blocks with syntax highlighting and attributes
- Images (with alt text and implicit figures), links, emphasis (bold, italic, strikethrough)
- Footnotes, citations, definition lists, abbreviations
- Math (LaTeX via $ delimiters), raw HTML/Tex, smart punctuation
- Header attributes, link attributes, table captions, native divs/spans
- And more via comprehensive Pandoc Markdown extensions (see [`Config.pandoc_extensions`](convert_to_docx.py:175) for full list)

## Installation

1. **Python 3.7+**: Required for dataclasses and type hints.
2. **Dependencies**:
   ```
   pip install pypandoc python-docx tqdm pyyaml
   ```
3. **Pandoc**: Download and install from [pandoc.org](https://pandoc.org/installing.html). Ensure it's in your PATH.
4. **Optional**: PyYAML for YAML config support (included in dependencies).

## Usage

### Basic Single File Conversion
```
python convert_to_docx.py input.md -o output.docx
```

### Batch Processing
Convert all Markdown files in a directory recursively:
```
python convert_to_docx.py ./docs/**/*.md --output-dir ./output --recursive
```

### Custom Styling
Use CLI flags for overrides:
```
python convert_to_docx.py document.md --font "Times New Roman" --body-size 12 --list-size 11
```

### Using Config File
Create `config.json`:
```json
{
  "default_font": "Times New Roman",
  "body_size": 12,
  "list_font": "Times New Roman",
  "list_size": 11,
  "heading_sizes": {
    "1": 28,
    "2": 22,
    "3": 18,
    "4": 14,
    "5": 12,
    "6": 10
  }
}
```
Then:
```
python convert_to_docx.py input.md --config config.json
```

YAML config (`config.yaml`):
```yaml
default_font: Times New Roman
body_size: 12
heading_sizes:
  1: 28
  2: 22
```

### Template Management
Use a custom template:
```
python convert_to_docx.py input.md --template custom_template.docx
```

Validate template:
```
python convert_to_docx.py --template custom_template.docx --validate-template
```

### Progress and Quiet Mode
With progress bar:
```
python convert_to_docx.py large_file.md --verbose
```

Suppress output:
```
python convert_to_docx.py input.md --quiet
```

### Compatibility Check
Verify setup without conversion:
```
python convert_to_docx.py --check
```

### Batch with Overrides
```
python convert_to_docx.py *.md --output-dir ./output --font Arial --extensions "footnotes,task_lists" --force
```

## Command-Line Options

- `input_files`: Markdown file(s) or glob patterns (e.g., `*.md` or `./docs/**/*.md` with `--recursive`).
- `-o, --output-dir`: Output directory for batch (required for multiple files).
- `-v, --verbose`: Enable detailed logging (DEBUG level).
- `-t, --template`: Path to custom DOCX template.
- `--no-template`: Use Pandoc defaults instead of template.
- `--extensions`: Custom Pandoc extensions (e.g., `--extensions "footnotes+task_lists"` or `--extensions footnotes,task_lists`).
- `--force, -f`: Overwrite existing output files.
- `--quiet, -q`: Suppress progress and success messages.
- `--recursive, -r`: Recursively search directories for `.md` files.
- `--config`: Path to JSON or YAML config file.
- `--font`: Default font name (CLI override).
- `--body-size`: Body font size in points.
- `--list-font`: List font name.
- `--list-size`: List font size in points.
- `--heading-sizes`: Heading sizes as "1:28,2:22,3:18,4:14,5:12,6:10".
- `--validate-template`: Validate template styles without conversion.
- `--check`: Check Python/Pandoc compatibility without conversion.
- `--version`: Show version.

## Configuration

### Environment Variables
Override defaults:
```
export DEFAULT_FONT="Times New Roman"
export BODY_SIZE=12
export HEADING_SIZES="1:28,2:22,3:18"
python convert_to_docx.py input.md
```

### Config File Structure
**JSON (`config.json`)**:
```json
{
  "default_font": "Arial",
  "body_size": 11,
  "list_font": "Arial",
  "list_size": 11,
  "heading_sizes": {
    "1": 24,
    "2": 18,
    "3": 14,
    "4": 12,
    "5": 10,
    "6": 9
  }
}
```

**YAML (`config.yaml`)**:
```yaml
default_font: Arial
body_size: 11
list_font: Arial
list_size: 11
heading_sizes:
  1: 24
  2: 18
  3: 14
  4: 12
  5: 10
  6: 9
```

## Template Requirements

Custom templates must include these styles for optimal results:
- Normal
- Heading 1-6
- List Bullet
- List Number

Use `--validate-template` to check.

## Logging Levels

- **DEBUG**: Internal details (use `--verbose`).
- **INFO**: Progress and success (default).
- **WARNING**: Recoverable issues (e.g., missing optional deps).
- **ERROR**: Failures with codes (E001-E003).

## Examples

### Single File with Custom Font
```
python convert_to_docx.py notes.md --font "Calibri" --body-size 11 --output notes.docx
```

### Batch Conversion with Template
```
python convert_to_docx.py ./src/*.md --output-dir ./dist --template styles.docx --recursive
```

### Validate Setup
```
python convert_to_docx.py --check
```

### Quiet Batch
```
python convert_to_docx.py ./docs --output-dir ./output --quiet --recursive
```

## Troubleshooting

- **Pandoc not found**: Ensure Pandoc is installed and in PATH. Run `pandoc --version`.
- **Large files**: Files >10MB are rejected for performance.
- **Template errors**: Use `--validate-template` to check styles.
- **YAML not working**: Install PyYAML: `pip install pyyaml`.
- **No progress bar**: Install tqdm: `pip install tqdm`.

## Limitations

- Progress bar is simulated (Pandoc doesn't support native progress).
- Multiprocessing works on Unix; Windows may require `if __name__ == '__main__':` adjustments.
- Template inheritance not supported; ensure all styles are defined.

## Contributing

See CONTRIBUTING.md for details.

---
Generated from the enhanced convert_to_docx.py script.
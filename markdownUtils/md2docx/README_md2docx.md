# Markdown to DOCX Converter

A generic, reusable command-line tool that converts markdown files to Microsoft Word documents with configurable styling.

## Requirements

- Python 3.7+
- Dependencies: `python-docx`, `markdown`, `pyyaml`

Install dependencies:
```bash
pip install python-docx markdown pyyaml
```

## Usage

### Basic Usage
```bash
python md2docx.py input.md output.docx
```

### With Custom Config
```bash
python md2docx.py input.md output.docx --config custom-config.yaml
```

## Configuration

Styling is managed through `config.yaml`. Key options:

- **document.font_family**: Font for entire document (default: Calibri)
- **document.line_spacing**: Line spacing (1.0, 1.5, 2.0)
- **headings.h1-h6.size**: Font size for each heading level
- **headings.h1-h6.bold**: Whether headings are bold
- **body.font_size**: Body text font size
- **body.paragraph_spacing_after**: Space after paragraphs
- **lists.indent_size**: List indentation in inches
- **lists.spacing_after**: Space after list items

### Customizing
1. Copy `config.yaml` to create your own config file
2. Modify styling options as needed
3. Pass it to the converter: `python md2docx.py input.md output.docx --config myconfig.yaml`

## Supported Markdown Elements

- Headings (H1 through H6)
- Paragraphs
- Bold text (`**text**` or `__text__`)
- Italic text (`*text*` or `_text_`)
- Unordered lists (`-`, `*`, `+`)
- Ordered lists (`1.`, `2.`, etc.)
- Links (rendered as plain text)

## Portability

This tool is self-contained and portable:
- Copy `md2docx.py` and `config.yaml` to any project
- Use as-is or customize styling via config file
- No external dependencies beyond the Python packages listed above

## Example

```bash
# Convert with default styling
python md2docx.py document.md document.docx

# Convert with custom styling
python md2docx.py document.md document.docx --config my-style.yaml
```

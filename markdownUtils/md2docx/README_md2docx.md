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

- **document.font_family**: Font for entire document (default: Times New Roman)
- **document.line_spacing**: Line spacing (1.0, 1.5, 2.0)
- **headings.h1-h6.size**: Font size for each heading level
- **headings.h1-h6.bold**: Whether headings are bold
- **body.font_size**: Body text font size
- **body.paragraph_spacing_after**: Space after paragraphs
- **lists.indent_size**: List indentation in inches
- **code.font_family**: Code block font (default: Courier New)
- **code.font_size**: Code block font size
- **code.background_color**: Code block background hex color
- **blockquote.indent**: Blockquote indentation in inches
- **blockquote.italic**: Whether blockquotes are italic
- **links.show_url**: Show URL after link text (true/false)
- **highlight.bold**: Whether ==highlights== render as bold

### Customizing
1. Copy `config.yaml` to create your own config file
2. Modify styling options as needed
3. Pass it to the converter: `python md2docx.py input.md output.docx --config myconfig.yaml`

## Supported Markdown Elements

- Headings (H1 through H6)
- Paragraphs with proper inline formatting
- **Bold** and *italic* text (correctly applied per-span)
- ~~Strikethrough~~ text
- `Inline code`
- Fenced code blocks (monospace with gray background)
- Unordered lists (`-`, `*`, `+`) with nesting
- Ordered lists (`1.`, `2.`, etc.) with nesting
- Tables (pipe tables)
- Blockquotes
- Horizontal rules
- Links (configurable: text only or text with URL)
- Definition lists
- Footnotes
- Obsidian ==highlight== syntax
- YAML frontmatter mapped to DOCX metadata (title, author, date, subject, keywords/tags)
- Smart quotes and abbreviations

### Not Supported

- Images (logged as warnings, skipped)
- Math expressions (TeX)
- Task lists

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

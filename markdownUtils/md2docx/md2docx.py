#!/usr/bin/env python
"""
Generic Markdown to DOCX Converter

Converts markdown files to Microsoft Word documents with configurable styling.
Styling can be customized via a YAML configuration file.

Usage:
    python md2docx.py input.md output.docx [--config config.yaml]

Feature Parity Note (vs convert_to_docx.py):
============================================
CURRENTLY SUPPORTED (md2docx):
- Headings (H1-H6)
- Paragraphs
- Bold/italic text
- Unordered/ordered lists (basic)
- Links (plain text only)

MISSING FEATURES (available in convert_to_docx.py):
- Tables (grid, pipe tables)
- Citations & footnotes
- Task lists (- [ ])
- Code blocks with syntax highlighting
- Math expressions (TeX)
- Definition lists
- Subscript/superscript
- Strikethrough
- Reference DOCX templates
- Progress bars, verbose/quiet modes
- File validation & size limits
- Batch processing
- Template validation mode

Implementation Plan for Feature Parity:
=======================================
Phase 1 (Quick wins):
1. Add strikethrough, subscript, superscript support
   - Update MarkdownHTMLParser to handle <del>, <sub>, <sup> tags
   - Extend formatting logic in add_text_with_formatting()

Phase 2 (Code & Tables):
2. Code blocks with syntax highlighting
   - Parse <pre><code> blocks
   - Apply monospace font styling
3. Table support
   - Add table parsing from HTML
   - Create docx tables with proper cell formatting

Phase 3 (Lists & Structure):
4. Task lists (- [ ])
   - Detect checkbox syntax in markdown
   - Render as unicode checkmarks
5. Nested lists
   - Track indentation level in list_stack
   - Apply proper indentation per level

Phase 4 (Advanced):
6. Footnotes
   - Parse footnote references
   - Add footnotes section at document end
7. Template support
   - Allow loading reference DOCX files
   - Copy styles from template

Phase 5 (CLI Enhancements):
8. Add progress bar, verbose mode
9. File validation (size limits, extensions)
10. Batch processing support

Architecture Decision:
======================
This module uses pure Python (markdown + python-docx) for portability.
Alternative: Could wrap Pandoc like convert_to_docx.py, but that adds
dependency on external Pandoc binary installation.
"""

import sys
import argparse
import os
from pathlib import Path
from html.parser import HTMLParser
import yaml
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import markdown


class MarkdownHTMLParser(HTMLParser):
    """Parses HTML from markdown and extracts structured elements."""

    def __init__(self):
        super().__init__()
        self.elements = []
        self.current_element = None
        self.current_text = []
        self.list_stack = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.current_element = {"type": tag, "text": "", "formatting": []}
        elif tag == "p":
            self.current_element = {"type": "p", "text": "", "formatting": []}
        elif tag == "ul":
            self.list_stack.append("ul")
        elif tag == "ol":
            self.list_stack.append("ol")
        elif tag == "li":
            list_type = self.list_stack[-1] if self.list_stack else "ul"
            self.current_element = {
                "type": "li",
                "list_type": list_type,
                "text": "",
                "formatting": [],
            }
        elif tag == "strong" or tag == "b":
            if self.current_element is not None:
                self.current_element["formatting"].append(("bold", True))
        elif tag == "em" or tag == "i":
            if self.current_element is not None:
                self.current_element["formatting"].append(("italic", True))
        elif tag == "a":
            # Extract href but render as plain text
            pass

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "li"):
            if self.current_element is not None:
                self.current_element["text"] = "".join(self.current_text).strip()
                self.current_text = []
                if self.current_element["text"]:
                    self.elements.append(self.current_element)
                self.current_element = None
        elif tag == "ul" or tag == "ol":
            if self.list_stack:
                self.list_stack.pop()

    def handle_data(self, data):
        text = data.strip()
        if text and self.current_element is not None:
            self.current_text.append(text)

    def get_elements(self):
        return self.elements


class MarkdownToDocx:
    """Converts markdown to DOCX with configurable styling."""

    def __init__(self, config):
        """Initialize converter with styling configuration."""
        self.config = config
        self.doc = None

    def load_markdown(self, md_text):
        """Parse markdown text and return structured elements."""
        html = markdown.markdown(md_text)
        parser = MarkdownHTMLParser()
        parser.feed(html)
        return parser.get_elements()

    def apply_heading_style(self, paragraph, level, config):
        """Apply heading style to paragraph."""
        heading_key = f"h{level}"
        if heading_key in config.get("headings", {}):
            heading_config = config["headings"][heading_key]
            run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
            run.font.size = Pt(heading_config.get("size", 12))
            if heading_config.get("bold", False):
                run.bold = True
        paragraph.style = f"Heading {level}"

    def apply_body_style(self, paragraph, config):
        """Apply body text style to paragraph."""
        body_config = config.get("body", {})
        font_size = body_config.get("font_size", 11)
        for run in paragraph.runs:
            run.font.size = Pt(font_size)
        if "paragraph_spacing_after" in body_config:
            paragraph.paragraph_format.space_after = Pt(
                body_config["paragraph_spacing_after"]
            )

    def add_text_with_formatting(self, paragraph, text, formatting):
        """Add text to paragraph with formatting."""
        if not formatting:
            run = paragraph.add_run(text)
            return

        # Simple implementation: apply all formatting to entire text
        run = paragraph.add_run(text)
        for fmt_type, fmt_value in formatting:
            if fmt_type == "bold":
                run.bold = fmt_value
            elif fmt_type == "italic":
                run.italic = fmt_value

    def convert(self, md_text, config):
        """Convert markdown text to DOCX document."""
        self.doc = Document()

        # Set document font
        doc_font = config.get("document", {}).get("font_family", "Calibri")
        elements = self.load_markdown(md_text)

        for element in elements:
            if element["type"].startswith("h"):
                level = int(element["type"][1])
                paragraph = self.doc.add_paragraph(element["text"])
                self.apply_heading_style(paragraph, level, config)
            elif element["type"] == "p":
                paragraph = self.doc.add_paragraph(element["text"])
                self.apply_body_style(paragraph, config)
            elif element["type"] == "li":
                list_type = element.get("list_type", "ul")
                # Get indent level (simplified - assume top level)
                level = 0
                paragraph = self.doc.add_paragraph(
                    element["text"],
                    style=f"List {'Number' if list_type == 'ol' else 'Bullet'}",
                )
                self.apply_body_style(paragraph, config)

        return self.doc

    def save(self, output_path):
        """Save DOCX document to file."""
        if self.doc is None:
            raise ValueError("No document to save. Convert markdown first.")
        self.doc.save(output_path)


def load_config(config_path=None):
    """Load styling configuration from YAML file."""
    if config_path is None:
        config_path = "config.yaml"

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown files to DOCX format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python md2docx.py input.md output.docx
  python md2docx.py input.md output.docx --config custom-config.yaml
        """,
    )

    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("output", help="Output DOCX file")
    parser.add_argument(
        "--config", default="config.yaml", help="Config file (default: config.yaml)"
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        # Load configuration
        config = load_config(args.config)

        # Read markdown file
        with open(args.input, "r", encoding="utf-8") as f:
            md_text = f.read()

        # Convert to DOCX
        converter = MarkdownToDocx(config)
        doc = converter.convert(md_text, config)
        converter.save(args.output)

        print(f"✓ Successfully converted {args.input} to {args.output}")
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

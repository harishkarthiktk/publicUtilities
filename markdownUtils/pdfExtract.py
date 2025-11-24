#!/usr/bin/env python3
"""
PDF Text Extractor to Markdown
Extracts text from PDF files (single or batch from directory, optionally recursive up to 3 levels) and converts to Markdown format with page separators.
Supports dry-run simulation and defaults output to source location if no output directory specified.
"""

import sys
import re
import argparse
from pathlib import Path
from typing import Optional, Generator
import logging
import os

logger = logging.getLogger(__name__)

try:
    import pypdf
    from tqdm import tqdm
except ImportError as e:
    logging.error(f"Error importing required libraries (pypdf or tqdm): {e}")
    logging.error("Install them with: pip install pypdf tqdm")
    sys.exit(1)





def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text as string

    Raises:
        pypdf.errors.PdfReadError: If the PDF file is corrupted or invalid.
        OSError: If there is an issue opening or reading the file.
    """
    text_content = []

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            total_pages = len(pdf_reader.pages)

            logger.info(f"Processing {total_pages} pages from {pdf_path.name}...")

            for page_num, page in enumerate(pdf_reader.pages, 1):
                logger.info(f"Extracting page {page_num}/{total_pages}")
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"## Page {page_num}\n\n{text}\n")

    except (pypdf.errors.PdfReadError, OSError) as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        sys.exit(1)

    return "\n".join(text_content)


def clean_text(text: str) -> str:
    """
    Clean and format extracted text for better Markdown output.

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    lines = []
    previous_empty = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
            previous_empty = False
        else:
            if not previous_empty:
                lines.append('')
                previous_empty = True
    # Remove trailing empty lines
    while lines and not lines[-1]:
        lines.pop()
    return '\n'.join(lines) + '\n' if lines else ''




def validate_pdf_path(pdf_path: Path) -> None:
    """
    Validate that the given path is an existing PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Raises:
        ValueError: If the file does not exist or is not a PDF file.
    """
    if not pdf_path.exists():
        raise ValueError(f"PDF file does not exist: {pdf_path}")
    if pdf_path.suffix.lower() != '.pdf':
        raise ValueError(f"Not a PDF file: {pdf_path}")


def generate_markdown_header(pdf_path: Path, text: str) -> str:
    """
    Generate the Markdown header and combine with text content.

    Args:
        pdf_path: Path to the original PDF file.
        text: Cleaned extracted text.

    Returns:
        Complete Markdown content string.
    """
    return f"""# {pdf_path.stem}

*Converted from PDF: {pdf_path.name}*

---

{text}
"""


def write_to_markdown(output_path: Path, content: str) -> None:
    """
    Write the Markdown content to the specified output path.

    Args:
        output_path: Path for the output Markdown file.
        content: The Markdown content to write.

    Raises:
        OSError: If there is an error writing the file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully extracted to {output_path}")
    except OSError as e:
        logger.error(f"Error writing output file {output_path}: {e}")
        sys.exit(1)


def process_pdf(pdf_path: Path, dry_run: bool = False, use_source_output: bool = False, output_dir: Optional[Path] = None) -> None:
    """
    Process a single PDF file and write Markdown output.

    Args:
        pdf_path: Path to the input PDF file
        dry_run: If True, simulate without extracting or writing
        use_source_output: If True and no output_dir, use PDF's parent dir for output
        output_dir: Directory to write the output .md file (if not using source)

    Raises:
        ValueError: If the input is not a valid PDF file (from validation).
        pypdf.errors.PdfReadError: If PDF extraction fails.
        OSError: If output writing fails.
    """
    validate_pdf_path(pdf_path)

    if dry_run:
        if use_source_output and output_dir is None:
            out_path = pdf_path.parent / f"{pdf_path.stem}.md"
        else:
            out_path = output_dir / f"{pdf_path.stem}.md"
        logger.info(f"Would extract from {pdf_path} to {out_path}")
        return

    text = extract_text_from_pdf(pdf_path)
    cleaned_text = clean_text(text)

    if use_source_output and output_dir is None:
        output_path = pdf_path.parent / f"{pdf_path.stem}.md"
    else:
        output_path = output_dir / f"{pdf_path.stem}.md"
    content = generate_markdown_header(pdf_path, cleaned_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_to_markdown(output_path, content)


def find_pdfs(path: Path, max_depth: int = 3) -> Generator[Path, None, None]:
    """
    Recursively find PDF files up to max_depth levels.

    Args:
        path: Starting directory path
        max_depth: Maximum recursion depth

    Yields:
        Path objects of PDF files found
    """
    depth = 0
    for root, dirs, files in os.walk(path):
        rel_path = path.resolve().relative_to(root.resolve()) if path.resolve() != root.resolve() else Path('.')
        current_depth = len(rel_path.parts) if rel_path != Path('.') else 0
        if current_depth > max_depth:
            dirs[:] = []  # Prune deeper directories
            continue
        for file in files:
            if file.lower().endswith('.pdf'):
                yield Path(root) / file


def process_directory(input_path: Path, recursive: bool = False, dry_run: bool = False, use_source_output: bool = False, output_dir: Optional[Path] = None) -> None:
    """
    Process all PDF files in a directory, optionally recursively up to 3 levels.

    Args:
        input_path: Path to the input directory
        recursive: If True, search subdirectories up to depth 3
        dry_run: If True, simulate without extracting or writing
        use_source_output: If True and no output_dir, use each PDF's parent dir for output
        output_dir: Directory to write the output .md files (if not using source)

    Raises:
        ValueError: If no PDF files are found in the directory.
    """
    if not recursive:
        pdf_files = [f for f in input_path.iterdir() if f.suffix.lower() == '.pdf']
    else:
        pdf_files = list(find_pdfs(input_path))

    if not pdf_files:
        raise ValueError(f"No PDF files found in {input_path}")

    logger.info(f"Found {len(pdf_files)} PDF files in {input_path}")

    if not use_source_output and output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        process_pdf(pdf_file, dry_run=dry_run, use_source_output=use_source_output, output_dir=output_dir if not use_source_output else None)




def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argparse parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description='Extract text from PDF files to Markdown format.',
        epilog="""
Examples:
  python pdfExtract.py -i document.pdf
  python pdfExtract.py -i /path/to/document.pdf -o /output/dir
  python pdfExtract.py -i /path/to/pdfs -o /output/dir
  python pdfExtract.py -i /path/to/dir -r
  python pdfExtract.py -i /path/to/dir -r -o /output/dir --dry-run
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Path to input PDF file or directory containing PDFs'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output directory for .md files (default: same directory as input)'
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Process PDFs recursively up to 3 levels deep'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate extraction without writing files'
    )

    return parser




def main() -> None:
    """
    Main entry point for the script.

    Handles argument parsing, validation, and dispatches to processing functions.

    Raises:
        SystemExit: On argument errors or processing failures.
    """
    logging.basicConfig(level=logging.INFO)
    global logger
    logger = logging.getLogger(__name__)
    parser = create_parser()
    args = parser.parse_args()

    recursive = args.recursive
    dry_run = args.dry_run

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Input path not found: {input_path}")

    use_source_output = not bool(args.output)
    if not use_source_output:
        output_dir = Path(args.output)
    else:
        output_dir = None

    try:
        if input_path.is_file():
            process_pdf(input_path, dry_run=dry_run, use_source_output=use_source_output, output_dir=output_dir)
        elif input_path.is_dir():
            process_directory(input_path, recursive=recursive, dry_run=dry_run, use_source_output=use_source_output, output_dir=output_dir)
        else:
            parser.error("Input must be a file or directory")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
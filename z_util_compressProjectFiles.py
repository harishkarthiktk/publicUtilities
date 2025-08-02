import re
import argparse
from pathlib import Path

# Configuration
INCLUSION_EXTENSIONS = {"py", "js", "html", "md", "jinja2", "css"}
EXCLUDED_FILES = {"z_allFiles.ignore", "z_util_compressProjectFiles.py"}
EXCLUDED_DIRS = {"env", ".env", "venv", ".venv", ".git", "__pycache__", ".idea", ".vscode"}
OUTPUT_FILE = "z_allFiles.txt"

def should_process_file(file_path: Path) -> bool:
    """Check if a file should be included based on its extension and directory path."""
    if file_path.name in EXCLUDED_FILES:
        return False
    if file_path.suffix[1:] not in INCLUSION_EXTENSIONS:
        return False
    if any(part in EXCLUDED_DIRS or part.startswith('.') for part in file_path.parts):
        return False
    return True

def strip_comments_and_blank_lines(content: str, ext: str) -> str:
    """Strip comments and blank lines for each file type."""
    lines = content.splitlines()
    if ext == 'py':
        lines = [line for line in lines if not line.strip().startswith('#')]
    elif ext == 'js':
        lines = [re.sub(r'//.*', '', line) for line in lines if not line.strip().startswith('//')]
    elif ext in {'html', 'jinja2'}:
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        lines = content.splitlines()
    elif ext == 'css':
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        lines = content.splitlines()
    elif ext == 'md':
        lines = [line for line in lines if not line.strip().startswith('<!--')]
    return '\n'.join(line for line in lines if line.strip())

def generate_project_structure(root: Path) -> str:
    """Generate a tree-style project structure, excluding unwanted dirs."""
    structure_lines = []
    def walk(dir_path: Path, prefix=""):
        entries = sorted([
            p for p in dir_path.iterdir()
            if not p.name.startswith('.') and
            p.name not in EXCLUDED_DIRS
        ])
        for idx, entry in enumerate(entries):
            connector = "└── " if idx == len(entries) - 1 else "├── "
            structure_lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                walk(entry, prefix + ("    " if idx == len(entries) - 1 else "│   "))

    structure_lines.append("## PROJECT STRUCTURE")
    walk(root)
    return '\n'.join(structure_lines)

def get_files_to_process(root: Path, specific_files=None):
    """Get list of files to process based on whether specific files are provided."""
    if specific_files:
        # When -f flag is used, only process the specified files
        files_to_process = []
        for file_name in specific_files:
            file_path = Path(file_name)
            # Handle both absolute and relative paths
            if file_path.is_absolute():
                if file_path.exists() and file_path.is_file():
                    files_to_process.append(file_path)
                else:
                    print(f"Warning: File not found: {file_path}")
            else:
                # Try relative to current directory
                full_path = root / file_path
                if full_path.exists() and full_path.is_file():
                    files_to_process.append(full_path)
                else:
                    print(f"Warning: File not found: {full_path}")
        return files_to_process
    else:
        # Original logic: use inclusion/exclusion rules
        return [
            file_path for file_path in root.rglob('*')
            if file_path.is_file() and should_process_file(file_path)
        ]

def main():
    parser = argparse.ArgumentParser(description='Consolidate project files into a single output file.')
    parser.add_argument('-f', '--files', nargs='+',
                       help='Specific files to process (bypasses inclusion/exclusion rules)')

    args = parser.parse_args()

    root = Path.cwd()
    output_path = Path(OUTPUT_FILE)

    # Write the project structure
    output_path.write_text(generate_project_structure(root) + '\n\n', encoding='utf-8')

    # Get files to process based on whether -f flag is used
    files_to_process = get_files_to_process(root, args.files)

    # Process and append files
    with output_path.open('a', encoding='utf-8') as wfile:
        for file_path in files_to_process:
            try:
                ext = file_path.suffix[1:] if file_path.suffix else ''
                raw_content = file_path.read_text(encoding='utf-8')
                processed = strip_comments_and_blank_lines(raw_content, ext)
                if processed.strip():
                    wfile.write(f"\n## {file_path.relative_to(root) if file_path.is_relative_to(root) else file_path}\n")
                    wfile.write(processed)
                    wfile.write("\n---\n")
            except (UnicodeDecodeError, PermissionError) as e:
                print(f"Skipping {file_path} due to error: {e}")

if __name__ == "__main__":
    main()

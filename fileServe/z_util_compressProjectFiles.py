import re
import argparse
from pathlib import Path
from typing import List, Set, Tuple, Dict
import ast
import json

# Enhanced Configuration
INCLUSION_EXTENSIONS = {
    "py": {"priority": 1, "comments": "smart"},
    "js": {"priority": 2, "comments": "smart"}, 
    "ts": {"priority": 2, "comments": "smart"},
    "jsx": {"priority": 2, "comments": "smart"},
    "tsx": {"priority": 2, "comments": "smart"},
    "html": {"priority": 3, "comments": "strip"},
    "css": {"priority": 4, "comments": "strip"},
    "md": {"priority": 3, "comments": "smart"},
    "json": {"priority": 2, "comments": "none"},
    "yaml": {"priority": 3, "comments": "smart"},
    "yml": {"priority": 3, "comments": "smart"},
    "sql": {"priority": 3, "comments": "smart"},
    "sh": {"priority": 4, "comments": "smart"},
}

EXCLUDED_FILES = {
    "z_allFiles.ignore", "z_util_compressProjectFiles.py", 
    "package-lock.json", "yarn.lock", ".DS_Store", 
    "Thumbs.db", "*.min.js", "*.min.css"
}

EXCLUDED_DIRS = {
    "env", ".env", "venv", ".venv", ".git", "__pycache__", 
    ".idea", ".vscode", "node_modules", "dist", "build", 
    ".next", "coverage", ".pytest_cache", "target"
}

HIGH_PRIORITY_FILES = {
    "main.py", "app.py", "index.js", "index.ts", "App.jsx", 
    "App.tsx", "requirements.txt", "package.json", "Dockerfile",
    "README.md", "config.py", "settings.py"
}

OUTPUT_FILE = "z_allFiles.txt"
MAX_FILE_SIZE = 50000  # Skip files larger than 50KB
TOKEN_ESTIMATE_RATIO = 0.75  # Rough tokens per character

def should_process_file(file_path: Path) -> Tuple[bool, int]:
    """Check if a file should be included and return its priority."""
    if file_path.name in EXCLUDED_FILES:
        return False, 0
    if any(pattern in file_path.name for pattern in ["*.min.js", "*.min.css"]):
        return False, 0
    
    ext = file_path.suffix[1:] if file_path.suffix else ''
    if ext not in INCLUSION_EXTENSIONS:
        return False, 0
        
    if any(part in EXCLUDED_DIRS or part.startswith('.') for part in file_path.parts):
        return False, 0
    
    # Check file size
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return False, 0
    except OSError:
        return False, 0
    
    priority = INCLUSION_EXTENSIONS[ext]["priority"]
    
    # Boost priority for important files
    if file_path.name in HIGH_PRIORITY_FILES:
        priority = 0
    elif file_path.name.startswith(('config', 'settings')):
        priority = 1
        
    return True, priority

def extract_python_metadata(content: str, file_path: Path) -> Dict:
    """Extract metadata from Python files."""
    metadata = {"imports": [], "classes": [], "functions": []}
    
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    metadata["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    metadata["imports"].append(node.module)
            elif isinstance(node, ast.ClassDef):
                metadata["classes"].append(node.name)
            elif isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):  # Skip private functions
                    metadata["functions"].append(node.name)
    except SyntaxError:
        pass
    
    return metadata

def strip_comments_smart(content: str, ext: str) -> str:
    """Intelligently strip comments while preserving important ones."""
    lines = content.splitlines()
    result_lines = []
    
    if ext == 'py':
        for line in lines:
            stripped = line.strip()
            # Keep docstrings, TODO comments, and type hints
            if (stripped.startswith('"""') or stripped.startswith("'''") or 
                'TODO' in line or 'FIXME' in line or 'XXX' in line or
                not stripped.startswith('#')):
                result_lines.append(line)
    
    elif ext in ['js', 'ts', 'jsx', 'tsx']:
        in_multiline = False
        for line in lines:
            if '/*' in line and '*/' in line:
                # Single line comment
                if 'TODO' in line or 'FIXME' in line or '@' in line:
                    result_lines.append(line)
                else:
                    result_lines.append(re.sub(r'/\*.*?\*/', '', line))
            elif '/*' in line:
                in_multiline = True
                if 'TODO' in line or 'FIXME' in line or '@' in line:
                    result_lines.append(line)
            elif '*/' in line:
                in_multiline = False
                if 'TODO' in line or 'FIXME' in line or '@' in line:
                    result_lines.append(line)
            elif not in_multiline:
                if not line.strip().startswith('//') or 'TODO' in line or 'FIXME' in line:
                    result_lines.append(re.sub(r'//(?!.*TODO|.*FIXME).*', '', line))
    
    else:
        # Fallback to original logic
        result_lines = lines
    
    return '\n'.join(line for line in result_lines if line.strip())

def strip_comments_and_blank_lines(content: str, ext: str, comment_strategy: str) -> str:
    """Enhanced comment stripping with different strategies."""
    if comment_strategy == "none":
        return content
    elif comment_strategy == "smart":
        return strip_comments_smart(content, ext)
    else:  # strip
        lines = content.splitlines()
        if ext == 'py':
            lines = [line for line in lines if not line.strip().startswith('#')]
        elif ext in ['js', 'ts', 'jsx', 'tsx']:
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            lines = [re.sub(r'//.*', '', line) for line in content.splitlines() 
                    if not line.strip().startswith('//')]
        elif ext in {'html', 'jinja2'}:
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
            lines = content.splitlines()
        elif ext == 'css':
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            lines = content.splitlines()
        elif ext == 'md':
            lines = [line for line in lines if not line.strip().startswith('<!--')]
        
        return '\n'.join(line for line in lines if line.strip())

def generate_project_structure(root: Path, files_to_process: List[Path]) -> str:
    """Generate enhanced project structure with file metadata."""
    structure_lines = ["## PROJECT STRUCTURE"]
    
    # Create a set of processed files for marking
    processed_files = {f.relative_to(root) if f.is_relative_to(root) else f 
                      for f in files_to_process}
    
    def walk(dir_path: Path, prefix=""):
        try:
            entries = sorted([
                p for p in dir_path.iterdir()
                if not p.name.startswith('.') and
                p.name not in EXCLUDED_DIRS
            ], key=lambda x: (x.is_file(), x.name.lower()))
        except PermissionError:
            return
            
        for idx, entry in enumerate(entries):
            connector = "└── " if idx == len(entries) - 1 else "├── "
            rel_path = entry.relative_to(root) if entry.is_relative_to(root) else entry
            
            # Mark files that will be included in output
            marker = " ✓" if entry.is_file() and rel_path in processed_files else ""
            
            structure_lines.append(f"{prefix}{connector}{entry.name}{marker}")
            
            if entry.is_dir():
                extension = "    " if idx == len(entries) - 1 else "│   "
                walk(entry, prefix + extension)

    walk(root)
    return '\n'.join(structure_lines)

def estimate_tokens(content: str) -> int:
    """Rough token count estimation."""
    return int(len(content) * TOKEN_ESTIMATE_RATIO)

def get_files_to_process(root: Path, specific_files=None) -> List[Path]:
    """Get prioritized list of files to process."""
    if specific_files:
        files_to_process = []
        for file_name in specific_files:
            file_path = Path(file_name)
            if file_path.is_absolute():
                if file_path.exists() and file_path.is_file():
                    files_to_process.append(file_path)
                else:
                    print(f"Warning: File not found: {file_path}")
            else:
                full_path = root / file_path
                if full_path.exists() and full_path.is_file():
                    files_to_process.append(full_path)
                else:
                    print(f"Warning: File not found: {full_path}")
        return files_to_process
    else:
        # Collect all valid files with priorities
        files_with_priority = []
        for file_path in root.rglob('*'):
            if file_path.is_file():
                should_process, priority = should_process_file(file_path)
                if should_process:
                    files_with_priority.append((file_path, priority))
        
        # Sort by priority (lower number = higher priority)
        files_with_priority.sort(key=lambda x: (x[1], str(x[0])))
        return [file_path for file_path, _ in files_with_priority]

def main():
    parser = argparse.ArgumentParser(
        description='Consolidate project files into a single output file optimized for AI context.'
    )
    parser.add_argument('-f', '--files', nargs='+',
                       help='Specific files to process (bypasses inclusion/exclusion rules)')
    parser.add_argument('--max-tokens', type=int, default=80000,
                       help='Maximum estimated tokens (default: 80000)')
    parser.add_argument('--include-metadata', action='store_true',
                       help='Include file metadata (imports, functions, etc.)')
    parser.add_argument('--output', default=OUTPUT_FILE,
                       help=f'Output file name (default: {OUTPUT_FILE})')
    
    args = parser.parse_args()
    
    root = Path.cwd()
    output_path = Path(args.output)
    
    # Get files to process
    files_to_process = get_files_to_process(root, args.files)
    
    # Generate project structure
    structure = generate_project_structure(root, files_to_process)
    
    # Start building output
    output_content = [structure, "\n"]
    
    total_tokens = estimate_tokens(structure)
    processed_files = 0
    skipped_files = 0
    
    print(f"Processing {len(files_to_process)} files...")
    
    for file_path in files_to_process:
        if total_tokens >= args.max_tokens:
            print(f"Reached token limit ({args.max_tokens}). Stopping.")
            break
            
        try:
            ext = file_path.suffix[1:] if file_path.suffix else ''
            raw_content = file_path.read_text(encoding='utf-8')
            
            # Get comment strategy for this file type
            comment_strategy = INCLUSION_EXTENSIONS.get(ext, {}).get("comments", "strip")
            processed = strip_comments_and_blank_lines(raw_content, ext, comment_strategy)
            
            if processed.strip():
                file_tokens = estimate_tokens(processed)
                
                # Check if adding this file would exceed token limit
                if total_tokens + file_tokens > args.max_tokens:
                    print(f"Skipping {file_path} - would exceed token limit")
                    skipped_files += 1
                    continue
                
                # File header
                relative_path = file_path.relative_to(root) if file_path.is_relative_to(root) else file_path
                header = f"\n## {relative_path}"
                
                # Add metadata if requested
                if args.include_metadata and ext == 'py':
                    metadata = extract_python_metadata(raw_content, file_path)
                    if metadata["imports"] or metadata["classes"] or metadata["functions"]:
                        header += f"\n### Metadata: {json.dumps(metadata, indent=2)}"
                
                output_content.extend([header, "\n", processed, "\n---\n"])
                total_tokens += file_tokens
                processed_files += 1
                
                if processed_files % 10 == 0:
                    print(f"Processed {processed_files} files ({total_tokens:,} tokens)")
                    
        except (UnicodeDecodeError, PermissionError) as e:
            print(f"Skipping {file_path} due to error: {e}")
            skipped_files += 1
    
    # Write output
    output_path.write_text(''.join(output_content), encoding='utf-8')
    
    print(f"\n✅ Complete!")
    print(f"📁 Processed: {processed_files} files")
    print(f"⏭️  Skipped: {skipped_files} files") 
    print(f"📊 Estimated tokens: {total_tokens:,}")
    print(f"📄 Output written to: {output_path}")

if __name__ == "__main__":
    main()
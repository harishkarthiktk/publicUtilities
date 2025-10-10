#!/usr/bin/env python3
"""
Directory Token Counter for AI Agent Context Analysis
Scans directories recursively, respects .gitignore, and counts tokens
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import mimetypes

# Initialize mimetypes
mimetypes.init()

# Try importing required libraries with helpful error messages
try:
    import tiktoken
except ImportError:
    print("ERROR: tiktoken not installed. Install with: pip install tiktoken")
    sys.exit(1)

try:
    import pathspec
except ImportError:
    print("ERROR: pathspec not installed. Install with: pip install pathspec")
    sys.exit(1)

try:
    import magic
except ImportError:
    print("WARNING: python-magic not installed. MIME detection will be limited.")
    print("Install with: pip install python-magic-bin (Windows) or python-magic (Unix)")
    magic = None


# Text file extensions that should be considered
TEXT_EXTENSIONS = {
    '.txt', '.md', '.rst', '.log', '.csv', '.tsv',
    '.py', '.pyw', '.pyi', '.pyc', '.pyx',
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.java', '.class', '.jar',
    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx',
    '.cs', '.vb', '.fs', '.fsx',
    '.go', '.rs', '.swift', '.kt', '.kts', '.scala',
    '.rb', '.php', '.pl', '.pm', '.r', '.m', '.mm',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.config',
    '.html', '.htm', '.xhtml', '.css', '.scss', '.sass', '.less',
    '.sql', '.db', '.sqlite',
    '.sh', '.bash', '.zsh', '.fish', '.bat', '.cmd', '.ps1', '.psm1',
    '.env', '.gitignore', '.gitattributes', '.dockerignore', '.editorconfig',
    '.makefile', '.cmake', '.gradle', '.maven',
    '.proto', '.graphql', '.vue', '.svelte',
    '.tex', '.bib', '.org', '.adoc',
}

MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB in bytes


class TokenCounter:
    """Handles token counting using multiple methods"""
    
    def __init__(self):
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        except Exception as e:
            print(f"ERROR: Failed to initialize tiktoken encoder: {e}")
            sys.exit(1)
    
    def count_tiktoken(self, text: str) -> int:
        """Count tokens using tiktoken"""
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            raise Exception(f"tiktoken counting error: {e}")
    
    def count_char_approx(self, text: str) -> int:
        """Count tokens using 4 chars ≈ 1 token approximation"""
        return len(text) // 4
    
    def count_all(self, text: str) -> Tuple[int, int, int]:
        """
        Count tokens using all methods
        Returns: (tiktoken_count, char_approx_count, average_count)
        """
        tiktoken_count = self.count_tiktoken(text)
        char_count = self.count_char_approx(text)
        average_count = (tiktoken_count + char_count) // 2
        return tiktoken_count, char_count, average_count


class DirectoryScanner:
    """Scans directory and analyzes token counts"""
    
    def __init__(self, working_dir: Path):
        self.working_dir = working_dir.resolve()
        self.token_counter = TokenCounter()
        self.exceptions: List[str] = []
        self.folder_stats: Dict[str, Tuple[int, int, int, int]] = defaultdict(lambda: (0, 0, 0, 0))
        self.gitignore_spec = None
        self._load_gitignore()
        
    def _load_gitignore(self):
        """Load and parse .gitignore file if it exists"""
        gitignore_path = self.working_dir / '.gitignore'
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    patterns = f.read()
                self.gitignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns.splitlines())
                print(f"✓ Loaded .gitignore from {gitignore_path}")
            except Exception as e:
                self.exceptions.append(f"Failed to load .gitignore: {e}")
    
    def _is_ignored(self, path: Path) -> bool:
        """Check if path should be ignored based on .gitignore"""
        if self.gitignore_spec is None:
            return False
        
        try:
            # Get relative path from working directory
            rel_path = path.relative_to(self.working_dir)
            # Check if path matches any gitignore pattern
            return self.gitignore_spec.match_file(str(rel_path))
        except Exception:
            return False
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Determine if a file is a text file"""
        # Check by extension first
        if file_path.suffix.lower() in TEXT_EXTENSIONS:
            return True
        
        # Check common text filenames without extensions
        if file_path.name.lower() in {'makefile', 'dockerfile', 'readme', 'license', 'changelog'}:
            return True
        
        # Use MIME type detection for extensionless files
        if magic:
            try:
                mime = magic.Magic(mime=True)
                mime_type = mime.from_file(str(file_path))
                return mime_type.startswith('text/') or 'json' in mime_type or 'xml' in mime_type
            except Exception as e:
                self.exceptions.append(f"MIME detection failed for {file_path}: {e}")
        else:
            # Fallback: use mimetypes library
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type and mime_type.startswith('text/'):
                return True
        
        return False
    
    def _read_file_content(self, file_path: Path) -> str:
        """Read file content with multiple encoding attempts"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise Exception(f"Read error: {e}")
        
        raise Exception("Unable to decode file with any supported encoding")
    
    def scan(self) -> Dict:
        """
        Scan directory and count tokens
        Returns dictionary with scan results
        """
        print(f"\n🔍 Scanning directory: {self.working_dir}")
        print(f"📏 Max file size: {MAX_FILE_SIZE / (1024*1024):.1f} MB\n")
        
        total_files = 0
        processed_files = 0
        skipped_files = 0
        total_size = 0
        
        total_tiktoken = 0
        total_char_approx = 0
        total_average = 0
        
        # Walk through directory
        for file_path in self.working_dir.rglob('*'):
            if not file_path.is_file():
                continue
            
            total_files += 1
            
            # Check if ignored by .gitignore
            if self._is_ignored(file_path):
                skipped_files += 1
                continue
            
            # Check file size
            try:
                file_size = file_path.stat().st_size
                if file_size > MAX_FILE_SIZE:
                    self.exceptions.append(f"Skipped (too large): {file_path.relative_to(self.working_dir)} ({file_size / (1024*1024):.2f} MB)")
                    skipped_files += 1
                    continue
            except Exception as e:
                self.exceptions.append(f"Failed to get size for {file_path}: {e}")
                skipped_files += 1
                continue
            
            # Check if text file
            if not self._is_text_file(file_path):
                skipped_files += 1
                continue
            
            # Read and count tokens
            try:
                content = self._read_file_content(file_path)
                tiktoken_count, char_count, avg_count = self.token_counter.count_all(content)
                
                # Update totals
                total_tiktoken += tiktoken_count
                total_char_approx += char_count
                total_average += avg_count
                total_size += file_size
                processed_files += 1
                
                # Update folder stats
                folder = file_path.parent.relative_to(self.working_dir)
                folder_key = str(folder) if str(folder) != '.' else '<root>'
                current_stats = self.folder_stats[folder_key]
                self.folder_stats[folder_key] = (
                    current_stats[0] + tiktoken_count,
                    current_stats[1] + char_count,
                    current_stats[2] + avg_count,
                    current_stats[3] + 1  # file count
                )
                
                print(f"✓ {file_path.relative_to(self.working_dir)}")
                
            except Exception as e:
                self.exceptions.append(f"Failed to process {file_path.relative_to(self.working_dir)}: {e}")
                skipped_files += 1
        
        return {
            'total_files': total_files,
            'processed_files': processed_files,
            'skipped_files': skipped_files,
            'total_size': total_size,
            'total_tiktoken': total_tiktoken,
            'total_char_approx': total_char_approx,
            'total_average': total_average,
        }


def format_report(results: Dict, folder_stats: Dict, exceptions: List[str]) -> str:
    """Format the analysis report"""
    lines = []
    lines.append("=" * 80)
    lines.append("DIRECTORY TOKEN ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Total Analysis
    lines.append("TOTAL ANALYSIS")
    lines.append("-" * 80)
    lines.append(f"Total files found:       {results['total_files']:,}")
    lines.append(f"Text files processed:    {results['processed_files']:,}")
    lines.append(f"Files skipped:           {results['skipped_files']:,}")
    lines.append(f"Total content size:      {results['total_size'] / (1024*1024):.2f} MB")
    lines.append("")
    lines.append("TOKEN COUNTS (for AI context initialization):")
    lines.append(f"  • TikToken (GPT-4):    {results['total_tiktoken']:,} tokens")
    lines.append(f"  • 4 Char ≈ 1 Token: {results['total_char_approx']:,} tokens")
    lines.append(f"  • Average of Both:      {results['total_average']:,} tokens")
    lines.append("")
    
    # Per-folder breakdown
    if folder_stats:
        lines.append("PER-FOLDER BREAKDOWN")
        lines.append("-" * 80)
        lines.append(f"{'Folder':<40} {'Files':>8} {'TikToken':>12} {'Char/4':>12} {'Average':>12}")
        lines.append("-" * 80)
        
        # Sort folders alphabetically
        for folder in sorted(folder_stats.keys()):
            stats = folder_stats[folder]
            tiktoken, char_approx, average, file_count = stats
            lines.append(f"{folder:<40} {file_count:>8} {tiktoken:>12,} {char_approx:>12,} {average:>12,}")
        lines.append("")
    
    # Exceptions/Warnings
    if exceptions:
        lines.append("EXCEPTIONS AND WARNINGS")
        lines.append("-" * 80)
        for exc in exceptions:
            lines.append(f"⚠ {exc}")
        lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze directory token count for AI agent context initialization",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-w', '--working-dir',
        type=str,
        required=True,
        help='Target directory to analyze'
    )
    parser.add_argument(
        '-o', '--log-out',
        type=str,
        default=None,
        help='Output directory for log file (default: same as working-dir)'
    )
    
    args = parser.parse_args()
    
    # Validate working directory
    working_dir = Path(args.working_dir)
    if not working_dir.exists():
        print(f"ERROR: Directory does not exist: {working_dir}")
        sys.exit(1)
    
    if not working_dir.is_dir():
        print(f"ERROR: Path is not a directory: {working_dir}")
        sys.exit(1)
    
    # Set output directory
    log_out_dir = Path(args.log_out) if args.log_out else working_dir
    if not log_out_dir.exists():
        log_out_dir.mkdir(parents=True)
    
    # Run scan
    scanner = DirectoryScanner(working_dir)
    results = scanner.scan()
    
    # Generate report
    report = format_report(results, scanner.folder_stats, scanner.exceptions)
    
    # Display report
    print("\n" + report)
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_out_dir / f"token_analysis_{timestamp}.txt"
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📝 Report saved to: {log_file}")
    except Exception as e:
        print(f"\n❌ Failed to save report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
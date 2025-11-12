
import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import tempfile
import json
import glob

from multiprocessing import Pool, cpu_count
from concurrent.futures import as_completed
import time

HAS_YAML = False
HAS_DOCX = False
HAS_TQDM = False
try:
    import yaml
    HAS_YAML = True

    from docx import Document
    from docx.enum.style import WD_STYLE_TYPE
    from docx.shared import Inches, Pt
    HAS_DOCX = True

    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    pass

from abc import ABC, abstractmethod
from typing import Optional

class FileIO(ABC):
    """Abstract interface for file operations to improve testability."""
    
    @abstractmethod
    def mkdir(self, path: Path, parents: bool = True, exist_ok: bool = True) -> None:
        pass
    
    @abstractmethod
    def unlink(self, path: Path) -> None:
        pass
    
    @abstractmethod
    def exists(self, path: Path) -> bool:
        pass
    
    @abstractmethod
    def stat_size(self, path: Path) -> int:
        pass
    
    @abstractmethod
    def is_file(self, path: Path) -> bool:
        pass


class DefaultFileIO(FileIO):
    """Default implementation of FileIO using standard library."""
    
    def mkdir(self, path: Path, parents: bool = True, exist_ok: bool = True) -> None:
        path.mkdir(parents=parents, exist_ok=exist_ok)
    
    def unlink(self, path: Path) -> None:
        if self.exists(path):
            os.unlink(path)
    
    def exists(self, path: Path) -> bool:
        return path.exists()
    
    def stat_size(self, path: Path) -> int:
        return path.stat().st_size
    
    def is_file(self, path: Path) -> bool:
        return path.is_file()


class PandocInterface(ABC):
    """Abstract interface for Pandoc operations to improve testability."""
    
    @abstractmethod
    def convert_file(self, input_path: str, output_format: str, outputfile: str, extra_args: list[str]) -> None:
        pass


class DefaultPandoc(PandocInterface):
    """Default implementation using pypandoc."""
    
    def convert_file(self, input_path: str, output_format: str, outputfile: str, extra_args: list[str]) -> None:
        import pypandoc
        pypandoc.convert_file(input_path, output_format, outputfile=outputfile, extra_args=extra_args)
__version__ = '2.0'

@dataclass(frozen=True)
class Config:
    """Immutable configuration for the Markdown to DOCX converter."""
    default_font: str = 'Arial'
    body_size: int = 11
    list_font: str = 'Arial'
    list_size: int = 11
    heading_sizes: dict[int, int] = field(default_factory=lambda: {
        1: 24, 2: 18, 3: 14, 4: 12, 5: 10, 6: 9
    })
    pandoc_extensions: dict[str, list[str]] = field(default_factory=lambda: {
        # Basic Markdown features
        'basic': [
            'abbreviations', 'auto_identifiers', 'backtick_code_blocks',
            'blank_before_blockquote', 'blank_before_header', 'citations',
            'definition_lists', 'escaped_line_breaks', 'four_space_rule',
            'gfm_auto_identifiers', 'intraword_underscores',
            'shortcut_reference_links', 'smart', 'strikeout',
            'subscript', 'superscript',
        ],
        # Code and blocks
        'code': [
            'fenced_code_blocks', 'fenced_code_attributes',
            'inline_code_attributes', 'markdown_in_html_blocks',
        ],
        # Tables and structure
        'structure': [
            'fenced_divs', 'grid_tables', 'header_attributes',
            'implicit_figures', 'inline_notes', 'link_attributes',
            'native_divs', 'native_spans', 'pipe_tables',
            'raw_attribute', 'raw_html', 'raw_tex', 'table_captions',
        ],
        # Advanced features
        'advanced': [
            'footnotes', 'task_lists', 'tex_math_dollars',
        ],
    })

def get_config(args: argparse.Namespace) -> Config:
    """Create configuration with environment variable overrides, file, and CLI."""
    # Default values from env
    default_font = os.environ.get('DEFAULT_FONT', 'Arial')
    body_size = int(os.environ.get('BODY_SIZE', 11))
    list_font = os.environ.get('LIST_FONT', 'Arial')
    list_size = int(os.environ.get('LIST_SIZE', 11))
    
    # Heading sizes from env
    heading_str = os.environ.get('HEADING_SIZES', '1:24,2:18,3:14,4:12,5:10,6:9')
    heading_sizes = {}
    for pair in heading_str.split(','):
        if ':' in pair:
            level, size = pair.split(':')
            heading_sizes[int(level)] = int(size)
    
    config = Config(
        default_font=default_font,
        body_size=body_size,
        list_font=list_font,
        list_size=list_size,
        heading_sizes=heading_sizes
    )
    
    # Load from file if provided
    if args.config:
        config_dict = load_config_file(args.config)
        for key, value in config_dict.items():
            if key in Config.__annotations__:
                config = replace(config, **{key: value})
    
    # CLI overrides
    if args.font:
        config = replace(config, default_font=args.font)
    if args.body_size is not None:
        config = replace(config, body_size=args.body_size)
    if args.list_font:
        config = replace(config, list_font=args.list_font)
    if args.list_size is not None:
        config = replace(config, list_size=args.list_size)
    if args.heading_sizes:
        heading_sizes = {}
        for pair in args.heading_sizes.split(','):
            if ':' in pair:
                level, size = pair.split(':')
                heading_sizes[int(level)] = int(size)
        config = replace(config, heading_sizes=heading_sizes)
    
    return config

def validate_config(config: Config) -> None:
    """Validate the configuration values."""
    if config.body_size <= 0:
        raise ValueError("body_size must be positive")
    if config.list_size <= 0:
        raise ValueError("list_size must be positive")
    for size in config.heading_sizes.values():
        if size <= 0:
            raise ValueError("All heading sizes must be positive")
    if not config.default_font or not isinstance(config.default_font, str):
        raise ValueError("default_font must be a non-empty string")
    if not config.list_font or not isinstance(config.list_font, str):
        raise ValueError("list_font must be a non-empty string")
    # Basic check for pandoc_extensions structure
    if not isinstance(config.pandoc_extensions, dict):
        raise ValueError("pandoc_extensions must be a dictionary")


def load_config_file(path: str) -> dict:
    """Load configuration from JSON or YAML file."""
    path = Path(path)
    if path.suffix.lower() == '.json':
        with open(path, 'r') as f:
            return json.load(f)
    elif path.suffix.lower() in {'.yaml', '.yml'}:
        if HAS_YAML:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        else:
            raise ValueError("YAML support not available. Install PyYAML.")
    else:
        raise ValueError("Unsupported config file format. Use JSON or YAML.")

class TemplateManager:
    """Manages template creation and handling for DOCX conversions."""
    
    def __init__(self, config: Config, file_io: FileIO):
        self.config = config
        self.file_io = file_io
        self._temp_template_path = None
    
    def create_default_template(self):
        """Create a default DOCX template with styles for headings and lists."""
        from docx import Document
        from docx.enum.style import WD_STYLE_TYPE
        from docx.shared import Inches, Pt
        
        doc = Document()
        styles = doc.styles
        
        # Normal style
        normal_style = styles['Normal']
        normal_style.font.name = self.config.default_font
        normal_style.font.size = Pt(self.config.body_size)
        
        # Heading styles
        for level, size in self.config.heading_sizes.items():
            heading_style = styles[f'Heading {level}']
            heading_style.font.name = self.config.default_font
            heading_style.font.size = Pt(size)
        
        # List Bullet style for unordered lists
        if 'List Bullet' in styles:
            list_bullet = styles['List Bullet']
        else:
            list_bullet = styles.add_style('List Bullet', WD_STYLE_TYPE.PARAGRAPH)
        list_bullet.base_style = styles['Normal']
        list_bullet.font.name = self.config.list_font
        list_bullet.font.size = Pt(self.config.list_size)
        # Indent for list appearance (Pandoc adds bullet symbol)
        list_bullet.paragraph_format.left_indent = Inches(0.25)
        list_bullet.paragraph_format.first_line_indent = Inches(-0.25)
        
        # List Number style for ordered lists
        if 'List Number' in styles:
            list_number = styles['List Number']
        else:
            list_number = styles.add_style('List Number', WD_STYLE_TYPE.PARAGRAPH)
        list_number.base_style = styles['Normal']
        list_number.font.name = self.config.list_font
        list_number.font.size = Pt(self.config.list_size)
        # Indent for list appearance (Pandoc adds numbering)
        list_number.paragraph_format.left_indent = Inches(0.25)
        list_number.paragraph_format.first_line_indent = Inches(-0.25)
        
        self._temp_template_path = None
        try:
            fd, tmp_path_str = tempfile.mkstemp(suffix='.docx')
            tmp_path = Path(tmp_path_str)
            os.close(fd)  # Not using the file descriptor
            doc.save(tmp_path)
            logger.debug(f"Created default template: {tmp_path}")
            self._temp_template_path = tmp_path
            return str(tmp_path)
        except Exception:
            if self._temp_template_path and self.file_io.exists(self._temp_template_path):
                self.file_io.unlink(self._temp_template_path)
            raise
    
    def get_template(self, provided_template: Optional[str], has_docx: bool, no_template: bool) -> Optional[str]:
        """Get the appropriate template path, handling defaults and temps."""
        if no_template:
            logger.info("No template used (Pandoc defaults for styling).")
            return None
        
        if provided_template:
            template_path = Path(provided_template)
            if not template_path.exists():
                raise ValueError(f"Template file '{provided_template}' does not exist.")
            if template_path.suffix.lower() != '.docx':
                raise ValueError("Template file must have .docx extension.")
            return str(template_path)
        
        if not has_docx:
            logger.warning("No template provided and python-docx not available. Using Pandoc defaults for styling. Install python-docx for better list support.")
            return None
        
        template_path = self.create_default_template()
        logger.info("Using auto-generated default template for consistent styling including lists.")
        return template_path
    
    def cleanup(self):
        """Clean up any temporary template files."""
        if self._temp_template_path and self.file_io.exists(self._temp_template_path):
            self.file_io.unlink(self._temp_template_path)
            logger.debug(f"Cleaned up temporary template: {self._temp_template_path}")
            self._temp_template_path = None

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import pypandoc
        version = pypandoc.get_pandoc_version()
        logger.info(f"Pandoc version {version} detected.")
    except ImportError:
        logger.error(
            "pypandoc is not installed. Install it with:\n"
            "pip install pypandoc\n"
            "Then install Pandoc binary from https://pandoc.org/installing.html and ensure it's in your PATH."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"Error detecting Pandoc: {e}\n"
            "Please install Pandoc from https://pandoc.org/installing.html and ensure it's in your PATH.\n"
            "Verify with: pandoc --version"
        )
        sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class MarkdownConverter:
    """Handles Markdown to DOCX conversion using Pandoc."""
    
    def __init__(self, config: Config, pandoc: PandocInterface, custom_extensions=None):
        self.config = config
        self.pandoc = pandoc
        if custom_extensions:
            self._pandoc_extensions = custom_extensions
        else:
            # Build extensions string from config groups
            all_extensions = []
            for category, exts in self.config.pandoc_extensions.items():
                all_extensions.extend(exts)
            self._pandoc_extensions = '+'.join(all_extensions)
    
    def convert(self, input_path: Path, output_path: Path, template_path: Optional[str] = None, verbose: bool = False, no_template: bool = False, quiet: bool = False) -> None:
        """Convert Markdown file to DOCX using Pandoc with full formatting support."""
        file_size_mb = input_path.stat().st_size / (1024 * 1024)
        
        extra_args = [
            '--standalone',
            f'--from=markdown+{self._pandoc_extensions}',  # Enable comprehensive Markdown extensions
            f'--resource-path={input_path.parent}',  # Resolve relative paths for images, etc.
        ]
        
        if template_path:
            extra_args.append(f'--reference-doc={template_path}')
        
        if verbose:
            logger.debug(f"Pandoc extra args: {extra_args}")
        
        if not quiet:
            logger.info(f"Starting conversion of '{input_path.name}' ({file_size_mb:.1f} MB)")
            if HAS_TQDM:
                with tqdm(total=100, desc="Converting", unit="%", leave=False) as pbar:
                    # Since Pandoc doesn't provide progress, we'll simulate completion
                    start_time = time.time()
                    self.pandoc.convert_file(
                        str(input_path),
                        'docx',
                        str(output_path),
                        extra_args
                    )
                    end_time = time.time()
                    duration = end_time - start_time
                    pbar.n = 100
                    pbar.set_postfix({"ETA": f"{duration:.1f}s", "Actual": f"{duration:.1f}s"})
                    pbar.update(0)
            else:
                start_time = time.time()
                self.pandoc.convert_file(
                    str(input_path),
                    'docx',
                    str(output_path),
                    extra_args
                )
                duration = time.time() - start_time
                logger.info(f"Conversion completed in {duration:.1f} seconds")
            logger.info(f"Successfully converted: {output_path}")
        else:
            self.pandoc.convert_file(
                str(input_path),
                'docx',
                str(output_path),
                extra_args
            )
        
        try:
            self.pandoc.convert_file(
                str(input_path),
                'docx',
                str(output_path),
                extra_args
            )
            logger.info(f"Successfully converted: {output_path}")
        except OSError as e:
            logger.error(f"[E001] File I/O or Pandoc binary error: {e}. Ensure Pandoc is installed and input file is accessible.")
            raise
        except RuntimeError as e:
            logger.error(f"[E002] Pandoc conversion runtime error: {e}. Check Markdown syntax or try without extensions.")
            raise
        except Exception as e:
            logger.error(f"[E003] Unexpected conversion error: {e}. Please report this with your input file.")
            raise

def parse_arguments(file_io: FileIO) -> tuple:
    parser = argparse.ArgumentParser(
        description='Convert Markdown to DOCX using Pandoc, preserving all formatting features.',
        epilog='Example: python convert_to_docx.py input.md -o output.docx -v'
    )
    parser.add_argument('input_file', type=str, help='Input Markdown file path')
    parser.add_argument('-o', '--output', type=str, help='Output DOCX file or directory path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('-t', '--template', type=str, help='Custom reference DOCX template path')
    parser.add_argument('--no-template', action='store_true', help='Skip using a reference template (use Pandoc defaults for styling)')
    parser.add_argument('--extensions', type=str, help='Custom Pandoc Markdown extensions (e.g., "fenced_code_blocks+footnotes" or comma-separated list)')
    parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing output file if it exists')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress progress output')
    parser.add_argument('--config', type=str, help='Path to JSON or YAML config file')
    parser.add_argument('--font', type=str, help='Default font name')
    parser.add_argument('--body-size', type=int, help='Body font size (pt)')
    parser.add_argument('--list-font', type=str, help='List font name')
    parser.add_argument('--list-size', type=int, help='List font size (pt)')
    parser.add_argument('--heading-sizes', type=str, help='Heading sizes as "1:24,2:18,3:14,4:12,5:10,6:9"')
    parser.add_argument('--validate-template', action='store_true', help='Validate the template file without conversion')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not file_io.exists(input_path):
        parser.error(f"Input file '{args.input_file}' does not exist.")
    if not file_io.is_file(input_path):
        parser.error(f"'{args.input_file}' is not a file.")
    if input_path.suffix.lower() not in {'.md', '.markdown'}:
        parser.error("Input file must have .md or .markdown extension.")
    
    # File size limit (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    try:
        file_size = file_io.stat_size(input_path)
        if file_size > MAX_FILE_SIZE:
            parser.error(f"Input file too large ({file_size / (1024*1024):.1f} MB). Maximum allowed: 10 MB.")
    except OSError as e:
        parser.error(f"Cannot check input file size: {e}")
    
    # Process custom extensions
    if args.extensions:
        if ',' in args.extensions:
            args.extensions = '+'.join(args.extensions.split(','))
        logger.info(f"Using custom extensions: {args.extensions}")
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    return args, input_path

def generate_output_path(args, input_path: Path, file_io: FileIO) -> Path:
    """Generate output path based on arguments."""
    if args.output:
        output_path = Path(args.output)
        if file_io.is_file(output_path) or (output_path.exists() and not output_path.is_dir()):
            # Treat as file path
            pass
        elif output_path.is_dir():
            # If output is a directory, append input stem + .docx
            output_path = output_path / f"{input_path.stem}.docx"
        else:
            # Assume file path, parent dir will be created
            pass
    else:
        # Default: same dir as input, with .docx
        output_path = input_path.with_suffix('.docx')
    
    # Check if output file exists and --force not set
    if file_io.exists(output_path) and not args.force:
        raise ValueError(f"Output file '{output_path}' already exists. Use --force to overwrite.")
    
    # Ensure output directory exists
    file_io.mkdir(output_path.parent, parents=True, exist_ok=True)
    
    logger.info(f"Output path: {output_path}")
    return output_path

if __name__ == "__main__":
    # Dependency injection setup
    file_io = DefaultFileIO()
    pandoc = DefaultPandoc()
    
    try:
        args, input_path = parse_arguments(file_io)
        
        if args.validate_template:
            if not args.template:
                logger.error("--validate-template requires --template")
                sys.exit(1)
            if not HAS_DOCX:
                logger.error("python-docx is required for template validation")
                sys.exit(1)
            try:
                doc = Document(args.template)
                required_styles = ['Normal', 'Heading 1', 'Heading 2', 'Heading 3', 'Heading 4', 'Heading 5', 'Heading 6', 'List Bullet', 'List Number']
                existing_styles = [style.name for style in doc.styles]
                missing = [s for s in required_styles if s not in existing_styles]
                if missing:
                    logger.error(f"Template missing required styles: {', '.join(missing)}")
                    sys.exit(1)
                logger.info("Template validation passed. All required styles are present.")
                sys.exit(0)
            except Exception as e:
                logger.error(f"Template validation failed: {e}")
                sys.exit(1)
        
        check_dependencies()
        output_path = generate_output_path(args, input_path, file_io)
        
        config = get_config(args)
        validate_config(config)
        template_mgr = TemplateManager(config, file_io)
        converter = MarkdownConverter(config, pandoc, args.extensions)
        
        try:
            template_path = template_mgr.get_template(args.template, HAS_DOCX, args.no_template)
            converter.convert(input_path, output_path, template_path, args.verbose, args.no_template, args.quiet)
        finally:
            template_mgr.cleanup()
        
        if not args.quiet:
            logger.info("Conversion completed successfully.")
    except argparse.ArgumentError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Input validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        sys.exit(1)

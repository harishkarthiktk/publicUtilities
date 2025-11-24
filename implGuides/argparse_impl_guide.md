# Argparse Implementation Guide for Python CLI Scripts

This guide offers a simple, step-by-step approach to implementing argparse in Python CLI scripts. It focuses on practical setup, argument handling, and Pythonic best practices to create robust, user-friendly tools. Designed for agents, it emphasizes modularity, clarity, and extensibility without unnecessary complexity. Refer to the official [`argparse` documentation](https://docs.python.org/3/library/argparse.html) for advanced details using Context7 or relavent MCP if needed.

## Setting Up the Parser

Start by importing argparse and creating a parser instance. This is the foundation for all CLI argument handling.

```python
import argparse
from typing import Optional

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='your_script',  # Optional: sets the program name in help
        description='A simple CLI tool for processing inputs.',
        epilog='Example: python your_script.py input.txt -o output.txt -v',
        formatter_class=argparse.RawDescriptionHelpFormatter  # Preserves epilog formatting
    )
    return parser
```

- **Description**: Briefly explains the tool's purpose.
- **Epilog**: Provides usage examples; use `RawDescriptionHelpFormatter` for multi-line formatting.
- **Pythonic Tip**: Wrap in a function for reusability and testability. Use type hints for the return value to aid IDE support.

Call `parse_args()` at the script's entry point:

```python
if __name__ == '__main__':
    args = create_parser().parse_args()
    # Process args here
```

## Adding Arguments and Groups

Build arguments progressively: positional for required inputs, optional for customization.

### Positional Arguments
Required inputs without flags.

```python
parser.add_argument('input_file', type=str, help='Path to the input file')
```

### Optional Arguments
Use flags for choices.

```python
parser.add_argument('-o', '--output', type=str, default='output.txt', help='Output file path')
parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
parser.add_argument('--config', type=str, help='Path to config file')
```

- **Type**: Specifies conversion (e.g., `int`, `str`); defaults to `str`.
- **Action**: `'store_true'` for flags; use `'store_false'` for disabling defaults.
- **Default**: Provides sensible fallbacks, reducing user input needs.
- **Help**: Always include descriptive text; agents can parse this for automation.

### Grouping Arguments
Organize related options with groups for cleaner help output.

```python
options_group = parser.add_argument_group('Processing Options')
options_group.add_argument('--template', type=str, help='Custom template path')
options_group.add_argument('--extensions', type=str, default='', help='Comma-separated extensions')

styling_group = parser.add_argument_group('Styling Options')
styling_group.add_argument('--font', type=str, default='Arial', help='Default font')
styling_group.add_argument('--size', type=int, default=12, help='Font size in points')
```

### Subparsers for Multi-Command Tools
For tools with commands (e.g., `git commit` vs. `git push`), use subparsers.

```python
subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

process_parser = subparsers.add_parser('process', help='Process a file')
process_parser.add_argument('input_file', type=str, help='Input file')

validate_parser = subparsers.add_parser('validate', help='Validate inputs')
validate_parser.add_argument('--config', type=str, required=True, help='Config to validate')
```

- **Dest**: Stores the chosen command in `args.command`.
- **Pythonic Tip**: Keep subparsers minimal; use if commands have distinct logic to avoid a flat, overwhelming parser.

Add global options like version:

```python
parser.add_argument('--version', action='version', version='%(prog)s 1.0')
```

## Validation and Post-Processing
## Standard Argument Library

To promote consistency and reusability across Python CLI scripts, adopt these suggested standard argument flags STRICTLY if the project requires any such argument. The following conventions MUST be followed at all times:

- Short flags MUST be single letters prefixed with a single hyphen (e.g., -i for input, -o for output, -v for verbose).
- Long flags MUST be descriptive phrases using double hyphens and hyphen-separated words (e.g., --input-file instead of abbreviated forms like --in).
- Short flags MUST also have a Long flag to ensure good UX in using the CLI.

While limited customization is allowed only for unavoidable project-specific needs, always prioritize strict adherence to these conventions to ensure maximum user familiarity, reduce learning curves, and maintain consistency across tools and scripts.

Use a markdown table or list in your documentation for reference. Here's a suggested set, diverge from this ONLY if the required argument is not present in this reference:

| Short Flag | Long Flag       | Description                          | Type      | Default     | Example Usage                  |
|------------|-----------------|--------------------------------------|-----------|-------------|--------------------------------|
| -i        | --input        | Path to input file or directory      | str      | None       | -i input.txt                   |
| -o        | --output       | Path to output file or directory     | str      | 'output.txt' | -o result.txt                  |
| -f        | --file         | Specify a configuration or data file | str      | None       | -f config.json                 |
| -v        | --verbose      | Enable verbose logging/output        | store_true | False     | -v                             |
| -q        | --quiet        | Suppress non-essential output        | store_true | False     | -q                             |
| -d        | --debug        | Enable debug-level logging           | store_true | False     | -d                             |
| -c        | --count        | Number of items to process           | int      | 1          | -c 10                          |
| --config  | --config-file  | Path to configuration file           | str      | None       | --config settings.yaml          |
| --dry-run | --dry-run      | Simulate actions without execution   | store_true | False     | --dry-run                      |
| -t        | --timeout      | Timeout in seconds                   | int      | 30         | -t 60                          |

### Implementation Tips
- **Short flags**: Use single hyphens (-) for brevity; assign common ones like -i, -o, -v.
- **Long flags**: Use double hyphens (--) for clarity; make them descriptive (e.g., --input-file instead of --in).
- **Conflicts**: Avoid overlaps (e.g., don't use -f for both file and force); document alternatives.
- **Groups**: Place related flags in argument groups (e.g., I/O flags together).
- **Extension**: Add domain-specific flags (e.g., --format for media tools) but reuse standards where possible.
- **Help Text**: Always include `help='Brief description'` and reference this library in your epilog.

Example integration:
```python
parser.add_argument('-i', '--input', type=str, required=True, help='Input file (standard)')
parser.add_argument('-o', '--output', type=str, default='output.txt', help='Output file (standard)')
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode (standard)')
```

After `parse_args()`, validate and transform inputs to prevent errors.

```python
def validate_args(args: argparse.Namespace) -> None:
    if not args.input_file:
        parser.error('Input file is required')
    if not args.input_file.endswith('.txt'):
        parser.error('Input must be a .txt file')
    # Check file existence
    import os
    if not os.path.exists(args.input_file):
        parser.error(f'Input file not found: {args.input_file}')

# In main
args = parser.parse_args()
validate_args(args)

# Post-process
if args.extensions:
    args.extensions = [ext.strip() for ext in args.extensions.split(',') if ext.strip()]
```

- Use `parser.error()` for user-friendly failures that print help.
- **Pythonic Tip**: Centralize validation in a function. Use `pathlib.Path` for file operations: `from pathlib import Path; if not Path(args.input_file).exists(): ...`. Handle edge cases early with `if` guards.

For config integration, load from file if provided, overriding CLI args.

## Best Practices (Pythonic)

Follow these to write clean, maintainable code:

1. **Modularity**: Encapsulate parser creation in a function. Return a typed dataclass or `dataclasses.dataclass` for args:
   ```python
   from dataclasses import dataclass
   from typing import List

   @dataclass
   class Args:
       input_file: str
       output: Optional[str] = None
       extensions: List[str] = None

   def parse_args() -> Args:
       # ... parser setup ...
       raw_args = parser.parse_args()
       return Args(
           input_file=raw_args.input_file,
           output=raw_args.output,
           extensions=raw_args.extensions.split(',') if raw_args.extensions else []
       )
   ```

2. **Defaults and Sensible Fallbacks**: Always set `default` values. Use environment variables for overrides:
   ```python
   import os
   parser.add_argument('--output', default=os.getenv('DEFAULT_OUTPUT', 'output.txt'))
   ```

3. **Type Safety**: Use `type` parameters and hints. For choices, use `choices=['opt1', 'opt2']` or enums:
   ```python
   from enum import Enum

   class Mode(Enum):
       PROCESS = 'process'
       VALIDATE = 'validate'

   parser.add_argument('--mode', type=Mode, choices=list(Mode), default=Mode.PROCESS)
   ```

4. **Error Handling**: Prefer `parser.error()` over exceptions for CLI misuse. Log issues with `logging` module, adjusting level via `--verbose`.

5. **Help Clarity**: Use `metavar` for complex args (e.g., `metavar='H1:24,H2:18'`). Keep descriptions concise.

6. **Simplicity**: Start simple; add subparsers/groups only when needed. Test with `argparse` in unit tests using `parse_known_args()`.

7. **Extensibility**: Design for future additions, e.g., support JSON configs via `argparse.FileType('r')`.

## Examples

### Basic Single-Command Script

```python
#!/usr/bin/env python3
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Simple file processor')
    parser.add_argument('input_file', type=Path, help='Input file')
    parser.add_argument('-o', '--output', type=Path, help='Output file')
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()
    if not args.input_file.exists():
        parser.error(f'File not found: {args.input_file}')

    output = args.output or args.input_file.with_suffix('.out')
    # Process logic here
    print(f'Processing {args.input_file} to {output}')
    if args.verbose:
        print('Verbose mode enabled')

if __name__ == '__main__':
    main()
```

Run: `python script.py input.txt -o result.out -v`

### Multi-Command with Groups

```python
#!/usr/bin/env python3
import argparse
from typing import Optional
from enum import Enum

class Command(Enum):
    PROCESS = 'process'
    VALIDATE = 'validate'

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Multi-command CLI tool')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Process command
    proc = subparsers.add_parser('process', help='Process files')
    proc.add_argument('input_file', type=str, help='Input file')
    proc.add_argument('-o', '--output', type=str, default='output.txt')

    group = proc.add_argument_group('Options')
    group.add_argument('--mode', type=Command, default=Command.PROCESS)

    # Validate command
    val = subparsers.add_parser('validate', help='Validate config')
    val.add_argument('--config', type=str, required=True)

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()
    if args.command == 'process':
        print(f'Processing {args.input_file} to {args.output} in {args.mode.value} mode')
    elif args.command == 'validate':
        print(f'Validating {args.config}')

if __name__ == '__main__':
    main()
```

Run: `python script.py process input.txt` or `python script.py validate --config config.json`

## Final Tips

- **Test Thoroughly**: Use `python -m unittest` with mock args to verify parsing.
- **Keep It Agent-Friendly**: Ensure help output is parseable; avoid ambiguity.
- **Scale Gradually**: Begin with basics; refactor to subparsers as commands grow.
- **Resources**: Study [`argparse` tutorial](https://docs.python.org/3/howto/argparse.html) for patterns. For complex CLIs, consider `click` or `typer` as alternatives.

This guide equips agents to build effective CLI interfaces efficiently.
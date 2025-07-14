import os
from pathlib import Path

INCLUSION_EXTENSION = {
    "py",
    "js",
    "html",
    "md"
}


def should_process_file(file_path: Path) -> bool:
    """Check if a file should be processed based on its extension."""
    return file_path.suffix[1:] in INCLUSION_EXTENSION  # [1:] to remove the dot

def main():
    output_path = Path('0_allpyfiles.ignore')
    output_path.write_text('# REFERENCE DUMP FOR ALL PY FILES. \n')

    for root, _, files in os.walk(os.getcwd()):
        for filename in files:
            file_path = Path(root) / filename

            if should_process_file(file_path):
               if 'env' not in str(file_path):
                   if '.git' not in str(file_path):
                        try:
                            content = file_path.read_text(encoding='utf-8')
                            with output_path.open('a', encoding='utf-8') as wfile:
                                wfile.write(f"## {filename}")
                                wfile.write(f'\n{content}')
                                wfile.write('\n--- \n')
                        except (UnicodeDecodeError, PermissionError) as e:
                            print(f"Skipping {file_path} due to error: {e}")

if __name__ == "__main__":
    main()

from flask import Flask, send_file, abort, render_template, request, jsonify, after_this_request
from markupsafe import escape
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import zipfile
import shutil
import atexit
import tempfile
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB limit

# Configuration
# SERVE_FOLDER = Path(r'/Users/harish-5102/Downloads/Movie2Delete').resolve()
SERVE_FOLDER = Path(r'serveFolder').resolve()
TEMP_DIR = Path('temp_zips').resolve()
UPLOAD_FOLDER = SERVE_FOLDER
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.jpg', '.jpeg', '.png', '.zip', '.csv', '.json', '.md'}

# Create directories if they don't exist
for folder in [SERVE_FOLDER, TEMP_DIR]:
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # If we cannot create the directory, logging is not yet configured below, so print
        print(f"Failed creating folder {folder}: {e}")

# Logging setup: file + stdout, rotate logs
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'app.log'
handler = RotatingFileHandler(str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Also print to console
console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.DEBUG)
app.logger.addHandler(console)

app.logger.info(f"Starting app. SERVE_FOLDER={SERVE_FOLDER}, TEMP_DIR={TEMP_DIR}, UPLOAD_FOLDER={UPLOAD_FOLDER}")
app.logger.info(f"Allowed extensions: {ALLOWED_EXTENSIONS}")

# Cleanup function
atexit.register(lambda: shutil.rmtree(TEMP_DIR, ignore_errors=True))

def zip_folder(folder_path, zip_path):
    app.logger.info(f"Zipping folder {folder_path} -> {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file
                # arcname relative to the folder being zipped, not the parent
                arcname = file_path.relative_to(folder_path)
                zipf.write(file_path, arcname)

def get_file_tree(base_path, current_path=None, depth=0):
    current_path = current_path or base_path
    file_tree = []
    try:
        for item in sorted(os.listdir(current_path)):
            full_path = current_path / item
            relative_path = full_path.relative_to(base_path)
            if full_path.is_dir():
                file_tree.append({
                    'name': item,
                    'path': str(relative_path),
                    'type': 'directory',
                    'depth': depth,
                    'children': get_file_tree(base_path, full_path, depth + 1)
                })
            else:
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    size = None
                file_tree.append({
                    'name': item,
                    'path': str(relative_path),
                    'type': 'file',
                    'size': size,
                    'depth': depth
                })
    except (FileNotFoundError, PermissionError) as e:
        app.logger.warning(f"get_file_tree error for {current_path}: {e}")
    except Exception as e:
        app.logger.exception(f"Unexpected error in get_file_tree for {current_path}: {e}")
    return file_tree

def is_allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def safe_resolve_join(base: Path, *parts) -> Path:
    """
    Join parts onto base, resolve, and ensure resulting path is under base.
    Returns resolved path or raises ValueError.
    """
    candidate = (base.joinpath(*parts)).resolve()
    base_resolved = base.resolve()
    try:
        # Convert both sides to strings for consistent comparison across platforms
        if not str(candidate).startswith(str(base_resolved)):
            raise ValueError(f"Resolved path {candidate} is outside of base {base_resolved}")
    except Exception as e:
        raise
    return candidate

@app.route('/')
def list_files():
    try:
        file_tree = get_file_tree(SERVE_FOLDER)
        app.logger.info("Serving file browser root")
        return render_template('browser.html', files=file_tree, root_path=SERVE_FOLDER.name)
    except FileNotFoundError:
        app.logger.error(f"Directory not found: {SERVE_FOLDER}")
        return render_template('error.html', message=f"Directory '{SERVE_FOLDER}' not found."), 404
    except Exception as e:
        app.logger.exception("Unhandled error listing files")
        return render_template('error.html', message=str(e)), 500

@app.route('/files/<path:filename>')
def serve_file(filename):
    try:
        filepath = (SERVE_FOLDER / filename).resolve()
        app.logger.info(f"Request for file: {filename} -> {filepath}")
        if not str(filepath).startswith(str(SERVE_FOLDER.resolve())):
            app.logger.warning(f"Forbidden file access attempt: {filepath}")
            abort(403)
        if filepath.is_file():
            return send_file(filepath)
        app.logger.warning(f"File not found: {filepath}")
        abort(404)
    except Exception as e:
        app.logger.exception(f"Error serving file {filename}: {e}")
        abort(500)

@app.route('/download-folder/<path:foldername>')
def download_folder(foldername):
    try:
        folderpath = (SERVE_FOLDER / foldername).resolve()
        app.logger.info(f"Download request for folder: {foldername} -> {folderpath}")
        if not str(folderpath).startswith(str(SERVE_FOLDER.resolve())):
            app.logger.warning(f"Forbidden folder access attempt: {folderpath}")
            abort(403)
        if not folderpath.is_dir():
            app.logger.warning(f"Folder not found for download: {folderpath}")
            abort(404, "Folder not found")

        zip_filename = f"{folderpath.name}.zip"
        zip_path = TEMP_DIR / zip_filename
        zip_folder(folderpath, zip_path)

        @after_this_request
        def cleanup(response):
            try:
                if zip_path.exists():
                    os.unlink(zip_path)
                    app.logger.info(f"Removed temporary zip {zip_path}")
            except Exception as e:
                app.logger.error(f"Cleanup failed: {e}")
            return response

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

    except Exception as e:
        app.logger.exception(f"Error creating zip for {foldername}: {e}")
        if 'zip_path' in locals() and zip_path.exists():
            try:
                os.unlink(zip_path)
            except Exception:
                pass
        abort(500, f"Error creating zip file: {str(e)}")


@app.route('/upload', methods=['POST'])
def handle_upload():
    requested_target = request.form.get('path', '').strip()
    app.logger.info(f"Upload request received. form.path={requested_target}. Files keys: {list(request.files.keys())}")
    
    results = []
    errors = []
    
    try:
        target_path = safe_resolve_join(Path(UPLOAD_FOLDER), requested_target)
    except Exception as e:
        error_msg = f'Invalid target path "{requested_target}": {str(e)}'
        app.logger.warning(f"Invalid target path provided: {requested_target} | err={e}")
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'files': [],
            'errors': [{'file': 'path', 'message': error_msg, 'type': 'error'}]
        }), 200

    if not str(target_path).startswith(str(Path(UPLOAD_FOLDER).resolve())):
        error_msg = f'Security violation: Path "{requested_target}" is outside allowed directory'
        app.logger.warning(f"Path check failed: target_path={target_path} not under upload folder {UPLOAD_FOLDER}")
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'files': [],
            'errors': [{'file': 'path', 'message': error_msg, 'type': 'error'}]
        }), 200

    if not request.files:
        app.logger.info("No files in request")
        return jsonify({
            'status': 'success',
            'message': 'No files were provided.',
            'files': [],
            'errors': []
        }), 200

    for file_key in request.files:
        file = request.files[file_key]
        original_filename = file.filename or ''
        
        if not file or not original_filename:
            error_msg = 'No file object or empty filename'
            app.logger.warning(f"No file object or empty filename for key {file_key}")
            errors.append({
                'file': file_key, 
                'message': error_msg, 
                'type': 'error'
            })
            continue

        filename = secure_filename(original_filename)
        
        # Check if secure_filename changed the name significantly
        if not filename:
            error_msg = f'Filename "{original_filename}" contains only invalid characters'
            app.logger.info(f"Filename became empty after secure_filename: {original_filename}")
            errors.append({
                'file': original_filename, 
                'message': error_msg, 
                'type': 'error'
            })
            continue
        
        if not is_allowed_file(filename):
            allowed_exts = ', '.join(sorted(ALLOWED_EXTENSIONS))
            error_msg = f'File extension not allowed. Allowed extensions: {allowed_exts}'
            app.logger.info(f"Rejected file due to disallowed extension: {filename}")
            errors.append({
                'file': filename, 
                'message': error_msg, 
                'type': 'warning'
            })
            continue

        relative_path = request.form.get(f'{file_key}_path', '').strip()
        
        try:
            full_path = safe_resolve_join(target_path, relative_path)
            full_path.mkdir(parents=True, exist_ok=True)
            save_path = full_path / filename
            
            # Check if file already exists
            if save_path.exists():
                app.logger.warning(f"File already exists, will overwrite: {save_path}")
            
            # Use a more robust temporary file approach
            with tempfile.NamedTemporaryFile(
                prefix=f"{filename}.", 
                dir=str(full_path), 
                delete=False,
                mode='wb'
            ) as tmpf:
                tmp_name = Path(tmpf.name)
                
                try:
                    file.stream.seek(0)
                    chunk_size = 8192
                    total_written = 0
                    
                    while True:
                        chunk = file.stream.read(chunk_size)
                        if not chunk:
                            break
                        tmpf.write(chunk)
                        total_written += len(chunk)
                    
                    tmpf.flush()
                    os.fsync(tmpf.fileno())
                    
                except Exception as write_error:
                    # Clean up temp file on write error
                    try:
                        tmp_name.unlink(missing_ok=True)
                    except:
                        pass
                    raise write_error

            # Atomic move to final location
            try:
                os.replace(str(tmp_name), str(save_path))
                size = os.path.getsize(save_path)
                
                results.append({
                    'name': filename,
                    'path': str(save_path.relative_to(UPLOAD_FOLDER)),
                    'size': size
                })
                
                app.logger.info(f"Saved file: {save_path} ({size} bytes)")
                
            except Exception as move_error:
                # Clean up temp file if move fails
                try:
                    tmp_name.unlink(missing_ok=True)
                except:
                    pass
                raise move_error
                
        except PermissionError as e:
            error_msg = f'Permission denied: {str(e)}'
            app.logger.error(f"Permission error saving {filename}: {e}")
            errors.append({
                'file': filename, 
                'message': error_msg, 
                'type': 'error'
            })
            
        except OSError as e:
            error_msg = f'File system error: {str(e)}'
            app.logger.error(f"OS error saving {filename}: {e}")
            errors.append({
                'file': filename, 
                'message': error_msg, 
                'type': 'error'
            })
            
        except Exception as e:
            error_msg = f'Unexpected error: {str(e)}'
            app.logger.exception(f"Unexpected error saving file {filename}: {e}")
            errors.append({
                'file': filename, 
                'message': error_msg, 
                'type': 'error'
            })

    # Determine final status and message
    total_files = len(request.files)
    successful_files = len(results)
    failed_files = len([e for e in errors if e['type'] == 'error'])
    warning_files = len([e for e in errors if e['type'] == 'warning'])
    
    if failed_files == 0 and warning_files == 0:
        final_status = 'success'
        message = f'All {successful_files} file(s) uploaded successfully.'
    elif successful_files == 0:
        final_status = 'error'
        message = f'All {total_files} file(s) failed to upload.'
    else:
        final_status = 'warning'
        message = f'{successful_files} file(s) uploaded successfully, {failed_files} failed, {warning_files} skipped.'

    app.logger.info(f"Upload completed - Status: {final_status}, Success: {successful_files}, Errors: {failed_files}, Warnings: {warning_files}")

    return jsonify({
        'status': final_status,
        'message': message,
        'files': results,
        'errors': errors
    }), 200
if __name__ == '__main__':
    try:
        app.run(debug=True, host="0.0.0.0", port=8000)
    except Exception as e:
        app.logger.exception(f"App failed to start: {e}")
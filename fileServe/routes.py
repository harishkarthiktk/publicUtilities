from flask import send_file, abort, render_template, request, jsonify, after_this_request, Blueprint, current_app, Response
import mimetypes
from markupsafe import escape
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import zipfile
import shutil
import tempfile
from core_auth import auth

bp = Blueprint('main', __name__, template_folder='templates')


def zip_folder(folder_path, zip_path):
    """
    Create a ZIP file of the folder contents, using relative paths to SERVE_FOLDER.
    """
    current_app.logger.info(f"Zipping folder {folder_path} -> {zip_path}")
    serve_folder = current_app.config['SERVE_FOLDER']
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file
                # arcname relative to SERVE_FOLDER to include folder name
                arcname = str(file_path.relative_to(serve_folder))
                zipf.write(file_path, arcname)


def get_file_tree(base_path, current_path=None, depth=0):
    """
    Recursively build a file tree dictionary with names, paths, types, sizes, and children.
    """
    current_path = current_path or base_path
    file_tree = []
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
    return file_tree


def is_allowed_file(filename):
    """
    Check if the file extension is allowed.
    """
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return Path(filename).suffix.lower() in allowed_extensions


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


@bp.route('/')
@auth.login_required
def list_files():
    try:
        serve_folder = current_app.config['SERVE_FOLDER']
        if not serve_folder.exists():
            raise FileNotFoundError(f"Directory not found: {serve_folder}")
        file_tree = get_file_tree(serve_folder)
        current_app.logger.info("Serving file browser root")
        return render_template('browser.html', files=file_tree, root_path=serve_folder.name)
    except FileNotFoundError:
        current_app.logger.error(f"Directory not found: {serve_folder}")
        return render_template('error.html', message=f"Directory '{serve_folder}' not found."), 404
    except Exception as e:
        current_app.logger.exception("Unhandled error listing files")
        return render_template('error.html', message=str(e)), 500


@bp.route('/files/<path:filename>')
@auth.login_required
def serve_file(filename):
    try:
        serve_folder = current_app.config['SERVE_FOLDER']
        filepath = (serve_folder / filename).resolve()
    except Exception as e:
        current_app.logger.exception(f"Error resolving path for {filename}: {e}")
        abort(500)

    current_app.logger.info(f"Request for file: {filename} -> {filepath}")
    if not str(filepath).startswith(str(serve_folder.resolve())):
        current_app.logger.warning(f"Forbidden file access attempt: {filepath}")
        abort(403)

    if not filepath.is_file():
        current_app.logger.warning(f"File not found: {filepath}")
        abort(404)

    # Use X-Accel-Redirect for Nginx to serve the file efficiently
    response = Response(status=200)
    response.headers['X-Accel-Redirect'] = f"/internal-files/{filename}"
    
    # Set content headers (Nginx will use these)
    content_type, _ = mimetypes.guess_type(str(filepath))
    if content_type:
        response.headers['Content-Type'] = content_type
    else:
        response.headers['Content-Type'] = 'application/octet-stream'
    
    response.headers['Content-Disposition'] = f'attachment; filename="{Path(filename).name}"'
    response.headers['Content-Length'] = str(filepath.stat().st_size)
    
    current_app.logger.info(f"X-Accel-Redirect issued for {filename}")
    return response


@bp.route('/download-folder/<path:foldername>')
@auth.login_required
def download_folder(foldername):
    try:
        serve_folder = current_app.config['SERVE_FOLDER']
        folderpath = (serve_folder / foldername).resolve()
    except Exception as e:
        current_app.logger.exception(f"Error resolving path for {foldername}: {e}")
        abort(500)

    current_app.logger.info(f"Download request for folder: {foldername} -> {folderpath}")
    if not str(folderpath).startswith(str(serve_folder.resolve())):
        current_app.logger.warning(f"Forbidden folder access attempt: {folderpath}")
        abort(403)

    if not folderpath.is_dir():
        current_app.logger.warning(f"Folder not found for download: {folderpath}")
        abort(404, "Folder not found")

    try:
        zip_filename = f"{folderpath.name}.zip"
        temp_dir = current_app.config['TEMP_DIR']
        zip_path = temp_dir / zip_filename
        zip_folder(folderpath, zip_path)

        @after_this_request
        def cleanup(response):
            try:
                if zip_path.exists():
                    os.unlink(zip_path)
                    current_app.logger.info(f"Removed temporary zip {zip_path}")
            except Exception as e:
                current_app.logger.error(f"Cleanup failed: {e}")
            return response

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
    except Exception as e:
        current_app.logger.exception(f"Error creating zip for {foldername}: {e}")
        if 'zip_path' in locals() and zip_path.exists():
            try:
                os.unlink(zip_path)
            except Exception:
                pass
        abort(500, f"Error creating zip file: {str(e)}")


@bp.route('/upload', methods=['POST'])
@auth.login_required
def handle_upload():
    requested_target = request.form.get('path', '').strip()
    current_app.logger.info(f"Upload request received. form.path={requested_target}. Files keys: {list(request.files.keys())}")

    results = []
    errors = []

    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        target_path = safe_resolve_join(Path(upload_folder), requested_target)
    except Exception as e:
        error_msg = f'Invalid target path "{requested_target}": {str(e)}'
        current_app.logger.warning(f"Invalid target path provided: {requested_target} | err={e}")
        abort(403, error_msg)

    if not str(target_path).startswith(str(Path(upload_folder).resolve())):
        error_msg = f'Security violation: Path "{requested_target}" is outside allowed directory'
        current_app.logger.warning(f"Path check failed: target_path={target_path} not under upload folder {upload_folder}")
        abort(403, error_msg)

    if not request.files:
        current_app.logger.info("No files in request")
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
            current_app.logger.warning(f"No file object or empty filename for key {file_key}")
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
            current_app.logger.info(f"Filename became empty after secure_filename: {original_filename}")
            errors.append({
                'file': original_filename,
                'message': error_msg,
                'type': 'error'
            })
            continue

        if not is_allowed_file(filename):
            allowed_exts = ', '.join(sorted(current_app.config['ALLOWED_EXTENSIONS']))
            error_msg = f'File extension not allowed. Allowed extensions: {allowed_exts}'
            current_app.logger.info(f"Rejected file due to disallowed extension: {filename}")
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
                current_app.logger.warning(f"File already exists, will overwrite: {save_path}")

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
                    'path': str(save_path.relative_to(upload_folder)),
                    'size': size
                })

                current_app.logger.info(f"Saved file: {save_path} ({size} bytes)")

            except Exception as move_error:
                # Clean up temp file if move fails
                try:
                    tmp_name.unlink(missing_ok=True)
                except:
                    pass
                raise move_error

        except PermissionError as e:
            error_msg = f'Permission denied: {str(e)}'
            current_app.logger.error(f"Permission error saving {filename}: {e}")
            errors.append({
                'file': filename,
                'message': error_msg,
                'type': 'error'
            })

        except OSError as e:
            error_msg = f'File system error: {str(e)}'
            current_app.logger.error(f"OS error saving {filename}: {e}")
            errors.append({
                'file': filename,
                'message': error_msg,
                'type': 'error'
            })

        except Exception as e:
            error_msg = f'Unexpected error: {str(e)}'
            current_app.logger.exception(f"Unexpected error saving file {filename}: {e}")
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

    current_app.logger.info(f"Upload completed - Status: {final_status}, Success: {successful_files}, Errors: {failed_files}, Warnings: {warning_files}")

    return jsonify({
        'status': final_status,
        'message': message,
        'files': results,
        'errors': errors
    }), 200


def register_routes(app):
    """
    Register the blueprint and set configuration values.
    """
    app.register_blueprint(bp)
    app.config['ALLOWED_EXTENSIONS'] = {'.txt', '.pdf', '.jpg', '.jpeg', '.png', '.zip', '.csv', '.json', '.md'}
    app.config['SERVE_FOLDER'] = Path('serveFolder').resolve()
    app.config['TEMP_DIR'] = Path('temp_zips').resolve()
    app.config['UPLOAD_FOLDER'] = app.config['SERVE_FOLDER']
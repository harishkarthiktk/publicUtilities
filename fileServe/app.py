from flask import Flask, send_file, abort, render_template, request, jsonify, after_this_request
from markupsafe import escape
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import zipfile
import shutil
import atexit

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB limit

# Configuration
# SERVE_FOLDER = Path(r'/Users/harish-5102/Downloads/Movie2Delete').resolve()
SERVE_FOLDER = Path(r'serveFolder').resolve()
TEMP_DIR = Path('temp_zips')
UPLOAD_FOLDER = SERVE_FOLDER
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.jpg', '.jpeg', '.png', '.zip', '.csv', '.json', '.md'}

# Create directories if they don't exist
for folder in [SERVE_FOLDER, TEMP_DIR]:
    folder.mkdir(exist_ok=True)

# Cleanup function
atexit.register(lambda: shutil.rmtree(TEMP_DIR, ignore_errors=True))

def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(folder_path.parent)
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
                file_tree.append({
                    'name': item,
                    'path': str(relative_path),
                    'type': 'file',
                    'size': os.path.getsize(full_path),
                    'depth': depth
                })
    except (FileNotFoundError, PermissionError):
        pass
    return file_tree

def is_allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

@app.route('/')
def list_files():
    try:
        file_tree = get_file_tree(SERVE_FOLDER)
        return render_template('browser.html', files=file_tree, root_path=SERVE_FOLDER.name)
    except FileNotFoundError:
        return render_template('error.html', message=f"Directory '{SERVE_FOLDER}' not found."), 404

@app.route('/files/<path:filename>')
def serve_file(filename):
    filepath = (SERVE_FOLDER / filename).resolve()
    if not str(filepath).startswith(str(SERVE_FOLDER)):
        abort(403)
    if filepath.is_file():
        return send_file(filepath)
    abort(404)

@app.route('/download-folder/<path:foldername>')
def download_folder(foldername):
    folderpath = (SERVE_FOLDER / foldername).resolve()
    if not str(folderpath).startswith(str(SERVE_FOLDER)):
        abort(403)
    if not folderpath.is_dir():
        abort(404, "Folder not found")

    try:
        zip_filename = f"{folderpath.name}.zip"
        zip_path = TEMP_DIR / zip_filename
        zip_folder(folderpath, zip_path)

        @after_this_request
        def cleanup(response):
            try:
                if zip_path.exists():
                    os.unlink(zip_path)
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
        if 'zip_path' in locals() and zip_path.exists():
            try:
                os.unlink(zip_path)
            except Exception:
                pass
        abort(500, f"Error creating zip file: {str(e)}")

@app.route('/upload', methods=['POST'])
def handle_upload():
    target_path = request.form.get('path', '')
    target_path = (Path(UPLOAD_FOLDER) / target_path).resolve()

    try:
        if not str(target_path).startswith(str(Path(UPLOAD_FOLDER).resolve())):
            return jsonify({'error': 'Invalid path'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    results = []
    for file_key in request.files:
        file = request.files[file_key]
        relative_path = request.form.get(f'{file_key}_path', '')
        filename = secure_filename(file.filename)
        full_path = target_path / relative_path
        full_path.mkdir(parents=True, exist_ok=True)
        save_path = full_path / filename

        if not is_allowed_file(filename):
            continue

        file.save(save_path)
        results.append({
            'name': filename,
            'path': str(save_path.relative_to(UPLOAD_FOLDER)),
            'size': os.path.getsize(save_path)
        })

    return jsonify({'success': True, 'files': results})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)

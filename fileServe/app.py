from flask import Flask, send_file, abort
from markupsafe import escape
import os

app = Flask(__name__)

SERVE_FOLDER = 'serveFolder'

@app.route('/')
def list_files():
    try:
        files = [f for f in os.listdir(SERVE_FOLDER) if os.path.isfile(os.path.join(SERVE_FOLDER, f))]
    except FileNotFoundError:
        return f"Directory '{SERVE_FOLDER}' not found.", 404

    links = [f"<a href='/files/{escape(f)}'>{escape(f)}</a>" for f in files]
    return "<br>".join(links)

@app.route('/files/<path:filename>')
def serve_file(filename):
    filepath = os.path.join(SERVE_FOLDER, filename)

    abs_serve_folder = os.path.abspath(SERVE_FOLDER)
    abs_filepath = os.path.abspath(filepath)
    if not abs_filepath.startswith(abs_serve_folder):
        abort(403)

    if os.path.isfile(filepath):
        return send_file(filepath)
    else:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)

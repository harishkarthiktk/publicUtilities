import logging
from logging.handlers import RotatingFileHandler

flask_app = Flask(__name__)

# Configure file-based logging
log_file = 'logs/app.log'
file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024 * 100, backupCount=20)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
flask_app.logger.addHandler(file_handler)

# Configure console logging
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
console.setLevel(logging.DEBUG)
flask_app.logger.addHandler(console)

# Set the overall logging level
flask_app.logger.setLevel(logging.DEBUG)


    flask_app = Flask(__name__)
    flask_app.config['MAX_CONTENT_LENGTH'] = config.get('max_content_length', 5 * 1024 * 1024 * 1024)  # Default 5GB


    # Load constants from config
    SERVE_FOLDER = Path(config['serve_folder']).resolve()
    TEMP_DIR = Path(config['temp_dir']).resolve()
    UPLOAD_FOLDER = Path(config['upload_folder']).resolve()
    ALLOWED_EXTENSIONS = set(config['allowed_extensions'])

    # Create directories if they don't exist
    for folder in [SERVE_FOLDER, TEMP_DIR]:
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed creating folder {folder}: {e}")

    # Logging setup: file + stdout, rotate logs
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'app.log'
    handler = RotatingFileHandler(str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    flask_app.logger.addHandler(handler)
    flask_app.logger.setLevel(logging.INFO)

    # Also print to console
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.DEBUG)
    flask_app.logger.addHandler(console)

    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        flask_app.logger.info(f"Starting app. SERVE_FOLDER={SERVE_FOLDER}, TEMP_DIR={TEMP_DIR}, UPLOAD_FOLDER={UPLOAD_FOLDER}")
        flask_app.logger.info(f"Allowed extensions: {ALLOWED_EXTENSIONS}")

    # Pass config to app for use in routes
    flask_app.config['SERVE_FOLDER'] = SERVE_FOLDER
    flask_app.config['TEMP_DIR'] = TEMP_DIR
    flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    flask_app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

    # Register routes
    register_routes(flask_app)

    # Cleanup function
    atexit.register(lambda: shutil.rmtree(TEMP_DIR, ignore_errors=True))

    return flask_app


app = create_app()

if __name__ == '__main__':
    pass
    # Comment out for Gunicorn/Nginx deployment
    # try:
    #     app.run(debug=True, host="0.0.0.0", port=8000)
    # except Exception as e:
    #     app.logger.exception(f"App failed to start: {e}")
    # For dev testing without Gunicorn, uncomment above
    #
    # To start using Gunicorn (for production deployment):
    # gunicorn -w 4 -b 0.0.0.0:8002 app:app
    #
    # To start using Waitress (for production deployment):
    # waitress-serve --host=0.0.0.0 --port=8000 --threads=4 app:app
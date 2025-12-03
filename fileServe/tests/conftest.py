import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import tempfile
import yaml
from pathlib import Path
from app import create_app

@pytest.fixture
def client():
    """Create a test client for the app."""
    app = create_app()
    with app.test_client() as client:
        yield client

@pytest.fixture
def temp_users_yaml(tmp_path):
    """Fixture to create a temporary users.yaml file with sample users."""
    users_file = tmp_path / "users.yaml"
    users_data = {
        "users": {
            "testuser": "testpass",
            "admin": "adminpass"
        }
    }
    with open(users_file, "w") as f:
        yaml.dump(users_data, f)
    # Set env to use this temp file
    os.environ["BASIC_AUTH_USERS_FILE"] = str(users_file)
    yield users_file
    # Cleanup
    if "BASIC_AUTH_USERS_FILE" in os.environ:
        del os.environ["BASIC_AUTH_USERS_FILE"]

@pytest.fixture
def temp_serve_folder(tmp_path):
    """Create a temporary serve folder with sample files for testing."""
    serve_folder = tmp_path / "serveFolder"
    serve_folder.mkdir()
    
    # Create sample files
    (serve_folder / "sample.txt").write_text("Hello, World!")
    (serve_folder / "sample.jpg").write_bytes(b"fake image data")
    
    # Create a subdir
    subdir = serve_folder / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("Nested file")
    
    # Set env or config if needed, but app uses config.yaml which points to 'serveFolder'
    # For tests, we'll override app config in specific tests
    yield serve_folder

@pytest.fixture
def temp_upload_folder(tmp_path):
    """Temporary upload folder."""
    upload_folder = tmp_path / "uploadFolder"
    upload_folder.mkdir()
    yield upload_folder

@pytest.fixture
def temp_temp_dir(tmp_path):
    """Temporary dir for zips."""
    temp_dir = tmp_path / "temp_zips"
    temp_dir.mkdir()
    yield temp_dir
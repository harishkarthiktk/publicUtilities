import io
import os
import zipfile
import pytest
from pathlib import Path
import base64
import yaml
import textwrap
from unittest.mock import patch
import builtins


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Set auth env vars for tests
    monkeypatch.setenv('BASIC_AUTH_USER', 'testuser')
    monkeypatch.setenv('BASIC_AUTH_PASSWORD', 'testpass')

    # Create test config dict
    test_config = {
        'serve_folder': str(tmp_path / "serveFolder"),
        'temp_dir': str(tmp_path / "temp_zips"),
        'upload_folder': str(tmp_path / "serveFolder"),
        'allowed_extensions': ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.zip', '.csv', '.json', '.md'],
        'max_content_length': 1024 * 1024  # 1MB for tests
    }

    # Create directories
    serve_folder = tmp_path / "serveFolder"
    temp_dir = tmp_path / "temp_zips"
    serve_folder.mkdir()
    temp_dir.mkdir()

    # Mock open for config.yaml to return test config
    original_open = builtins.open
    def mock_open(filename, mode='r', *args, **kwargs):
        if filename == 'config.yaml':
            f = io.StringIO(yaml.dump(test_config))
            f.name = filename
            return f
        return original_open(filename, mode, *args, **kwargs)

    with patch('builtins.open', mock_open):
        from app import create_app
        test_app = create_app()
        from core_auth import auth, verify_password
        auth.verify_password = verify_password
        test_app.config['TESTING'] = True
        test_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests if needed

        with test_app.test_client() as client:
            yield client


def test_homepage_unauthorized(client):
    res = client.get("/")
    assert res.status_code == 401


def test_homepage_authorized(client):
    test_file = Path(client.application.config['SERVE_FOLDER']) / "example.txt"
    test_file.write_text("sample content")

    res = client.get("/", auth=('testuser', 'testpass'))
    assert res.status_code == 200
    assert b"example.txt" in res.data


def test_valid_file_download_unauthorized(client):
    f = Path(client.application.config['SERVE_FOLDER']) / "test.txt"
    f.write_text("hello")
    res = client.get("/files/test.txt")
    assert res.status_code == 401


def test_valid_file_download_authorized(client):
    f = Path(client.application.config['SERVE_FOLDER']) / "test.txt"
    f.write_text("hello")
    res = client.get("/files/test.txt", auth=('testuser', 'testpass'))
    assert res.status_code == 200
    assert res.data == b"hello"


def test_invalid_file_path_authorized(client):
    res = client.get("/files/../../etc/passwd", auth=('testuser', 'testpass'))
    assert res.status_code == 403


def test_file_not_found_authorized(client):
    res = client.get("/files/missing.txt", auth=('testuser', 'testpass'))
    assert res.status_code == 404


def test_folder_download_as_zip(client):
    folder = Path(client.application.config['SERVE_FOLDER']) / "dir"
    folder.mkdir()
    (folder / "a.txt").write_text("data")

    res = client.get("/download-folder/dir", auth=('testuser', 'testpass'))
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/zip'

    with zipfile.ZipFile(io.BytesIO(res.data)) as z:
        assert "dir/a.txt" in z.namelist()


def test_download_nonexistent_folder_authorized(client):
    res = client.get("/download-folder/ghost", auth=('testuser', 'testpass'))
    assert res.status_code == 404


def test_file_upload_authorized(client):
    data = {
        'path': '',
        'file_0': (io.BytesIO(b"test upload"), 'uploaded.txt'),
        'file_0_path': ''
    }
    res = client.post("/upload", data=data, content_type='multipart/form-data', auth=('testuser', 'testpass'))
    assert res.status_code == 200

    saved = Path(client.application.config['SERVE_FOLDER']) / "uploaded.txt"
    assert saved.exists()
    assert saved.read_text() == "test upload"


def test_upload_invalid_path_authorized(client):
    data = {
        'path': '../outside',
        'file_0': (io.BytesIO(b"hack"), 'hack.txt'),
        'file_0_path': ''
    }
    res = client.post("/upload", data=data, content_type='multipart/form-data', auth=('testuser', 'testpass'))
    assert res.status_code == 403


def test_yaml_auth_success(client, monkeypatch):
    def mock_load_yaml_users():
        return {'yamluser': 'ymlpass', 'another': 'anotherpass'}

    monkeypatch.setattr('core_auth.load_yaml_users', mock_load_yaml_users)

    # Test successful login with YAML user
    res = client.get("/", auth=('yamluser', 'ymlpass'))
    assert res.status_code == 200


def test_yaml_auth_unauthorized(client, monkeypatch):
    def mock_load_yaml_users():
        return {'yamluser': 'ymlpass'}

    monkeypatch.setattr('core_auth.load_yaml_users', mock_load_yaml_users)

    res = client.get("/", auth=('yamluser', 'wrongpass'))
    assert res.status_code == 401


def test_yaml_auth_failure_but_env_fallback(client, monkeypatch):
    def mock_load_yaml_users():
        return {'yamluser': 'ymlpass'}

    monkeypatch.setattr('core_auth.load_yaml_users', mock_load_yaml_users)

    # Login with env user should succeed via fallback
    res = client.get("/", auth=('testuser', 'testpass'))
    assert res.status_code == 200

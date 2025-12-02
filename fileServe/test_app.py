import io
import os
import zipfile
import pytest
from pathlib import Path
import app
import base64
import textwrap

@pytest.fixture
def client(tmp_path, monkeypatch):
    # Create isolated folders
    serve_folder = tmp_path / "serveFolder"
    temp_dir = tmp_path / "temp_zips"
    serve_folder.mkdir()
    temp_dir.mkdir()

    # Set auth env vars for tests
    monkeypatch.setenv('BASIC_AUTH_USER', 'testuser')
    monkeypatch.setenv('BASIC_AUTH_PASSWORD', 'testpass')

    # Patch globals in app
    app.SERVE_FOLDER = serve_folder.resolve()
    app.UPLOAD_FOLDER = app.SERVE_FOLDER
    app.TEMP_DIR = temp_dir.resolve()

    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client

def test_homepage_unauthorized(client):
    res = client.get("/")
    assert res.status_code == 401

def test_homepage_authorized(client):
    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    test_file = Path(app.SERVE_FOLDER) / "example.txt"
    test_file.write_text("sample content")

    res = client.get("/", headers=headers)
    assert res.status_code == 200
    assert b"example.txt" in res.data

def test_valid_file_download_unauthorized(client):
    f = Path(app.SERVE_FOLDER) / "test.txt"
    f.write_text("hello")
    res = client.get("/files/test.txt")
    assert res.status_code == 401

def test_valid_file_download_authorized(client):
    f = Path(app.SERVE_FOLDER) / "test.txt"
    f.write_text("hello")
    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.get("/files/test.txt", headers=headers)
    assert res.status_code == 200
    assert res.data == b"hello"

def test_invalid_file_path_authorized(client):
    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.get("/files/../../etc/passwd", headers=headers)
    assert res.status_code == 403

def test_file_not_found_authorized(client):
    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.get("/files/missing.txt", headers=headers)
    assert res.status_code == 404

def test_folder_download_as_zip(client):
    folder = Path(app.SERVE_FOLDER) / "dir"
    folder.mkdir()
    (folder / "a.txt").write_text("data")

    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.get("/download-folder/dir", headers=headers)
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/zip'

    with zipfile.ZipFile(io.BytesIO(res.data)) as z:
        assert "dir/a.txt" in z.namelist()

def test_download_nonexistent_folder_authorized(client):
    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.get("/download-folder/ghost", headers=headers)
    assert res.status_code == 404

def test_file_upload_authorized(client):
    data = {
        'path': '',
        'file_0': (io.BytesIO(b"test upload"), 'uploaded.txt'),
        'file_0_path': ''
    }
    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.post("/upload", data=data, content_type='multipart/form-data', headers=headers)
    assert res.status_code == 200

    saved = Path(app.SERVE_FOLDER) / "uploaded.txt"
    assert saved.exists()
    assert saved.read_text() == "test upload"

def test_upload_invalid_path_authorized(client):
    data = {
        'path': '../outside',
        'file_0': (io.BytesIO(b"hack"), 'hack.txt'),
        'file_0_path': ''
    }
    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.post("/upload", data=data, content_type='multipart/form-data', headers=headers)
    assert res.status_code == 403

def test_yaml_auth_success(client, monkeypatch):
    def mock_load_yaml_users():
        return {'yamluser': 'ymlpass', 'another': 'anotherpass'}
    
    monkeypatch.setattr('app.load_yaml_users', mock_load_yaml_users)
    
    # Test successful login with YAML user
    auth_header = 'Basic ' + base64.b64encode(b'yamluser:ymlpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.get("/", headers=headers)
    assert res.status_code == 200

def test_yaml_auth_unauthorized(client, monkeypatch):
    def mock_load_yaml_users():
        return {'yamluser': 'ymlpass'}
    
    monkeypatch.setattr('app.load_yaml_users', mock_load_yaml_users)
    
    wrong_header = 'Basic ' + base64.b64encode(b'yamluser:wrongpass').decode('utf-8')
    wrong_headers = {'Authorization': wrong_header}
    res = client.get("/", headers=wrong_headers)
    assert res.status_code == 401

def test_yaml_auth_failure_but_env_fallback(client, monkeypatch):
    def mock_load_yaml_users():
        return {'yamluser': 'ymlpass'}
    
    monkeypatch.setattr('app.load_yaml_users', mock_load_yaml_users)
    
    # Login with env user should succeed via fallback
    auth_header = 'Basic ' + base64.b64encode(b'testuser:testpass').decode('utf-8')
    headers = {'Authorization': auth_header}
    res = client.get("/", headers=headers)
    assert res.status_code == 200

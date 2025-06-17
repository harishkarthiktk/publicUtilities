import io
import os
import zipfile
import pytest
from pathlib import Path
import app


@pytest.fixture
def client(tmp_path):
    # Create isolated folders
    serve_folder = tmp_path / "serveFolder"
    temp_dir = tmp_path / "temp_zips"
    serve_folder.mkdir()
    temp_dir.mkdir()

    # Patch globals in app
    app.SERVE_FOLDER = serve_folder.resolve()
    app.UPLOAD_FOLDER = app.SERVE_FOLDER
    app.TEMP_DIR = temp_dir.resolve()

    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client

def test_homepage_lists_files(client):
    test_file = Path(app.SERVE_FOLDER) / "example.txt"
    test_file.write_text("sample content")

    res = client.get("/")
    assert res.status_code == 200
    assert b"example.txt" in res.data

def test_valid_file_download(client):
    f = Path(app.SERVE_FOLDER) / "test.txt"
    f.write_text("hello")
    res = client.get("/files/test.txt")
    assert res.status_code == 200
    assert res.data == b"hello"

def test_invalid_file_path(client):
    res = client.get("/files/../../etc/passwd")
    assert res.status_code == 403

def test_file_not_found(client):
    res = client.get("/files/missing.txt")
    assert res.status_code == 404

def test_folder_download_as_zip(client):
    folder = Path(app.SERVE_FOLDER) / "dir"
    folder.mkdir()
    (folder / "a.txt").write_text("data")

    res = client.get("/download-folder/dir")
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/zip'

    with zipfile.ZipFile(io.BytesIO(res.data)) as z:
        assert "dir/a.txt" in z.namelist()

def test_download_nonexistent_folder(client):
    res = client.get("/download-folder/ghost")
    assert res.status_code == 404

def test_file_upload(client):
    data = {
        'path': '',
        'file_0': (io.BytesIO(b"test upload"), 'uploaded.txt'),
        'file_0_path': ''
    }
    res = client.post("/upload", data=data, content_type='multipart/form-data')
    assert res.status_code == 200

    saved = Path(app.SERVE_FOLDER) / "uploaded.txt"
    assert saved.exists()
    assert saved.read_text() == "test upload"

def test_upload_invalid_path(client):
    data = {
        'path': '../outside',
        'file_0': (io.BytesIO(b"hack"), 'hack.txt'),
        'file_0_path': ''
    }
    res = client.post("/upload", data=data, content_type='multipart/form-data')
    assert res.status_code == 403

def test_secure_filename(client):
    data = {
        'path': '',
        'file_0': (io.BytesIO(b"123"), '../../evil.sh'),
        'file_0_path': ''
    }
    res = client.post("/upload", data=data, content_type='multipart/form-data')
    assert res.status_code == 200

    for path in Path(app.SERVE_FOLDER).rglob("*"):
        assert ".." not in str(path)

def test_temp_zip_cleanup(client):
    folder = Path(app.SERVE_FOLDER) / "tozip"
    folder.mkdir()
    (folder / "one.txt").write_text("zip me")

    zip_path = Path(app.TEMP_DIR) / "tozip.zip"
    if zip_path.exists():
        zip_path.unlink()

    res = client.get("/download-folder/tozip")
    assert res.status_code == 200

    # Wait briefly to allow cleanup to occur
    import time
    time.sleep(0.2)

    assert not zip_path.exists()

def test_filtered_mime_type_is_skipped(client):
    # Use an invalid MIME file with .php extension
    data = {
        'path': '',
        'file_0': (io.BytesIO(b"<php?>"), 'malicious.php'),
        'file_0_path': ''
    }
    res = client.post("/upload", data=data, content_type='multipart/form-data')
    assert res.status_code == 200

    found = any("malicious.php" in str(p) for p in Path(app.SERVE_FOLDER).rglob("*"))
    assert not found

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import zipfile
import io
from flask import url_for
from pathlib import Path
from app import create_app
import base64
import yaml

@pytest.fixture
def app_with_folders(temp_serve_folder, temp_users_yaml, temp_temp_dir):
    """Create app with temp folders for download testing."""
    app = create_app()
    
    # Override config to use temp dirs
    app.config['SERVE_FOLDER'] = temp_serve_folder
    app.config['TEMP_DIR'] = temp_temp_dir
    app.config['UPLOAD_FOLDER'] = temp_serve_folder
    app.config['ALLOWED_EXTENSIONS'] = set(['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.zip', '.csv', '.json', '.md'])
    app.config['MAX_CONTENT_LENGTH'] = 5368709120
    
    with app.test_client() as client:
        yield client

def test_download_folder_success(app_with_folders, temp_serve_folder):
    """Test successful folder download as ZIP."""
    # Create sample folder structure
    sample_folder = temp_serve_folder / 'sample_folder'
    sample_folder.mkdir()
    (sample_folder / 'file1.txt').write_text('Content 1')
    (sample_folder / 'file2.jpg').write_bytes(b'fake image')
    
    subdir = sample_folder / 'subdir'
    subdir.mkdir()
    (subdir / 'nested.txt').write_text('Nested content')
    
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    response = app_with_folders.get(f'/download-folder/{sample_folder.name}', headers=auth_header)
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/zip'
    assert response.headers['Content-Disposition'] == f'attachment; filename={sample_folder.name}.zip'
    
    # Verify ZIP contents
    with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
        assert len(zf.namelist()) == 3  # file1.txt, file2.jpg, subdir/nested.txt
        assert zf.read('sample_folder/file1.txt').decode() == 'Content 1'
        assert zf.read('sample_folder/subdir/nested.txt').decode() == 'Nested content'
        assert zf.read('sample_folder/file2.jpg') == b'fake image'

def test_download_folder_nonexistent(app_with_folders):
    """Test download non-existent folder."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    response = app_with_folders.get('/download-folder/nonexistent/', headers=auth_header)
    assert response.status_code == 404

def test_download_folder_path_traversal(app_with_folders, temp_serve_folder):
    """Test path traversal in folder download."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    response = app_with_folders.get('/download-folder/../nonexistent/', headers=auth_header)
    assert response.status_code == 403

def test_download_folder_no_auth(app_with_folders):
    """Test download without authentication."""
    response = app_with_folders.get('/download-folder/sample/')
    assert response.status_code == 401

def test_download_empty_folder(app_with_folders, temp_serve_folder):
    """Test download empty folder."""
    empty_folder = temp_serve_folder / 'empty'
    empty_folder.mkdir()
    
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    response = app_with_folders.get(f'/download-folder/{empty_folder.name}', headers=auth_header)
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/zip'
    
    # Verify empty ZIP
    with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
        assert len(zf.namelist()) == 0

def test_download_folder_cleanup(app_with_folders, temp_temp_dir, temp_serve_folder):
    """Test temporary ZIP cleanup after download."""
    sample_folder = temp_serve_folder / 'sample'
    sample_folder.mkdir()
    (sample_folder / 'test.txt').write_text('test')
    
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    # Before download
    assert not list(temp_temp_dir.iterdir())  # Empty
    
    response = app_with_folders.get(f'/download-folder/{sample_folder.name}', headers=auth_header)
    assert response.status_code == 200
    
    # After download, temp should be cleaned
    assert not list(temp_temp_dir.iterdir())  # Empty again
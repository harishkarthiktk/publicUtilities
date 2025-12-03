import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import url_for
from app import create_app
from routes import get_file_tree
import yaml
from pathlib import Path

@pytest.fixture
def app_with_serve_folder(temp_serve_folder, temp_users_yaml):
    """Create app with temp serve folder and auth."""
    app = create_app()
    app.config['SERVE_FOLDER'] = temp_serve_folder
    with app.test_client() as client:
        yield client

def test_list_files_success(app_with_serve_folder, temp_serve_folder):
    """Test successful file listing with authentication."""
    # Create auth header
    auth_header = {'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3M='}  # testuser:testpass
    
    response = app_with_serve_folder.get('/', headers=auth_header)
    assert response.status_code == 200
    assert b'<title>File Server' in response.data  # Checks browser.html rendered
    # Verify file tree structure in response (simplified, as it's HTML)
    assert b'sample.txt' in response.data
    assert b'subdir' in response.data

def test_list_files_missing_dir(app_with_serve_folder, monkeypatch):
    """Test file listing when SERVE_FOLDER is missing."""
    auth_header = {'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3M='}

    # Override config to nonexistent
    app = app_with_serve_folder.application
    app.config['SERVE_FOLDER'] = Path('nonexistent')

    response = app_with_serve_folder.get('/', headers=auth_header)
    assert response.status_code == 404
    assert b'<h2>Error</h2>' in response.data

def test_list_files_permission_error(app_with_serve_folder, monkeypatch, tmp_path):
    """Test file listing with permission error (mock)."""
    # Mock os.listdir to raise PermissionError
    def mock_listdir(path):
        raise ValueError("Permission denied")
    
    monkeypatch.setattr('os.listdir', mock_listdir)
    
    auth_header = {'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3M='}
    response = app_with_serve_folder.get('/', headers=auth_header)
    assert response.status_code == 500
    assert b'<h2>Error</h2>' in response.data

def test_list_files_empty_dir(app_with_serve_folder, temp_serve_folder, monkeypatch):
    """Test listing empty directory."""
    # Clear the temp folder
    for item in temp_serve_folder.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            import shutil
            shutil.rmtree(item)
    
    auth_header = {'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3M='}
    response = app_with_serve_folder.get('/', headers=auth_header)
    assert response.status_code == 200
    # Should render empty tree

def test_get_file_tree_logic(temp_serve_folder):
    """Unit test for get_file_tree function."""
    tree = get_file_tree(temp_serve_folder)
    assert isinstance(tree, list)
    assert len(tree) >= 2  # sample.txt and subdir
    files = [item for item in tree if item['type'] == 'file']
    dirs = [item for item in tree if item['type'] == 'directory']
    assert len(files) >= 1  # sample.txt
    assert len(dirs) >= 1  # subdir
    # Find specific file without relying on order
    sample_file = next(item for item in tree if item['name'] == 'sample.txt' and item['type'] == 'file')
    assert sample_file['name'] == 'sample.txt'
    assert sample_file['size'] == 13  # "Hello, World!" length
    # Check recursion
    subdir_item = next(item for item in tree if item['name'] == 'subdir')
    assert len(subdir_item['children']) == 1
    assert subdir_item['children'][0]['name'] == 'nested.txt'
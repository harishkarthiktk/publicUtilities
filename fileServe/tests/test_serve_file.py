import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import url_for
from pathlib import Path
from app import create_app
import base64

@pytest.fixture
def app_with_serve_folder(monkeypatch, temp_serve_folder, temp_users_yaml):
    """Create app with temp serve folder and auth, overriding config."""
    import yaml
    from pathlib import Path

    # Write test users to temp file
    test_users = {
        'testuser': 'testpass'
    }
    with open(temp_users_yaml, 'w') as f:
        yaml.dump(test_users, f)

    # Prepare config data
    config_data = {
        'APPLICATION_ROOT': '/',
        'SECRET_KEY': 'test-secret',
        'SERVER_NAME': 'localhost',
        'serve_folder': str(temp_serve_folder),
        'temp_dir': 'temp_zips',
        'upload_folder': str(temp_serve_folder),
        'allowed_extensions': ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.zip', '.csv', '.json', '.md'],
        'max_content_length': 5368709120,
        'users_yaml': str(temp_users_yaml)
    }

    # Create temp config file
    temp_config = Path('temp_config.yaml')
    with open(temp_config, 'w') as f:
        yaml.dump(config_data, f)

    # Monkeypatch Path.resolve for 'config.yaml' and 'users.yaml'
    original_resolve = Path.resolve
    def custom_resolve(self):
        if str(self) == 'config.yaml':
            return temp_config
        if str(self) == 'users.yaml':
            return temp_users_yaml
        return original_resolve(self)
    monkeypatch.setattr(Path, 'resolve', custom_resolve)

    # Import app (now uses temp config and users)
    import app

    # Override SERVE_FOLDER after routes registration to use temp folder (routes.py overrides it)
    app.app.config['SERVE_FOLDER'] = temp_serve_folder

    # Reload serve_folder from config to use temp (using correct config key)
    app.serve_folder = Path(app.app.config['SERVE_FOLDER'])

    return app.app.test_client()

def test_serve_file_success(app_with_serve_folder, temp_serve_folder):
    """Test successful file serving with authentication."""
    # Create a sample file
    sample_file = temp_serve_folder / 'sample.txt'
    sample_file.write_text('Test content')
    
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    response = app_with_serve_folder.get(f'/files/{sample_file.name}', headers=auth_header)
    assert response.status_code == 200
    assert 'X-Accel-Redirect' in response.headers
    assert response.headers['X-Accel-Redirect'] == f'/internal-files/{sample_file.name}'
    assert response.headers['Content-Type'] == 'text/plain'  # mimetypes.guess_type doesn't add charset for .txt
    assert response.headers['Content-Disposition'] == f'attachment; filename="{sample_file.name}"'
    assert int(response.headers['Content-Length']) == len('Test content')

def test_serve_file_nonexistent(app_with_serve_folder):
    """Test serving non-existent file."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    response = app_with_serve_folder.get('/files/nonexistent.txt', headers=auth_header)
    assert response.status_code == 404

def test_serve_file_path_traversal(app_with_serve_folder, temp_serve_folder):
    """Test path traversal attempt."""
    # Create a file outside, but test traversal
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    traversal_path = '../nonexistent.txt'  # Relative traversal
    response = app_with_serve_folder.get(f'/files/{traversal_path}', headers=auth_header)
    assert response.status_code == 403

def test_serve_file_no_auth(app_with_serve_folder):
    """Test serving without authentication."""
    response = app_with_serve_folder.get('/files/sample.txt')
    assert response.status_code == 401

def test_serve_file_special_chars(app_with_serve_folder, temp_serve_folder):
    """Test serving file with special characters in name."""
    special_file = temp_serve_folder / 'file with space.txt'
    special_file.write_text('Special content')
    
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    response = app_with_serve_folder.get(f'/files/{special_file.name}', headers=auth_header)
    assert response.status_code == 200
    assert 'X-Accel-Redirect' in response.headers
    assert response.headers['Content-Disposition'] == f'attachment; filename="{special_file.name}"'

def test_serve_large_file(app_with_serve_folder, temp_serve_folder):
    """Test serving a large file (simulate)."""
    large_content = b'A' * 10240  # 10KB
    large_file = temp_serve_folder / 'large.bin'
    large_file.write_bytes(large_content)
    
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    
    response = app_with_serve_folder.get(f'/files/{large_file.name}', headers=auth_header)
    assert response.status_code == 200
    assert int(response.headers['Content-Length']) == len(large_content)
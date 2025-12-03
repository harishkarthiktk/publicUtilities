import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from flask import url_for
from pathlib import Path
from app import create_app
import base64
import yaml

@pytest.fixture
def app_with_upload(temp_serve_folder, temp_users_yaml, temp_upload_folder):
    """Create app with temp upload folder and auth, overriding config."""
    # Use temp_upload_folder as upload_folder
    temp_config = Path('temp_config.yaml')
    config_data = {
        'serve_folder': str(temp_serve_folder),
        'temp_dir': 'temp_zips',
        'upload_folder': str(temp_upload_folder),
        'allowed_extensions': ['.txt', '.pdf', '.jpg', '.jpeg', '.png', '.zip', '.csv', '.json', '.md'],
        'max_content_length': 5368709120
    }
    with open(temp_config, 'w') as f:
        yaml.dump(config_data, f)
    
    # Patch config path in app
    from unittest.mock import patch
    with patch('app.Path') as mock_path:
        mock_path.return_value.resolve.return_value = temp_config
        app = create_app()
    
    with app.test_client() as client:
        yield client
    
    if temp_config.exists():
        temp_config.unlink()




def test_upload_single_file_success(app_with_upload, temp_upload_folder):
    """Test successful single file upload."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': ''}
    files = {'file': ('test.txt', b'Upload content')}

    response = app_with_upload.post('/upload', data=data, files=files, headers=auth_header)
    assert response.status_code == 200
    json_data = response.json
    assert json_data['status'] == 'success'
    assert len(json_data['files']) == 1
    assert json_data['files'][0]['name'] == 'test.txt'
    assert json_data['files'][0]['size'] == 14  # len('Upload content')
    
    # Verify file saved
    saved_file = temp_upload_folder / 'test.txt'
    assert saved_file.exists()
    assert saved_file.read_bytes() == b'Upload content'

def test_upload_multiple_files(app_with_upload, temp_upload_folder):
    """Test upload multiple files."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': ''}
    files = {
        'file1': ('doc1.txt', b'Content 1'),
        'file2': ('doc2.txt', b'Content 2')
    }
    
    response = app_with_upload.post('/upload', data=data, files=files, headers=auth_header)
    assert response.status_code == 200
    json_data = response.json
    assert json_data['status'] == 'success'
    assert len(json_data['files']) == 2
    assert json_data['files'][0]['name'] == 'doc1.txt'
    assert json_data['files'][1]['name'] == 'doc2.txt'
    
    # Verify both saved
    assert (temp_upload_folder / 'doc1.txt').read_bytes() == b'Content 1'
    assert (temp_upload_folder / 'doc2.txt').read_bytes() == b'Content 2'

def test_upload_to_target_path(app_with_upload, temp_upload_folder):
    """Test upload to specific target path with subdir."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': 'sub/dir'}
    files = {'file': ('target.txt', b'Target content')}
    
    response = app_with_upload.open('/upload', method='POST', data=data, files=files, headers=auth_header, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.json
    assert json_data['status'] == 'success'
    assert json_data['files'][0]['path'] == 'sub/dir/target.txt'
    
    # Verify nested dir created and file saved
    saved_file = temp_upload_folder / 'sub' / 'dir' / 'target.txt'
    assert saved_file.exists()
    assert saved_file.read_bytes() == b'Target content'

def test_upload_disallowed_extension(app_with_upload):
    """Test upload with disallowed extension (skipped with warning)."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': ''}
    files = {'file': ('bad.exe', b'Bad content')}
    
    response = app_with_upload.open('/upload', method='POST', data=data, files=files, headers=auth_header, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.json
    assert json_data['status'] == 'warning'
    assert len(json_data['files']) == 0
    assert len(json_data['errors']) == 1
    assert 'not allowed' in json_data['errors'][0]['message']
    assert json_data['errors'][0]['type'] == 'warning'
    
    # Verify no file saved
    assert not (app_with_upload.config['UPLOAD_FOLDER'] / 'bad.exe').exists()

def test_upload_path_traversal(app_with_upload):
    """Test upload with traversal path (403)."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': '../../../bad'}
    files = {'file': ('test.txt', b'content')}
    
    response = app_with_upload.open('/upload', method='POST', data=data, files=files, headers=auth_header, content_type='multipart/form-data')
    assert response.status_code == 403

def test_upload_no_auth(app_with_upload):
    """Test upload without authentication."""
    data = {'path': ''}
    files = {'file': ('test.txt', b'content')}
    
    response = app_with_upload.open('/upload', method='POST', data=data, files=files, content_type='multipart/form-data')
    assert response.status_code == 401

def test_upload_no_files(app_with_upload):
    """Test upload with no files."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': ''}
    
    response = app_with_upload.post('/upload', data=data, headers=auth_header)
    assert response.status_code == 200
    json_data = response.json
    assert json_data['status'] == 'success'
    assert json_data['message'] == 'No files were provided.'
    assert len(json_data['files']) == 0
    assert len(json_data['errors']) == 0

def test_upload_overwrite_existing(app_with_upload, temp_upload_folder):
    """Test overwriting existing file."""
    # Create existing file
    existing = temp_upload_folder / 'existing.txt'
    existing.write_text('Old content')
    
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': ''}
    files = {'file': ('existing.txt', b'New content')}
    
    response = app_with_upload.open('/upload', method='POST', data=data, files=files, headers=auth_header, content_type='multipart/form-data')
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    
    # Verify overwritten
    assert existing.read_text() == 'New content'

def test_upload_large_file(app_with_upload, temp_upload_folder):
    """Test upload large file (simulate chunks)."""
    large_content = b'A' * 102400  # 100KB
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': ''}
    files = {'file': ('large.bin', large_content)}
    
    response = app_with_upload.open('/upload', method='POST', data=data, files=files, headers=auth_header, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.json
    assert json_data['status'] == 'success'
    assert json_data['files'][0]['size'] == len(large_content)
    
    saved = temp_upload_folder / 'large.bin'
    assert saved.read_bytes() == large_content

def test_upload_invalid_filename(app_with_upload, temp_upload_folder):
    """Test upload with invalid filename (secured)."""
    auth_header = {'Authorization': 'Basic ' + base64.b64encode(b'testuser:testpass').decode()}
    data = {'path': ''}
    files = {'file': ('<script>bad</script>.txt', b'content')}
    
    response = app_with_upload.open('/upload', method='POST', data=data, files=files, headers=auth_header, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.json
    assert json_data['status'] == 'success'
    assert json_data['files'][0]['name'] == 'script_bad.txt'  # secure_filename result
    
    saved = temp_upload_folder / 'script_bad.txt'
    assert saved.exists()
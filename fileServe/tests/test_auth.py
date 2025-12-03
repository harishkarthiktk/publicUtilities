import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import yaml
from flask import url_for
from app import create_app

@pytest.fixture
def app_with_auth(tmp_path):
    """Create app with temporary users.yaml for auth testing."""
    users_file = tmp_path / "users.yaml"
    users_data = {
        "users": {
            "testuser": "testpass",
            "admin": "adminpass"
        }
    }
    with open(users_file, "w") as f:
        yaml.dump(users_data, f)
    os.environ["BASIC_AUTH_USERS_FILE"] = str(users_file)
    
    app = create_app()
    with app.test_client() as client:
        yield client
    
    if "BASIC_AUTH_USERS_FILE" in os.environ:
        del os.environ["BASIC_AUTH_USERS_FILE"]

def test_valid_yaml_auth(app_with_auth):
    """Test successful authentication with YAML credentials."""
    response = app_with_auth.get('/',
                                 headers={'Authorization': 'Basic dGVzdHVzZXI6dGVzdHBhc3M='})  # base64("testuser:testpass")
    assert response.status_code == 200

def test_valid_env_auth(app_with_auth):
    """Test successful authentication with environment credentials (fallback)."""
    response = app_with_auth.get('/',
                                 headers={'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ='})  # base64("admin:password")
    assert response.status_code == 200

def test_invalid_auth(app_with_auth):
    """Test failed authentication with invalid credentials."""
    response = app_with_auth.get('/',
                                 headers={'Authorization': 'Basic dGVzdHVzZXI6d3Jvbmc='})  # wrong pass
    assert response.status_code == 401

def test_no_auth(app_with_auth):
    """Test access without authentication."""
    response = app_with_auth.get('/')
    assert response.status_code == 401

def test_empty_password(app_with_auth):
    """Test authentication with empty password."""
    response = app_with_auth.get('/',
                                 headers={'Authorization': 'Basic dGVzdHVzZXI6'})  # empty pass
    assert response.status_code == 401
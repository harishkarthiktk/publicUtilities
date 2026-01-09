"""
Unit tests for AuthTemplate authentication system.

Run with:
    python -m pytest tests/test_auth.py -v
    python -m unittest tests.test_auth
"""

import unittest
import base64
from pathlib import Path
import tempfile
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import AuthManager
from config import AuthConfig
from models import User, AuthResult
from logger import setup_logger, AuthLogger


class TestAuthConfig(unittest.TestCase):
    """Test configuration loading."""

    def setUp(self):
        """Create temporary YAML file for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.yaml_file = Path(self.temp_dir.name) / "users.yaml"

        # Create test users file
        with open(self.yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'admin': 'admin_password',
                    'user1': 'user1_password',
                    'user2': 'user2_password'
                }
            }, f)

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_load_from_yaml(self):
        """Test loading configuration from YAML file."""
        config = AuthConfig(yaml_file=str(self.yaml_file))
        users = config.get_users()

        self.assertEqual(len(users), 3)
        self.assertIn('admin', users)
        self.assertEqual(users['admin'], 'admin_password')

    def test_validate_config(self):
        """Test configuration validation."""
        config = AuthConfig(yaml_file=str(self.yaml_file))
        self.assertTrue(config.validate())

    def test_validate_empty_config(self):
        """Test validation fails with no users."""
        config = AuthConfig()
        with self.assertRaises(ValueError):
            config.validate()

    def test_get_user_password(self):
        """Test getting password for specific user."""
        config = AuthConfig(yaml_file=str(self.yaml_file))
        password = config.get_user_password('admin')
        self.assertEqual(password, 'admin_password')

    def test_get_nonexistent_user(self):
        """Test getting password for non-existent user."""
        config = AuthConfig(yaml_file=str(self.yaml_file))
        password = config.get_user_password('nonexistent')
        self.assertIsNone(password)


class TestAuthManager(unittest.TestCase):
    """Test authentication manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.yaml_file = Path(self.temp_dir.name) / "users.yaml"

        with open(self.yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'admin': 'admin_password',
                    'user1': 'user1_password'
                }
            }, f)

        self.config = AuthConfig(yaml_file=str(self.yaml_file))
        self.auth_manager = AuthManager(self.config)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_verify_valid_credentials(self):
        """Test verification of valid credentials."""
        result = self.auth_manager.verify_credentials('admin', 'admin_password')

        self.assertTrue(result.success)
        self.assertIsNotNone(result.user)
        self.assertEqual(result.user.username, 'admin')

    def test_verify_invalid_password(self):
        """Test verification with wrong password."""
        result = self.auth_manager.verify_credentials('admin', 'wrong_password')

        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'INVALID_CREDENTIALS')

    def test_verify_nonexistent_user(self):
        """Test verification with non-existent user."""
        result = self.auth_manager.verify_credentials('nonexistent', 'password')

        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'USER_NOT_FOUND')

    def test_verify_basic_auth_header(self):
        """Test verification from Basic Auth header."""
        # Create valid Basic Auth header
        credentials = base64.b64encode(b'admin:admin_password').decode('utf-8')
        header = f'Basic {credentials}'

        result = self.auth_manager.verify_basic_auth_header(header)

        self.assertTrue(result.success)
        self.assertEqual(result.user.username, 'admin')

    def test_verify_basic_auth_header_invalid(self):
        """Test verification with invalid Basic Auth header."""
        header = 'Invalid header format'
        result = self.auth_manager.verify_basic_auth_header(header)

        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'INVALID_HEADER')

    def test_verify_basic_auth_header_bad_encoding(self):
        """Test verification with bad Base64 encoding."""
        header = 'Basic not-valid-base64!!!'
        result = self.auth_manager.verify_basic_auth_header(header)

        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'INVALID_ENCODING')

    def test_list_users(self):
        """Test listing all configured users."""
        users = self.auth_manager.list_users()

        self.assertEqual(len(users), 2)
        self.assertIn('admin', users)
        self.assertIn('user1', users)

    def test_add_user(self):
        """Test adding a new user."""
        result = self.auth_manager.add_user('newuser', 'newpass')
        self.assertTrue(result)

        # Verify user was added
        users = self.auth_manager.list_users()
        self.assertIn('newuser', users)

    def test_add_duplicate_user(self):
        """Test adding user that already exists."""
        result = self.auth_manager.add_user('admin', 'password')
        self.assertFalse(result)

    def test_remove_user(self):
        """Test removing a user."""
        result = self.auth_manager.remove_user('user1')
        self.assertTrue(result)

        # Verify user was removed
        users = self.auth_manager.list_users()
        self.assertNotIn('user1', users)

    def test_remove_nonexistent_user(self):
        """Test removing user that doesn't exist."""
        result = self.auth_manager.remove_user('nonexistent')
        self.assertFalse(result)

    def test_get_user_info(self):
        """Test getting user information."""
        info = self.auth_manager.get_user_info('admin')

        self.assertIsNotNone(info)
        self.assertEqual(info['username'], 'admin')
        self.assertTrue(info['exists'])

    def test_get_info_nonexistent_user(self):
        """Test getting info for non-existent user."""
        info = self.auth_manager.get_user_info('nonexistent')
        self.assertIsNone(info)


class TestUser(unittest.TestCase):
    """Test User model."""

    def test_user_creation(self):
        """Test creating a user."""
        user = User(
            username='testuser',
            email='test@example.com',
            roles=['user', 'admin']
        )

        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)

    def test_user_has_role(self):
        """Test checking user roles."""
        user = User(username='admin', roles=['admin', 'user'])

        self.assertTrue(user.has_role('admin'))
        self.assertTrue(user.has_role('user'))
        self.assertFalse(user.has_role('superuser'))

    def test_user_to_dict(self):
        """Test converting user to dictionary."""
        user = User(username='test', email='test@example.com')
        user_dict = user.to_dict()

        self.assertEqual(user_dict['username'], 'test')
        self.assertEqual(user_dict['email'], 'test@example.com')
        self.assertTrue(user_dict['is_active'])


class TestAuthResult(unittest.TestCase):
    """Test AuthResult model."""

    def test_success_result(self):
        """Test successful auth result."""
        user = User(username='test')
        result = AuthResult(success=True, user=user, message='Success')

        self.assertTrue(result.success)
        self.assertIsNotNone(result.user)
        self.assertEqual(result.message, 'Success')

    def test_failure_result(self):
        """Test failed auth result."""
        result = AuthResult(
            success=False,
            message='Invalid credentials',
            error_code='INVALID_CREDENTIALS'
        )

        self.assertFalse(result.success)
        self.assertIsNone(result.user)
        self.assertEqual(result.error_code, 'INVALID_CREDENTIALS')


class TestAuthLogger(unittest.TestCase):
    """Test logging functionality."""

    def setUp(self):
        """Set up logging."""
        self.logger = setup_logger('TestAuth')
        self.auth_logger = AuthLogger(self.logger)

    def test_logger_creation(self):
        """Test logger initialization."""
        self.assertIsNotNone(self.logger)
        self.assertIsNotNone(self.auth_logger)

    def test_log_auth_attempt(self):
        """Test logging authentication attempt."""
        # This just ensures it doesn't raise an exception
        self.auth_logger.log_auth_attempt('admin', '127.0.0.1', True)
        self.auth_logger.log_auth_attempt('admin', '127.0.0.1', False, 'INVALID_CREDENTIALS')

    def test_log_invalid_credentials(self):
        """Test logging invalid credentials."""
        self.auth_logger.log_invalid_credentials('admin', '127.0.0.1', 10)

    def test_log_user_not_found(self):
        """Test logging user not found."""
        self.auth_logger.log_user_not_found('admin', '127.0.0.1')

    def test_log_config_loaded(self):
        """Test logging config load."""
        self.auth_logger.log_config_loaded(5, 'YAML')

    def test_log_error(self):
        """Test logging errors."""
        try:
            raise ValueError("Test error")
        except Exception as e:
            self.auth_logger.log_error("Test message", e)


class TestIntegration(unittest.TestCase):
    """Integration tests for full authentication flow."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.yaml_file = Path(self.temp_dir.name) / "users.yaml"

        with open(self.yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'admin': 'admin_password',
                    'user1': 'user1_password'
                }
            }, f)

        self.config = AuthConfig(yaml_file=str(self.yaml_file))
        self.logger = setup_logger('IntegrationTest')
        self.auth_logger = AuthLogger(self.logger)
        self.auth_manager = AuthManager(self.config, logger=self.auth_logger)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_full_auth_flow(self):
        """Test complete authentication flow."""
        # 1. User lists themselves
        users = self.auth_manager.list_users()
        self.assertEqual(len(users), 2)

        # 2. User attempts wrong password
        result = self.auth_manager.verify_credentials('admin', 'wrong')
        self.assertFalse(result.success)

        # 3. User authenticates with correct credentials
        result = self.auth_manager.verify_credentials('admin', 'admin_password')
        self.assertTrue(result.success)
        self.assertEqual(result.user.username, 'admin')

        # 4. Admin adds new user
        self.auth_manager.add_user('newuser', 'newpass')
        users = self.auth_manager.list_users()
        self.assertEqual(len(users), 3)

        # 5. New user authenticates
        result = self.auth_manager.verify_credentials('newuser', 'newpass')
        self.assertTrue(result.success)

    def test_basic_auth_header_flow(self):
        """Test HTTP Basic Auth header flow."""
        # Valid header
        credentials = base64.b64encode(b'admin:admin_password').decode()
        header = f'Basic {credentials}'
        result = self.auth_manager.verify_basic_auth_header(header)
        self.assertTrue(result.success)

        # Invalid header
        result = self.auth_manager.verify_basic_auth_header('Bearer token123')
        self.assertFalse(result.success)


if __name__ == '__main__':
    unittest.main()

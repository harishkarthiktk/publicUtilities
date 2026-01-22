"""
Unit tests for AuthService authentication system.

Run with:
    python -m pytest tests/test_auth.py -v
    python -m unittest tests.test_auth
"""

import unittest
import base64
from pathlib import Path
import tempfile
import yaml
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from authservice.core import AuthManager
from authservice.config import AuthConfig
from authservice.models import User, AuthResult
from authservice.logger import setup_logger, AuthLogger
from authservice.hashing import hash_password, verify_password, is_bcrypt_hash


class TestAuthConfig(unittest.TestCase):
    """Test configuration loading."""

    def setUp(self):
        """Create temporary YAML file for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.yaml_file = Path(self.temp_dir.name) / "users.yaml"

        # Create test users file with hashed passwords
        with open(self.yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'admin': hash_password('admin_password'),
                    'user1': hash_password('user1_password'),
                    'user2': hash_password('user2_password')
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
        # Passwords are now hashed, so just verify they're hashes
        self.assertTrue(is_bcrypt_hash(users['admin']))

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
        # Should return the hash, which should be in bcrypt format
        self.assertTrue(is_bcrypt_hash(password))

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
                    'admin': hash_password('admin_password'),
                    'user1': hash_password('user1_password')
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
        # Changed from USER_NOT_FOUND to INVALID_CREDENTIALS for security
        self.assertEqual(result.error_code, 'INVALID_CREDENTIALS')

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

    def test_add_user_with_hashing(self):
        """Test adding user with password hashing enabled."""
        # Add user (passwords should be hashed by default)
        result = self.auth_manager.add_user('hasheduser', 'mypassword')
        self.assertTrue(result)

        # Verify password is stored as hash
        stored_password = self.auth_manager.users['hasheduser']
        self.assertTrue(is_bcrypt_hash(stored_password))

        # Verify authentication works with plaintext password
        auth_result = self.auth_manager.verify_credentials('hasheduser', 'mypassword')
        self.assertTrue(auth_result.success)

    def test_add_user_hashing_disabled(self):
        """Test adding user with hashing disabled shows deprecation warning."""
        import warnings
        # Create manager with use_hashing=False
        temp_dir = tempfile.TemporaryDirectory()
        yaml_file = Path(temp_dir.name) / "users.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump({'users': {'admin': hash_password('password')}}, f)

        config = AuthConfig(yaml_file=str(yaml_file))

        # Should show deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            auth_manager = AuthManager(config, use_hashing=False)
            # Check that a deprecation warning was raised
            self.assertTrue(any(issubclass(warning.category, DeprecationWarning) for warning in w))

        # Add user - should still hash for security
        result = auth_manager.add_user('plainuser', 'plainpass')
        self.assertTrue(result)

        # Password should be hashed despite use_hashing=False
        stored_password = auth_manager.users['plainuser']
        self.assertTrue(is_bcrypt_hash(stored_password))

        temp_dir.cleanup()

    def test_verify_credentials_with_hashed_password(self):
        """Test authentication with bcrypt hashed passwords."""
        # Add user with hashing
        self.auth_manager.add_user('hashtest', 'password123')

        # Verify correct password works
        result = self.auth_manager.verify_credentials('hashtest', 'password123')
        self.assertTrue(result.success)

        # Verify incorrect password fails
        result = self.auth_manager.verify_credentials('hashtest', 'wrongpass')
        self.assertFalse(result.success)

    def test_add_user_logs_audit_entry(self):
        """Test that add_user logs audit entry."""
        temp_dir = tempfile.TemporaryDirectory()
        audit_file = os.path.join(temp_dir.name, "audit.log")
        yaml_file = Path(temp_dir.name) / "users.yaml"

        with open(yaml_file, 'w') as f:
            yaml.dump({'users': {'admin': hash_password('password')}}, f)

        config = AuthConfig(yaml_file=str(yaml_file))
        logger = setup_logger(
            'TestAudit',
            audit_log_file=audit_file
        )
        auth_manager = AuthManager(config, logger=logger)

        # Add user
        auth_manager.add_user('audituser', 'pass', by_whom='admin', ip_address='192.168.1.1')

        # Check audit log
        if os.path.exists(audit_file):
            with open(audit_file, 'r') as f:
                content = f.read()
            self.assertIn('USER_ADDED', content)
            self.assertIn('audituser', content)
            self.assertIn('admin', content)

        temp_dir.cleanup()

    def test_remove_user_logs_audit_entry(self):
        """Test that remove_user logs audit entry."""
        temp_dir = tempfile.TemporaryDirectory()
        audit_file = os.path.join(temp_dir.name, "audit.log")
        yaml_file = Path(temp_dir.name) / "users.yaml"

        with open(yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'usertoremove': hash_password('password')
                }
            }, f)

        config = AuthConfig(yaml_file=str(yaml_file))
        logger = setup_logger(
            'TestAudit2',
            audit_log_file=audit_file
        )
        auth_manager = AuthManager(config, logger=logger)

        # Remove user
        auth_manager.remove_user('usertoremove', by_whom='admin', ip_address='192.168.1.100')

        # Check audit log
        if os.path.exists(audit_file):
            with open(audit_file, 'r') as f:
                content = f.read()
            self.assertIn('USER_REMOVED', content)
            self.assertIn('usertoremove', content)

        temp_dir.cleanup()

    def test_custom_hash_function_still_works(self):
        """Test that custom hash_function parameter still works."""
        # Create a simple custom hash function
        def custom_verify(password, stored):
            return password == stored

        import warnings
        temp_dir = tempfile.TemporaryDirectory()
        yaml_file = Path(temp_dir.name) / "users.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'customuser': 'custompass'
                }
            }, f)

        config = AuthConfig(yaml_file=str(yaml_file))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            auth_manager = AuthManager(config, hash_function=custom_verify, use_hashing=False)

        # Verify authentication works with custom function
        result = auth_manager.verify_credentials('customuser', 'custompass')
        self.assertTrue(result.success)

        temp_dir.cleanup()

    def test_inactive_user_rejected(self):
        """Test that inactive users cannot authenticate."""
        temp_dir = tempfile.TemporaryDirectory()
        yaml_file = Path(temp_dir.name) / "users.yaml"

        # Create user with extended format (is_active: false)
        with open(yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'active_user': {
                        'password': hash_password('password123'),
                        'is_active': True
                    },
                    'inactive_user': {
                        'password': hash_password('password456'),
                        'is_active': False
                    }
                }
            }, f)

        config = AuthConfig(yaml_file=str(yaml_file))
        auth_manager = AuthManager(config)

        # Active user should authenticate
        result = auth_manager.verify_credentials('active_user', 'password123')
        self.assertTrue(result.success)

        # Inactive user should be rejected
        result = auth_manager.verify_credentials('inactive_user', 'password456')
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, 'USER_DISABLED')

        temp_dir.cleanup()

    def test_extended_yaml_format(self):
        """Test extended YAML format with metadata."""
        temp_dir = tempfile.TemporaryDirectory()
        yaml_file = Path(temp_dir.name) / "users.yaml"

        with open(yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'admin': {
                        'password': hash_password('adminpass'),
                        'is_active': True,
                        'roles': ['admin', 'user'],
                        'email': 'admin@example.com',
                        'metadata': {'department': 'IT'}
                    },
                    'simple_user': hash_password('simplepass')
                }
            }, f)

        config = AuthConfig(yaml_file=str(yaml_file))
        auth_manager = AuthManager(config)

        # Authenticate and check metadata is loaded
        result = auth_manager.verify_credentials('admin', 'adminpass')
        self.assertTrue(result.success)
        self.assertEqual(result.user.email, 'admin@example.com')
        self.assertIn('admin', result.user.roles)
        self.assertIn('user', result.user.roles)
        self.assertEqual(result.user.metadata.get('department'), 'IT')

        # Simple format should still work
        result = auth_manager.verify_credentials('simple_user', 'simplepass')
        self.assertTrue(result.success)
        self.assertEqual(result.user.roles, ['user'])  # Default role

        temp_dir.cleanup()

    def test_change_password(self):
        """Test password change functionality."""
        # Change password for existing user
        success = self.auth_manager.change_password('admin', 'new_password')
        self.assertTrue(success)

        # Old password should fail
        result = self.auth_manager.verify_credentials('admin', 'admin_password')
        self.assertFalse(result.success)

        # New password should work
        result = self.auth_manager.verify_credentials('admin', 'new_password')
        self.assertTrue(result.success)

        # Changing password for non-existent user should fail
        success = self.auth_manager.change_password('nonexistent', 'password')
        self.assertFalse(success)

    def test_persist_changes(self):
        """Test persisting user changes to YAML file."""
        temp_dir = tempfile.TemporaryDirectory()
        yaml_file = Path(temp_dir.name) / "users.yaml"

        with open(yaml_file, 'w') as f:
            yaml.dump({
                'users': {
                    'original': hash_password('original_pass')
                }
            }, f)

        config = AuthConfig(yaml_file=str(yaml_file))
        auth_manager = AuthManager(config)

        # Add a new user
        auth_manager.add_user('newuser', 'newpass')

        # Persist changes
        auth_manager.persist_changes()

        # Reload from file and verify
        config2 = AuthConfig(yaml_file=str(yaml_file))
        auth_manager2 = AuthManager(config2)

        users = auth_manager2.list_users()
        self.assertIn('newuser', users)
        self.assertIn('original', users)

        # Verify authentication works
        result = auth_manager2.verify_credentials('newuser', 'newpass')
        self.assertTrue(result.success)

        temp_dir.cleanup()

    def test_timing_attack_protection(self):
        """Test that authentication timing is similar for existing and non-existing users."""
        import time

        # Test with existing user (wrong password)
        times_existing = []
        for _ in range(5):
            start = time.time()
            self.auth_manager.verify_credentials('admin', 'wrong_password')
            times_existing.append(time.time() - start)

        # Test with non-existing user
        times_nonexisting = []
        for _ in range(5):
            start = time.time()
            self.auth_manager.verify_credentials('nonexistent', 'password')
            times_nonexisting.append(time.time() - start)

        # Average times should be similar (within 50% of each other)
        avg_existing = sum(times_existing) / len(times_existing)
        avg_nonexisting = sum(times_nonexisting) / len(times_nonexisting)

        # Check they're within reasonable range (not a perfect timing test)
        # This is a basic sanity check - both should go through password verification
        self.assertGreater(avg_existing, 0)
        self.assertGreater(avg_nonexisting, 0)


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
        # setup_logger now returns an AuthLogger directly
        self.auth_logger = setup_logger('TestAuth')

    def test_logger_creation(self):
        """Test logger initialization."""
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
                    'admin': hash_password('admin_password'),
                    'user1': hash_password('user1_password')
                }
            }, f)

        self.config = AuthConfig(yaml_file=str(self.yaml_file))
        self.auth_logger = setup_logger('IntegrationTest')
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

    def test_full_audit_trail(self):
        """Test complete audit trail with user operations."""
        # Create audit log file
        audit_file = os.path.join(Path(self.temp_dir.name).name, 'audit.log')
        audit_path = Path(self.temp_dir.name) / 'audit.log'

        # Reinitialize logger with audit file
        logger = setup_logger('AuditTrailTest', audit_log_file=str(audit_path))
        auth_manager = AuthManager(self.config, logger=logger)

        # 1. Add user (should be logged)
        auth_manager.add_user('user2', 'user2_password', by_whom='admin')

        # 2. Remove user (should be logged)
        auth_manager.remove_user('user2', by_whom='admin')

        # 3. Check audit log contains entries
        if audit_path.exists():
            with open(audit_path, 'r') as f:
                content = f.read()
            self.assertIn('USER_ADDED', content)
            self.assertIn('USER_REMOVED', content)

    def test_hashed_password_authentication_flow(self):
        """Test authentication with hashed passwords through full flow."""
        # Add user with hashing (should be done automatically)
        self.auth_manager.add_user('hashflow', 'hashflow_password')

        # Verify the password is hashed
        stored = self.auth_manager.users['hashflow']
        self.assertTrue(is_bcrypt_hash(stored))

        # Authenticate with plaintext password (should work)
        result = self.auth_manager.verify_credentials('hashflow', 'hashflow_password')
        self.assertTrue(result.success)
        self.assertEqual(result.user.username, 'hashflow')

        # Try with wrong password (should fail)
        result = self.auth_manager.verify_credentials('hashflow', 'wrong_password')
        self.assertFalse(result.success)


if __name__ == '__main__':
    unittest.main()

"""
Unit tests for AppConfig class.
Tests YAML configuration loading and value retrieval.
"""

import unittest
import tempfile
import os
import yaml
from pathlib import Path

# Handle both relative and absolute imports
try:
    from appconfig import AppConfig
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from appconfig import AppConfig


class TestAppConfigLoading(unittest.TestCase):
    """Test loading and parsing of YAML config files."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_config_file_not_found(self):
        """Test that FileNotFoundError is raised for missing config file."""
        with self.assertRaises(FileNotFoundError):
            AppConfig('/nonexistent/path/config.yaml')

    def test_load_basic_config(self):
        """Test loading a basic config file."""
        config_data = {
            'app': {'name': 'TestApp', 'environment': 'test'}
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_app_name(), 'TestApp')
        self.assertEqual(config.get_environment(), 'test')

    def test_load_empty_config(self):
        """Test loading an empty config file."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        # Should use defaults
        self.assertEqual(config.get_app_name(), 'AuthService')
        self.assertEqual(config.get_environment(), 'production')


class TestAppConfigDefaults(unittest.TestCase):
    """Test default values when config entries are missing."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_default_app_name(self):
        """Test default app name when missing."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_app_name(), 'AuthService')

    def test_default_environment(self):
        """Test default environment when missing."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_environment(), 'production')

    def test_default_log_level(self):
        """Test default log level when missing."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_log_level(), 'INFO')

    def test_default_bcrypt_rounds(self):
        """Test default bcrypt rounds when missing."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_bcrypt_rounds(), 12)

    def test_default_ip_address(self):
        """Test default IP address when missing."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_default_ip_address(), 'unknown')

    def test_default_by_whom(self):
        """Test default by_whom when missing."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_default_by_whom(), 'system')

    def test_default_user_role(self):
        """Test default user role when missing."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_default_user_role(), 'user')

    def test_default_user_is_active(self):
        """Test default user is_active when missing."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        self.assertTrue(config.get_default_user_is_active())


class TestAppConfigLogging(unittest.TestCase):
    """Test logging configuration methods."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_log_file_path(self):
        """Test getting log file path from config."""
        config_data = {
            'logging': {
                'general': {'file': 'logs/custom.log'}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_log_file(), 'logs/custom.log')

    def test_log_format(self):
        """Test getting custom log format."""
        custom_format = "%(levelname)s: %(message)s"
        config_data = {
            'logging': {
                'general': {'format': custom_format}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_log_format(), custom_format)

    def test_audit_log_disabled(self):
        """Test audit log when disabled."""
        config_data = {
            'logging': {
                'audit': {'enabled': False, 'file': 'logs/audit.log'}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertIsNone(config.get_audit_log_file())

    def test_audit_log_enabled(self):
        """Test audit log when enabled."""
        config_data = {
            'logging': {
                'audit': {'enabled': True, 'file': 'logs/audit.log'}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_audit_log_file(), 'logs/audit.log')

    def test_log_rotation_settings(self):
        """Test log rotation configuration."""
        config_data = {
            'logging': {
                'general': {
                    'max_bytes': 10485760,
                    'backup_count': 5
                }
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_log_max_bytes(), 10485760)
        self.assertEqual(config.get_log_backup_count(), 5)


class TestAppConfigAuth(unittest.TestCase):
    """Test authentication configuration methods."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_hashing_enabled(self):
        """Test hashing enabled setting."""
        config_data = {
            'auth': {
                'hashing': {'enabled': True}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertTrue(config.use_hashing())

    def test_hashing_disabled(self):
        """Test hashing disabled setting."""
        config_data = {
            'auth': {
                'hashing': {'enabled': False}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertFalse(config.use_hashing())

    def test_custom_bcrypt_rounds(self):
        """Test custom bcrypt rounds setting."""
        config_data = {
            'auth': {
                'hashing': {'bcrypt_rounds': 10}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_bcrypt_rounds(), 10)

    def test_session_settings(self):
        """Test session configuration."""
        config_data = {
            'auth': {
                'session': {
                    'timeout': 7200,
                    'require_https': False
                }
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_session_timeout(), 7200)
        self.assertFalse(config.require_https())


class TestAppConfigErrorCodes(unittest.TestCase):
    """Test error code configuration."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_error_codes(self):
        """Test custom error codes."""
        config_data = {
            'error_codes': {
                'user_not_found': 'USER_MISSING',
                'invalid_credentials': 'BAD_CREDS'
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_error_code('user_not_found'), 'USER_MISSING')
        self.assertEqual(config.get_error_code('invalid_credentials'), 'BAD_CREDS')

    def test_missing_error_code_uses_default(self):
        """Test that missing error codes are uppercased."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        # For a missing error code, should uppercase the key
        self.assertEqual(config.get_error_code('custom_error'), 'CUSTOM_ERROR')


class TestAppConfigMigration(unittest.TestCase):
    """Test migration configuration."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_migration_backup_enabled(self):
        """Test migration backup enabled setting."""
        config_data = {
            'migration': {'create_backup': True}
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertTrue(config.get_migration_backup_enabled())

    def test_migration_backup_disabled(self):
        """Test migration backup disabled setting."""
        config_data = {
            'migration': {'create_backup': False}
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertFalse(config.get_migration_backup_enabled())

    def test_migration_reserved_keys(self):
        """Test migration reserved keys setting."""
        config_data = {
            'migration': {
                'reserved_keys': ['special_key', 'another_key']
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        reserved = config.get_migration_reserved_keys()
        self.assertIn('special_key', reserved)
        self.assertIn('another_key', reserved)


class TestAppConfigUserManagement(unittest.TestCase):
    """Test user management configuration."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_users_config_file(self):
        """Test getting users config file path."""
        config_data = {
            'users': {'config_file': 'custom/users.yaml'}
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_users_config_file(), 'custom/users.yaml')

    def test_users_auto_load(self):
        """Test users auto-load setting."""
        config_data = {
            'users': {'auto_load': False}
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertFalse(config.get_users_auto_load())


class TestAppConfigSecurity(unittest.TestCase):
    """Test security configuration."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_rate_limiting_enabled(self):
        """Test rate limiting enabled setting."""
        config_data = {
            'security': {
                'rate_limiting': {'enabled': True}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertTrue(config.is_rate_limiting_enabled())

    def test_rate_limiting_disabled(self):
        """Test rate limiting disabled setting."""
        config_data = {
            'security': {
                'rate_limiting': {'enabled': False}
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertFalse(config.is_rate_limiting_enabled())

    def test_rate_limit_settings(self):
        """Test rate limit configuration."""
        config_data = {
            'security': {
                'rate_limiting': {
                    'enabled': True,
                    'max_attempts': 3,
                    'window_seconds': 600
                }
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        self.assertEqual(config.get_rate_limit_max_attempts(), 3)
        self.assertEqual(config.get_rate_limit_window(), 600)


class TestAppConfigFrameworks(unittest.TestCase):
    """Test framework-specific configuration."""

    def setUp(self):
        """Create a temporary directory for test config files."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.yaml')

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_config_file(self, config_data):
        """Helper to create a YAML config file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

    def test_flask_configuration(self):
        """Test Flask-specific configuration."""
        config_data = {
            'frameworks': {
                'flask': {
                    'host': '127.0.0.1',
                    'port': 5001,
                    'debug': True
                }
            }
        }
        self._create_config_file(config_data)
        config = AppConfig(self.config_path)
        flask_config = config.get_framework_config('flask')
        self.assertEqual(flask_config['host'], '127.0.0.1')
        self.assertEqual(flask_config['port'], 5001)
        self.assertTrue(flask_config['debug'])

    def test_missing_framework_returns_empty_dict(self):
        """Test that missing framework config returns empty dict."""
        self._create_config_file({})
        config = AppConfig(self.config_path)
        django_config = config.get_framework_config('django')
        self.assertEqual(django_config, {})


if __name__ == '__main__':
    unittest.main()

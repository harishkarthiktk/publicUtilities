"""
Tests for password hashing functionality using bcrypt.
"""

import unittest
import tempfile
import os
import yaml
from datetime import datetime

# Handle imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from authservice.hashing import (
    hash_password,
    verify_password,
    is_bcrypt_hash,
    migrate_users_dict,
    migrate_yaml_file
)


class TestHashPassword(unittest.TestCase):
    """Test password hashing functionality."""

    def test_hash_password_returns_string(self):
        """hash_password should return a string."""
        result = hash_password("test_password")
        self.assertIsInstance(result, str)

    def test_hash_password_returns_bcrypt_format(self):
        """Hash should be in bcrypt format ($2b$12$...)."""
        result = hash_password("test_password")
        self.assertTrue(result.startswith("$2b$") or result.startswith("$2a$"))
        self.assertEqual(len(result), 60)

    def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (due to salt)."""
        password = "test_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        self.assertNotEqual(hash1, hash2)

    def test_hash_password_with_special_characters(self):
        """Should handle passwords with special characters."""
        passwords = [
            "p@ssw0rd!",
            "password with spaces",
            "пароль",  # Russian
            "パスワード",  # Japanese
            "café",  # Accented characters
        ]
        for pwd in passwords:
            result = hash_password(pwd)
            self.assertTrue(is_bcrypt_hash(result))

    def test_hash_password_type_error(self):
        """Should raise TypeError for non-string input."""
        with self.assertRaises(TypeError):
            hash_password(12345)

        with self.assertRaises(TypeError):
            hash_password(None)

    def test_hash_password_empty_string(self):
        """Should handle empty string."""
        result = hash_password("")
        self.assertTrue(is_bcrypt_hash(result))


class TestVerifyPassword(unittest.TestCase):
    """Test password verification."""

    def setUp(self):
        """Set up test password and hash."""
        self.password = "test_password"
        self.password_hash = hash_password(self.password)

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        result = verify_password(self.password, self.password_hash)
        self.assertTrue(result)

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        result = verify_password("wrong_password", self.password_hash)
        self.assertFalse(result)

    def test_verify_password_case_sensitive(self):
        """Password verification should be case-sensitive."""
        result = verify_password(self.password.upper(), self.password_hash)
        self.assertFalse(result)

    def test_verify_password_empty_string(self):
        """Should handle empty string verification."""
        empty_hash = hash_password("")
        result = verify_password("", empty_hash)
        self.assertTrue(result)

    def test_verify_password_invalid_hash_format(self):
        """Should return False for invalid hash format."""
        result = verify_password(self.password, "not_a_valid_hash")
        self.assertFalse(result)

    def test_verify_password_type_error(self):
        """Should raise TypeError for non-string input."""
        with self.assertRaises(TypeError):
            verify_password(12345, self.password_hash)

        with self.assertRaises(TypeError):
            verify_password(self.password, None)


class TestIsBcryptHash(unittest.TestCase):
    """Test bcrypt hash detection."""

    def test_valid_bcrypt_hash(self):
        """Should detect valid bcrypt hashes."""
        test_hash = hash_password("test")
        self.assertTrue(is_bcrypt_hash(test_hash))

    def test_invalid_plaintext(self):
        """Should reject plaintext strings."""
        self.assertFalse(is_bcrypt_hash("plaintext_password"))

    def test_invalid_format_short(self):
        """Should reject hashes that are too short."""
        self.assertFalse(is_bcrypt_hash("$2b$12$short"))

    def test_invalid_format_wrong_prefix(self):
        """Should reject hashes with wrong prefix."""
        self.assertFalse(is_bcrypt_hash("$1$12$" + "x" * 53))

    def test_valid_bcrypt_variants(self):
        """Should accept all bcrypt variants ($2a, $2b, $2x, $2y)."""
        # We can't easily generate these, but we can test the logic
        for variant in ["$2a$", "$2b$", "$2x$", "$2y$"]:
            # Create a string that looks like a bcrypt hash
            fake_hash = variant + "12$" + "x" * 53
            self.assertTrue(is_bcrypt_hash(fake_hash))

    def test_non_string_input(self):
        """Should return False for non-string input."""
        self.assertFalse(is_bcrypt_hash(None))
        self.assertFalse(is_bcrypt_hash(12345))
        self.assertFalse(is_bcrypt_hash([]))


class TestMigrateUsersDict(unittest.TestCase):
    """Test migration of user dictionaries."""

    def test_migrate_plaintext_users(self):
        """Should convert plaintext passwords to hashes."""
        users = {
            "admin": "admin_password",
            "user1": "user1_password"
        }

        migrated = migrate_users_dict(users)

        self.assertEqual(len(migrated), 2)
        self.assertIn("admin", migrated)
        self.assertIn("user1", migrated)

        # Check all are hashes
        for username, password_hash in migrated.items():
            self.assertTrue(is_bcrypt_hash(password_hash))

        # Check original passwords still verify
        self.assertTrue(verify_password("admin_password", migrated["admin"]))
        self.assertTrue(verify_password("user1_password", migrated["user1"]))

    def test_migrate_already_hashed_users(self):
        """Should not re-hash already hashed passwords."""
        original_hash = hash_password("password")
        users = {
            "admin": original_hash,
            "user1": "plaintext"
        }

        migrated = migrate_users_dict(users)

        # The already-hashed password should be unchanged
        self.assertEqual(migrated["admin"], original_hash)
        # The plaintext should be hashed
        self.assertTrue(is_bcrypt_hash(migrated["user1"]))

    def test_migrate_mixed_users(self):
        """Should handle mixed plaintext and hashed passwords."""
        hash1 = hash_password("password1")
        users = {
            "user1": hash1,
            "user2": "plaintext2",
            "user3": "plaintext3"
        }

        migrated = migrate_users_dict(users)

        self.assertEqual(migrated["user1"], hash1)
        self.assertNotEqual(migrated["user2"], "plaintext2")
        self.assertNotEqual(migrated["user3"], "plaintext3")

    def test_migrate_empty_dict(self):
        """Should handle empty user dictionary."""
        users = {}
        migrated = migrate_users_dict(users)
        self.assertEqual(len(migrated), 0)

    def test_migrate_type_error(self):
        """Should raise TypeError for non-dict input."""
        with self.assertRaises(TypeError):
            migrate_users_dict("not_a_dict")

        with self.assertRaises(TypeError):
            migrate_users_dict(None)


class TestMigrateYamlFile(unittest.TestCase):
    """Test YAML file migration."""

    def setUp(self):
        """Create temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        for file in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(self.test_dir)

    def test_migrate_yaml_with_users_key(self):
        """Should migrate YAML file with 'users' key."""
        yaml_file = os.path.join(self.test_dir, "users.yaml")
        config = {
            "users": {
                "admin": "admin_password",
                "user1": "user1_password"
            }
        }

        with open(yaml_file, 'w') as f:
            yaml.dump(config, f)

        migrate_yaml_file(yaml_file, backup=False)

        with open(yaml_file, 'r') as f:
            migrated = yaml.safe_load(f)

        # Check all passwords are hashed
        for username, password_hash in migrated["users"].items():
            self.assertTrue(is_bcrypt_hash(password_hash))

        # Check passwords still verify
        self.assertTrue(verify_password("admin_password", migrated["users"]["admin"]))

    def test_migrate_yaml_flat_structure(self):
        """Should migrate YAML with flat username:password structure."""
        yaml_file = os.path.join(self.test_dir, "users.yaml")
        config = {
            "admin": "admin_password",
            "user1": "user1_password"
        }

        with open(yaml_file, 'w') as f:
            yaml.dump(config, f)

        migrate_yaml_file(yaml_file, backup=False)

        with open(yaml_file, 'r') as f:
            migrated = yaml.safe_load(f)

        # Check all passwords are hashed (but not auth_type etc if present)
        self.assertTrue(is_bcrypt_hash(migrated["admin"]))
        self.assertTrue(is_bcrypt_hash(migrated["user1"]))

    def test_migrate_yaml_creates_backup(self):
        """Should create .bak backup file."""
        yaml_file = os.path.join(self.test_dir, "users.yaml")
        config = {"users": {"admin": "password"}}

        with open(yaml_file, 'w') as f:
            yaml.dump(config, f)

        migrate_yaml_file(yaml_file, backup=True)

        backup_file = yaml_file + ".bak"
        self.assertTrue(os.path.exists(backup_file))

        # Check backup contains original plaintext
        with open(backup_file, 'r') as f:
            backup_config = yaml.safe_load(f)
        self.assertEqual(backup_config["users"]["admin"], "password")

    def test_migrate_yaml_no_duplicate_backup(self):
        """Should not overwrite existing backup."""
        yaml_file = os.path.join(self.test_dir, "users.yaml")
        backup_file = yaml_file + ".bak"

        # Create backup with marker
        with open(backup_file, 'w') as f:
            f.write("ORIGINAL_BACKUP")

        config = {"users": {"admin": "password"}}
        with open(yaml_file, 'w') as f:
            yaml.dump(config, f)

        migrate_yaml_file(yaml_file, backup=True)

        # Backup should still be original
        with open(backup_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "ORIGINAL_BACKUP")

    def test_migrate_yaml_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        yaml_file = os.path.join(self.test_dir, "nonexistent.yaml")
        with self.assertRaises(FileNotFoundError):
            migrate_yaml_file(yaml_file)

    def test_migrate_yaml_preserves_other_config(self):
        """Should preserve non-user configuration."""
        yaml_file = os.path.join(self.test_dir, "users.yaml")
        config = {
            "users": {
                "admin": "admin_password"
            },
            "auth_type": "http_basic",
            "log_level": "INFO"
        }

        with open(yaml_file, 'w') as f:
            yaml.dump(config, f)

        migrate_yaml_file(yaml_file, backup=False)

        with open(yaml_file, 'r') as f:
            migrated = yaml.safe_load(f)

        # Check other config is preserved
        self.assertEqual(migrated.get("auth_type"), "http_basic")
        self.assertEqual(migrated.get("log_level"), "INFO")
        # Check user password is hashed
        self.assertTrue(is_bcrypt_hash(migrated["users"]["admin"]))

    def test_migrate_yaml_with_special_characters(self):
        """Should handle passwords with special characters."""
        yaml_file = os.path.join(self.test_dir, "users.yaml")
        config = {
            "users": {
                "user1": "p@ssw0rd!",
                "user2": "password with spaces"
            }
        }

        with open(yaml_file, 'w') as f:
            yaml.dump(config, f)

        migrate_yaml_file(yaml_file, backup=False)

        with open(yaml_file, 'r') as f:
            migrated = yaml.safe_load(f)

        # Verify special character passwords work
        self.assertTrue(verify_password("p@ssw0rd!", migrated["users"]["user1"]))
        self.assertTrue(verify_password("password with spaces", migrated["users"]["user2"]))


if __name__ == "__main__":
    unittest.main()

"""
Tests for audit logging functionality.
"""

import unittest
import tempfile
import os
import logging

# Handle imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from authservice.logger import setup_logger, AuthLogger


class TestAuditLogging(unittest.TestCase):
    """Test audit logging functionality."""

    def setUp(self):
        """Set up test audit log file."""
        self.test_dir = tempfile.mkdtemp()
        self.audit_log_file = os.path.join(self.test_dir, "audit.log")

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _read_audit_log(self):
        """Helper to read audit log file."""
        if os.path.exists(self.audit_log_file):
            with open(self.audit_log_file, 'r') as f:
                return f.read()
        return ""

    def test_setup_logger_with_audit_file(self):
        """Should create separate audit log file."""
        logger = setup_logger(
            name="test_logger",
            audit_log_file=self.audit_log_file
        )

        # Log an audit event
        logger.log_user_added("testuser", "admin", "127.0.0.1")

        # Audit file should exist
        self.assertTrue(os.path.exists(self.audit_log_file))

    def test_setup_logger_without_audit_file(self):
        """Should work without audit log file."""
        logger = setup_logger(name="test_logger_2")
        # Should not raise any exception
        logger.log_user_added("testuser", "admin", "127.0.0.1")

    def test_audit_logger_init(self):
        """AuthLogger should initialize with optional audit handler."""
        test_logger = logging.getLogger("test")
        auth_logger = AuthLogger(test_logger)
        self.assertIsNotNone(auth_logger.logger)
        self.assertIsNone(auth_logger.audit_handler)

    def test_log_user_added_format(self):
        """log_user_added should produce correct format."""
        logger = setup_logger(
            name="test_user_added",
            audit_log_file=self.audit_log_file
        )

        logger.log_user_added(
            username="testuser",
            by_whom="admin",
            ip_address="192.168.1.1"
        )

        content = self._read_audit_log()
        self.assertIn("[AUDIT]", content)
        self.assertIn("USER_ADDED", content)
        self.assertIn("username=testuser", content)
        self.assertIn("by=admin", content)
        self.assertIn("ip=192.168.1.1", content)

    def test_log_user_removed_format(self):
        """log_user_removed should produce correct format."""
        logger = setup_logger(
            name="test_user_removed",
            audit_log_file=self.audit_log_file
        )

        logger.log_user_removed(
            username="olduser",
            by_whom="admin",
            ip_address="192.168.1.100"
        )

        content = self._read_audit_log()
        self.assertIn("[AUDIT]", content)
        self.assertIn("USER_REMOVED", content)
        self.assertIn("username=olduser", content)
        self.assertIn("by=admin", content)

    def test_log_user_modified_format(self):
        """log_user_modified should produce correct format."""
        logger = setup_logger(
            name="test_user_modified",
            audit_log_file=self.audit_log_file
        )

        logger.log_user_modified(
            username="testuser",
            field_changed="email",
            by_whom="system",
            ip_address="localhost"
        )

        content = self._read_audit_log()
        self.assertIn("[AUDIT]", content)
        self.assertIn("USER_MODIFIED", content)
        self.assertIn("username=testuser", content)
        self.assertIn("field=email", content)
        self.assertIn("by=system", content)

    def test_log_password_changed_format(self):
        """log_password_changed should produce correct format."""
        logger = setup_logger(
            name="test_password_changed",
            audit_log_file=self.audit_log_file
        )

        logger.log_password_changed(
            username="testuser",
            by_whom="user",
            ip_address="192.168.1.50"
        )

        content = self._read_audit_log()
        self.assertIn("[AUDIT]", content)
        self.assertIn("PASSWORD_CHANGED", content)
        self.assertIn("username=testuser", content)

    def test_audit_log_default_parameters(self):
        """Audit log methods should work with default parameters."""
        logger = setup_logger(
            name="test_defaults",
            audit_log_file=self.audit_log_file
        )

        # Call with minimal parameters
        logger.log_user_added("user1")
        logger.log_user_removed("user1")
        logger.log_user_modified("user1", "field1")
        logger.log_password_changed("user1")

        content = self._read_audit_log()
        self.assertIn("USER_ADDED", content)
        self.assertIn("USER_REMOVED", content)
        self.assertIn("USER_MODIFIED", content)
        self.assertIn("PASSWORD_CHANGED", content)
        self.assertIn("by=system", content)
        self.assertIn("ip=unknown", content)

    def test_multiple_audit_entries(self):
        """Should log multiple audit entries in sequence."""
        logger = setup_logger(
            name="test_multiple",
            audit_log_file=self.audit_log_file
        )

        logger.log_user_added("user1", "admin")
        logger.log_user_added("user2", "admin")
        logger.log_user_removed("user1", "admin")

        content = self._read_audit_log()
        entries = content.strip().split('\n')
        self.assertGreaterEqual(len(entries), 3)

    def test_audit_log_with_special_characters(self):
        """Should handle special characters in audit logs."""
        logger = setup_logger(
            name="test_special",
            audit_log_file=self.audit_log_file
        )

        logger.log_user_added(
            username="user@example.com",
            by_whom="admin/system",
            ip_address="192.168.1.1:8080"
        )

        content = self._read_audit_log()
        self.assertIn("user@example.com", content)
        self.assertIn("admin/system", content)

    def test_audit_log_file_rotation(self):
        """Audit log should support file rotation."""
        logger = setup_logger(
            name="test_rotation",
            audit_log_file=self.audit_log_file,
            max_bytes=100,  # Small size to trigger rotation
            backup_count=2
        )

        # Log many events to trigger rotation
        for i in range(5):
            logger.log_user_added(f"user{i}", "admin")

        # Audit log file should exist
        self.assertTrue(os.path.exists(self.audit_log_file))

    def test_audit_log_timestamps(self):
        """Audit log entries should include timestamps."""
        logger = setup_logger(
            name="test_timestamps",
            audit_log_file=self.audit_log_file
        )

        logger.log_user_added("testuser", "admin")

        content = self._read_audit_log()
        # Should contain [AUDIT] and a timestamp (format: YYYY-MM-DD HH:MM:SS)
        self.assertIn("[AUDIT]", content)
        # Check for date format (basic check)
        import re
        date_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        self.assertIsNotNone(re.search(date_pattern, content))

    def test_audit_log_without_handler_fallback(self):
        """Should fallback to main logger if no audit handler."""
        test_logger = logging.getLogger("test_fallback")
        test_logger.setLevel(logging.INFO)

        # Add a stream handler to capture output
        import io
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        test_logger.addHandler(handler)

        auth_logger = AuthLogger(test_logger)

        # Log audit event (should fallback to main logger)
        auth_logger.log_user_added("testuser")

        output = stream.getvalue()
        self.assertIn("USER_ADDED", output)

    def test_audit_log_directory_creation(self):
        """Should create audit log directory if it doesn't exist."""
        nested_dir = os.path.join(self.test_dir, "logs", "audit")
        audit_log = os.path.join(nested_dir, "audit.log")

        logger = setup_logger(
            name="test_nested",
            audit_log_file=audit_log
        )

        logger.log_user_added("testuser")

        self.assertTrue(os.path.exists(audit_log))

    def test_audit_log_preserves_main_logger_format(self):
        """Audit logs should have different format from main logs."""
        main_log = os.path.join(self.test_dir, "main.log")
        audit_log = os.path.join(self.test_dir, "audit.log")

        logger = setup_logger(
            name="test_format",
            log_file=main_log,
            audit_log_file=audit_log
        )

        logger.log_auth_attempt("user1", "127.0.0.1", True)
        logger.log_user_added("user2", "admin")

        with open(main_log, 'r') as f:
            main_content = f.read()

        with open(audit_log, 'r') as f:
            audit_content = f.read()

        # Main log should contain auth attempt
        self.assertIn("Auth attempt", main_content)

        # Audit log should contain audit entries
        self.assertIn("[AUDIT]", audit_content)
        self.assertIn("USER_ADDED", audit_content)

        # Main log should not have audit prefix
        self.assertNotIn("[AUDIT]", main_content)

    def test_audit_log_with_none_values(self):
        """Should handle None/empty audit values gracefully."""
        logger = setup_logger(
            name="test_none",
            audit_log_file=self.audit_log_file
        )

        # These should not raise exceptions
        logger.log_user_added("user1", by_whom="")
        logger.log_user_modified("user1", field_changed="")

        content = self._read_audit_log()
        self.assertIn("USER_ADDED", content)
        self.assertIn("USER_MODIFIED", content)


if __name__ == "__main__":
    unittest.main()

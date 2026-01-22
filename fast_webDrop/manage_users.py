#!/usr/bin/env python
"""
User management utility for FastWebDrop.
Provides CLI interface to manage users following authService patterns.

Usage:
    python manage_users.py add <username> <password> [--email EMAIL] [--role ROLE]
    python manage_users.py remove <username>
    python manage_users.py change-password <username> <new_password>
    python manage_users.py list
    python manage_users.py info <username>
"""

import sys
import argparse
import os
from pathlib import Path
from authService.authservice import AuthManager, AuthConfig, hash_password, setup_logger


def get_auth_manager():
    """Initialize and return AuthManager with logger."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logger = setup_logger(
        name="UserManagement",
        log_file=str(logs_dir / "auth.log"),
        level="INFO",
        max_bytes=5242880,  # 5MB
        backup_count=5
    )

    config = AuthConfig(yaml_file='users.yaml')
    return AuthManager(config, logger=logger)


def add_user(manager, username, password, email=None, roles=None):
    """Add a new user."""
    try:
        # Check if user already exists
        if manager.get_user_info(username):
            print(f"Error: User '{username}' already exists")
            return False

        # Hash password
        password_hash = hash_password(password, rounds=12)

        # Prepare user data
        user_data = {
            "password": password_hash,
            "is_active": True,
            "roles": roles or ["user"],
            "email": email or "",
            "metadata": {"created_by": "manage_users.py"}
        }

        # Add to in-memory config
        manager.add_user(username, password, by_whom="manage_users.py", ip_address="localhost")
        manager.persist_changes()

        print(f"Successfully added user '{username}'")
        print(f"  - Email: {email or '(none)'}")
        print(f"  - Roles: {', '.join(roles or ['user'])}")
        print(f"  - Active: Yes")
        return True
    except Exception as e:
        print(f"Error adding user: {e}")
        return False


def remove_user(manager, username):
    """Remove a user."""
    try:
        if not manager.get_user_info(username):
            print(f"Error: User '{username}' not found")
            return False

        manager.remove_user(username, by_whom="manage_users.py", ip_address="localhost")
        manager.persist_changes()

        print(f"Successfully removed user '{username}'")
        return True
    except Exception as e:
        print(f"Error removing user: {e}")
        return False


def change_password(manager, username, new_password):
    """Change user password."""
    try:
        if not manager.get_user_info(username):
            print(f"Error: User '{username}' not found")
            return False

        manager.change_password(username, new_password, by_whom="manage_users.py", ip_address="localhost")
        manager.persist_changes()

        print(f"Successfully changed password for '{username}'")
        return True
    except Exception as e:
        print(f"Error changing password: {e}")
        return False


def list_users(manager):
    """List all users."""
    try:
        users = manager.list_users()
        if not users:
            print("No users found")
            return True

        print(f"\nFound {len(users)} user(s):\n")
        for username in users:
            user_info = manager.get_user_info(username)
            if user_info:
                status = "Active" if user_info.get("is_active", True) else "Inactive"
                email = user_info.get("email", "(none)")
                roles = ", ".join(user_info.get("roles", ["user"]))
                print(f"  {username}")
                print(f"    - Email: {email}")
                print(f"    - Roles: {roles}")
                print(f"    - Status: {status}\n")
        return True
    except Exception as e:
        print(f"Error listing users: {e}")
        return False


def show_user_info(manager, username):
    """Show detailed user information."""
    try:
        user_info = manager.get_user_info(username)
        if not user_info:
            print(f"Error: User '{username}' not found")
            return False

        print(f"\nUser Information for '{username}':")
        print(f"  - Email: {user_info.get('email', '(none)')}")
        print(f"  - Status: {'Active' if user_info.get('is_active', True) else 'Inactive'}")
        print(f"  - Roles: {', '.join(user_info.get('roles', ['user']))}")
        print(f"  - Created: {user_info.get('created_at', 'unknown')}")
        print(f"  - Last Modified: {user_info.get('last_modified', 'never')}")
        print(f"  - Last Login: {user_info.get('last_login', 'never')}\n")
        return True
    except Exception as e:
        print(f"Error retrieving user info: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage FastWebDrop users",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_users.py add alice pass123 --email alice@example.com
  python manage_users.py add bob mypass --role user --role developer
  python manage_users.py remove alice
  python manage_users.py change-password bob newpass456
  python manage_users.py list
  python manage_users.py info bob
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new user')
    add_parser.add_argument('username', help='Username')
    add_parser.add_argument('password', help='Password')
    add_parser.add_argument('--email', help='Email address', default=None)
    add_parser.add_argument('--role', action='append', dest='roles', help='User role (can specify multiple)')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a user')
    remove_parser.add_argument('username', help='Username to remove')

    # Change password command
    passwd_parser = subparsers.add_parser('change-password', help='Change user password')
    passwd_parser.add_argument('username', help='Username')
    passwd_parser.add_argument('password', help='New password')

    # List command
    subparsers.add_parser('list', help='List all users')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show user information')
    info_parser.add_argument('username', help='Username')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Check if users.yaml exists
    if not os.path.exists('users.yaml'):
        print("Error: users.yaml not found. Please ensure it exists in the project root.")
        return 1

    # Get auth manager
    try:
        manager = get_auth_manager()
    except Exception as e:
        print(f"Error initializing AuthManager: {e}")
        return 1

    # Execute command
    if args.command == 'add':
        success = add_user(manager, args.username, args.password, args.email, args.roles)
    elif args.command == 'remove':
        success = remove_user(manager, args.username)
    elif args.command == 'change-password':
        success = change_password(manager, args.username, args.password)
    elif args.command == 'list':
        success = list_users(manager)
    elif args.command == 'info':
        success = show_user_info(manager, args.username)
    else:
        parser.print_help()
        return 1

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

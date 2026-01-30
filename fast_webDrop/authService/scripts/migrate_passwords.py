#!/usr/bin/env python
"""
Migration script to convert plaintext passwords to bcrypt hashes.

Usage:
    python scripts/migrate_passwords.py example_users.yaml
    python scripts/migrate_passwords.py config/users.yaml --backup
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path to import authService modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from authservice.hashing import migrate_yaml_file, is_bcrypt_hash
import yaml


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate plaintext passwords in YAML files to bcrypt hashes"
    )
    parser.add_argument(
        "yaml_file",
        help="Path to YAML file with user credentials"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup file with .bak extension (default: True)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_false",
        dest="backup",
        help="Don't create backup file"
    )

    args = parser.parse_args()

    yaml_file = args.yaml_file

    # Validate file exists
    if not os.path.exists(yaml_file):
        print(f"❌ Error: File not found: {yaml_file}")
        return 1

    # Load and inspect file
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if config is None:
            print("❌ Error: Empty or invalid YAML file")
            return 1

        # Count users to migrate
        users_to_migrate = 0
        already_hashed = 0

        if 'users' in config and isinstance(config['users'], dict):
            for username, password in config['users'].items():
                if isinstance(password, str):
                    if is_bcrypt_hash(password):
                        already_hashed += 1
                    else:
                        users_to_migrate += 1
        else:
            # Flat structure
            for key, value in config.items():
                if key not in ['auth_type', 'log_level', 'log_file', 'require_https']:
                    if isinstance(value, str):
                        if is_bcrypt_hash(value):
                            already_hashed += 1
                        else:
                            users_to_migrate += 1

        total_users = users_to_migrate + already_hashed

        print(f"\n📋 Migration Report for: {yaml_file}")
        print(f"   Total users: {total_users}")
        print(f"   Already hashed: {already_hashed}")
        print(f"   Need migration: {users_to_migrate}")

        if users_to_migrate == 0:
            print("\n✅ No migration needed - all passwords are already hashed!")
            return 0

        print(f"\n🔄 Migrating {users_to_migrate} passwords...")

        # Create backup
        if args.backup:
            backup_path = f"{yaml_file}.bak"
            if not os.path.exists(backup_path):
                with open(yaml_file, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                print(f"   ✓ Backup created: {backup_path}")
            else:
                print(f"   ⚠️  Backup already exists: {backup_path}")

        # Perform migration
        try:
            migrate_yaml_file(yaml_file, backup=False)  # We already handled backup
            print(f"\n✅ Migration complete!")
            print(f"   File updated: {yaml_file}")
            print(f"   {users_to_migrate} passwords hashed with bcrypt")

            # Verify
            with open(yaml_file, 'r', encoding='utf-8') as f:
                migrated_config = yaml.safe_load(f)

            verified_hashed = 0
            if 'users' in migrated_config and isinstance(migrated_config['users'], dict):
                for username, password in migrated_config['users'].items():
                    if isinstance(password, str) and is_bcrypt_hash(password):
                        verified_hashed += 1
            else:
                for key, value in migrated_config.items():
                    if key not in ['auth_type', 'log_level', 'log_file', 'require_https']:
                        if isinstance(value, str) and is_bcrypt_hash(value):
                            verified_hashed += 1

            if verified_hashed == total_users:
                print(f"   ✓ Verification passed: all {total_users} passwords verified as hashed\n")
                return 0
            else:
                print(f"   ⚠️  Verification warning: expected {total_users} hashed, found {verified_hashed}\n")
                return 0

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            if args.backup:
                print(f"   Your original file is safe in: {backup_path}")
            return 1

    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML file: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Algorithm-to-Algorithm Password Migration - Implementation Plan

## Overview
Implement support for migrating passwords between different hashing algorithms (SHA256→bcrypt, MD5→bcrypt, Argon2→bcrypt, etc.) and remove the unnecessary plaintext password migration functionality. Provide both runtime automatic migration during login and a separate batch migration script.

## Current Problem
**Current migration system is limited:**
- Only supports plaintext→bcrypt migration (not needed)
- Cannot migrate between hashing algorithms (SHA256, MD5, Argon2 → bcrypt)
- `_compare_passwords()` in core.py only accepts bcrypt hashes
- No support for gradual migration during user authentication

**Current files that need changes:**
- `scripts/migrate_passwords.py` - Only handles plaintext→bcrypt
- `hashing.py` - `migrate_yaml_file()` assumes plaintext input
- `core.py:239-243` - Rejects non-bcrypt hashes entirely

## Proposed Solution
Create a flexible algorithm migration system that:
1. **Detects** hash algorithm automatically (SHA256, MD5, SHA512, Argon2, PBKDF2, bcrypt)
2. **Verifies** passwords using the detected algorithm
3. **Migrates automatically** during login (runtime migration)
4. **Provides separate script** for batch migration when plaintext passwords are available
5. **Removes** plaintext migration functionality

---

## Implementation Phases

### PHASE 1: Hash Algorithm Detection (1-2 hours)

#### 1.1 Create hash_detection.py module
**File**: `hash_detection.py` (NEW - ~150 lines)

Key features:
- Auto-detection by hash format (length, prefix, pattern)
- Supports 6 common algorithms: bcrypt, SHA256, SHA512, MD5, Argon2, PBKDF2
- Returns 'unknown' for unrecognized formats
- Type hints for safety

---

### PHASE 2: Legacy Algorithm Verification (2-3 hours)

#### 2.1 Create legacy_verify.py module
**File**: `legacy_verify.py` (NEW - ~200 lines)

Key features:
- Supports common legacy algorithms
- Handles both salted and unsalted hashes
- Graceful degradation (Argon2 requires extra dependency)
- Clear security warnings for weak algorithms (MD5)

---

### PHASE 3: Runtime Migration in Core (2-3 hours)

#### 3.1 Update core.py - Modify _compare_passwords()
**File**: `core.py` (MODIFY - lines 224-245)

Key changes:
- Import detection and verification functions
- Auto-detect algorithm from hash format
- Verify using appropriate algorithm
- **Automatically migrate** to bcrypt on successful login
- Log migration events for audit trail
- Handle errors gracefully

#### 3.2 Update verify_credentials() to pass username
**File**: `core.py:144` (MODIFY)

Pass username parameter to _compare_passwords for logging.

#### 3.3 Add update_user_password() to AuthConfig
**File**: `config.py` (MODIFY)

New method to update password hash in YAML file during runtime migration.

---

### PHASE 4: Create Batch Migration Script (2-3 hours)

#### 4.1 Create scripts/migrate_hash_algorithms.py
**File**: `scripts/migrate_hash_algorithms.py` (NEW - ~300 lines)

Key features:
- Requires plaintext passwords (from CSV or JSON file)
- Verifies old hash before migrating (safety check)
- Supports auto-detection or explicit algorithm specification
- Detailed progress reporting
- Backup creation before migration

---

### PHASE 5: Remove Plaintext Migration (1 hour)

#### 5.1 Deprecate functions in hashing.py
**File**: `hashing.py` (MODIFY)

- Add deprecation warnings to `migrate_users_dict()`
- Add deprecation warnings to `migrate_yaml_file()`

#### 5.2 Mark scripts/migrate_passwords.py as deprecated
**File**: `scripts/migrate_passwords.py` (MODIFY or RENAME)

Add deprecation notice at top of file.

#### 5.3 Update __init__.py exports
**File**: `__init__.py` (MODIFY)

Remove or mark migration functions as deprecated. Export new detection/verification functions.

---

### PHASE 6: Update Tests (3-4 hours)

#### 6.1 Create tests/test_hash_detection.py
**File**: `tests/test_hash_detection.py` (NEW - ~200 lines)

Test all algorithm detection functions with known hash values.

#### 6.2 Create tests/test_legacy_verify.py
**File**: `tests/test_legacy_verify.py` (NEW - ~250 lines)

Test all legacy verification functions with known test vectors.

#### 6.3 Create tests/test_algorithm_migration.py
**File**: `tests/test_algorithm_migration.py` (NEW - ~300 lines)

Test runtime algorithm migration during login scenarios.

#### 6.4 Update existing tests
**Files**: Update tests that use the deprecated migration functions.

---

### PHASE 7: Update Documentation (2-3 hours)

#### 7.1 Create ALGORITHM_MIGRATION.md
**File**: `ALGORITHM_MIGRATION.md` (NEW - ~400 lines)

Complete documentation covering:
- Why algorithm migration is needed
- Supported algorithms
- Runtime migration (automatic during login)
- Batch migration script usage
- Security considerations
- Examples for each algorithm
- Troubleshooting

#### 7.2 Update README.md
**File**: `README.md` (MODIFY)

- Remove plaintext password migration references
- Add new section on algorithm migration

#### 7.3 Update QUICKSTART.md
**File**: `QUICKSTART.md` (MODIFY)

- Remove plaintext migration step
- Add algorithm migration section

#### 7.4 Create or update MIGRATION.md
**File**: `MIGRATION.md` (MODIFY or RENAME)

Mark old migration guide as deprecated.

---

## Critical Files Summary

### Files to CREATE (7 new files):
1. `hash_detection.py` (~150 lines) - Hash algorithm detection
2. `legacy_verify.py` (~200 lines) - Legacy algorithm verification
3. `scripts/migrate_hash_algorithms.py` (~300 lines) - Batch migration script
4. `tests/test_hash_detection.py` (~200 lines) - Detection tests
5. `tests/test_legacy_verify.py` (~250 lines) - Verification tests
6. `tests/test_algorithm_migration.py` (~300 lines) - Migration tests
7. `ALGORITHM_MIGRATION.md` (~400 lines) - Comprehensive migration guide

### Files to MODIFY (7 files):
1. `core.py` - Update `_compare_passwords()` for runtime migration
2. `core.py` - Update `verify_credentials()` to pass username
3. `config.py` - Add `update_user_password()` method
4. `hashing.py` - Deprecate `migrate_users_dict()` and `migrate_yaml_file()`
5. `__init__.py` - Export new detection/verification functions
6. `README.md` - Add algorithm migration section
7. `QUICKSTART.md` - Update migration references

### Files to DEPRECATE (1 file):
1. `scripts/migrate_passwords.py` - Mark as deprecated or rename

---

## Verification & Testing Plan

### 1. Unit Tests
```bash
python -m unittest tests.test_hash_detection -v
python -m unittest tests.test_legacy_verify -v
python -m unittest tests.test_algorithm_migration -v
python -m unittest discover tests/ -v
```

### 2. Runtime Migration Test
- Create test users.yaml with SHA256 hashes
- Verify login triggers migration
- Confirm password is now bcrypt

### 3. Batch Migration Script Test
- Create test files with plaintext passwords
- Run migration script
- Verify all users migrated to bcrypt

### 4. Algorithm Detection Test
- Test detection for all 6 algorithms
- Verify correct identification

### 5. Integration Test
- Full end-to-end test from SHA256 to bcrypt
- Test multiple users with different algorithms

---

## Backward Compatibility

### Breaking Changes:
None - all changes are additive

### Deprecated Features:
- `migrate_users_dict()` in hashing.py (still works, emits warning)
- `migrate_yaml_file()` in hashing.py (still works, emits warning)
- `scripts/migrate_passwords.py` (marked deprecated)

### Migration Path for Users:
1. **No action required** for most users - runtime migration handles everything
2. **Optional:** Use new batch migration script if you have plaintext passwords
3. **Recommended:** Update documentation references from old to new migration guide

---

## Benefits Summary

✅ **Algorithm Flexibility** - Supports 6 common hashing algorithms
✅ **Automatic Migration** - Happens during login, zero user impact
✅ **Security Improvement** - Migrates from weak (MD5) to strong (bcrypt)
✅ **Batch Migration** - Script for offline migration with plaintext passwords
✅ **Audit Trail** - Logs all migration events
✅ **Backward Compatible** - Old code continues to work
✅ **Detection Agnostic** - Auto-detects algorithm by hash format
✅ **Graceful Degradation** - Handles missing dependencies (Argon2)

---

## Security Considerations

### Runtime Migration Safety
1. **Verification before migration** - Old hash must verify before migrating
2. **Atomic updates** - YAML file updated only if verification succeeds
3. **Audit logging** - All migrations logged with username and algorithms
4. **No password exposure** - Plaintext password only in memory during login

### Batch Migration Safety
1. **Backup creation** - Automatic backup before migration
2. **Verification step** - Verifies plaintext matches old hash before migrating
3. **Detailed reporting** - Shows success/failure for each user
4. **Rollback possible** - Backup file allows restoration

### Algorithm Support Rationale
- **bcrypt** - Target algorithm, industry standard
- **SHA256/SHA512** - Common in older systems, no salt support
- **MD5** - Legacy support only, immediate migration with warning
- **Argon2** - Modern algorithm, optional dependency
- **PBKDF2** - Django-style support

---

## Implementation Notes

### Why Not Support Plaintext Migration?
1. **Security risk** - Storing plaintext passwords is never acceptable
2. **False security** - If plaintext is in YAML, system is already compromised
3. **Legacy concern** - Modern systems should never use plaintext
4. **Migration alternative** - Runtime migration handles all practical cases

### Why Runtime Migration?
1. **Zero downtime** - No service interruption
2. **Gradual rollout** - Migrates as users log in naturally
3. **No plaintext needed** - Works with existing hashes
4. **User transparent** - No user action required

### Salt Handling
- **SHA256/SHA512** - Current implementation assumes unsalted (most common)
- **Future enhancement** - Could add salt parameter if needed
- **bcrypt** - Always salted automatically

---

## Success Criteria

✅ Hash detection works for all 6 algorithms (bcrypt, SHA256, SHA512, MD5, Argon2, PBKDF2)
✅ Legacy verification functions correctly verify passwords
✅ Runtime migration automatically converts hashes during login
✅ Migrated hashes are persisted to YAML file
✅ Batch migration script successfully migrates passwords
✅ All 100+ existing tests pass
✅ New tests cover detection, verification, and migration
✅ Documentation completely updated
✅ Deprecated functions emit warnings
✅ No breaking changes to existing code

---

## End of Plan

This plan implements comprehensive algorithm-to-algorithm password migration, removes unnecessary plaintext migration, and provides both automatic runtime migration and a batch migration script for maximum flexibility.

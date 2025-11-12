# Code Review Template

## Code Critique

### Strengths
- [List 4-6 key positives, e.g., clear structure, effective logging]

### Critical Issues & Improvements

## Priority 1: Critical Fixes
[Issues that could cause failures, e.g., bugs, leaks, missing dependencies]

### 1. **[Issue Title]**
**Issue**: [Description and impact].

**Problem Code**:
```python
[Relevant code snippet with line references, e.g., filename.py:line]
```

**Steps to Fix**:
1. [Actionable step 1]
2. [Actionable step 2]
3. [Additional steps as needed]

[Additional Priority 1 issues...]

---

## Priority 2: Code Quality & Maintainability
[Refactoring, magic values, error handling]

### [Number]. **[Issue Title]**
**Issue**: [Description].

**Problem Code**:
```python
[Snippet]
```

**Steps to Improve**:
1. [Step 1]
2. [Step 2]

[Additional issues...]

---

## Priority 3: Architecture & Design
[Global state, validation, testability]

### [Number]. **[Issue Title]**
**Issue**: [Description].

**Problem Code**:
```python
[Snippet]
```

**Steps to Fix**:
1. [Step 1]
2. [Step 2]

[Additional issues...]

---

## Priority 4: Feature Enhancements
[Missing capabilities, e.g., batch processing]

### [Number]. **[Issue Title]**
**Issue**: [Description].

**Steps to Add**:
1. [Step 1]
2. [Step 2]

[Additional issues...]

---

## Priority 5: Polish & User Experience
[Logging, documentation, UX]

### [Number]. **[Issue Title]**
**Issue**: [Description].

**Steps to Add**:
1. [Step 1]
2. [Step 2]

[Additional issues...]

---

## Implementation Order Summary
1. **Phase 1 (Critical)**: Address #1, #2 [from Priority 1]
2. **Phase 2 (Quality)**: Address #[numbers] [from Priority 2]
3. **Phase 3 (Architecture)**: Address #[numbers] [from Priority 3]
4. **Phase 4 (Features)**: Address #[numbers] [from Priority 4]
5. **Phase 5 (Polish)**: Address #[numbers] [from Priority 5]

## Additional Outputs
- **Implementation Task**: Create `impl-task.md` summarizing phases as a checklist with effort estimates (low/medium/high) and verification steps.
- **Guidelines**: Aim for 10-14 issues total. Tailor to language/context. Promote best practices (SOLID, security e.g., use python-dotenv for loading API keys from .env files instead of direct environment variables, testability).
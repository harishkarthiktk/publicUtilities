# Python code implementation guide

## Exception handling

- Group try-except blocks wherever possible to reduce code duplication:
	Try to group all import exceptions under a single try/except block.
	Group related operations that can fail with the same exception types.
- Use specific exception types rather than bare `except:` clauses.
- Include informative error messages that aid debugging.
- Avoid silencing exceptions without logging or handling them appropriately.

---

## Function design

- Target: Keep functions under 30 lines of code (excluding comments, docstrings, and blank lines).
- Principle: Functions should do ONE thing well (single responsibility principle).
- If a function exceeds 30 lines, ask:
	- Can this be split into logical sub-functions?
	- Am I mixing concerns (validation + processing + formatting)?
	- Is this naturally complex (algorithms, configuration) or just poorly organized?
- Acceptable exceptions (document why they're longer):
	- Argument parser setup with many CLI options
	- Comprehensive input validation with multiple fields
	- Complex but cohesive algorithms that lose clarity when split
	- Configuration/initialization functions setting up multiple related components
- Red flags (always refactor):
	- Multiple levels of nested conditionals (>3 levels)
	- Repeated code patterns
	- Function doing validation AND processing AND formatting
	- Long if-elif-else chains (consider dispatch tables or strategy pattern)

---

## Code organization

- Organize imports in the following order: standard library, third-party, local imports (PEP 8).
- Group related imports together and separate groups with blank lines.
- Avoid wildcard imports if possible (`from module import *`).

---

## Naming conventions

- Follow PEP 8 naming standards:
	- `snake_case` for functions, variables, and module names.
	- `PascalCase` for class names.
	- `UPPER_SNAKE_CASE` for constants.
- Use descriptive, meaningful names that convey intent.

---

## Documentation

- If `argparse_impl_guide.md` is present in the same directory, it MUST be used for any argparse implementation.
- Include a module-level docstring describing the module's purpose.
- Document complex algorithms or non-obvious logic with inline comments.
- Keep comments up-to-date with code changes.

---

## Code quality

- Limit line length to 88-100 characters (configurable, but be consistent).
- Use list/dict comprehensions for simple transformations, but prioritize readability.
- Avoid deep nesting (max 3-4 levels); refactor into helper functions if needed.
- Remove dead code, commented-out code blocks, and unused imports.

---

## Testing and validation

### Development phases

#### Phase 1: MVP development

- Focus on functionality over test coverage
- Tests are NOT required during MVP phase
- Exception: Write tests for complex algorithms if they aid development/debugging

#### Phase 2: Post-MVP hardening

- Comprehensive testing REQUIRED before production deployment
- Write unit tests for:
	- All public API functions
	- Critical business logic
	- Complex private functions
	- Integration points
- Test naming: `test_<function>_<scenario>_<expected_outcome>`
- Cover happy paths, edge cases, and error conditions
- Document known issues or technical debt from MVP phase

### Input validation (all phases)

- ALWAYS validate inputs, regardless of development phase:
	- External inputs: CLI args, API requests, file I/O, environment variables
	- Fail fast with specific error messages
	- Use type hints and runtime checks where appropriate
	- Document expected input formats in docstrings
- Validation prevents cascading failures and aids debugging even without formal tests

---

## Logging

- Use the `logging` module instead of print statements for production code.
- Set appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
- Include contextual information in log messages.
- If logging is used, use decorators for function entry/exit logging where appropriate:
	- Decorators are ideal for: cross-cutting concerns like function call tracing, performance timing, and consistent entry/exit logging.
	- Do NOT force decorators for all logging scenarios; inline logging is often more appropriate for business logic, error conditions, and contextual events.
	- Example use case for decorators: `@log_function_call` for debugging function flows.

---

## Performance considerations

- Avoid premature optimization; prioritize readability first.
- Use appropriate data structures (sets for membership tests, deque for queues, etc.).
- Profile code before optimizing bottlenecks.

---

## Security

- Validate and sanitize all external inputs.
- Never hardcode sensitive information (passwords, API keys, etc.); use environment variables or config files unless explicitly done by user for quick testing.
- Use `dotenv` package for handling environment variables.
- Use parameterized queries for database operations to prevent SQL injection.
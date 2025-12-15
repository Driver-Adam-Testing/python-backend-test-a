# Project Standards for Claude Code

## Code Generation Standards

When writing or modifying Python code in this project, always follow these standards:

### Self-Documenting Code

- Use descriptive function and variable names—no `data`, `result`, `temp`, `process`
- Break complex logic into small, well-named helper functions (under 15 lines each)
- Each function does ONE thing
- NO docstrings that restate function names (e.g., `"""Get user by ID."""` on `get_user_by_id`)
- Comments explain WHY, never WHAT—if code is clear, no comment needed
- Good comment example: `# Public visibility takes precedence per product spec v2.3`

### Function Naming

- Action-oriented: `fetch_nodes_with_descriptions`, `validate_user_permissions`
- Private functions start with underscore: `_build_tree_from_nodes`
- Describe WHAT it does, not HOW: `notify_all_users` not `loop_through_users`

### Type Hints (Required)

- ALL function parameters must have type hints
- ALL functions must have return type hints
- Use specific types: `dict[str, Any]` not `dict`
- Use `Literal["a", "b"]` or Enum for constrained string values
- Use defined schemas over raw strings for API parameters

```python
# CORRECT
def set_visibility(node_id: str, vis: Literal["private", "internal", "public"]) -> None:
    ...

# WRONG
def set_visibility(node_id, vis):
    ...
```

### Error Handling

- Try/except blocks must be NARROW—wrap only the specific operation that can fail
- Never use bare `except:` or `except Exception:`
- Use descriptive error messages with context
- Never swallow exceptions silently

```python
# CORRECT
try:
    user = db.users.find_one({"_id": user_id})
except DocumentNotFoundError:
    raise UserNotFoundError(f"No user found with ID: {user_id}")

# WRONG
try:
    user = db.users.find_one({"_id": user_id})
    process(user)
    save(user)
except Exception:
    pass
```

### Code Smells to Avoid

- Functions over 15 lines → extract helpers
- Nesting over 3 levels → use early returns
- Duplicated logic → extract to shared utility
- Inline comments as section dividers → extract to named functions

### Network Requests

- Use `retry_with_exponential_backoff` for critical external API calls
- Always include timeout parameters
- Handle network failures explicitly

### Testing

- Unit tests for business logic
- Integration tests should test REAL behavior, not just mock verification
- Don't write tests that are pure maintenance burden with no value

## Running Commands

Always use Poetry for Python commands:

```bash
# CORRECT
cd backend && poetry run python -m pytest tests/
cd backend && poetry run python scripts/my_script.py

# WRONG
python -m pytest tests/
python scripts/my_script.py
```

## Code Review Mode

When asked to review code, use the `/review` command format and check against all standards above. Report issues with severity levels:

- **blocker**: Must fix (missing types, broad exception handling, duplicated logic)
- **warning**: Should fix (long functions, deep nesting, missing retries on network calls)
- **nit**: Optional improvement (naming could be clearer, minor style)

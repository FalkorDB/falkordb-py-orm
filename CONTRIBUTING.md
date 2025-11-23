# Contributing to FalkorDB Python ORM

Thank you for your interest in contributing to the FalkorDB Python ORM! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Coding Standards](#coding-standards)
7. [Submitting Changes](#submitting-changes)
8. [Reporting Bugs](#reporting-bugs)
9. [Requesting Features](#requesting-features)

## Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)
- FalkorDB instance (local or remote)
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/falkordb-py-orm.git
cd falkordb-py-orm
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/FalkorDB/falkordb-py-orm.git
```

## Development Setup

### Install Dependencies

```bash
# Install poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Start FalkorDB

You need a running FalkorDB instance for testing:

```bash
# Using Docker
docker run -p 6379:6379 falkordb/falkordb:latest

# Or use your existing Redis with FalkorDB module
```

### Verify Setup

```bash
# Run tests to verify everything works
pytest tests/

# Run linters
black --check falkordb_orm/
ruff check falkordb_orm/
mypy falkordb_orm/
```

## Making Changes

### Create a Branch

Create a new branch for your feature or bugfix:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### Development Workflow

1. Make your changes in the appropriate files
2. Add or update tests for your changes
3. Update documentation if needed
4. Run tests and linters locally
5. Commit your changes

### Commit Messages

Write clear, concise commit messages following this format:

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:

```
feat: add support for composite indexes

Added ability to create composite indexes on multiple properties
for improved query performance.

Closes #123
```

```
fix: resolve N+1 query issue in eager loading

Updated QueryBuilder to generate optimized OPTIONAL MATCH
queries for eager loading relationships.
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_repository.py

# Run with coverage
pytest --cov=falkordb_orm --cov-report=html

# Run specific test
pytest tests/test_repository.py::test_save_creates_new_entity
```

### Writing Tests

- Write tests for all new features and bug fixes
- Aim for high test coverage (>80%)
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern
- Use fixtures for common setup

Example:

```python
def test_find_by_age_greater_than_returns_matching_entities():
    # Arrange
    repo = Repository(graph, Person)
    person1 = Person(name="Alice", age=25)
    person2 = Person(name="Bob", age=30)
    repo.save(person1)
    repo.save(person2)
    
    # Act
    results = repo.find_by_age_greater_than(26)
    
    # Assert
    assert len(results) == 1
    assert results[0].name == "Bob"
```

### Integration Tests

Integration tests require a running FalkorDB instance:

```python
# Mark integration tests
@pytest.mark.integration
def test_complex_relationship_loading():
    # Your test here
    pass
```

Run only unit tests:
```bash
pytest -m "not integration"
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications. Key points:

- **Line Length**: 100 characters maximum
- **Imports**: Group stdlib, third-party, and local imports
- **Type Hints**: Use type hints for all public APIs
- **Docstrings**: Use Google-style docstrings

### Code Formatting

We use:
- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking

```bash
# Format code
black falkordb_orm/

# Lint
ruff check falkordb_orm/

# Type check
mypy falkordb_orm/
```

### Docstring Example

```python
def find_by_id(self, entity_id: int, fetch: Optional[List[str]] = None) -> Optional[T]:
    """Find an entity by its ID.
    
    Args:
        entity_id: The ID of the entity to find
        fetch: Optional list of relationships to eager load
        
    Returns:
        The entity if found, None otherwise
        
    Raises:
        QueryException: If the query fails
        
    Example:
        >>> person = repo.find_by_id(1, fetch=["friends"])
        >>> print(person.name)
        Alice
    """
    pass
```

### Type Hints

Always use type hints for public APIs:

```python
from typing import Optional, List, Generic, TypeVar

T = TypeVar('T')

class Repository(Generic[T]):
    def save(self, entity: T) -> T:
        pass
    
    def find_all(self) -> List[T]:
        pass
    
    def find_by_id(self, entity_id: int) -> Optional[T]:
        pass
```

## Submitting Changes

### Pull Request Process

1. **Update your branch** with the latest upstream changes:

```bash
git fetch upstream
git rebase upstream/main
```

2. **Run all checks** before submitting:

```bash
# Format
black falkordb_orm/ tests/

# Lint
ruff check falkordb_orm/ tests/

# Type check
mypy falkordb_orm/

# Test
pytest --cov=falkordb_orm
```

3. **Push to your fork**:

```bash
git push origin feature/your-feature-name
```

4. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what and why
   - Reference to related issues (Fixes #123)
   - Screenshots/examples if applicable

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2

## Testing
- [ ] All tests pass
- [ ] New tests added for changes
- [ ] Manual testing performed

## Related Issues
Fixes #123

## Screenshots (if applicable)
```

### Review Process

- All PRs require at least one approval
- Address review comments promptly
- Keep PRs focused on a single change
- Large changes should be discussed in an issue first

## Reporting Bugs

### Before Reporting

1. Check existing issues to avoid duplicates
2. Verify the bug with the latest version
3. Collect relevant information

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Python version:
- falkordb-orm version:
- FalkorDB version:
- OS:

## Additional Context
Any other relevant information, logs, or screenshots
```

## Requesting Features

### Feature Request Template

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other ways to achieve the same goal

## Additional Context
Examples, mockups, or references
```

## Development Guidelines

### Adding a New Feature

1. **Discuss First**: Open an issue to discuss large features
2. **Design**: Consider the API design and backwards compatibility
3. **Implement**: Follow the existing patterns and conventions
4. **Test**: Write comprehensive tests
5. **Document**: Update docs and examples
6. **Submit**: Create a PR following the guidelines above

### Fixing a Bug

1. **Reproduce**: Write a test that reproduces the bug
2. **Fix**: Implement the fix
3. **Verify**: Ensure the test now passes
4. **Prevent**: Consider adding additional tests
5. **Document**: Update CHANGELOG.md

### Updating Documentation

- Keep documentation in sync with code
- Use examples liberally
- Update API docs for any public API changes
- Check for broken links

## Project Structure

```
falkordb-py-orm/
├── falkordb_orm/          # Source code
│   ├── __init__.py
│   ├── decorators.py
│   ├── repository.py
│   └── ...
├── tests/                 # Test suite
│   ├── test_repository.py
│   └── ...
├── examples/              # Usage examples
├── docs/                  # Documentation
│   └── api/              # API reference
├── pyproject.toml         # Project configuration
└── README.md
```

## Questions?

If you have questions:
- Check existing documentation
- Search existing issues
- Ask in discussions
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to FalkorDB Python ORM! 🎉

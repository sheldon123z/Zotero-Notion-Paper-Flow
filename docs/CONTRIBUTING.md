# Contributing to Paper Flow

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 18+ (for desktop app)
- Git

### Setup Steps

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR-USERNAME/Zotero-Notion-Paper-Flow.git
cd Zotero-Notion-Paper-Flow
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks (optional but recommended):
```bash
pip install pre-commit
pre-commit install
```

## Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

Follow the project structure:
- `src/core/` - Core business logic
- `src/models/` - Data models
- `src/services/` - Service implementations
- `src/interfaces/` - Interface definitions
- `tests/` - Test files

### 3. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/unit/test_processor.py
```

### 4. Code Quality Checks

```bash
# Lint with ruff
ruff check src/

# Type check with mypy
mypy src/

# Security check with bandit
bandit -r src/
```

### 5. Commit Your Changes

Follow conventional commits format:
```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in processor"
git commit -m "docs: update README"
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process or auxiliary tool changes

### 6. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 120 characters
- Use dataclasses for data structures

### Code Organization
- Keep functions small and focused
- Use dependency injection
- Follow interface-based design patterns
- Write docstrings for public APIs

### Example
```python
from typing import Optional
from dataclasses import dataclass

@dataclass
class Paper:
    """Represents a research paper."""
    
    id: str
    title: str
    abstract: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert paper to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "abstract": self.abstract
        }
```

## Testing Guidelines

### Write Tests For
- All new features
- Bug fixes
- Core business logic
- Service integrations (with mocks)

### Test Structure
```python
import pytest
from unittest.mock import Mock

def test_processor_fetch_papers():
    """Test that processor fetches papers correctly."""
    # Arrange
    mock_source = Mock()
    mock_source.fetch_papers.return_value = [...]
    
    # Act
    result = processor.process(source=mock_source)
    
    # Assert
    assert len(result) > 0
    mock_source.fetch_papers.assert_called_once()
```

## Documentation

### Update Documentation When
- Adding new features
- Changing APIs
- Modifying configuration options
- Fixing significant bugs

### Documentation Locations
- `README.md` - Main user guide
- `docs/` - Detailed documentation
- `CHANGELOG.md` - Version history
- Docstrings - API reference

## Pull Request Guidelines

### Before Submitting
- [ ] Tests pass
- [ ] Code is linted and formatted
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for significant changes)
- [ ] Commit messages follow conventions

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Release Process

For maintainers:

1. Update `VERSION` file
2. Update `CHANGELOG.md`
3. Commit changes: `git commit -m "chore: bump version to X.Y.Z"`
4. Create tag: `git tag vX.Y.Z`
5. Push: `git push && git push --tags`
6. GitHub Actions will automatically create the release

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues before creating new ones

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Keep discussions on-topic

Thank you for contributing! 🎉

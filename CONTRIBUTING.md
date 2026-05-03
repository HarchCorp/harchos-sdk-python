# Contributing to HarchOS SDK Python

Thank you for your interest in contributing to the HarchOS Python SDK! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub account

### Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/harchos-sdk-python.git
   cd harchos-sdk-python
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Create a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```

## Development

### Code Style

- Follow PEP 8 with a line length of 100 characters
- Use type hints for all function signatures
- Write docstrings for all public modules, classes, and functions
- Use `ruff` for linting:
  ```bash
  ruff check src/ tests/
  ```

### Type Checking

- Use `mypy` for static type checking:
  ```bash
  mypy src/harchos
  ```

### Testing

- Write tests for all new functionality
- Use `pytest` with `pytest-asyncio` for async tests
- Aim for comprehensive test coverage
- Run tests:
  ```bash
  pytest --tb=short -q
  ```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `test:` — Test additions or changes
- `refactor:` — Code refactoring
- `ci:` — CI/CD changes
- `chore:` — Maintenance tasks

### Sovereignty Principles

All contributions must respect HarchOS sovereignty principles:

1. **Data Residency** — No data should leave the configured region without explicit consent
2. **Carbon Awareness** — Carbon-aware defaults should be preserved
3. **Sovereignty Enforcement** — Strict sovereignty should be the default

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Update the CHANGELOG.md with your changes
5. Submit a pull request with a clear description

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated
- [ ] No sovereignty principles violated
- [ ] Type hints and docstrings added for new code

## Release Process

Releases are automated via GitHub Actions:

1. Create a tag: `git tag v0.x.0`
2. Push the tag: `git push origin v0.x.0`
3. The release workflow will build and publish to PyPI

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

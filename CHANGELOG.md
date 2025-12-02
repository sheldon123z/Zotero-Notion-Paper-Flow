# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Planned features will be listed here

### Changed
- Planned changes will be listed here

### Deprecated
- Features marked for removal will be listed here

### Removed
- Removed features will be listed here

### Fixed
- Bug fixes will be listed here

### Security
- Security updates will be listed here

---

## [2.0.0] - 2025-12-02

### Added
- **Architecture Overhaul**: Complete refactoring to interface-driven design
  - New unified entry point: `paper-flow` command
  - Clean separation via interfaces: `DataSourceInterface`, `StorageInterface`, `LLMInterface`
  - Dependency injection pattern with `ServiceContainer`
- **Build System**: Modern Python packaging with `pyproject.toml` (PEP 517/518)
- **Release Automation**: GitHub Actions workflow for automated releases
  - Multi-platform Desktop app builds (macOS, Windows, Linux)
  - Automatic PyPI publishing (optional)
  - Release asset generation with checksums
- **Version Management**: Centralized version control with `VERSION` file
- **Documentation**: Comprehensive docs in `docs/` directory
  - Architecture documentation
  - Migration guide from legacy code
  - API reference
  - Contributing guidelines
- **Desktop App**: Electron-based configuration management UI
  - Cross-platform support (macOS/Windows/Linux)
  - Visual configuration editor
  - Integrated with Python backend

### Changed
- **Entry Point**: Migrated from `daily_paper_app.py` to `main.py`
  - New command: `paper-flow` (recommended)
  - Legacy command: `paper-assistant` (deprecated, will be removed in v3.0.0)
- **Code Organization**: Improved project structure
  - Core business logic in `src/core/`
  - Clean data models in `src/models/`
  - Service implementations in `src/service/`
  - Configuration management in `src/config/`
- **Configuration**: Enhanced settings with type safety via dataclasses
- **Testing**: Improved CI/CD pipeline
  - Multi-version Python testing (3.9, 3.10, 3.11)
  - Code quality checks (ruff, mypy, bandit)
  - Test coverage reporting
  - Security scanning

### Deprecated
- `src/daily_paper_app.py` - Use `paper-flow` command or `python -m main` instead
- `paper-assistant` CLI command - Use `paper-flow` instead

### Removed
- `src/daily_paper_app2.py` - Duplicate legacy file removed

### Fixed
- Improved error handling and logging throughout codebase
- Better checkpoint file management
- Enhanced PDF download reliability
- Fixed Zotero collection mapping issues

### Security
- Added security scanning with Bandit
- Updated dependencies to latest secure versions
- Improved API key management via environment variables

---

## [1.0.0] - 2024-11-22

### Added
- Initial release
- Basic paper fetching from HuggingFace Daily Papers
- ArXiv API integration with keyword and category search
- LLM-powered paper analysis (Moonshot/DeepSeek)
- Multi-service synchronization:
  - Notion database integration
  - Zotero library management
  - Wolai workspace integration
- PDF download functionality
- Command-line interface with multiple options
- Configuration via `config.json`
- Checkpoint system to prevent duplicate processing
- Slack notifications (optional)
- Category mapping for Zotero collections

### Features
- Search papers by keywords and arXiv categories
- Automatic Chinese translation of abstracts
- Paper categorization and tagging
- Batch processing support
- Multi-day data processing
- Proxy support for network requests

---

[Unreleased]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/releases/tag/v1.0.0

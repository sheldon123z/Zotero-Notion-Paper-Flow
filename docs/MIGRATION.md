# Migration Guide

This guide helps you migrate from the legacy `daily_paper_app.py` to the new unified `paper-flow` command.

## Quick Start

### Old Way (Deprecated)
```bash
python src/daily_paper_app.py --keywords "LLM" --limit 10
```

### New Way (Recommended)
```bash
paper-flow --keywords "LLM" --limit 10
```

## What Changed?

### v2.0.0 Architecture Overhaul

1. **New Entry Point**: Use `paper-flow` command instead of running `daily_paper_app.py` directly
2. **Interface-Based Design**: Clean separation between data sources, storage, and LLM services
3. **Modern Packaging**: Uses `pyproject.toml` following PEP 517/518 standards
4. **Improved Configuration**: Type-safe settings with dataclasses

## Installation

### Old Installation
```bash
pip install -r requirements.txt
python setup.py install
```

### New Installation
```bash
# From PyPI (when published)
pip install paper-flow

# From source
pip install -e .
```

## Command Line Interface

All command-line arguments remain the same:

```bash
paper-flow --keywords "reinforcement learning" "LLM" \
          --categories cs.LG cs.AI \
          --date 2025-01-01 \
          --limit 20 \
          --download-pdf \
          --pdf-dir ./papers
```

## Configuration File

The `config.json` format remains **100% compatible**. No changes needed!

```json
{
  "keywords": ["reinforcement learning"],
  "categories": ["cs.LG", "cs.AI"],
  "services": {
    "notion": true,
    "zotero": true,
    "wolai": false
  },
  "download_pdf": true,
  "pdf_dir": "papers",
  "search_limit": 10
}
```

## Environment Variables

All environment variables remain the same:

```bash
# LLM Service
KIMI_API_KEY=your-key
DEEPSEEK_API_KEY=your-key

# Notion
NOTION_SECRET=your-secret
NOTION_DB_ID=your-db-id

# Zotero
ZOTERO_API_KEY=your-key
ZOTERO_USER_ID=your-user-id

# Optional
SLACK_API_KEY=your-key
HTTP_PROXY=http://127.0.0.1:7890
```

## Code Migration

If you're importing modules directly:

### Old Code
```python
from daily_paper_app import process_arxiv_papers, process_hf_papers
```

### New Code
```python
from main import main
from core.processor import PaperProcessor
from config.settings import Settings
```

## Deprecated Features

The following will be removed in v3.0.0:

- ❌ `src/daily_paper_app.py` direct execution
- ❌ `paper-assistant` CLI command (use `paper-flow` instead)
- ❌ Direct imports from `daily_paper_app` module

## Timeline

- **v2.0.0** (Current): Legacy code marked as deprecated with warnings
- **v2.x.x**: Both old and new entry points work side-by-side
- **v3.0.0** (Future): Legacy code will be removed

## Need Help?

- Check the [README](../README.md) for updated usage examples
- See [ARCHITECTURE.md](./ARCHITECTURE.md) for design details
- Open an issue on [GitHub](https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/issues)

## Benefits of Migrating

✅ **Better Architecture**: Clean, testable, maintainable code  
✅ **Modern Tooling**: Latest Python packaging standards  
✅ **Active Development**: All new features only in v2.0+  
✅ **Better Documentation**: Comprehensive guides and API reference  
✅ **Desktop App**: New GUI for easy configuration  

Start using `paper-flow` today! 🚀

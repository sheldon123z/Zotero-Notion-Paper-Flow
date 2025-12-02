# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Zotero-Notion-Paper-Flow is an automated paper collection and management tool that fetches papers from HuggingFace Daily Papers and arXiv, uses LLM services (Moonshot/DeepSeek) for Chinese translation and analysis, and syncs results to Notion, Zotero, and Wolai.

## Common Commands

### Installation
```bash
# Using pip
pip install -r requirements.txt

# Using conda (recommended)
conda create -n daily_paper_app python=3.10
conda activate daily_paper_app
pip install -r requirements.txt

# Using venv
python3 -m venv daily_paper_app
source daily_paper_app/bin/activate
python setup.py install
```

### Running the Application
```bash
# Direct execution with parameters
python src/daily_paper_app.py --keywords "LLM" "RL" --categories cs.LG cs.AI --limit 20 --download-pdf

# Using the startup script (after configuring environment variables)
sh bin/start_daily_paper_app.sh

# Example startup script parameters
sh bin/start_daily_paper_app.sh --date=2025-04-21 --limit=10 --no-hf
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run specific test file
pytest tests/unit/test_processor.py
```

### Code Quality
```bash
# Lint with ruff
ruff check src/

# Type checking with mypy
mypy src/

# Security audit with bandit
bandit -r src/
```

### Desktop App (Electron)
```bash
cd desktop-app
npm install
npm run dev        # Development mode
npm start          # Production mode
npm run build:mac  # Build for macOS
npm run build:win  # Build for Windows
```

## Architecture

### Data Flow
The application follows a pipeline architecture:
```
HuggingFace/arXiv → ArxivVisitor → LLM Analysis → Storage Services (Notion/Zotero/Wolai)
```

### Core Components

**Main Entry Points:**
- `src/daily_paper_app.py` - Legacy main entry with CLI argument parsing
- `src/core/processor.py` - Refactored processor with clean interface architecture

**Data Models:**
- `src/entity/formatted_arxiv_obj.py` - Legacy ArXiv object (dataclass)
- `src/models/paper.py` - New unified Paper model with multiple factory methods (`from_arxiv`, `from_semantic_scholar`, `from_dict`)

**Services:**
- `src/service/arxiv_visitor.py` - ArXiv API integration with search by keywords/categories
- `src/service/hf_visotor.py` - HuggingFace Daily Papers page scraper
- `src/service/llm_service.py` - LLM API calls (supports Moonshot and DeepSeek)
- `src/service/notion_service.py` - Notion database operations
- `src/service/zotero_service.py` - Zotero library management with collection mapping
- `src/service/wolai_service.py` - Wolai integration
- `src/service/pdf_downloader.py` - Automated PDF downloads

**Configuration:**
- `src/config/settings.py` - Configuration management with dataclasses
- `config.json` - Main configuration file (keywords, categories, service toggles, category_map)

### Key Design Patterns

**Checkpoint System:**
- Processed paper IDs stored in `output/cache/arxiv_ckpt.txt`
- Prevents duplicate processing on subsequent runs

**Category Mapping:**
- `category_map` in config.json maps paper categories to Zotero collection IDs
- Format: `{"NLP": ["WXBCJ969", "DFGZNVCM"], ...}`
- `default_category` used when no match found

**Interface Architecture (Refactored Code):**
- Clean separation via interfaces: `DataSourceInterface`, `StorageInterface`, `LLMInterface`
- Found in `src/interfaces/` directory
- Enables dependency injection and testing

## Environment Variables

The application requires several API keys and configuration via environment variables:

### Required
```bash
# LLM Service (at least one)
KIMI_API_KEY=sk-xxx
KIMI_URL=https://api.moonshot.cn/v1
# OR
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_URL=https://api.deepseek.com
```

### Optional Services
```bash
# Notion
NOTION_SECRET=secret_xxx
NOTION_DB_ID=xxx

# Zotero
ZOTERO_API_KEY=xxx
ZOTERO_USER_ID=xxx
ZOTERO_LIBRARY_ID=xxx

# Wolai
WOLAI_APP_ID=xxx
WOLAI_APP_SECRETE=xxx
WOLAI_TOKEN=xxx
WOLAI_DB_ID=xxx

# Slack notifications
SLACK_API_KEY=xxx

# Proxy (if needed)
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

**Important:** Copy `bin/start_daily_paper_app_example.sh` to `bin/start_daily_paper_app.sh` and fill in your credentials before running.

## Configuration File

The `config.json` file controls search parameters and service behavior:

```json
{
  "keywords": ["reinforcement learning", ["power system", "energy"]],
  "categories": ["cs.LG", "cs.AI", "eess.SY"],
  "services": {
    "notion": true,
    "zotero": false,
    "wolai": true
  },
  "download_pdf": true,
  "pdf_dir": "papers",
  "search_limit": 10,
  "category_map": {
    "NLP": ["WXBCJ969", "DFGZNVCM"],
    "RL": ["DXU9QIKA", "DFGZNVCM"]
  },
  "default_category": ["DFGZNVCM"]
}
```

**Note:** Keywords support AND logic with nested arrays - `["power system", "energy"]` means papers must contain both terms.

## Project Structure Notes

**Dual Architectures:**
The codebase contains both legacy and refactored code:
- Legacy: `daily_paper_app.py`, `formatted_arxiv_obj.py`, direct service imports
- Refactored: `core/processor.py`, `models/paper.py`, interface-based design

When adding new features, prefer the refactored architecture in `src/core/` and `src/models/`.

**Logging:**
- All logs saved to `logs/daily_paper_YYYYMMDD.log`
- Both file and console output configured in `setup_logging()`

**Crontab Scheduling:**
The tool is designed for automated daily runs:
```bash
# Example: Run daily at 8 AM
0 8 * * * sh /path/to/start_daily_paper_app.sh
```
For conda environments, ensure the script activates the environment before execution.

## Desktop App Architecture

The `desktop-app/` directory contains an Electron-based GUI:
- `main.js` - Main process, handles IPC and Python subprocess management
- `renderer/` - Frontend HTML/CSS/JS for configuration UI
- Uses `electron-store` for persistent settings storage
- Communicates with Python backend via subprocess

## Important Implementation Details

**Zotero Collection IDs:**
- Collection IDs in `category_map` are specific to your Zotero library
- Update these IDs in config.json to match your own collections
- Obtain IDs from Zotero web interface or API

**LLM Service Selection:**
- Default: uses Moonshot (Kimi) API
- Switch to DeepSeek by setting appropriate env vars
- To add other LLM providers, modify `src/service/llm_service.py`

**PDF Downloads:**
- PDFs saved to directory specified in `pdf_dir` config
- Downloaded via `src/service/pdf_downloader.py`
- Filenames format: `{arxiv_id}.pdf`

**Error Handling:**
- Service failures logged but don't halt entire pipeline
- Individual paper processing errors increment `error_count` but continue batch
- Checkpoint file updated only after successful processing

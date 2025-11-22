# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zotero-Notion-Paper-Flow 是一个论文自动采集和管理工具，从 HuggingFace Daily Papers 和 arXiv 获取论文，使用 LLM（Moonshot/DeepSeek）进行中文摘要翻译和解析，然后同步到 Notion、Zotero 和 Wolai。

## Common Commands

### Python 依赖安装
```bash
pip install -r requirements.txt
```

### 运行主程序
```bash
python src/daily_paper_app.py [选项]

# 常用参数
--keywords "LLM" "RL"     # 搜索关键词（多个）
--categories cs.LG cs.AI  # arXiv 分类
--date 2025-04-21         # 指定日期
--days 3                  # 处理过去 n 天
--limit 20                # 每日最多处理论文数
--download-pdf            # 下载 PDF
--no-arxiv                # 跳过 arXiv 抓取
--no-hf                   # 跳过 HuggingFace 抓取
--config ./config.json    # 指定配置文件
```

### 使用启动脚本（需先配置环境变量）
```bash
sh bin/start_daily_paper_app.sh
```

### Desktop App（Electron）
```bash
cd desktop-app
npm install
npm run dev        # 开发模式
npm start          # 生产模式
npm run build:mac  # 构建 macOS
npm run build:win  # 构建 Windows
```

## Architecture

### 核心数据流
```
HuggingFace/arXiv → ArxivVisitor → LLM翻译解析 → Notion/Zotero/Wolai
```

### 主要模块 (src/)
- `daily_paper_app.py` - 主入口，CLI 参数解析和流程控制
- `service/arxiv_visitor.py` - arXiv API 访问和论文搜索
- `service/hf_visotor.py` - HuggingFace Daily Papers 页面解析
- `service/llm_service.py` - LLM API 调用（Moonshot/DeepSeek）
- `service/notion_service.py` - Notion API 集成
- `service/zotero_service.py` - Zotero API 集成
- `service/wolai_service.py` - Wolai API 集成
- `service/pdf_downloader.py` - PDF 下载
- `entity/formatted_arxiv_obj.py` - 论文数据实体类

### 配置系统
- `config.json` - 主配置文件（关键词、分类、服务开关、category_map 等）
- 环境变量配置各服务 API Key（见 `bin/start_daily_paper_app_example.sh`）

### Desktop App (desktop-app/)
Electron 桌面应用，提供 GUI 配置管理，包含：
- `main.js` - Electron 主进程
- `renderer/` - 前端 HTML/CSS/JS
- 使用 electron-store 存储配置

## Required Environment Variables

```bash
# LLM (至少一个)
KIMI_API_KEY, KIMI_URL
DEEPSEEK_API_KEY, DEEPSEEK_URL

# Notion
NOTION_SECRET, NOTION_DB_ID

# Zotero
ZOTERO_API_KEY, ZOTERO_USER_ID, ZOTERO_LIBRARY_ID

# 可选
SLACK_API_KEY
WOLAI_APP_ID, WOLAI_APP_SECRETE, WOLAI_TOKEN, WOLAI_DB_ID

# 代理
HTTP_PROXY, HTTPS_PROXY
```

## Key Implementation Details

- 检查点机制：`output/cache/` 存储已处理论文 ID，避免重复处理
- 日志输出：`logs/daily_paper_YYYYMMDD.log`
- Zotero category_map：配置文件中定义论文分类到 Zotero Collection ID 的映射
- 定时调度：通过 crontab 实现，参考 README.md

#!/bin/bash
# 注意 使用前把环境变量设置好 
export SLACK_API_KEY=
export WOLAI_APP_ID=
export WOLAI_APP_SECRETE=
export WOLAI_TOKEN=
export WOLAI_DB_ID=
export NOTION_DB_ID=
export NOTION_SECRET=

export KIMI_API_KEY=sk-
export KIMI_URL=https://api.moonshot.cn/v1

export DEEPSEEK_URL=https://api.deepseek.com
export DEEPSEEK_API_KEY=sk-
export ZOTERO_USER_ID=
export ZOTERO_API_KEY=
export ZOTERO_LIBRARY_ID=

python src/daily_paper_app.py
conda deactivate




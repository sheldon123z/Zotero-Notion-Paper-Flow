# API 文档 | API Documentation

本文档详细说明 Zotero-Notion-Paper-Flow 项目的核心 API。

## 目录

- [数据模型](#数据模型)
- [数据源服务](#数据源服务)
- [LLM 服务](#llm-服务)
- [存储服务](#存储服务)
- [配置管理](#配置管理)
- [工具函数](#工具函数)

---

## 数据模型

### Paper

论文数据模型，定义在 `src/models/paper.py`。

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class Paper:
    id: Optional[str] = None
    title: Optional[str] = ""
    authors: List[str] = field(default_factory=list)
    published_dt: Optional[str] = ""
    summary: Optional[str] = ""
    summary_cn: Optional[str] = ""
    short_summary: Optional[str] = ""
    pdf_url: Optional[str] = ""
    tldr: Dict[str, str] = field(default_factory=dict)
    raw_tldr: Optional[str] = ""
    category: Optional[str] = ""
    tags: List[str] = field(default_factory=list)
    media_type: Optional[str] = ""
    media_url: Optional[str] = ""
    journal_ref: Optional[str] = ""
    doi: Optional[str] = ""
    arxiv_categories: List[str] = field(default_factory=list)
```

#### 属性说明

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | `str` | arXiv 论文 ID (如 "2401.00001") |
| `title` | `str` | 论文标题 |
| `authors` | `List[str]` | 作者列表 |
| `published_dt` | `str` | 发布日期 (格式: "YYYY-MM") |
| `summary` | `str` | 英文摘要 |
| `summary_cn` | `str` | 中文翻译摘要 |
| `short_summary` | `str` | 简短摘要 (50字以内) |
| `pdf_url` | `str` | PDF 下载链接 |
| `tldr` | `Dict[str, str]` | TLDR 信息 (动机/方法/结果) |
| `category` | `str` | 主要领域分类 |
| `tags` | `List[str]` | 标签列表 |
| `arxiv_categories` | `List[str]` | arXiv 分类列表 |

### FormattedArxivObj (旧版)

旧版数据模型，定义在 `src/entity/formatted_arxiv_obj.py`，与 `Paper` 结构相似。

---

## 数据源服务

### ArxivVisitor

arXiv 数据访问类，定义在 `src/service/arxiv_visitor.py`。

#### 初始化

```python
from service.arxiv_visitor import ArxivVisitor

visitor = ArxivVisitor(
    output_dir="./output",    # 输出目录
    page_size=10,             # 分页大小
    disable_cache=False       # 是否禁用缓存
)
```

#### 方法

##### search_by_keywords

通过关键词搜索论文。

```python
def search_by_keywords(
    self,
    keywords: Union[str, List[str]],
    categories: List[str] = None,
    limit: int = 10,
    format_result: bool = True
) -> Union[List[FormattedArxivObj], List[arxiv.Result]]
```

**参数:**
- `keywords`: 搜索关键词，可以是字符串或列表
- `categories`: arXiv 分类列表 (如 `["cs.LG", "cs.AI"]`)
- `limit`: 返回结果数量限制
- `format_result`: 是否格式化结果

**示例:**

```python
# 单个关键词
results = visitor.search_by_keywords("reinforcement learning", limit=10)

# 多个关键词 (AND 关系)
results = visitor.search_by_keywords(
    ["reinforcement learning", "robotics"],
    categories=["cs.LG", "cs.RO"],
    limit=20
)

# 嵌套关键词 (内层 OR，外层 AND)
results = visitor.search_by_keywords(
    ["reinforcement learning", ["power system", "energy"]],
    categories=["cs.LG", "eess.SY"]
)
```

##### find_by_id

通过 arXiv ID 获取论文。

```python
def find_by_id(
    self,
    id_or_idlist: Union[str, List[str]],
    hf_obj: dict = None,
    format_result: bool = True
) -> Union[FormattedArxivObj, arxiv.Result]
```

**参数:**
- `id_or_idlist`: 论文 ID 或 ID 列表
- `hf_obj`: HuggingFace 对象 (可选，用于获取媒体信息)
- `format_result`: 是否格式化结果

**示例:**

```python
# 获取单篇论文
paper = visitor.find_by_id("2401.00001")

# 获取原始结果
raw_result = visitor.find_by_id("2401.00001", format_result=False)
```

##### search_by_title

通过标题搜索论文。

```python
def search_by_title(
    self,
    title: str,
    limit: int = 10,
    format_result: bool = True
) -> Union[List[FormattedArxivObj], List[arxiv.Result]]
```

##### download_pdf

下载论文 PDF。

```python
@classmethod
def download_pdf(
    cls,
    obj: Union[FormattedArxivObj, arxiv.Result],
    save_dir: str
) -> str
```

**示例:**

```python
paper = visitor.find_by_id("2401.00001")
pdf_path = ArxivVisitor.download_pdf(paper, "./papers")
```

### HFDailyPaperVisitor

HuggingFace Daily Papers 访问类，定义在 `src/service/hf_visotor.py`。

#### 初始化

```python
from service.hf_visotor import HFDailyPaperVisitor

visitor = HFDailyPaperVisitor(
    output_dir="./output",
    dt="2025-04-21"  # 可选，默认为当天
)
```

#### 属性

```python
visitor.paper_list    # 论文列表
visitor.datetime      # 日期对象
```

#### 论文对象结构

```python
{
    "id": "2401.00001",
    "title": "Paper Title",
    "media_type": "image",  # 或 "video"
    "media_url": "https://..."
}
```

---

## LLM 服务

### llm_service.chat

LLM 聊天函数，定义在 `src/service/llm_service.py`。

```python
def chat(
    prompt: str,
    retry_count: int = 2,
    service: str = "deepseek",
    response_format: str = "text",
    **kwargs
) -> Union[str, dict]
```

**参数:**
- `prompt`: 提示词
- `retry_count`: 重试次数
- `service`: LLM 服务 (`"deepseek"`, `"kimi"`, `"zhipu"`)
- `response_format`: 响应格式 (`"text"` 或 `"json_object"`)
- `**kwargs`: 其他参数 (`api_key`, `base_url`, `model_name`)

**示例:**

```python
from service import llm_service

# 文本响应
response = llm_service.chat(
    "翻译这段话: Hello, world!",
    service="deepseek"
)

# JSON 响应
response = llm_service.chat(
    "提取关键信息并以JSON格式返回",
    service="kimi",
    response_format="json_object"
)

# 自定义服务
response = llm_service.chat(
    "Hello",
    service="custom",
    api_key="your-key",
    base_url="https://api.example.com/v1",
    model_name="model-name"
)
```

### BaseLLMService (新架构)

LLM 服务基类，定义在 `src/services/llm/base.py`。

```python
from services.llm import LLMServiceFactory

# 创建服务实例
llm = LLMServiceFactory.create('deepseek')

# 聊天
response = llm.chat("Hello")

# 生成摘要
summary = llm.generate_summary(text)

# 生成标签
tags = llm.generate_tags(text)
```

---

## 存储服务

### NotionService

Notion 服务类，定义在 `src/service/notion_service.py`。

#### 初始化

```python
from service.notion_service import NotionService
from datetime import datetime

service = NotionService(
    create_time=datetime.now(),
    db_id="your-database-id",      # 默认从环境变量
    secret="your-secret",          # 默认从环境变量
    use_proxy=True
)
```

#### 方法

##### insert

插入论文到 Notion 数据库。

```python
def insert(
    self,
    formatted_arxiv_obj: FormattedArxivObj,
    hf_obj: dict = None
)
```

**示例:**

```python
paper = arxiv_visitor.find_by_id("2401.00001")
service.insert(paper, hf_obj={"media_type": "image", "media_url": "..."})
```

##### 属性设置方法

```python
# 设置数据库
service.set_database_id(db_id)

# 添加属性
service.add_property_title('标题', '论文标题')
service.add_property_rich_text('作者', '作者列表')
service.add_property_date('日期', '2025-04-21')
service.add_property_select('领域', 'NLP')
service.add_property_multi_select('标签', ['tag1', 'tag2'])
service.add_property_url('链接', 'https://...')

# 添加内容块
service.add_h1('标题')
service.add_h2('子标题')
service.add_paragraph('段落内容')
service.add_image('https://...')
service.add_video('https://...')
```

### ZoteroService

Zotero 服务类，定义在 `src/service/zotero_service.py`。

#### 初始化

```python
from service.zotero_service import ZoteroService
from datetime import datetime

service = ZoteroService(
    create_time=datetime.now(),
    item_type="preprint",
    api_key="your-api-key",      # 默认从环境变量
    user_id="your-user-id",      # 默认从环境变量
    group_id="your-group-id",    # 可选
    use_proxy=True
)
```

#### 方法

##### insert

插入论文到 Zotero 库。

```python
def insert(
    self,
    formatted_arxiv_obj: FormattedArxivObj,
    collection: List[str] = ["DFGZNVCM"],
    library_type: str = "user"
) -> dict
```

**参数:**
- `formatted_arxiv_obj`: 论文对象
- `collection`: Collection ID 列表
- `library_type`: 库类型 (`"user"` 或 `"group"`)

**示例:**

```python
paper = arxiv_visitor.find_by_id("2401.00001")
result = service.insert(paper, collection=["COLLECTION_ID"])
```

##### item_exists

检查论文是否已存在。

```python
def item_exists(
    self,
    doi: str = None,
    arxiv_id: str = None,
    title: str = None,
    library_type: str = "user"
) -> dict
```

**返回值:**
```python
{
    "exists": True,
    "count": 1,
    "query_type": "arxiv_id",
    "message": "检索到 1 个条目。",
    "items": [...]
}
```

#### 异常

```python
from service.zotero_service import ZoteroItemExistsError

try:
    service.insert(paper)
except ZoteroItemExistsError as e:
    print(f"论文已存在: {e}")
```

### WolaiService

Wolai 服务类，定义在 `src/service/wolai_service.py`。

#### 初始化

```python
from service.wolai_service import WolaiService

service = WolaiService()
```

#### 方法

##### insert

插入论文到 Wolai 数据库。

```python
def insert(self, formatted_arxiv_obj: FormattedArxivObj)
```

---

## 配置管理

### Settings

配置类，定义在 `src/config/settings.py`。

```python
from config.settings import Settings

# 从文件加载
settings = Settings.from_file('config.json')

# 从环境变量加载
settings = Settings.from_env()
```

### 配置文件结构

```json
{
    "keywords": ["reinforcement learning"],
    "categories": ["cs.LG", "cs.AI"],
    "date": null,
    "proxy": "http://127.0.0.1:7890",
    "services": {
        "notion": true,
        "zotero": false,
        "wolai": true
    },
    "download_pdf": true,
    "pdf_dir": "papers",
    "search_limit": 10,
    "retries": 3,
    "category_map": {
        "NLP": ["COLLECTION_ID_1"],
        "RL": ["COLLECTION_ID_2"]
    },
    "default_category": ["DEFAULT_COLLECTION_ID"]
}
```

---

## 工具函数

### common_utils

通用工具函数，定义在 `src/common_utils/utils.py`。

#### get_logger

获取日志记录器。

```python
from common_utils import get_logger

logger = get_logger(__name__)
logger.info("信息日志")
logger.error("错误日志")
```

#### send_slack

发送 Slack 通知。

```python
from common_utils import send_slack

send_slack("消息内容")
```

### pdf_downloader

PDF 下载工具，定义在 `src/service/pdf_downloader.py`。

```python
from service.pdf_downloader import download_paper_pdfs

# 批量下载 PDF
pdf_paths = download_paper_pdfs(
    paper_ids=["2401.00001", "2401.00002"],
    save_dir="./papers",
    arxiv_visitor=visitor
)
```

---

## 命令行接口

### 参数说明

```bash
python src/daily_paper_app.py [OPTIONS]

Options:
  --keywords TEXT...      搜索关键词 (可多个)
  --categories TEXT...    arXiv 分类 (可多个)
  --date TEXT            指定日期 (YYYY-MM-DD)
  --days INTEGER         处理过去 N 天
  --limit INTEGER        每日处理限制
  --config PATH          配置文件路径
  --download-pdf         下载 PDF
  --no-download-pdf      不下载 PDF
  --pdf-dir PATH         PDF 保存目录
  --no-hf               跳过 HuggingFace
  --no-arxiv            跳过 arXiv 搜索
```

---

## 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 是* |
| `DEEPSEEK_URL` | DeepSeek API URL | 否 |
| `DEEPSEEK_MODEL` | DeepSeek 模型名 | 否 |
| `KIMI_API_KEY` | Kimi API Key | 是* |
| `KIMI_URL` | Kimi API URL | 否 |
| `KIMI_MODEL` | Kimi 模型名 | 否 |
| `NOTION_SECRET` | Notion Integration Secret | 否 |
| `NOTION_DB_ID` | Notion Database ID | 否 |
| `ZOTERO_API_KEY` | Zotero API Key | 否 |
| `ZOTERO_USER_ID` | Zotero User ID | 否 |
| `ZOTERO_GROUP_ID` | Zotero Group ID | 否 |
| `HTTP_PROXY` | HTTP 代理 | 否 |
| `HTTPS_PROXY` | HTTPS 代理 | 否 |
| `SLACK_API_KEY` | Slack API Key | 否 |

*至少需要一个 LLM API Key

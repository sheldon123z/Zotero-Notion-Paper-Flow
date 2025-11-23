# 架构迁移指南

本文档说明如何从旧架构（v1.x）迁移到新架构（v2.0）。

## 变更概述

### 新架构特点
- **依赖注入**: 使用 `ServiceContainer` 管理服务实例
- **接口抽象**: 定义 `DataSourceInterface`、`StorageInterface`、`LLMInterface`
- **策略模式**: LLM服务可动态切换
- **工厂模式**: 各服务通过工厂类创建
- **配置管理**: 使用 `Settings` dataclass

### 目录结构变更

```
旧结构                          新结构
src/                            src/
├── service/                    ├── services/           # 新服务实现
│   ├── arxiv_visitor.py        │   ├── llm/
│   ├── hf_visotor.py           │   ├── data_sources/
│   ├── notion_service.py       │   └── storage/
│   ├── zotero_service.py       ├── interfaces/         # 抽象接口
│   └── llm_service.py          ├── models/             # 数据模型
├── entity/                     ├── config/             # 配置管理
│   └── formatted_arxiv_obj.py  ├── core/               # 业务逻辑
└── daily_paper_app.py          ├── apps/               # 应用入口
                                └── compat.py           # 兼容层
```

## 迁移步骤

### 1. 更新导入语句

**旧代码:**
```python
from service.arxiv_visitor import ArxivVisitor
from service.notion_service import NotionService
from service.zotero_service import ZoteroService
from service import llm_service
```

**新代码:**
```python
from services.data_sources import ArxivDataSource, HuggingFaceDataSource
from services.storage import NotionStorage, ZoteroStorage
from services.llm import LLMServiceFactory
```

### 2. LLM服务迁移

**旧代码:**
```python
from service import llm_service
result = llm_service.chat(prompt, service="deepseek")
```

**新代码:**
```python
from services.llm import LLMServiceFactory

llm = LLMServiceFactory.create('deepseek')
result = llm.chat(prompt)

# 或生成摘要
summary = llm.generate_summary(text)
tags = llm.generate_tags(text)
```

### 3. 数据源迁移

**旧代码:**
```python
from service.arxiv_visitor import ArxivVisitor

visitor = ArxivVisitor(output_dir='./output')
results = visitor.search_by_keywords(['reinforcement learning'], categories=['cs.LG'])
paper = visitor.find_by_id('2401.00001')
```

**新代码:**
```python
from services.data_sources import ArxivDataSource
from services.llm import LLMServiceFactory

llm = LLMServiceFactory.create('deepseek')
source = ArxivDataSource(output_dir='./output', llm_service=llm)

# 搜索
papers = source.search(['reinforcement learning'], categories=['cs.LG'])

# 通过ID获取
paper = source.get_by_id('2401.00001')
```

### 4. 存储服务迁移

**旧代码:**
```python
from service.notion_service import NotionService
from service.zotero_service import ZoteroService

notion = NotionService(create_time=datetime.now())
notion.insert(formatted_arxiv_obj)

zotero = ZoteroService(create_time=datetime.now())
zotero.insert(formatted_arxiv_obj, collection=['COLLECTION_ID'])
```

**新代码:**
```python
from services.storage import NotionStorage, ZoteroStorage

notion = NotionStorage(create_time=datetime.now())
notion.insert(paper)

zotero = ZoteroStorage(create_time=datetime.now())
zotero.insert(paper, collections=['COLLECTION_ID'])
```

### 5. 数据模型迁移

**旧代码:**
```python
from entity.formatted_arxiv_obj import FormattedArxivObj
```

**新代码:**
```python
from models.paper import Paper

paper = Paper(
    id='2401.00001',
    title='Paper Title',
    authors=['Author 1', 'Author 2'],
    summary='...',
    # ...
)
```

### 6. 使用配置管理

**旧代码:**
```python
import os
api_key = os.environ.get('DEEPSEEK_API_KEY')
```

**新代码:**
```python
from config.settings import Settings

settings = Settings.from_file('config.json')
# 或
settings = Settings.from_env()
```

### 7. 使用新的应用入口

**旧代码:**
```bash
python src/daily_paper_app.py --keywords "RL" --limit 10
```

**新代码:**
```bash
# 使用新入口
python src/main.py --keywords "RL" --limit 10

# 或使用CLI
python src/cli.py run -k "RL" -l 10

# 或使用DailyPaperApp类
python src/apps/daily_paper.py --keywords "RL" --limit 10
```

## 兼容层使用

如果您暂时无法完全迁移，可以使用兼容层：

```python
# 兼容层会显示弃用警告，但代码仍可运行
from compat import ArxivVisitor, NotionService, ZoteroService, chat

# 这些类会自动使用新架构的实现
visitor = ArxivVisitor(output_dir='./output')
```

## 可删除的旧文件

迁移完成后，以下文件可以安全删除：

```
# 旧服务文件（已被 src/services/ 替代）
src/service/arxiv_visitor.py
src/service/hf_visotor.py
src/service/notion_service.py
src/service/zotero_service.py
src/service/wolai_service.py
src/service/llm_service.py
src/service/pdf_downloader.py

# 旧实体文件（已被 src/models/paper.py 替代）
src/entity/formatted_arxiv_obj.py

# 旧入口文件（已被 src/apps/daily_paper.py 替代）
src/daily_paper_app.py
src/daily_paper_app2.py
src/paper_query_app.py

# 兼容层（确认不再需要后可删除）
src/compat.py
src/service/__init__.py
```

## 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-mock

# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 常见问题

### Q: 如何添加新的LLM服务？
```python
from services.llm import LLMServiceFactory, BaseLLMService

class MyLLMService(BaseLLMService):
    def get_service_name(self):
        return "my_llm"

LLMServiceFactory.register('my_llm', MyLLMService)
```

### Q: 如何添加新的数据源？
```python
from services.data_sources import DataSourceFactory, BaseDataSource

class MyDataSource(BaseDataSource):
    def get_source_name(self):
        return "my_source"

    def search(self, keywords, **kwargs):
        # 实现搜索逻辑
        pass

DataSourceFactory.register('my_source', MyDataSource)
```

### Q: 如何添加新的存储服务？
```python
from services.storage import StorageFactory, BaseStorage

class MyStorage(BaseStorage):
    def get_storage_name(self):
        return "my_storage"

    def insert(self, paper, **kwargs):
        # 实现插入逻辑
        pass

StorageFactory.register('my_storage', MyStorage)
```

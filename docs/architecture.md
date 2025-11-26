# 架构文档 | Architecture Documentation

本文档详细说明 Zotero-Notion-Paper-Flow 项目的架构设计。

## 系统概述

Zotero-Notion-Paper-Flow 是一个自动化的学术论文采集和管理系统，采用模块化设计，支持多数据源、多 LLM 服务和多存储后端。

## 架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户界面层 (UI Layer)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │   CLI (cli.py)  │  │ Desktop App     │  │ Crontab Script  │         │
│  │                 │  │ (Electron)      │  │                 │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
└───────────┼─────────────────────┼───────────────────┼───────────────────┘
            │                     │                   │
            └─────────────────────┼───────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         应用层 (Application Layer)                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    daily_paper_app.py                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │   │
│  │  │ 参数解析    │  │ 配置加载    │  │ 流程控制    │              │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          服务层 (Service Layer)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐                                               │
│  │   ServiceContainer  │ ◄── 依赖注入容器                              │
│  └──────────┬──────────┘                                               │
│             │                                                           │
│  ┌──────────┼──────────────────────────────────────────────────────┐   │
│  │          │                                                       │   │
│  │  ┌───────▼───────┐  ┌───────────────┐  ┌───────────────────┐   │   │
│  │  │  Data Sources │  │  LLM Services │  │  Storage Services │   │   │
│  │  │               │  │               │  │                   │   │   │
│  │  │ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────────┐ │   │   │
│  │  │ │  ArXiv    │ │  │ │  DeepSeek │ │  │ │    Notion     │ │   │   │
│  │  │ └───────────┘ │  │ └───────────┘ │  │ └───────────────┘ │   │   │
│  │  │ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────────┐ │   │   │
│  │  │ │HuggingFace│ │  │ │   Kimi    │ │  │ │    Zotero     │ │   │   │
│  │  │ └───────────┘ │  │ └───────────┘ │  │ └───────────────┘ │   │   │
│  │  │               │  │ ┌───────────┐ │  │ ┌───────────────┐ │   │   │
│  │  │               │  │ │   Zhipu   │ │  │ │    Wolai      │ │   │   │
│  │  │               │  │ └───────────┘ │  │ └───────────────┘ │   │   │
│  │  └───────────────┘  └───────────────┘  └───────────────────┘   │   │
│  └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          接口层 (Interface Layer)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │DataSourceInterface│ │  LLMInterface  │  │StorageInterface │         │
│  │                 │  │                 │  │                 │         │
│  │ + search()      │  │ + chat()        │  │ + insert()      │         │
│  │ + get_by_id()   │  │ + generate_*()  │  │ + update()      │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         数据层 (Data Layer)                              │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Paper Model    │  │  Cache (JSON)   │  │  Checkpoint     │         │
│  │                 │  │                 │  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
src/
├── daily_paper_app.py      # 主入口（旧版兼容）
├── main.py                 # 新版入口
├── cli.py                  # 命令行接口
├── compat.py               # 兼容层
├── container.py            # 依赖注入容器
│
├── apps/                   # 应用模块
│   └── daily_paper.py      # 每日论文应用
│
├── config/                 # 配置管理
│   ├── __init__.py
│   └── settings.py         # Settings dataclass
│
├── interfaces/             # 抽象接口
│   ├── __init__.py
│   ├── data_source.py      # DataSourceInterface
│   ├── llm.py              # LLMInterface
│   └── storage.py          # StorageInterface
│
├── models/                 # 数据模型
│   ├── __init__.py
│   └── paper.py            # Paper dataclass
│
├── core/                   # 核心业务逻辑
│   ├── __init__.py
│   └── processor.py        # PaperProcessor
│
├── services/               # 服务实现（新架构）
│   ├── __init__.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py         # BaseLLMService
│   │   ├── factory.py      # LLMServiceFactory
│   │   ├── deepseek.py
│   │   ├── kimi.py
│   │   └── zhipu.py
│   ├── data_sources/
│   │   ├── __init__.py
│   │   ├── base.py         # BaseDataSource
│   │   ├── factory.py      # DataSourceFactory
│   │   ├── arxiv.py
│   │   └── huggingface.py
│   └── storage/
│       ├── __init__.py
│       ├── base.py         # BaseStorage
│       ├── factory.py      # StorageFactory
│       ├── notion.py
│       └── zotero.py
│
├── service/                # 旧版服务（保留兼容）
│   ├── __init__.py
│   ├── arxiv_visitor.py
│   ├── hf_visotor.py
│   ├── llm_service.py
│   ├── notion_service.py
│   ├── zotero_service.py
│   ├── wolai_service.py
│   └── pdf_downloader.py
│
├── entity/                 # 旧版实体（保留兼容）
│   ├── __init__.py
│   └── formatted_arxiv_obj.py
│
└── common_utils/           # 通用工具
    ├── __init__.py
    ├── utils.py
    └── zotero_utils.py
```

## 核心组件

### 1. 数据源 (Data Sources)

数据源负责从外部获取论文数据。

#### ArxivDataSource

```python
class ArxivDataSource(BaseDataSource):
    """arXiv 数据源"""

    def search(self, keywords, categories=None, limit=10):
        """通过关键词搜索论文"""
        pass

    def get_by_id(self, paper_id):
        """通过 ID 获取论文"""
        pass
```

#### HuggingFaceDataSource

```python
class HuggingFaceDataSource(BaseDataSource):
    """HuggingFace Daily Papers 数据源"""

    def search(self, date=None):
        """获取指定日期的论文列表"""
        pass
```

### 2. LLM 服务 (LLM Services)

LLM 服务负责论文摘要翻译、TLDR 生成和标签提取。

```python
class BaseLLMService(LLMInterface):
    """LLM 服务基类"""

    def chat(self, prompt, **kwargs):
        """发送聊天请求"""
        pass

    def generate_summary(self, text):
        """生成摘要"""
        pass

    def generate_tags(self, text):
        """生成标签"""
        pass

    def translate(self, text, target_lang='zh'):
        """翻译文本"""
        pass
```

### 3. 存储服务 (Storage Services)

存储服务负责将论文数据同步到各平台。

```python
class BaseStorage(StorageInterface):
    """存储服务基类"""

    def insert(self, paper, **kwargs):
        """插入论文"""
        pass

    def update(self, paper_id, data):
        """更新论文"""
        pass

    def exists(self, paper_id):
        """检查是否存在"""
        pass
```

### 4. 依赖注入容器 (Service Container)

```python
class ServiceContainer:
    """服务容器，管理服务实例"""

    def __init__(self, settings):
        self.settings = settings
        self._services = {}

    def get_llm_service(self, provider=None):
        """获取 LLM 服务实例"""
        pass

    def get_data_source(self, source_type):
        """获取数据源实例"""
        pass

    def get_storage(self, storage_type):
        """获取存储服务实例"""
        pass
```

## 数据流程

### 论文处理流程

```
1. 数据采集
   ┌─────────────┐     ┌─────────────┐
   │   ArXiv     │     │ HuggingFace │
   └──────┬──────┘     └──────┬──────┘
          │                   │
          └─────────┬─────────┘
                    ▼
2. 数据解析与缓存检查
   ┌─────────────────────────┐
   │    ArxivVisitor         │
   │  - 解析论文元数据         │
   │  - 检查本地缓存           │
   └───────────┬─────────────┘
               ▼
3. LLM 处理
   ┌─────────────────────────┐
   │    LLM Service          │
   │  - 摘要翻译              │
   │  - TLDR 生成             │
   │  - 标签提取              │
   └───────────┬─────────────┘
               ▼
4. 数据存储
   ┌─────────┬─────────┬─────────┐
   │         │         │         │
   ▼         ▼         ▼         ▼
┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐
│Notion│  │Zotero│  │Wolai │  │ PDF │
└─────┘  └─────┘  └─────┘  └─────┘

5. 检查点更新
   ┌─────────────────────────┐
   │    Checkpoint File      │
   │  - 记录已处理论文 ID      │
   └─────────────────────────┘
```

## 设计模式

### 1. 工厂模式 (Factory Pattern)

用于创建 LLM 服务、数据源和存储服务实例。

```python
class LLMServiceFactory:
    _services = {}

    @classmethod
    def register(cls, name, service_class):
        cls._services[name] = service_class

    @classmethod
    def create(cls, name, **kwargs):
        service_class = cls._services.get(name)
        if not service_class:
            raise ValueError(f"Unknown service: {name}")
        return service_class(**kwargs)
```

### 2. 策略模式 (Strategy Pattern)

LLM 服务可以动态切换：

```python
# 使用 DeepSeek
llm = LLMServiceFactory.create('deepseek')
summary = llm.generate_summary(text)

# 切换到 Kimi
llm = LLMServiceFactory.create('kimi')
summary = llm.generate_summary(text)
```

### 3. 依赖注入 (Dependency Injection)

通过 `ServiceContainer` 管理依赖：

```python
container = ServiceContainer(settings)
llm = container.get_llm_service()
arxiv = container.get_data_source('arxiv')
notion = container.get_storage('notion')
```

### 4. 模板方法模式 (Template Method Pattern)

基类定义算法框架，子类实现具体步骤：

```python
class BaseLLMService:
    def chat(self, prompt, **kwargs):
        # 模板方法
        self._validate_prompt(prompt)
        response = self._do_request(prompt, **kwargs)
        return self._process_response(response)

    def _do_request(self, prompt, **kwargs):
        # 抽象方法，子类实现
        raise NotImplementedError
```

## 配置管理

### Settings Dataclass

```python
@dataclass
class Settings:
    # LLM 配置
    llm_provider: str = 'deepseek'
    deepseek_api_key: str = ''
    kimi_api_key: str = ''

    # 数据源配置
    keywords: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)

    # 存储配置
    notion_enabled: bool = True
    zotero_enabled: bool = False
    notion_db_id: str = ''
    zotero_api_key: str = ''

    # 其他配置
    proxy: str = ''
    download_pdf: bool = True
    pdf_dir: str = 'papers'

    @classmethod
    def from_file(cls, path):
        """从配置文件加载"""
        pass

    @classmethod
    def from_env(cls):
        """从环境变量加载"""
        pass
```

## 缓存策略

### 论文缓存

- **位置**: `output/cache/`
- **格式**: JSON 文件（每篇论文一个文件）
- **内容**: 论文元数据、TLDR、标签等

```json
{
    "id": "2401.00001",
    "title": "Paper Title",
    "tldr": {
        "动机": "...",
        "方法": "...",
        "结果": "..."
    },
    "tag_info": {
        "主要领域": "RL",
        "标签": ["reinforcement-learning", "..."]
    }
}
```

### 检查点文件

- **位置**: `output/cache/ckpt_YYYY-MM-DD.txt`
- **格式**: 每行一个论文 ID
- **用途**: 避免重复处理

## 错误处理

### 重试机制

所有外部 API 调用都实现了指数退避重试：

```python
def _fetch_with_retry(self, func, max_retries=3):
    retry_wait = 2
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_wait)
                retry_wait *= 2
            else:
                raise
```

### 错误日志

- **位置**: `logs/daily_paper_YYYYMMDD.log`
- **级别**: INFO, WARNING, ERROR, CRITICAL

## 扩展指南

### 添加新的 LLM 服务

1. 在 `src/services/llm/` 创建新文件
2. 继承 `BaseLLMService`
3. 实现必要方法
4. 在工厂中注册

### 添加新的数据源

1. 在 `src/services/data_sources/` 创建新文件
2. 继承 `BaseDataSource`
3. 实现 `search()` 和 `get_by_id()` 方法
4. 在工厂中注册

### 添加新的存储服务

1. 在 `src/services/storage/` 创建新文件
2. 继承 `BaseStorage`
3. 实现 `insert()` 方法
4. 在工厂中注册

## 性能考量

### 并发处理

目前采用串行处理，未来可考虑：
- 异步 IO (asyncio)
- 多线程/多进程处理
- 批量 API 调用

### 缓存优化

- 使用内存缓存减少文件 IO
- 实现 LRU 缓存策略
- 考虑使用 Redis 等外部缓存

### API 限制

- 遵守各 API 的速率限制
- 实现请求队列
- 监控 API 配额使用

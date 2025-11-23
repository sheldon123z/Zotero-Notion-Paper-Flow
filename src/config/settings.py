"""
配置管理模块

该模块提供应用程序的配置管理功能，支持从文件、环境变量等多种来源加载配置。
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """
    LLM服务配置

    配置LLM服务的连接参数和模型设置。

    Attributes:
        service: LLM服务名称，如 "deepseek", "openai", "claude"
        api_key: API密钥
        base_url: API基础URL（用于自定义端点）
        model_name: 模型名称
        temperature: 温度参数
        max_tokens: 最大生成token数
        timeout: 请求超时时间（秒）
    """

    service: str = "deepseek"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60

    def __post_init__(self) -> None:
        """初始化后处理，从环境变量加载敏感配置"""
        if self.api_key is None:
            env_key_map = {
                "deepseek": "DEEPSEEK_API_KEY",
                "openai": "OPENAI_API_KEY",
                "claude": "ANTHROPIC_API_KEY",
            }
            env_key = env_key_map.get(self.service, f"{self.service.upper()}_API_KEY")
            self.api_key = os.getenv(env_key)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含敏感信息）"""
        return {
            "service": self.service,
            "base_url": self.base_url,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "has_api_key": self.api_key is not None,
        }


@dataclass
class ServiceConfig:
    """
    服务启用配置

    控制各个服务的启用状态。

    Attributes:
        notion: 是否启用 Notion 存储
        zotero: 是否启用 Zotero 存储
        wolai: 是否启用 Wolai 存储
        arxiv: 是否启用 ArXiv 数据源
        semantic_scholar: 是否启用 Semantic Scholar 数据源
    """

    notion: bool = True
    zotero: bool = True
    wolai: bool = False
    arxiv: bool = True
    semantic_scholar: bool = False

    def to_dict(self) -> Dict[str, bool]:
        """转换为字典"""
        return {
            "notion": self.notion,
            "zotero": self.zotero,
            "wolai": self.wolai,
            "arxiv": self.arxiv,
            "semantic_scholar": self.semantic_scholar,
        }


@dataclass
class NotionConfig:
    """
    Notion服务配置

    Attributes:
        api_key: Notion API密钥
        database_id: Notion数据库ID
        page_id: Notion页面ID（可选）
    """

    api_key: Optional[str] = None
    database_id: Optional[str] = None
    page_id: Optional[str] = None

    def __post_init__(self) -> None:
        """初始化后处理，从环境变量加载配置"""
        if self.api_key is None:
            self.api_key = os.getenv("NOTION_API_KEY")
        if self.database_id is None:
            self.database_id = os.getenv("NOTION_DATABASE_ID")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含敏感信息）"""
        return {
            "has_api_key": self.api_key is not None,
            "database_id": self.database_id,
            "page_id": self.page_id,
        }


@dataclass
class ZoteroConfig:
    """
    Zotero服务配置

    Attributes:
        api_key: Zotero API密钥
        library_id: Zotero库ID
        library_type: 库类型，"user" 或 "group"
        collection_id: 收藏夹ID（可选）
    """

    api_key: Optional[str] = None
    library_id: Optional[str] = None
    library_type: str = "user"
    collection_id: Optional[str] = None

    def __post_init__(self) -> None:
        """初始化后处理，从环境变量加载配置"""
        if self.api_key is None:
            self.api_key = os.getenv("ZOTERO_API_KEY")
        if self.library_id is None:
            self.library_id = os.getenv("ZOTERO_LIBRARY_ID")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含敏感信息）"""
        return {
            "has_api_key": self.api_key is not None,
            "library_id": self.library_id,
            "library_type": self.library_type,
            "collection_id": self.collection_id,
        }


@dataclass
class Settings:
    """
    应用配置

    应用程序的主配置类，包含所有配置选项。

    Attributes:
        keywords: 搜索关键词列表
        categories: 论文分类列表
        date: 日期筛选
        proxy: 代理服务器地址
        services: 服务启用配置
        llm: LLM服务配置
        notion: Notion服务配置
        zotero: Zotero服务配置
        download_pdf: 是否下载PDF
        pdf_dir: PDF存储目录
        search_limit: 搜索结果数量限制
        retries: 重试次数
        retry_delay: 重试延迟（秒）
        category_map: 分类映射表
        default_category: 默认分类
        log_level: 日志级别
    """

    # 搜索配置
    keywords: List[str] = field(default_factory=lambda: ["reinforcement learning"])
    categories: List[str] = field(default_factory=lambda: ["cs.LG", "cs.AI"])
    date: Optional[str] = None

    # 网络配置
    proxy: str = "http://127.0.0.1:7890"
    timeout: int = 30

    # 服务配置
    services: ServiceConfig = field(default_factory=ServiceConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    notion: NotionConfig = field(default_factory=NotionConfig)
    zotero: ZoteroConfig = field(default_factory=ZoteroConfig)

    # 下载配置
    download_pdf: bool = True
    pdf_dir: str = "papers/pdf"

    # 处理配置
    search_limit: int = 20
    retries: int = 3
    retry_delay: float = 1.0

    # 分类配置
    category_map: Dict[str, List[str]] = field(default_factory=dict)
    default_category: List[str] = field(default_factory=lambda: ["DFGZNVCM"])

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None

    @classmethod
    def from_file(cls, config_path: str) -> "Settings":
        """
        从配置文件加载

        支持 JSON 格式的配置文件。

        Args:
            config_path: 配置文件路径

        Returns:
            Settings 实例

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        return cls._from_dict(config_data)

    @classmethod
    def from_env(cls) -> "Settings":
        """
        从环境变量加载

        从环境变量加载配置，优先级低于配置文件。

        Returns:
            Settings 实例
        """
        settings = cls()

        # 从环境变量加载基本配置
        if os.getenv("PAPER_KEYWORDS"):
            settings.keywords = os.getenv("PAPER_KEYWORDS", "").split(",")
        if os.getenv("PAPER_CATEGORIES"):
            settings.categories = os.getenv("PAPER_CATEGORIES", "").split(",")
        if os.getenv("PROXY"):
            settings.proxy = os.getenv("PROXY", settings.proxy)
        if os.getenv("SEARCH_LIMIT"):
            settings.search_limit = int(os.getenv("SEARCH_LIMIT", str(settings.search_limit)))
        if os.getenv("DOWNLOAD_PDF"):
            settings.download_pdf = os.getenv("DOWNLOAD_PDF", "").lower() == "true"
        if os.getenv("PDF_DIR"):
            settings.pdf_dir = os.getenv("PDF_DIR", settings.pdf_dir)
        if os.getenv("LOG_LEVEL"):
            settings.log_level = os.getenv("LOG_LEVEL", settings.log_level)

        return settings

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """
        从字典创建 Settings 实例

        Args:
            data: 配置字典

        Returns:
            Settings 实例
        """
        # 处理嵌套配置
        services_data = data.pop("services", {})
        llm_data = data.pop("llm", {})
        notion_data = data.pop("notion", {})
        zotero_data = data.pop("zotero", {})

        services = ServiceConfig(**services_data) if services_data else ServiceConfig()
        llm = LLMConfig(**llm_data) if llm_data else LLMConfig()
        notion = NotionConfig(**notion_data) if notion_data else NotionConfig()
        zotero = ZoteroConfig(**zotero_data) if zotero_data else ZoteroConfig()

        return cls(
            services=services,
            llm=llm,
            notion=notion,
            zotero=zotero,
            **{k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        )

    def validate(self) -> bool:
        """
        验证配置

        检查配置的有效性和完整性。

        Returns:
            配置是否有效

        Raises:
            ValueError: 配置无效
        """
        errors: List[str] = []

        # 验证关键词
        if not self.keywords:
            errors.append("关键词列表不能为空")

        # 验证分类
        if not self.categories:
            errors.append("分类列表不能为空")

        # 验证搜索限制
        if self.search_limit <= 0:
            errors.append("搜索限制必须大于0")

        # 验证重试次数
        if self.retries < 0:
            errors.append("重试次数不能为负数")

        # 验证 Notion 配置（如果启用）
        if self.services.notion:
            if not self.notion.api_key:
                errors.append("启用 Notion 服务但未配置 API Key")
            if not self.notion.database_id:
                errors.append("启用 Notion 服务但未配置 Database ID")

        # 验证 Zotero 配置（如果启用）
        if self.services.zotero:
            if not self.zotero.api_key:
                errors.append("启用 Zotero 服务但未配置 API Key")
            if not self.zotero.library_id:
                errors.append("启用 Zotero 服务但未配置 Library ID")

        # 验证 LLM 配置
        if not self.llm.api_key:
            logger.warning("未配置 LLM API Key，LLM 功能可能不可用")

        if errors:
            for error in errors:
                logger.error(f"配置验证失败: {error}")
            raise ValueError(f"配置验证失败: {'; '.join(errors)}")

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        将配置转换为字典格式，用于序列化或日志记录。
        注意：不包含敏感信息（如 API Key）。

        Returns:
            配置字典
        """
        return {
            "keywords": self.keywords,
            "categories": self.categories,
            "date": self.date,
            "proxy": self.proxy,
            "timeout": self.timeout,
            "services": self.services.to_dict(),
            "llm": self.llm.to_dict(),
            "notion": self.notion.to_dict(),
            "zotero": self.zotero.to_dict(),
            "download_pdf": self.download_pdf,
            "pdf_dir": self.pdf_dir,
            "search_limit": self.search_limit,
            "retries": self.retries,
            "retry_delay": self.retry_delay,
            "category_map": self.category_map,
            "default_category": self.default_category,
            "log_level": self.log_level,
            "log_file": self.log_file,
        }

    def save(self, config_path: str) -> None:
        """
        保存配置到文件

        将当前配置保存为 JSON 文件。

        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # 构建可保存的配置（包含 API Key）
        save_data = {
            "keywords": self.keywords,
            "categories": self.categories,
            "date": self.date,
            "proxy": self.proxy,
            "timeout": self.timeout,
            "services": self.services.to_dict(),
            "llm": {
                "service": self.llm.service,
                "base_url": self.llm.base_url,
                "model_name": self.llm.model_name,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
                # 注意：不保存 API Key 到文件
            },
            "notion": {
                "database_id": self.notion.database_id,
                "page_id": self.notion.page_id,
            },
            "zotero": {
                "library_id": self.zotero.library_id,
                "library_type": self.zotero.library_type,
                "collection_id": self.zotero.collection_id,
            },
            "download_pdf": self.download_pdf,
            "pdf_dir": self.pdf_dir,
            "search_limit": self.search_limit,
            "retries": self.retries,
            "retry_delay": self.retry_delay,
            "category_map": self.category_map,
            "default_category": self.default_category,
            "log_level": self.log_level,
            "log_file": self.log_file,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        logger.info(f"配置已保存到: {config_path}")

    def merge(self, other: "Settings") -> "Settings":
        """
        合并配置

        将另一个配置合并到当前配置，other 中的非空值会覆盖当前值。

        Args:
            other: 另一个 Settings 实例

        Returns:
            合并后的 Settings 实例
        """
        merged_data = self.to_dict()

        for key, value in other.to_dict().items():
            if value is not None and value != "" and value != []:
                merged_data[key] = value

        return self._from_dict(merged_data)

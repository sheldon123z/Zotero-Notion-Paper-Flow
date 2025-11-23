"""
论文数据模型模块

该模块定义了论文的数据模型，用于在系统各组件之间传递论文信息。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Paper:
    """
    论文数据模型

    表示一篇学术论文的所有相关信息。

    Attributes:
        id: 论文唯一标识符（如 ArXiv ID、DOI 等）
        title: 论文标题
        authors: 作者列表
        published_date: 发布日期
        summary: 原始摘要（英文）
        summary_cn: 中文摘要（LLM 生成）
        short_summary: 简短摘要（一句话总结）
        pdf_url: PDF 下载链接
        tldr: TLDR 摘要字典（包含中英文）
        category: 主分类
        tags: 标签列表
        doi: DOI 标识符
        journal_ref: 期刊引用
        arxiv_categories: ArXiv 分类列表
        media_type: 媒体类型（如 video、audio）
        media_url: 媒体链接
        abstract_url: 摘要页面链接
        source: 数据来源（如 arxiv、semantic_scholar）
        raw_data: 原始数据（用于调试和扩展）
    """

    # 核心字段
    id: str
    title: str
    authors: List[str] = field(default_factory=list)
    published_date: Optional[datetime] = None

    # 摘要相关
    summary: str = ""
    summary_cn: str = ""
    short_summary: str = ""
    tldr: Dict[str, str] = field(default_factory=dict)

    # 链接相关
    pdf_url: str = ""
    abstract_url: str = ""

    # 分类相关
    category: str = ""
    tags: List[str] = field(default_factory=list)
    arxiv_categories: List[str] = field(default_factory=list)

    # 元数据
    doi: Optional[str] = None
    journal_ref: Optional[str] = None

    # 媒体相关
    media_type: str = ""
    media_url: str = ""

    # 数据来源
    source: str = ""

    # 原始数据
    raw_data: Optional[Any] = None

    # 附加字段
    citation_count: int = 0
    influence_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 确保列表字段不为 None
        if self.authors is None:
            self.authors = []
        if self.tags is None:
            self.tags = []
        if self.arxiv_categories is None:
            self.arxiv_categories = []
        if self.tldr is None:
            self.tldr = {}
        if self.keywords is None:
            self.keywords = []
        if self.references is None:
            self.references = []

    @property
    def first_author(self) -> str:
        """获取第一作者"""
        return self.authors[0] if self.authors else ""

    @property
    def author_string(self) -> str:
        """获取作者字符串（逗号分隔）"""
        return ", ".join(self.authors)

    @property
    def published_year(self) -> Optional[int]:
        """获取发布年份"""
        return self.published_date.year if self.published_date else None

    @property
    def published_date_str(self) -> str:
        """获取发布日期字符串"""
        if self.published_date:
            return self.published_date.strftime("%Y-%m-%d")
        return ""

    @property
    def primary_category(self) -> str:
        """获取主分类"""
        if self.category:
            return self.category
        return self.arxiv_categories[0] if self.arxiv_categories else ""

    @property
    def tldr_cn(self) -> str:
        """获取中文 TLDR"""
        return self.tldr.get("zh", "") or self.tldr.get("tldr_zh", "")

    @property
    def tldr_en(self) -> str:
        """获取英文 TLDR"""
        return self.tldr.get("en", "") or self.tldr.get("tldr_en", "")

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        将论文对象转换为字典格式，用于序列化或存储。

        Returns:
            包含论文信息的字典
        """
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "summary": self.summary,
            "summary_cn": self.summary_cn,
            "short_summary": self.short_summary,
            "tldr": self.tldr,
            "pdf_url": self.pdf_url,
            "abstract_url": self.abstract_url,
            "category": self.category,
            "tags": self.tags,
            "arxiv_categories": self.arxiv_categories,
            "doi": self.doi,
            "journal_ref": self.journal_ref,
            "media_type": self.media_type,
            "media_url": self.media_url,
            "source": self.source,
            "citation_count": self.citation_count,
            "influence_score": self.influence_score,
            "keywords": self.keywords,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paper":
        """
        从字典创建 Paper 实例

        Args:
            data: 包含论文信息的字典

        Returns:
            Paper 实例
        """
        # 处理日期字段
        published_date = data.get("published_date")
        if isinstance(published_date, str):
            try:
                published_date = datetime.fromisoformat(published_date)
            except ValueError:
                published_date = None

        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            authors=data.get("authors", []),
            published_date=published_date,
            summary=data.get("summary", ""),
            summary_cn=data.get("summary_cn", ""),
            short_summary=data.get("short_summary", ""),
            tldr=data.get("tldr", {}),
            pdf_url=data.get("pdf_url", ""),
            abstract_url=data.get("abstract_url", ""),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            arxiv_categories=data.get("arxiv_categories", []),
            doi=data.get("doi"),
            journal_ref=data.get("journal_ref"),
            media_type=data.get("media_type", ""),
            media_url=data.get("media_url", ""),
            source=data.get("source", ""),
            citation_count=data.get("citation_count", 0),
            influence_score=data.get("influence_score", 0.0),
            keywords=data.get("keywords", []),
            raw_data=data.get("raw_data"),
        )

    @classmethod
    def from_arxiv(
        cls,
        arxiv_result: Any,
        tldr: Optional[Dict[str, str]] = None,
        tag_info: Optional[Dict[str, Any]] = None
    ) -> "Paper":
        """
        从 ArXiv 结果创建 Paper 实例

        将 ArXiv API 返回的结果转换为 Paper 对象。

        Args:
            arxiv_result: ArXiv API 返回的论文结果对象
            tldr: TLDR 摘要字典（由 LLM 生成）
            tag_info: 标签信息字典（由 LLM 生成）

        Returns:
            Paper 实例
        """
        # 提取作者列表
        authors: List[str] = []
        if hasattr(arxiv_result, "authors"):
            authors = [str(author) for author in arxiv_result.authors]

        # 提取分类列表
        categories: List[str] = []
        if hasattr(arxiv_result, "categories"):
            categories = list(arxiv_result.categories)

        # 提取发布日期
        published_date = None
        if hasattr(arxiv_result, "published"):
            published_date = arxiv_result.published

        # 提取 PDF 链接
        pdf_url = ""
        if hasattr(arxiv_result, "pdf_url"):
            pdf_url = str(arxiv_result.pdf_url)

        # 提取摘要页面链接
        abstract_url = ""
        if hasattr(arxiv_result, "entry_id"):
            abstract_url = str(arxiv_result.entry_id)

        # 提取论文 ID（从 entry_id 中解析）
        paper_id = ""
        if abstract_url:
            # ArXiv entry_id 格式: http://arxiv.org/abs/2301.00001v1
            paper_id = abstract_url.split("/")[-1]
            # 移除版本号
            if "v" in paper_id:
                paper_id = paper_id.rsplit("v", 1)[0]

        # 处理标签信息
        tags: List[str] = []
        category = ""
        if tag_info:
            tags = tag_info.get("tags", [])
            category = tag_info.get("category", "")

        return cls(
            id=paper_id,
            title=getattr(arxiv_result, "title", ""),
            authors=authors,
            published_date=published_date,
            summary=getattr(arxiv_result, "summary", ""),
            pdf_url=pdf_url,
            abstract_url=abstract_url,
            arxiv_categories=categories,
            category=category or (categories[0] if categories else ""),
            tags=tags,
            doi=getattr(arxiv_result, "doi", None),
            journal_ref=getattr(arxiv_result, "journal_ref", None),
            tldr=tldr or {},
            source="arxiv",
            raw_data=arxiv_result,
        )

    @classmethod
    def from_semantic_scholar(
        cls,
        ss_result: Dict[str, Any],
        tldr: Optional[Dict[str, str]] = None,
        tag_info: Optional[Dict[str, Any]] = None
    ) -> "Paper":
        """
        从 Semantic Scholar 结果创建 Paper 实例

        将 Semantic Scholar API 返回的结果转换为 Paper 对象。

        Args:
            ss_result: Semantic Scholar API 返回的论文结果字典
            tldr: TLDR 摘要字典（由 LLM 生成）
            tag_info: 标签信息字典（由 LLM 生成）

        Returns:
            Paper 实例
        """
        # 提取作者列表
        authors: List[str] = []
        for author in ss_result.get("authors", []):
            if isinstance(author, dict):
                authors.append(author.get("name", ""))
            else:
                authors.append(str(author))

        # 提取发布日期
        published_date = None
        pub_date_str = ss_result.get("publicationDate")
        if pub_date_str:
            try:
                published_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
            except ValueError:
                try:
                    published_date = datetime.strptime(pub_date_str, "%Y")
                except ValueError:
                    pass

        # 处理标签信息
        tags: List[str] = []
        category = ""
        if tag_info:
            tags = tag_info.get("tags", [])
            category = tag_info.get("category", "")

        # 提取外部 ID
        external_ids = ss_result.get("externalIds", {})
        doi = external_ids.get("DOI")
        arxiv_id = external_ids.get("ArXiv")

        return cls(
            id=ss_result.get("paperId", ""),
            title=ss_result.get("title", ""),
            authors=authors,
            published_date=published_date,
            summary=ss_result.get("abstract", ""),
            pdf_url=ss_result.get("openAccessPdf", {}).get("url", ""),
            abstract_url=ss_result.get("url", ""),
            arxiv_categories=[],
            category=category,
            tags=tags,
            doi=doi,
            citation_count=ss_result.get("citationCount", 0),
            influence_score=ss_result.get("influentialCitationCount", 0),
            tldr=tldr or {},
            source="semantic_scholar",
            raw_data=ss_result,
        )

    def merge(self, other: "Paper") -> "Paper":
        """
        合并另一篇论文的信息

        将另一篇论文的非空字段合并到当前论文。

        Args:
            other: 另一篇论文

        Returns:
            合并后的论文（新实例）
        """
        merged_data = self.to_dict()

        for key, value in other.to_dict().items():
            if value and not merged_data.get(key):
                merged_data[key] = value
            # 合并列表字段
            elif isinstance(value, list) and isinstance(merged_data.get(key), list):
                merged_data[key] = list(set(merged_data[key] + value))
            # 合并字典字段
            elif isinstance(value, dict) and isinstance(merged_data.get(key), dict):
                merged_data[key] = {**merged_data[key], **value}

        return Paper.from_dict(merged_data)

    def update_with_llm_results(
        self,
        summary_result: Optional[Dict[str, Any]] = None,
        tag_result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        使用 LLM 结果更新论文

        将 LLM 生成的摘要和标签信息更新到论文。

        Args:
            summary_result: LLM 生成的摘要结果
            tag_result: LLM 生成的标签结果
        """
        if summary_result:
            if summary_result.get("success", True):
                self.summary_cn = summary_result.get("summary", self.summary_cn)
                self.short_summary = summary_result.get("short_summary", self.short_summary)
                keywords = summary_result.get("keywords", [])
                if keywords:
                    self.keywords = keywords
                # 更新 TLDR
                if summary_result.get("short_summary"):
                    self.tldr["zh"] = summary_result["short_summary"]

        if tag_result:
            if tag_result.get("success", True):
                tags = tag_result.get("tags", [])
                if tags:
                    self.tags = list(set(self.tags + tags))
                category = tag_result.get("category")
                if category:
                    self.category = category

    def __str__(self) -> str:
        """字符串表示"""
        return f"Paper(id={self.id}, title={self.title[:50]}...)"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (
            f"Paper(id={self.id!r}, title={self.title!r}, "
            f"authors={self.authors!r}, source={self.source!r})"
        )

    def __eq__(self, other: object) -> bool:
        """相等比较"""
        if not isinstance(other, Paper):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.id)

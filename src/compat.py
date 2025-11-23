"""
兼容层 - 为旧代码提供向后兼容的接口
已弃用，建议迁移到新架构
"""
import warnings
from functools import wraps

def deprecated(message: str):
    """弃用装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} 已弃用: {message}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ============ LLM服务兼容层 ============
from services.llm import LLMServiceFactory, BaseLLMService

_default_llm_service = None

@deprecated("请使用 services.llm.LLMServiceFactory.create()")
def chat(prompt, retry_count=3, service="deepseek", response_format="text", **kwargs):
    """
    兼容旧的 llm_service.chat 函数
    """
    global _default_llm_service

    if _default_llm_service is None or _default_llm_service.get_service_name() != service:
        _default_llm_service = LLMServiceFactory.create(service, **kwargs)

    return _default_llm_service.chat(
        prompt=prompt,
        response_format=response_format,
        retry_count=retry_count
    )

# ============ ArxivVisitor兼容层 ============
from services.data_sources import ArxivDataSource
from services.llm import LLMServiceFactory

class ArxivVisitor(ArxivDataSource):
    """
    兼容旧的 ArxivVisitor 类
    已弃用，请使用 services.data_sources.ArxivDataSource
    """

    def __init__(self, output_dir, page_size=10, disable_cache=False):
        warnings.warn(
            "ArxivVisitor 已弃用，请使用 services.data_sources.ArxivDataSource",
            DeprecationWarning,
            stacklevel=2
        )
        # 创建默认的LLM服务
        llm_service = LLMServiceFactory.create('deepseek')

        super().__init__(
            output_dir=output_dir,
            page_size=page_size,
            cache_enabled=not disable_cache,
            llm_service=llm_service
        )

    def find_by_id(self, id_or_idlist, hf_obj=None, format_result=True):
        """兼容旧的find_by_id方法"""
        paper = self.get_by_id(id_or_idlist, hf_obj=hf_obj)
        if paper and format_result:
            # 返回FormattedArxivObj兼容对象
            return FormattedArxivObjCompat(paper)
        return paper

    def search_by_keywords(self, keywords, categories=None, limit=10, format_result=True):
        """兼容旧的search_by_keywords方法"""
        papers = self.search(keywords, categories=categories, limit=limit)
        if format_result:
            return [FormattedArxivObjCompat(p) for p in papers]
        return papers

    def search_by_title(self, title, limit=10, format_result=True):
        """兼容旧的search_by_title方法"""
        return self.search([title], limit=limit)

    def smart_find(self, title_or_id, format_result=False):
        """兼容旧的smart_find方法"""
        import re
        if re.match(r'\d{4}.*', title_or_id):
            return self.find_by_id(title_or_id, format_result=format_result)
        return self.search_by_title(title_or_id, format_result=format_result)

# ============ FormattedArxivObj兼容层 ============
from models.paper import Paper

class FormattedArxivObjCompat:
    """
    兼容旧的 FormattedArxivObj
    包装 Paper 对象，提供旧属性接口
    """

    def __init__(self, paper: Paper):
        self._paper = paper

    @property
    def id(self): return self._paper.id

    @property
    def title(self): return self._paper.title

    @property
    def authors(self): return self._paper.authors

    @property
    def published_dt(self):
        if self._paper.published_date:
            return self._paper.published_date.strftime('%Y-%m')
        return ''

    @property
    def summary(self): return self._paper.summary

    @property
    def summary_cn(self): return self._paper.summary_cn

    @property
    def short_summary(self): return self._paper.short_summary

    @property
    def pdf_url(self): return self._paper.pdf_url

    @property
    def tldr(self): return self._paper.tldr

    @property
    def raw_tldr(self): return str(self._paper.tldr)

    @property
    def category(self): return self._paper.category

    @property
    def tags(self): return self._paper.tags

    @property
    def arxiv_result(self): return self._paper.raw_data

    @property
    def media_type(self): return self._paper.media_type

    @property
    def media_url(self): return self._paper.media_url

    @property
    def journal_ref(self): return self._paper.journal_ref

    @property
    def doi(self): return self._paper.doi

    @property
    def arxiv_categories(self): return self._paper.arxiv_categories

    def to_paper(self) -> Paper:
        """转换回Paper对象"""
        return self._paper

# ============ HFDailyPaperVisitor兼容层 ============
from services.data_sources import HuggingFaceDataSource

class HFDailyPaperVisitor(HuggingFaceDataSource):
    """
    兼容旧的 HFDailyPaperVisitor 类
    已弃用，请使用 services.data_sources.HuggingFaceDataSource
    """

    def __init__(self, output_dir, url='https://huggingface.co/papers', dt=None):
        warnings.warn(
            "HFDailyPaperVisitor 已弃用，请使用 services.data_sources.HuggingFaceDataSource",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(output_dir=output_dir)

        # 立即获取数据
        self.fetch_papers(date=dt)

    @property
    def datetime(self):
        """兼容旧的datetime属性"""
        return self.fetch_datetime

    @property
    def paper_list(self):
        """兼容旧的paper_list属性"""
        return self._paper_list

# ============ NotionService兼容层 ============
from services.storage import NotionStorage

class NotionService(NotionStorage):
    """
    兼容旧的 NotionService 类
    已弃用，请使用 services.storage.NotionStorage
    """

    def __init__(self, create_time, db_id=None, secret=None, use_proxy=True):
        import os
        warnings.warn(
            "NotionService 已弃用，请使用 services.storage.NotionStorage",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(
            db_id=db_id or os.environ.get('NOTION_DB_ID'),
            secret=secret or os.environ.get('NOTION_SECRET'),
            create_time=create_time,
            use_proxy=use_proxy
        )

    def insert(self, formatted_arxiv_obj, hf_obj=None):
        """兼容旧的insert方法"""
        # 如果是兼容对象，转换为Paper
        if hasattr(formatted_arxiv_obj, 'to_paper'):
            paper = formatted_arxiv_obj.to_paper()
        elif hasattr(formatted_arxiv_obj, '_paper'):
            paper = formatted_arxiv_obj._paper
        else:
            # 假设是Paper对象
            paper = formatted_arxiv_obj

        return super().insert(paper, hf_obj=hf_obj)

# ============ ZoteroService兼容层 ============
from services.storage import ZoteroStorage
from services.storage.zotero import ZoteroItemExistsError

class ZoteroService(ZoteroStorage):
    """
    兼容旧的 ZoteroService 类
    已弃用，请使用 services.storage.ZoteroStorage
    """

    def __init__(self, create_time, item_type="preprint", api_key=None,
                 user_id=None, group_id=None, use_proxy=True):
        import os
        warnings.warn(
            "ZoteroService 已弃用，请使用 services.storage.ZoteroStorage",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(
            api_key=api_key or os.environ.get('ZOTERO_API_KEY'),
            user_id=user_id or os.environ.get('ZOTERO_USER_ID'),
            group_id=group_id or os.environ.get('ZOTERO_GROUP_ID'),
            item_type=item_type,
            create_time=create_time,
            use_proxy=use_proxy
        )

    def insert(self, formatted_arxiv_obj, collection=None, library_type="user"):
        """兼容旧的insert方法"""
        # 如果是兼容对象，转换为Paper
        if hasattr(formatted_arxiv_obj, 'to_paper'):
            paper = formatted_arxiv_obj.to_paper()
        elif hasattr(formatted_arxiv_obj, '_paper'):
            paper = formatted_arxiv_obj._paper
        else:
            paper = formatted_arxiv_obj

        self.library_type = library_type
        return super().insert(paper, collections=collection or ["DFGZNVCM"])

# 导出兼容类
__all__ = [
    'chat',
    'ArxivVisitor',
    'HFDailyPaperVisitor',
    'NotionService',
    'ZoteroService',
    'FormattedArxivObjCompat',
    'ZoteroItemExistsError',
    'deprecated',
]

import os
import time
import pickle
import re
import logging
from typing import List, Optional, Union
from pathlib import Path
from urllib.request import urlretrieve

import arxiv

from .base import BaseDataSource
from models.paper import Paper
from services.llm import LLMServiceFactory, BaseLLMService

logger = logging.getLogger(__name__)

class ArxivDataSource(BaseDataSource):
    """ArXiv数据源服务"""

    def __init__(
        self,
        output_dir: str = "./output",
        page_size: int = 10,
        llm_service: BaseLLMService = None,
        **kwargs
    ):
        super().__init__(output_dir=output_dir, **kwargs)
        self.client = arxiv.Client(page_size=page_size)
        self.llm_service = llm_service

    def set_llm_service(self, llm_service: BaseLLMService):
        """设置LLM服务"""
        self.llm_service = llm_service

    def get_source_name(self) -> str:
        return "arxiv"

    def fetch_papers(self, **kwargs) -> List[Paper]:
        """获取论文（通过关键词搜索）"""
        keywords = kwargs.get('keywords', [])
        categories = kwargs.get('categories', [])
        limit = kwargs.get('limit', 10)
        return self.search(keywords, categories=categories, limit=limit)

    def search(
        self,
        keywords: List[str],
        categories: List[str] = None,
        limit: int = 10,
        **kwargs
    ) -> List[Paper]:
        """搜索论文"""
        query = self._build_query(keywords, categories)
        logger.info(f"构建的查询: {query}")

        papers = []
        for attempt in range(self.max_retries):
            try:
                search = arxiv.Search(
                    query=query,
                    max_results=limit,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )

                for result in self.client.results(search):
                    paper = self._process_result(result)
                    papers.append(paper)
                    if len(papers) >= limit:
                        break
                break

            except Exception as e:
                logger.warning(f"ArXiv API请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_wait * (attempt + 1))

        return papers

    def get_by_id(self, paper_id: str, **kwargs) -> Optional[Paper]:
        """通过ID获取论文"""
        # 检查缓存
        cache_key = f"arxiv_{paper_id}"
        cached = self._load_cache(cache_key)
        if cached:
            logger.info(f"从缓存加载论文: {paper_id}")
            return Paper.from_dict(cached)

        for attempt in range(self.max_retries):
            try:
                search = arxiv.Search(id_list=[paper_id])
                results = list(self.client.results(search))

                if results:
                    paper = self._process_result(results[0], **kwargs)
                    # 保存缓存
                    self._save_cache(cache_key, paper.to_dict())
                    return paper
                return None

            except Exception as e:
                logger.warning(f"获取论文失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_wait * (attempt + 1))

        return None

    def _build_query(self, keywords: List[str], categories: List[str] = None) -> str:
        """构建ArXiv查询字符串"""
        query_parts = []

        if keywords:
            if isinstance(keywords, list):
                keyword_parts = []
                for keyword in keywords:
                    if isinstance(keyword, list):
                        sub_parts = [f'(ti:"{kw}" OR abs:"{kw}")' for kw in keyword]
                        keyword_parts.append('(' + ' OR '.join(sub_parts) + ')')
                    else:
                        keyword_parts.append(f'(ti:"{keyword}" OR abs:"{keyword}")')
                query_parts.append(' AND '.join(keyword_parts))
            else:
                query_parts.append(f'(ti:"{keywords}" OR abs:"{keywords}")')

        if categories:
            if isinstance(categories, list):
                cat_query = ' OR '.join([f'cat:{cat}' for cat in categories])
                query_parts.append('(' + cat_query + ')')
            else:
                query_parts.append(f'cat:{categories}')

        return ' AND '.join(query_parts)

    def _process_result(self, arxiv_result, **kwargs) -> Paper:
        """处理ArXiv结果，生成Paper对象"""
        paper_id = arxiv_result.entry_id.split('/')[-1]
        summary = arxiv_result.summary.replace('\n', ' ').replace('  ', ' ')

        # 生成TLDR和标签（如果有LLM服务）
        tldr = {}
        tag_info = {}

        if self.llm_service:
            try:
                tldr = self.llm_service.generate_summary(summary)
                tag_info = self.llm_service.generate_tags(summary)
            except Exception as e:
                logger.error(f"LLM处理失败: {e}")

        # 从hf_obj获取媒体信息（如果有）
        hf_obj = kwargs.get('hf_obj')
        media_type = hf_obj.get('media_type', '') if hf_obj else ''
        media_url = hf_obj.get('media_url', '') if hf_obj else ''

        return Paper(
            id=paper_id,
            title=arxiv_result.title,
            authors=[author.name for author in arxiv_result.authors],
            published_date=arxiv_result.published,
            summary=summary,
            summary_cn=tldr.get('翻译', ''),
            short_summary=tldr.get('short_summary', ''),
            pdf_url=arxiv_result.pdf_url,
            tldr=tldr,
            category=tag_info.get('主要领域', ''),
            tags=tag_info.get('标签', []),
            doi=arxiv_result.doi if hasattr(arxiv_result, 'doi') else None,
            journal_ref=arxiv_result.journal_ref if hasattr(arxiv_result, 'journal_ref') else None,
            arxiv_categories=arxiv_result.categories if hasattr(arxiv_result, 'categories') else [],
            media_type=media_type,
            media_url=media_url,
            raw_data=arxiv_result
        )

    @staticmethod
    def download_pdf(paper: Paper, save_dir: str) -> Optional[str]:
        """下载论文PDF"""
        if not paper.pdf_url:
            return None

        filename = f"{paper.title}.pdf"
        for ch in ('?', '/', ':', '\\', '*', '"', '<', '>', '|'):
            filename = filename.replace(ch, '_')

        if len(filename) > 150:
            filename = filename[:147] + "..."

        save_path = Path(save_dir) / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            urlretrieve(paper.pdf_url, str(save_path))
            logger.info(f"PDF已下载: {save_path}")
            return str(save_path)
        except Exception as e:
            logger.error(f"下载PDF失败: {e}")
            return None

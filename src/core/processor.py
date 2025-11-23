"""
论文处理器模块

该模块实现了论文处理的核心业务逻辑，包括论文获取、增强和存储。
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.request import urlretrieve

from ..interfaces.data_source import DataSourceInterface
from ..interfaces.llm import LLMInterface
from ..interfaces.storage import StorageInterface
from ..models.paper import Paper

logger = logging.getLogger(__name__)


class ProcessingError(Exception):
    """论文处理错误"""

    def __init__(self, paper_id: str, message: str, cause: Optional[Exception] = None):
        self.paper_id = paper_id
        self.cause = cause
        super().__init__(f"处理论文 {paper_id} 失败: {message}")


class PaperProcessor:
    """
    论文处理器

    实现论文处理的核心业务逻辑，包括：
    - 从数据源获取论文
    - 使用 LLM 增强论文信息
    - 保存论文到存储服务
    - 下载 PDF 文件

    Attributes:
        data_sources: 数据源服务字典
        storages: 存储服务字典
        llm: LLM 服务
        config: 处理配置
    """

    def __init__(
        self,
        data_sources: Dict[str, DataSourceInterface],
        storages: Dict[str, StorageInterface],
        llm_service: Optional[LLMInterface] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化论文处理器

        Args:
            data_sources: 数据源服务字典，键为服务名称
            storages: 存储服务字典，键为服务名称
            llm_service: LLM 服务（可选，如果不提供则不进行 LLM 增强）
            config: 处理配置字典
        """
        self.data_sources = data_sources
        self.storages = storages
        self.llm = llm_service
        self.config = config or {}

        # 默认配置
        self._retries = self.config.get("retries", 3)
        self._retry_delay = self.config.get("retry_delay", 1.0)
        self._batch_size = self.config.get("batch_size", 10)
        self._parallel_downloads = self.config.get("parallel_downloads", 3)

        # 处理统计
        self._stats: Dict[str, int] = {
            "fetched": 0,
            "enhanced": 0,
            "saved": 0,
            "failed": 0,
            "skipped": 0,
        }

        # 进度回调
        self._progress_callback: Optional[Callable[[str, int, int], None]] = None

    def set_progress_callback(
        self,
        callback: Callable[[str, int, int], None]
    ) -> None:
        """
        设置进度回调函数

        Args:
            callback: 回调函数，参数为 (阶段名称, 当前进度, 总数)
        """
        self._progress_callback = callback

    def _report_progress(self, stage: str, current: int, total: int) -> None:
        """报告处理进度"""
        if self._progress_callback:
            self._progress_callback(stage, current, total)
        logger.debug(f"[{stage}] 进度: {current}/{total}")

    def process_papers(
        self,
        source: str,
        keywords: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 20,
        download_pdf: bool = False,
        pdf_dir: Optional[str] = None,
        storage_names: Optional[List[str]] = None,
        skip_existing: bool = True,
        enhance_with_llm: bool = True,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        处理论文的主流程

        从指定数据源获取论文，进行增强处理，并保存到存储服务。

        Args:
            source: 数据源名称
            keywords: 搜索关键词列表
            categories: 论文分类列表
            limit: 获取论文数量限制
            download_pdf: 是否下载 PDF
            pdf_dir: PDF 存储目录
            storage_names: 目标存储服务名称列表（默认保存到所有启用的存储）
            skip_existing: 是否跳过已存在的论文
            enhance_with_llm: 是否使用 LLM 增强论文信息
            **kwargs: 其他参数

        Returns:
            处理结果字典，包含：
            - success: 是否成功
            - papers: 处理的论文列表
            - stats: 处理统计信息
            - errors: 错误列表
        """
        # 重置统计
        self._stats = {
            "fetched": 0,
            "enhanced": 0,
            "saved": 0,
            "failed": 0,
            "skipped": 0,
        }
        errors: List[Dict[str, Any]] = []
        processed_papers: List[Paper] = []

        # 验证数据源
        if source not in self.data_sources:
            available = list(self.data_sources.keys())
            return {
                "success": False,
                "message": f"数据源 '{source}' 不可用，可用的数据源: {available}",
                "papers": [],
                "stats": self._stats,
                "errors": errors,
            }

        data_source = self.data_sources[source]

        # 第一步：获取论文
        logger.info(f"从 {source} 获取论文，关键词: {keywords}, 分类: {categories}")
        try:
            papers = self._fetch_papers(
                data_source,
                keywords=keywords,
                categories=categories,
                limit=limit,
                **kwargs
            )
            self._stats["fetched"] = len(papers)
            logger.info(f"获取到 {len(papers)} 篇论文")
        except Exception as e:
            logger.error(f"获取论文失败: {e}")
            return {
                "success": False,
                "message": f"获取论文失败: {e}",
                "papers": [],
                "stats": self._stats,
                "errors": [{"stage": "fetch", "error": str(e)}],
            }

        if not papers:
            return {
                "success": True,
                "message": "没有找到匹配的论文",
                "papers": [],
                "stats": self._stats,
                "errors": [],
            }

        # 确定目标存储服务
        target_storages = self._get_target_storages(storage_names)

        # 第二步：处理每篇论文
        total = len(papers)
        for i, paper in enumerate(papers):
            self._report_progress("processing", i + 1, total)

            try:
                # 检查是否已存在
                if skip_existing and self._paper_exists(paper.id, target_storages):
                    logger.debug(f"论文已存在，跳过: {paper.id}")
                    self._stats["skipped"] += 1
                    continue

                # 使用 LLM 增强
                if enhance_with_llm and self.llm:
                    paper = self._enhance_paper(paper)
                    self._stats["enhanced"] += 1

                # 下载 PDF
                if download_pdf and paper.pdf_url:
                    self._download_pdf(paper, pdf_dir)

                # 保存到存储服务
                save_result = self._save_to_storages(paper, target_storages)
                if save_result.get("success_count", 0) > 0:
                    self._stats["saved"] += 1
                    processed_papers.append(paper)
                else:
                    self._stats["failed"] += 1
                    errors.append({
                        "paper_id": paper.id,
                        "stage": "save",
                        "error": save_result.get("errors", [])
                    })

            except ProcessingError as e:
                logger.error(f"处理论文失败: {e}")
                self._stats["failed"] += 1
                errors.append({
                    "paper_id": paper.id,
                    "stage": "process",
                    "error": str(e)
                })
            except Exception as e:
                logger.error(f"处理论文时发生未知错误: {e}")
                self._stats["failed"] += 1
                errors.append({
                    "paper_id": paper.id,
                    "stage": "unknown",
                    "error": str(e)
                })

        # 返回结果
        return {
            "success": True,
            "message": f"处理完成，成功保存 {self._stats['saved']} 篇论文",
            "papers": processed_papers,
            "stats": self._stats,
            "errors": errors,
        }

    def _fetch_papers(
        self,
        data_source: DataSourceInterface,
        keywords: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 20,
        **kwargs: Any
    ) -> List[Paper]:
        """
        从数据源获取论文

        Args:
            data_source: 数据源服务
            keywords: 搜索关键词列表
            categories: 论文分类列表
            limit: 获取数量限制
            **kwargs: 其他参数

        Returns:
            论文列表
        """
        for attempt in range(self._retries):
            try:
                if keywords:
                    papers = data_source.search(
                        keywords=keywords,
                        categories=categories,
                        limit=limit,
                        **kwargs
                    )
                else:
                    papers = data_source.fetch_papers(
                        categories=categories,
                        limit=limit,
                        **kwargs
                    )
                return papers
            except Exception as e:
                logger.warning(
                    f"获取论文失败 (尝试 {attempt + 1}/{self._retries}): {e}"
                )
                if attempt < self._retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                else:
                    raise

        return []

    def _enhance_paper(self, paper: Paper) -> Paper:
        """
        使用 LLM 增强论文信息

        Args:
            paper: 论文对象

        Returns:
            增强后的论文对象
        """
        if not self.llm:
            return paper

        try:
            # 生成摘要
            text = f"Title: {paper.title}\n\nAbstract: {paper.summary}"
            summary_result = self.llm.generate_summary(text, language="zh")
            paper.update_with_llm_results(summary_result=summary_result)

            # 生成标签
            tag_result = self.llm.generate_tags(text)
            paper.update_with_llm_results(tag_result=tag_result)

            logger.debug(f"论文 {paper.id} LLM 增强完成")

        except Exception as e:
            logger.warning(f"LLM 增强失败: {paper.id}, 错误: {e}")
            # 增强失败不影响整体流程

        return paper

    def _save_to_storages(
        self,
        paper: Paper,
        storages: Optional[Dict[str, StorageInterface]] = None
    ) -> Dict[str, Any]:
        """
        保存论文到存储服务

        Args:
            paper: 论文对象
            storages: 目标存储服务字典

        Returns:
            保存结果字典
        """
        target_storages = storages or self.storages
        results: List[Dict[str, Any]] = []
        success_count = 0
        fail_count = 0
        errors: List[str] = []

        for name, storage in target_storages.items():
            try:
                result = storage.insert(paper)
                if result.get("success"):
                    success_count += 1
                    results.append({
                        "storage": name,
                        "success": True,
                        "result": result
                    })
                    logger.debug(f"论文 {paper.id} 已保存到 {name}")
                else:
                    fail_count += 1
                    errors.append(f"{name}: {result.get('message', '未知错误')}")
                    results.append({
                        "storage": name,
                        "success": False,
                        "error": result.get("message")
                    })
            except Exception as e:
                fail_count += 1
                errors.append(f"{name}: {str(e)}")
                results.append({
                    "storage": name,
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"保存到 {name} 失败: {e}")

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results,
            "errors": errors,
        }

    def _paper_exists(
        self,
        paper_id: str,
        storages: Dict[str, StorageInterface]
    ) -> bool:
        """
        检查论文是否已存在于任一存储服务

        Args:
            paper_id: 论文 ID
            storages: 存储服务字典

        Returns:
            是否存在
        """
        for name, storage in storages.items():
            try:
                if storage.exists(paper_id):
                    return True
            except Exception as e:
                logger.warning(f"检查论文存在性失败 ({name}): {e}")

        return False

    def _get_target_storages(
        self,
        storage_names: Optional[List[str]] = None
    ) -> Dict[str, StorageInterface]:
        """
        获取目标存储服务

        Args:
            storage_names: 存储服务名称列表

        Returns:
            存储服务字典
        """
        if storage_names:
            return {
                name: self.storages[name]
                for name in storage_names
                if name in self.storages
            }
        return self.storages

    def _download_pdf(
        self,
        paper: Paper,
        pdf_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        下载论文 PDF

        Args:
            paper: 论文对象
            pdf_dir: PDF 存储目录

        Returns:
            PDF 文件路径，下载失败返回 None
        """
        if not paper.pdf_url:
            return None

        # 确定存储目录
        save_dir = pdf_dir or self.config.get("pdf_dir", "papers/pdf")
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名（使用论文 ID）
        safe_id = paper.id.replace("/", "_").replace(":", "_")
        file_path = save_path / f"{safe_id}.pdf"

        # 如果文件已存在，跳过下载
        if file_path.exists():
            logger.debug(f"PDF 已存在: {file_path}")
            return str(file_path)

        # 下载文件
        for attempt in range(self._retries):
            try:
                logger.debug(f"下载 PDF: {paper.pdf_url}")
                urlretrieve(paper.pdf_url, str(file_path))
                logger.info(f"PDF 已下载: {file_path}")
                return str(file_path)
            except Exception as e:
                logger.warning(
                    f"下载 PDF 失败 (尝试 {attempt + 1}/{self._retries}): {e}"
                )
                if attempt < self._retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))

        return None

    def batch_download_pdfs(
        self,
        papers: List[Paper],
        pdf_dir: Optional[str] = None,
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批量下载论文 PDF

        Args:
            papers: 论文列表
            pdf_dir: PDF 存储目录
            max_workers: 最大并行下载数

        Returns:
            下载结果字典
        """
        workers = max_workers or self._parallel_downloads
        results: Dict[str, Optional[str]] = {}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._download_pdf, paper, pdf_dir): paper.id
                for paper in papers
                if paper.pdf_url
            }

            for future in as_completed(futures):
                paper_id = futures[future]
                try:
                    path = future.result()
                    results[paper_id] = path
                except Exception as e:
                    logger.error(f"下载 PDF 失败 ({paper_id}): {e}")
                    results[paper_id] = None

        success_count = sum(1 for v in results.values() if v is not None)
        return {
            "total": len(papers),
            "success": success_count,
            "failed": len(papers) - success_count,
            "results": results,
        }

    def search_and_process(
        self,
        keywords: List[str],
        sources: Optional[List[str]] = None,
        merge_duplicates: bool = True,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        从多个数据源搜索并处理论文

        Args:
            keywords: 搜索关键词列表
            sources: 数据源名称列表（默认使用所有可用数据源）
            merge_duplicates: 是否合并重复论文
            **kwargs: 其他参数

        Returns:
            处理结果字典
        """
        target_sources = sources or list(self.data_sources.keys())
        all_papers: Dict[str, Paper] = {}
        all_errors: List[Dict[str, Any]] = []

        # 从各数据源获取论文
        for source in target_sources:
            try:
                result = self.process_papers(
                    source=source,
                    keywords=keywords,
                    enhance_with_llm=False,  # 先获取，后统一增强
                    **kwargs
                )
                for paper in result.get("papers", []):
                    if merge_duplicates:
                        # 使用 DOI 或标题作为去重键
                        key = paper.doi or paper.title.lower()
                        if key in all_papers:
                            all_papers[key] = all_papers[key].merge(paper)
                        else:
                            all_papers[key] = paper
                    else:
                        all_papers[paper.id] = paper

                all_errors.extend(result.get("errors", []))

            except Exception as e:
                logger.error(f"从 {source} 获取论文失败: {e}")
                all_errors.append({
                    "source": source,
                    "error": str(e)
                })

        # 统一使用 LLM 增强
        papers = list(all_papers.values())
        if self.llm and kwargs.get("enhance_with_llm", True):
            for i, paper in enumerate(papers):
                self._report_progress("enhancing", i + 1, len(papers))
                papers[i] = self._enhance_paper(paper)

        return {
            "success": True,
            "papers": papers,
            "total": len(papers),
            "errors": all_errors,
        }

    def get_stats(self) -> Dict[str, int]:
        """
        获取处理统计信息

        Returns:
            统计信息字典
        """
        return self._stats.copy()

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "fetched": 0,
            "enhanced": 0,
            "saved": 0,
            "failed": 0,
            "skipped": 0,
        }

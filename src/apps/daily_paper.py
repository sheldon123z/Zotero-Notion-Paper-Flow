#!/usr/bin/env python3
"""
Daily Paper App - 使用新架构重写
论文抓取和同步应用
"""
import os
import sys
import argparse
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from tqdm import tqdm

# 配置路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config.settings import Settings
from container import ServiceContainer
from models.paper import Paper
from services.llm import LLMServiceFactory, BaseLLMService
from services.data_sources import ArxivDataSource, HuggingFaceDataSource
from services.storage import NotionStorage, ZoteroStorage
from services.storage.zotero import ZoteroItemExistsError
import common_utils

logger = common_utils.get_logger(__name__)

class DailyPaperApp:
    """每日论文应用"""

    def __init__(self, settings: Settings = None, config_path: str = None):
        """
        初始化应用

        Args:
            settings: 配置对象
            config_path: 配置文件路径
        """
        self.project_root = PROJECT_ROOT
        self.output_dir = self.project_root / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载配置
        if settings:
            self.settings = settings
        elif config_path:
            self.settings = Settings.from_file(config_path)
        else:
            default_config = self.project_root / "config.json"
            if default_config.exists():
                self.settings = Settings.from_file(str(default_config))
            else:
                self.settings = Settings()

        # 初始化服务
        self._init_services()

        # 检查点管理
        self.checkpoint_dir = self.output_dir / "cache"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _init_services(self):
        """初始化各项服务"""
        # LLM服务
        self.llm_service = LLMServiceFactory.create(
            self.settings.llm.service,
            api_key=self.settings.llm.api_key,
            base_url=self.settings.llm.base_url,
            model_name=self.settings.llm.model_name
        )

        # 数据源
        self.arxiv_source = ArxivDataSource(
            output_dir=str(self.output_dir),
            llm_service=self.llm_service
        )

        self.hf_source = HuggingFaceDataSource(
            output_dir=str(self.output_dir),
            proxy=self.settings.proxy
        )

        # 存储服务
        self.notion_storage = None
        self.zotero_storage = None

        if self.settings.services.notion:
            try:
                self.notion_storage = NotionStorage(
                    create_time=datetime.now(),
                    use_proxy=True
                )
                if not self.notion_storage.is_available():
                    logger.warning("Notion服务不可用，请检查环境变量")
                    self.notion_storage = None
            except Exception as e:
                logger.warning(f"初始化Notion服务失败: {e}")

        if self.settings.services.zotero:
            try:
                self.zotero_storage = ZoteroStorage(
                    create_time=datetime.now(),
                    use_proxy=True
                )
                if not self.zotero_storage.is_available():
                    logger.warning("Zotero服务不可用，请检查环境变量")
                    self.zotero_storage = None
            except Exception as e:
                logger.warning(f"初始化Zotero服务失败: {e}")

    def _load_checkpoint(self, name: str) -> set:
        """加载检查点"""
        ckpt_file = self.checkpoint_dir / f"{name}.txt"
        if ckpt_file.exists():
            with open(ckpt_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_checkpoint(self, name: str, paper_id: str):
        """保存检查点"""
        ckpt_file = self.checkpoint_dir / f"{name}.txt"
        with open(ckpt_file, 'a') as f:
            f.write(paper_id + '\n')

    def _get_collections(self, category: str) -> List[str]:
        """获取Zotero集合ID"""
        return self.settings.category_map.get(
            category,
            self.settings.default_category
        )

    def _save_paper(self, paper: Paper, hf_obj: Dict = None) -> Dict[str, bool]:
        """保存论文到各存储服务"""
        results = {"notion": False, "zotero": False}

        # 保存到Notion
        if self.notion_storage:
            try:
                self.notion_storage.create_time = datetime.now()
                self.notion_storage.insert(paper, hf_obj=hf_obj)
                results["notion"] = True
                logger.info(f"成功保存到Notion: {paper.id}")
            except Exception as e:
                logger.error(f"保存到Notion失败: {e}")

        # 保存到Zotero
        if self.zotero_storage:
            try:
                collections = self._get_collections(paper.category)
                self.zotero_storage.create_time = datetime.now()
                self.zotero_storage.insert(paper, collections=collections)
                results["zotero"] = True
                logger.info(f"成功保存到Zotero: {paper.id}")
            except ZoteroItemExistsError:
                logger.info(f"论文已存在于Zotero: {paper.id}")
                results["zotero"] = True  # 标记为成功（已存在）
            except Exception as e:
                logger.error(f"保存到Zotero失败: {e}")

        return results

    def process_arxiv(
        self,
        keywords: List[str] = None,
        categories: List[str] = None,
        limit: int = None,
        download_pdf: bool = None
    ) -> Dict[str, int]:
        """
        处理ArXiv论文

        Returns:
            {"processed": int, "errors": int, "total": int}
        """
        keywords = keywords or self.settings.keywords
        categories = categories or self.settings.categories
        limit = limit or self.settings.search_limit
        download_pdf = download_pdf if download_pdf is not None else self.settings.download_pdf

        logger.info(f"开始处理ArXiv论文: keywords={keywords}, categories={categories}, limit={limit}")

        # 加载检查点
        checkpoint = self._load_checkpoint("arxiv_ckpt")

        # 搜索论文
        try:
            papers = self.arxiv_source.search(keywords, categories=categories, limit=limit)
        except Exception as e:
            logger.error(f"搜索ArXiv论文失败: {e}")
            return {"processed": 0, "errors": 1, "total": 0}

        results = {"processed": 0, "errors": 0, "total": len(papers)}

        for paper in tqdm(papers, desc="处理ArXiv论文"):
            if paper.id in checkpoint:
                logger.info(f"跳过已处理: {paper.id}")
                continue

            try:
                # 下载PDF
                if download_pdf and self.settings.pdf_dir:
                    pdf_dir = Path(self.settings.pdf_dir)
                    pdf_dir.mkdir(parents=True, exist_ok=True)
                    ArxivDataSource.download_pdf(paper, str(pdf_dir))

                # 保存到存储服务
                save_results = self._save_paper(paper)

                if any(save_results.values()):
                    self._save_checkpoint("arxiv_ckpt", paper.id)
                    results["processed"] += 1
                else:
                    results["errors"] += 1

            except Exception as e:
                logger.error(f"处理论文失败 {paper.id}: {e}")
                results["errors"] += 1

        return results

    def process_huggingface(
        self,
        date: str = None,
        download_pdf: bool = None
    ) -> Dict[str, int]:
        """
        处理HuggingFace每日论文

        Returns:
            {"processed": int, "errors": int, "total": int}
        """
        download_pdf = download_pdf if download_pdf is not None else self.settings.download_pdf

        logger.info(f"开始处理HuggingFace论文: date={date}")

        # 获取HuggingFace论文列表
        try:
            hf_papers = self.hf_source.fetch_papers(date=date)
        except Exception as e:
            logger.error(f"获取HuggingFace论文失败: {e}")
            return {"processed": 0, "errors": 1, "total": 0}

        # 加载检查点
        ckpt_name = f"hf_{date or datetime.now().strftime('%Y-%m-%d')}"
        checkpoint = self._load_checkpoint(ckpt_name)

        results = {"processed": 0, "errors": 0, "total": len(hf_papers)}

        for hf_paper in tqdm(hf_papers, desc="处理HuggingFace论文"):
            if hf_paper.id in checkpoint:
                logger.info(f"跳过已处理: {hf_paper.id}")
                continue

            try:
                # 从ArXiv获取详细信息
                paper = self.arxiv_source.get_by_id(
                    hf_paper.id,
                    hf_obj={
                        'media_type': hf_paper.media_type,
                        'media_url': hf_paper.media_url
                    }
                )

                if not paper:
                    logger.warning(f"无法获取论文详情: {hf_paper.id}")
                    results["errors"] += 1
                    continue

                # 下载PDF
                if download_pdf and self.settings.pdf_dir:
                    pdf_dir = Path(self.settings.pdf_dir)
                    pdf_dir.mkdir(parents=True, exist_ok=True)
                    ArxivDataSource.download_pdf(paper, str(pdf_dir))

                # 保存到存储服务
                hf_obj = {
                    'media_type': hf_paper.media_type,
                    'media_url': hf_paper.media_url
                }
                save_results = self._save_paper(paper, hf_obj=hf_obj)

                if any(save_results.values()):
                    self._save_checkpoint(ckpt_name, hf_paper.id)
                    results["processed"] += 1
                else:
                    results["errors"] += 1

            except Exception as e:
                logger.error(f"处理论文失败 {hf_paper.id}: {e}")
                logger.debug(traceback.format_exc())
                results["errors"] += 1

        return results

    def run(
        self,
        process_arxiv: bool = True,
        process_hf: bool = True,
        date: str = None,
        days: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        运行应用

        Args:
            process_arxiv: 是否处理ArXiv
            process_hf: 是否处理HuggingFace
            date: 指定日期
            days: 处理过去N天
            **kwargs: 其他参数传递给处理函数

        Returns:
            运行结果统计
        """
        total_results = {
            "arxiv": {"processed": 0, "errors": 0, "total": 0},
            "hf": {"processed": 0, "errors": 0, "total": 0}
        }

        if days:
            # 处理多天
            for i in range(days):
                current_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                logger.info(f"处理日期: {current_date}")

                if process_arxiv:
                    result = self.process_arxiv(**kwargs)
                    for key in result:
                        total_results["arxiv"][key] += result[key]

                if process_hf:
                    result = self.process_huggingface(date=current_date, **kwargs)
                    for key in result:
                        total_results["hf"][key] += result[key]
        else:
            # 处理单天
            if process_arxiv:
                total_results["arxiv"] = self.process_arxiv(**kwargs)

            if process_hf:
                total_results["hf"] = self.process_huggingface(date=date, **kwargs)

        # 发送通知
        arxiv_count = total_results["arxiv"]["processed"]
        hf_count = total_results["hf"]["processed"]

        if arxiv_count > 0 or hf_count > 0:
            try:
                common_utils.send_slack(
                    f'论文更新完成: ArXiv {arxiv_count} 篇, HuggingFace {hf_count} 篇'
                )
            except Exception as e:
                logger.warning(f"发送Slack通知失败: {e}")

        return total_results


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='每日论文抓取工具')

    parser.add_argument('--keywords', type=str, nargs='+', help='搜索关键词')
    parser.add_argument('--categories', type=str, nargs='+', help='ArXiv分类')
    parser.add_argument('--date', type=str, help='指定日期 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, help='处理过去N天')
    parser.add_argument('--limit', type=int, help='搜索结果限制')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--no-hf', action='store_true', help='不处理HuggingFace')
    parser.add_argument('--no-arxiv', action='store_true', help='不处理ArXiv')
    parser.add_argument('--download-pdf', action='store_true', help='下载PDF')
    parser.add_argument('--no-download-pdf', action='store_false', dest='download_pdf')
    parser.add_argument('--pdf-dir', type=str, help='PDF保存目录')

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    try:
        # 创建应用
        app = DailyPaperApp(config_path=args.config)

        # 命令行参数覆盖配置
        if args.keywords:
            app.settings.keywords = args.keywords
        if args.categories:
            app.settings.categories = args.categories
        if args.limit:
            app.settings.search_limit = args.limit
        if args.pdf_dir:
            app.settings.pdf_dir = args.pdf_dir
        if args.download_pdf is not None:
            app.settings.download_pdf = args.download_pdf

        logger.info(f"开始运行 Daily Paper App")
        logger.info(f"关键词: {app.settings.keywords}")
        logger.info(f"分类: {app.settings.categories}")

        # 运行
        results = app.run(
            process_arxiv=not args.no_arxiv,
            process_hf=not args.no_hf,
            date=args.date,
            days=args.days
        )

        logger.info(f"运行完成: {results}")

    except Exception as e:
        logger.critical(f"程序运行错误: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

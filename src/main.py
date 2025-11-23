#!/usr/bin/env python3
"""
Zotero-Notion-Paper-Flow 主入口
使用重构后的架构运行论文抓取和同步
"""
import os
import sys
import argparse
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta

# 配置路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config.settings import Settings
from container import ServiceContainer
from core.processor import PaperProcessor
from services.llm import LLMServiceFactory
from services.data_sources import DataSourceFactory, ArxivDataSource, HuggingFaceDataSource
from services.storage import StorageFactory, NotionStorage, ZoteroStorage

# 设置日志
def setup_logging(log_dir: Path = None) -> logging.Logger:
    """配置日志"""
    if log_dir is None:
        log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"paper_flow_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='论文抓取和同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py --keywords "reinforcement learning" --limit 10
  python main.py --date 2025-01-01 --no-hf
  python main.py --days 3 --download-pdf
        '''
    )

    # 搜索参数
    parser.add_argument('--keywords', type=str, nargs='+', help='搜索关键词')
    parser.add_argument('--categories', type=str, nargs='+', help='ArXiv分类 (如 cs.LG)')
    parser.add_argument('--limit', type=int, help='搜索结果限制')

    # 日期参数
    parser.add_argument('--date', type=str, help='指定日期 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, help='处理过去N天的数据')

    # 数据源参数
    parser.add_argument('--no-hf', action='store_true', help='不处理HuggingFace')
    parser.add_argument('--no-arxiv', action='store_true', help='不处理ArXiv搜索')

    # PDF参数
    parser.add_argument('--download-pdf', action='store_true', help='下载PDF')
    parser.add_argument('--no-download-pdf', action='store_false', dest='download_pdf')
    parser.add_argument('--pdf-dir', type=str, help='PDF保存目录')

    # 配置参数
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--llm-service', type=str, choices=['deepseek', 'kimi', 'zhipu'],
                        help='LLM服务选择')

    # 服务开关
    parser.add_argument('--no-notion', action='store_true', help='禁用Notion')
    parser.add_argument('--no-zotero', action='store_true', help='禁用Zotero')

    return parser.parse_args()

def create_container(settings: Settings) -> ServiceContainer:
    """创建服务容器"""
    container = ServiceContainer(settings)

    # 注册LLM服务
    container.register('llm', lambda s: LLMServiceFactory.create(
        s.llm.service,
        api_key=s.llm.api_key,
        base_url=s.llm.base_url,
        model_name=s.llm.model_name
    ))

    # 注册数据源
    container.register('arxiv', lambda s: ArxivDataSource(
        output_dir=str(PROJECT_ROOT / "output"),
        llm_service=container.get('llm')
    ))

    container.register('huggingface', lambda s: HuggingFaceDataSource(
        output_dir=str(PROJECT_ROOT / "output"),
        proxy=s.proxy
    ))

    # 注册存储服务
    if settings.services.notion:
        container.register('notion', lambda s: NotionStorage(
            db_id=s.notion.db_id if hasattr(s, 'notion') else None,
            secret=s.notion.secret if hasattr(s, 'notion') else None,
            create_time=datetime.now()
        ))

    if settings.services.zotero:
        container.register('zotero', lambda s: ZoteroStorage(
            api_key=s.zotero.api_key if hasattr(s, 'zotero') else None,
            user_id=s.zotero.user_id if hasattr(s, 'zotero') else None,
            create_time=datetime.now()
        ))

    return container

def run_processor(
    container: ServiceContainer,
    settings: Settings,
    process_arxiv: bool = True,
    process_hf: bool = True,
    date: str = None
):
    """运行处理器"""
    results = {
        "arxiv": {"processed": 0, "errors": 0},
        "hf": {"processed": 0, "errors": 0}
    }

    # 获取服务
    llm_service = container.get('llm')

    data_sources = {}
    if process_arxiv:
        data_sources['arxiv'] = container.get('arxiv')

    storages = {}
    try:
        if settings.services.notion:
            storages['notion'] = container.get('notion')
    except Exception as e:
        logger.warning(f"Notion服务不可用: {e}")

    try:
        if settings.services.zotero:
            storages['zotero'] = container.get('zotero')
    except Exception as e:
        logger.warning(f"Zotero服务不可用: {e}")

    # 创建处理器
    processor = PaperProcessor(
        data_sources=data_sources,
        storages=storages,
        llm_service=llm_service,
        config={
            "category_map": settings.category_map,
            "default_category": settings.default_category,
            "download_pdf": settings.download_pdf,
            "pdf_dir": settings.pdf_dir
        }
    )

    # 处理ArXiv论文
    if process_arxiv and 'arxiv' in data_sources:
        try:
            logger.info(f"开始处理ArXiv论文: 关键词={settings.keywords}, 分类={settings.categories}")
            result = processor.process_papers(
                source='arxiv',
                keywords=settings.keywords,
                categories=settings.categories,
                limit=settings.search_limit,
                download_pdf=settings.download_pdf
            )
            results["arxiv"] = result
            logger.info(f"ArXiv处理完成: {result}")
        except Exception as e:
            logger.error(f"ArXiv处理失败: {e}")
            logger.debug(traceback.format_exc())

    # 处理HuggingFace论文
    if process_hf:
        try:
            hf_source = container.get('huggingface')
            logger.info(f"开始处理HuggingFace论文: 日期={date}")

            # 获取论文列表
            hf_papers = hf_source.fetch_papers(date=date)

            # 使用ArXiv补充详细信息
            arxiv_source = container.get('arxiv') if process_arxiv else ArxivDataSource(
                output_dir=str(PROJECT_ROOT / "output"),
                llm_service=llm_service
            )

            processed = 0
            for hf_paper in hf_papers:
                try:
                    # 从ArXiv获取详细信息
                    paper = arxiv_source.get_by_id(
                        hf_paper.id,
                        hf_obj={
                            'media_type': hf_paper.media_type,
                            'media_url': hf_paper.media_url
                        }
                    )

                    if paper:
                        # 保存到存储服务
                        for storage_name, storage in storages.items():
                            try:
                                storage.insert(paper)
                                processed += 1
                            except Exception as e:
                                logger.error(f"保存到{storage_name}失败: {e}")

                except Exception as e:
                    logger.error(f"处理HuggingFace论文失败 {hf_paper.id}: {e}")

            results["hf"]["processed"] = processed
            logger.info(f"HuggingFace处理完成: 处理 {processed}/{len(hf_papers)} 篇")

        except Exception as e:
            logger.error(f"HuggingFace处理失败: {e}")
            logger.debug(traceback.format_exc())

    return results

def main():
    """主函数"""
    args = parse_args()

    try:
        # 加载配置
        config_path = args.config or str(PROJECT_ROOT / "config.json")
        if Path(config_path).exists():
            settings = Settings.from_file(config_path)
        else:
            settings = Settings()

        # 命令行参数覆盖配置
        if args.keywords:
            settings.keywords = args.keywords
        if args.categories:
            settings.categories = args.categories
        if args.limit:
            settings.search_limit = args.limit
        if args.llm_service:
            settings.llm.service = args.llm_service
        if args.download_pdf is not None:
            settings.download_pdf = args.download_pdf
        if args.pdf_dir:
            settings.pdf_dir = args.pdf_dir
        if args.no_notion:
            settings.services.notion = False
        if args.no_zotero:
            settings.services.zotero = False

        # 确定日期
        if args.date:
            target_date = args.date
        else:
            target_date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"开始运行 - 日期: {target_date}")
        logger.info(f"关键词: {settings.keywords}")
        logger.info(f"分类: {settings.categories}")
        logger.info(f"服务: Notion={settings.services.notion}, Zotero={settings.services.zotero}")

        # 创建服务容器
        container = create_container(settings)

        # 处理多天数据
        if args.days:
            total_results = {"arxiv": 0, "hf": 0}

            for i in range(args.days):
                current_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                logger.info(f"处理日期: {current_date}")

                results = run_processor(
                    container, settings,
                    process_arxiv=not args.no_arxiv,
                    process_hf=not args.no_hf,
                    date=current_date
                )

                total_results["arxiv"] += results.get("arxiv", {}).get("processed", 0)
                total_results["hf"] += results.get("hf", {}).get("processed", 0)

            logger.info(f"多天处理完成: ArXiv={total_results['arxiv']}, HuggingFace={total_results['hf']}")
        else:
            # 处理单天
            results = run_processor(
                container, settings,
                process_arxiv=not args.no_arxiv,
                process_hf=not args.no_hf,
                date=target_date
            )

            logger.info(f"处理完成: {results}")

        logger.info("程序运行完成")

    except Exception as e:
        logger.critical(f"程序运行错误: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()

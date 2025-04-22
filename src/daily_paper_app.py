"""
Modified by Xiaodong Zheng on 2025/4/22
增加错误处理、命令行参数解析、日志记录、PDF自动下载和可配置性
"""
import os
import sys
import json
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from tqdm import tqdm
import time

# 配置路径
project_root = Path(__file__).parent.parent.resolve()
sys.path.append(str(project_root))

# 导入项目模块
import common_utils
from service.arxiv_visitor import ArxivVisitor
from service.hf_visotor import HFDailyPaperVisitor
from service.notion_service import NotionService
from service.wolai_service import WolaiService 
from service.zotero_service import ZoteroService
from service.pdf_downloader import download_paper_pdfs

# 设置日志

# 在setup_logging函数中修改日志文件路径
def setup_logging():
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.resolve()
    
    # 将日志文件保存在项目根目录下，可以根据需要修改这个路径
    log_file = os.path.join(project_root, f'daily_paper_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# 创建日志记录器
logger = setup_logging()

# 定义分类映射 - 将论文主题映射到Zotero分类
category_map = {
    'NLP': ["WXBCJ969", "DFGZNVCM"],
    'RL': ["DXU9QIKA", "DFGZNVCM"],
    'MARL': ["8DXU5DFC", "DFGZNVCM"],
    'MTS': ["JSYLDU9Z", "DFGZNVCM"],
    '多模态': ["H2AHAFZF", "DFGZNVCM"],
    'CV': ["H8W7XVEC", "DFGZNVCM"],
    'ML': ["TFK8IUCH", "DFGZNVCM"],
    'LLM': ["WXBCJ969", "DFGZNVCM"],  # 默认与NLP同类
    'DL': ["TFK8IUCH", "DFGZNVCM"],   # 深度学习与机器学习同类
}

def load_config(config_path=None):
    """加载配置文件"""
    if not config_path:
        config_path = os.path.join(project_root, 'config.json')
    
    # 默认配置
    default_config = {
        "keywords": ["reinforcement learning"],
        "date": None,
        "categories": ["cs.LG", "cs.AI"],
        "proxy": "http://127.0.0.1:7890",
        "services": {
            "notion": True,
            "zotero": True,
            "wolai": False
        },
        "download_pdf": True,  # 新增: 是否下载PDF
        "pdf_dir": "papers/pdf",  # 新增: PDF保存目录
        "search_limit": 10,
        "retries": 3
    }
    
    # 尝试加载配置文件
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                logger.info(f"已加载配置文件: {config_path}")
                # 合并配置
                for key, value in user_config.items():
                    default_config[key] = value
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.debug(traceback.format_exc())
    else:
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        
    return default_config

def process_arxiv_papers(arxiv_visitor, notion_service, wolai_service, zotero_service, 
                        keywords, categories, date, limit=20, enable_services=None, download_pdf=True, pdf_dir=None):
    """处理ArXiv论文"""
    if enable_services is None:
        enable_services = {"notion": True, "zotero": True, "wolai": True}
    
    logger.info(f"搜索关键词: {keywords}, 分类: {categories}, 限制: {limit}")
    
    output_root = os.path.join(project_root, 'output')
    arxiv_ckpt_filename = os.path.join(output_root, 'cache', 'arxiv_ckpt.txt')
    
    # 确保检查点文件存在
    os.makedirs(os.path.dirname(arxiv_ckpt_filename), exist_ok=True)
    if not os.path.exists(arxiv_ckpt_filename):
        open(arxiv_ckpt_filename, 'w').close()
    
    # 确保PDF目录存在
    if download_pdf and pdf_dir:
        os.makedirs(pdf_dir, exist_ok=True)
        logger.info(f"PDF将保存到: {pdf_dir}")
    
    # 加载已处理的论文ID
    with open(arxiv_ckpt_filename, 'r') as f:
        arxiv_ckpt = set(line.strip() for line in f if line.strip())
    
    # 搜索论文
    try:
        search_results = arxiv_visitor.search_by_keywords(keywords, categories=categories, limit=limit)
    except Exception as e:
        logger.error(f"搜索ArXiv论文时出错: {e}")
        logger.debug(traceback.format_exc())
        return 0, 0, 0
    
    processed_count = 0
    error_count = 0
    
    with open(arxiv_ckpt_filename, 'a') as arxiv_ckpt_file:
        for arxiv_obj in tqdm(search_results, desc="处理搜索结果"):
            if arxiv_obj.id in arxiv_ckpt:
                logger.info(f"已处理过文章: {arxiv_obj.id}, 跳过")
                continue
                
            try:
                logger.info(f"处理文章: {arxiv_obj.id}, 标题: {arxiv_obj.title}, 分类: {arxiv_obj.category}")
                
                # 下载PDF文件
                if download_pdf and pdf_dir:
                    try:
                        logger.info(f"开始下载PDF: {arxiv_obj.id}")
                        # 使用pdf_downloader中的下载函数
                        pdf_paths = download_paper_pdfs([arxiv_obj.id], pdf_dir, arxiv_visitor)
                        if pdf_paths:
                            logger.info(f"PDF已下载到: {pdf_paths[0]}")
                        else:
                            logger.warning(f"PDF下载失败: {arxiv_obj.id}")
                    except Exception as e:
                        logger.error(f"下载PDF时出错: {e}")
                        logger.debug(traceback.format_exc())
                
                # 插入到Zotero
                if enable_services.get("zotero", True) and zotero_service is not None:
                    try:
                        logger.info(f"插入到Zotero: {arxiv_obj.id}")
                        # 查找匹配的分类，如果没有则使用默认分类
                        params = category_map.get(arxiv_obj.category, ["DFGZNVCM"])
                        zotero_service.insert(arxiv_obj, params)
                        logger.info(f"成功插入到Zotero: {arxiv_obj.id}")
                    except Exception as e:
                        logger.error(f"插入到Zotero时出错: {e}")
                        logger.debug(traceback.format_exc())
                
                # 插入到Notion
                if enable_services.get("notion", True) and notion_service is not None:
                    try:
                        logger.info(f"插入到Notion: {arxiv_obj.id}")
                        notion_service.insert(arxiv_obj)
                        logger.info(f"成功插入到Notion: {arxiv_obj.id}")
                    except Exception as e:
                        logger.error(f"插入到Notion时出错: {e}")
                        logger.debug(traceback.format_exc())
                
                # 插入到我来
                if enable_services.get("wolai", True) and wolai_service is not None:
                    try:
                        logger.info(f"插入到我来: {arxiv_obj.id}")
                        wolai_service.insert(arxiv_obj)
                        logger.info(f"成功插入到我来: {arxiv_obj.id}")
                    except Exception as e:
                        logger.error(f"插入到我来时出错: {e}")
                        logger.debug(traceback.format_exc())
                
                # 标记为已处理
                arxiv_ckpt.add(arxiv_obj.id)
                arxiv_ckpt_file.write(arxiv_obj.id + '\n')
                arxiv_ckpt_file.flush()  # 确保实时写入
                processed_count += 1
                
            except Exception as e:
                logger.error(f"处理文章时出错: {arxiv_obj.id}, 错误: {e}")
                logger.debug(traceback.format_exc())
                error_count += 1
    
    return processed_count, error_count, len(search_results)

def process_hf_papers(hf_visitor, arxiv_visitor, notion_service, wolai_service, zotero_service, 
                      enable_services=None, download_pdf=True, pdf_dir=None):
    """处理HuggingFace论文"""
    if enable_services is None:
        enable_services = {"notion": True, "zotero": True, "wolai": True}
    
    output_root = os.path.join(project_root, 'output')
    create_dt = hf_visitor.datetime.strftime('%Y-%m-%d')
    ckpt_filename = os.path.join(output_root, "cache", f"ckpt_{create_dt}.txt")
    
    # 确保检查点文件存在
    os.makedirs(os.path.dirname(ckpt_filename), exist_ok=True)
    if not os.path.exists(ckpt_filename):
        open(ckpt_filename, 'w').close()
        
    # 确保PDF目录存在
    if download_pdf and pdf_dir:
        os.makedirs(pdf_dir, exist_ok=True)
        logger.info(f"PDF将保存到: {pdf_dir}")
    
    # 加载已处理的论文ID
    with open(ckpt_filename, 'r') as f:
        ckpt = set(line.strip() for line in f if line.strip())
    
    processed_count = 0
    error_count = 0
    
    with open(ckpt_filename, 'a') as ckpt_file:
        for hf_obj in tqdm(hf_visitor.paper_list, desc=create_dt):
            if hf_obj['id'] in ckpt:
                logger.info(f"已处理过文章: {hf_obj['id']}, 跳过")
                continue
                
            try:
                logger.info(f"处理文章: {hf_obj['id']}, 标题: {hf_obj['title']}")
                
                # 获取ArXiv详细信息
                try:
                    arxiv_obj = arxiv_visitor.find_by_id(hf_obj['id'])
                except Exception as e:
                    logger.error(f"获取ArXiv信息时出错: {hf_obj['id']}, 错误: {e}")
                    logger.debug(traceback.format_exc())
                    continue
                
                logger.info(f"分类: {arxiv_obj.category}")
                
                # 下载PDF文件
                if download_pdf and pdf_dir:
                    try:
                        logger.info(f"开始下载PDF: {hf_obj['id']}")
                        # 使用pdf_downloader中的下载函数
                        pdf_paths = download_paper_pdfs([hf_obj['id']], pdf_dir, arxiv_visitor)
                        if pdf_paths:
                            logger.info(f"PDF已下载到: {pdf_paths[0]}")
                        else:
                            logger.warning(f"PDF下载失败: {hf_obj['id']}")
                    except Exception as e:
                        logger.error(f"下载PDF时出错: {e}")
                        logger.debug(traceback.format_exc())
                
                # 插入到Zotero
                if enable_services.get("zotero", True) and zotero_service is not None:
                    try:
                        logger.info(f"插入到Zotero: {hf_obj['id']}")
                        params = category_map.get(arxiv_obj.category, ["DFGZNVCM"])
                        zotero_service.insert(arxiv_obj, params)
                        logger.info(f"成功插入到Zotero: {hf_obj['id']}")
                    except Exception as e:
                        logger.error(f"插入到Zotero时出错: {e}")
                        logger.debug(traceback.format_exc())
                
                # 插入到Notion
                if enable_services.get("notion", True) and notion_service is not None:
                    try:
                        logger.info(f"插入到Notion: {hf_obj['id']}")
                        notion_service.insert(arxiv_obj, hf_obj)
                        logger.info(f"成功插入到Notion: {hf_obj['id']}")
                    except Exception as e:
                        logger.error(f"插入到Notion时出错: {e}")
                        logger.debug(traceback.format_exc())
                
                # 插入到我来
                if enable_services.get("wolai", True) and wolai_service is not None:
                    try:
                        logger.info(f"插入到我来: {hf_obj['id']}")
                        # 如果HF对象具有媒体信息，应该一并传递
                        if 'media_type' in hf_obj and 'media_url' in hf_obj and hf_obj['media_type'] and hf_obj['media_url']:
                            # 确保arxiv_obj已包含媒体信息
                            arxiv_obj.media_type = hf_obj['media_type']
                            arxiv_obj.media_url = hf_obj['media_url']
                        wolai_service.insert(arxiv_obj)
                        logger.info(f"成功插入到我来: {hf_obj['id']}")
                    except Exception as e:
                        logger.error(f"插入到我来时出错: {e}")
                        logger.debug(traceback.format_exc())
                
                # 标记为已处理
                ckpt.add(hf_obj['id'])
                ckpt_file.write(hf_obj['id'] + '\n')
                ckpt_file.flush()  # 确保实时写入
                processed_count += 1
                
            except Exception as e:
                logger.error(f"处理文章时出错: {hf_obj['id']}, 错误: {e}")
                logger.debug(traceback.format_exc())
                error_count += 1
    
    return processed_count, error_count, len(hf_visitor.paper_list)

def main(args=None):
    """主函数"""
    if args is None:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='ArXiv论文搜索工具')
        parser.add_argument('--keywords', type=str, nargs='+', help='要搜索的关键字列表')
        parser.add_argument('--categories', type=str, nargs='+', help='要搜索的分类列表，例如 cs.LG')
        parser.add_argument('--date', type=str, help='指定日期，格式为 YYYY-MM-DD')
        parser.add_argument('--config', type=str, help='配置文件路径')
        parser.add_argument('--no-hf', action='store_true', help='不处理HuggingFace论文')
        parser.add_argument('--no-arxiv', action='store_true', help='不处理ArXiv搜索')
        parser.add_argument('--limit', type=int, help='搜索结果限制')
        parser.add_argument('--days', type=int, help='处理过去几天的数据（与date互斥）')
        parser.add_argument('--download-pdf', action='store_true', help='下载论文PDF')
        parser.add_argument('--no-download-pdf', action='store_false', dest='download_pdf', help='不下载论文PDF')
        parser.add_argument('--pdf-dir', type=str, help='PDF保存目录')
        args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config if hasattr(args, 'config') and args.config else None)
    
    # 命令行参数覆盖配置文件
    keywords = args.keywords if hasattr(args, 'keywords') and args.keywords else config.get('keywords')
    categories = args.categories if hasattr(args, 'categories') and args.categories else config.get('categories')
    date = args.date if hasattr(args, 'date') and args.date else config.get('date')
    limit = args.limit if hasattr(args, 'limit') and args.limit else config.get('search_limit', 20)
    
    # PDF下载相关配置
    download_pdf = args.download_pdf if hasattr(args, 'download_pdf') and args.download_pdf is not None else config.get('download_pdf', True)
    pdf_dir = args.pdf_dir if hasattr(args, 'pdf_dir') and args.pdf_dir else config.get('pdf_dir', os.path.join(project_root, 'papers', 'pdf'))
    
    # 设置日期
    if date:
        # 使用指定日期
        create_time = datetime.strptime(date, '%Y-%m-%d')
    else:
        # 使用当前日期
        create_time = datetime.now()
    
    # 设置服务启用状态
    services_config = config.get('services', {})
    enable_services = {
        "notion": services_config.get("notion", True),
        "zotero": services_config.get("zotero", True),
        "wolai": services_config.get("wolai", False)
    }
    
    logger.info(f"开始运行，日期: {create_time.strftime('%Y-%m-%d')}")
    logger.info(f"关键词: {keywords}")
    logger.info(f"分类: {categories}")
    logger.info(f"启用服务: {enable_services}")
    logger.info(f"下载PDF: {download_pdf}")
    if download_pdf:
        logger.info(f"PDF保存目录: {pdf_dir}")
    
    # 初始化组件
    output_root = os.path.join(project_root, 'output')
    os.makedirs(os.path.join(output_root, 'cache'), exist_ok=True)
    
    arxiv_visitor = ArxivVisitor(output_dir=output_root)
    notion_service = NotionService(create_time=create_time) if enable_services.get("notion") else None
    wolai_service = WolaiService() if enable_services.get("wolai") else None
    zotero_service = ZoteroService(create_time=create_time, use_proxy=True) if enable_services.get("zotero") else None
    
    # 处理多天数据
    if hasattr(args, 'days') and args.days:
        days = args.days
        logger.info(f"处理过去 {days} 天的数据")
        
        total_arxiv_processed = 0
        total_hf_processed = 0
        
        for i in range(days):
            current_date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            logger.info(f"处理日期: {current_date}")
            
            # 更新服务的日期
            current_datetime = datetime.strptime(current_date, '%Y-%m-%d')
            if notion_service:
                notion_service.create_time = current_datetime
            if zotero_service:
                zotero_service.create_time = current_datetime
            
            # 处理ArXiv论文
            if not (hasattr(args, 'no_arxiv') and args.no_arxiv):
                try:
                    processed, errors, total = process_arxiv_papers(
                        arxiv_visitor, notion_service, wolai_service, zotero_service,
                        keywords, categories, current_date, limit, enable_services,
                        download_pdf, pdf_dir
                    )
                    total_arxiv_processed += processed
                    logger.info(f"日期 {current_date} ArXiv论文: 处理 {processed}/{total}, 错误 {errors}")
                except Exception as e:
                    logger.error(f"处理日期 {current_date} 的ArXiv论文时出错: {e}")
                    logger.debug(traceback.format_exc())
            
            # 处理HuggingFace论文
            if not (hasattr(args, 'no_hf') and args.no_hf):
                try:
                    hf_visitor = HFDailyPaperVisitor(output_root, dt=current_date)
                    processed, errors, total = process_hf_papers(
                        hf_visitor, arxiv_visitor, notion_service, wolai_service, zotero_service, 
                        enable_services, download_pdf, pdf_dir
                    )
                    total_hf_processed += processed
                    logger.info(f"日期 {current_date} HuggingFace论文: 处理 {processed}/{total}, 错误 {errors}")
                except Exception as e:
                    logger.error(f"处理日期 {current_date} 的HuggingFace论文时出错: {e}")
                    logger.debug(traceback.format_exc())
            
            # 防止API限制，休眠一段时间
            if i < days - 1:
                time.sleep(5)
        
        logger.info(f"完成多天处理! 共处理 ArXiv论文: {total_arxiv_processed}, HuggingFace论文: {total_hf_processed}")
        
        if total_arxiv_processed > 0 or total_hf_processed > 0:
            try:
                common_utils.send_slack(f'更新了 ArXiv文章 {total_arxiv_processed} 篇, HuggingFace文章 {total_hf_processed} 篇')
                logger.info("已发送Slack通知")
            except Exception as e:
                logger.error(f"发送Slack通知失败: {e}")
    else:
        # 处理单天数据
        arxiv_processed = 0
        hf_processed = 0
        
        # 处理ArXiv论文
        if not (hasattr(args, 'no_arxiv') and args.no_arxiv):
            try:
                processed, errors, total = process_arxiv_papers(
                    arxiv_visitor, notion_service, wolai_service, zotero_service,
                    keywords, categories, date, limit, enable_services,
                    download_pdf, pdf_dir
                )
                arxiv_processed = processed
                logger.info(f"ArXiv论文: 处理 {processed}/{total}, 错误 {errors}")
            except Exception as e:
                logger.error(f"处理ArXiv论文时发生错误: {e}")
                logger.debug(traceback.format_exc())
        
        # 处理HuggingFace论文
        if not (hasattr(args, 'no_hf') and args.no_hf):
            try:
                hf_visitor = HFDailyPaperVisitor(output_root, dt=date)
                processed, errors, total = process_hf_papers(
                    hf_visitor, arxiv_visitor, notion_service, wolai_service, zotero_service, 
                    enable_services, download_pdf, pdf_dir
                )
                hf_processed = processed
                logger.info(f"HuggingFace论文: 处理 {processed}/{total}, 错误 {errors}")
            except Exception as e:
                logger.error(f"处理HuggingFace论文时发生错误: {e}")
                logger.debug(traceback.format_exc())
        
        # 发送通知
        if arxiv_processed > 0 or hf_processed > 0:
            try:
                common_utils.send_slack(f'更新了 ArXiv文章 {arxiv_processed} 篇, HuggingFace文章 {hf_processed} 篇')
                logger.info("已发送Slack通知")
            except Exception as e:
                logger.error(f"发送Slack通知失败: {e}")
    
    logger.info("程序运行完成")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(f"程序运行时出现严重错误: {e}")
        logger.critical(traceback.format_exc())
        try:
            common_utils.send_slack(f'每日论文应用程序运行失败: {str(e)}')
        except:
            pass
        sys.exit(1)
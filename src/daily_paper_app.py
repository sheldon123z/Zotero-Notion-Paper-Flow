"""
Modified by: Xiaodong Zheng
"""
import os
import sys
import json
import common_utils
import logging  # 导入 logging 模块
from pathlib import Path
from tqdm import tqdm
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent.resolve()))
from service.arxiv_visitor import ArxivVisitor
from service.hf_visotor import HFDailyPaperVisitor
from service.notion_service import NotionService
from service.wolai_service import WolaiService
from service.zotero_service import ZoteroService

# 设置日志记录
log_file = os.path.join(Path(__file__).parent.parent.resolve(), 'output', 'logfile.log')
logging.basicConfig(
    filename=log_file,  # 日志输出文件
    level=logging.INFO,  # 设置日志级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    datefmt='%Y-%m-%d %H:%M:%S'  # 日期格式
)

# 创建 logger 实例
logger = logging.getLogger(__name__)

# 这里记录的是 zotero 的分类的 ID，需要根据你的数据库进行修改，
# 是将主题为 key 值的文章插入到 zotero 的对应分类下
# value 的分类可以增加或修改，但是 key 的值如果需要修改的话需要在 llm 服务中进行修改
category_map = {
    'NLP': ["WXBCJ969", "DFGZNVCM"],
    'RL': ["DXU9QIKA", "DFGZNVCM"],
    'MARL': ["8DXU5DFC", "DFGZNVCM"],
    'MTS': ["JSYLDU9Z", "DFGZNVCM"],
    '多模态': ["H2AHAFZF", "DFGZNVCM"],
    'CV': ["H8W7XVEC", "DFGZNVCM"]
}

def main(dt=None, keywords=None, categories=None):
    output_root = os.path.join(Path(__file__).parent.parent.resolve(), 'output')
    os.makedirs(os.path.join(output_root, 'cache'), exist_ok=True)
    
    # 定义 arXiv checkpoint 文件路径
    arxiv_ckpt_filename = os.path.join(output_root, 'cache', 'arxiv_ckpt.txt')
    if not os.path.exists(arxiv_ckpt_filename):
        open(arxiv_ckpt_filename, 'w').close()  # 创建空文件

    # 加载已处理的 arXiv 论文 ID
    with open(arxiv_ckpt_filename, 'r') as f:
        arxiv_ckpt = set(line.strip() for line in f if line.strip())
 
    # 如果没有提供关键词或日期，从配置文件中读取
    if not keywords or not dt or not categories:
        config_path = os.path.join(Path(__file__).parent.parent.resolve(), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if not keywords:
                    keywords = config.get('keywords', [])
                if not dt:
                    dt = config.get('date')
                if not categories:
                    categories = config.get('categories')
        else:
            # 如果没有配置文件，使用默认关键字和分类
            if not keywords:
                keywords = ['reinforcement learning', 'power system', 'large language model']
            if not dt:
                dt = datetime.now().strftime('%Y-%m-%d')
            if not categories:
                categories = None  # 或者设置为您希望的默认分类
    if dt:
        # 如果指定了日期，使用指定日期
        create_time = datetime.strptime(dt, '%Y-%m-%d')
    else:
        # 如果未指定日期，使用当前日期
        create_time = datetime.now()
        

    arxiv_visitor = ArxivVisitor(output_dir=output_root)
    notion_service = NotionService(create_time=create_time)
    wolai_service = WolaiService()
    zotero_service = ZoteroService(create_time=create_time, use_proxy=True)
    
    # 搜索并插入特定关键词的文章
    search_results = arxiv_visitor.search_by_keywords(keywords, categories=categories, limit=20)  # limit 可以根据需要调整

    with open(arxiv_ckpt_filename, 'a') as arxiv_ckpt_file:
        for arxiv_obj in tqdm(search_results, desc="处理搜索结果"):
            if arxiv_obj.id in arxiv_ckpt:
                logger.info(f"存在记录，跳过文章:{arxiv_obj.id}")
                continue
            # 日志记录
            logger.info(f"处理文章: {arxiv_obj.id} 分类为: {arxiv_obj.category}")

            # 插入 Zotero
            try:
                logger.info(f"将文章插入 Zotero: {arxiv_obj.id}")
                params = category_map.get(arxiv_obj.category, ["9DDH4UIZ"])  # 使用一个默认分类存放 arXiv 上的文章
                zotero_service.insert(arxiv_obj, params)
                logger.info(f"已将文章插入 Zotero: {arxiv_obj.id}")
            except Exception as e:
                logger.error(f"将文章插入 Zotero 时出错: {e}")
                continue

            # 如果需要，您也可以插入到 Notion 或 Wolai
            try:
                notion_service.insert(formatted_arxiv_obj=arxiv_obj)
                logger.info(f"已将文章插入 Notion: {arxiv_obj.id}")
            except Exception as e:
                logger.error(f"将文章插入 Notion 时出错: {e}")

            try:
                wolai_service.insert(arxiv_obj)
                logger.info(f"已将文章插入我来: {arxiv_obj.id}")
            except Exception as e:
                logger.error(f"将文章插入我来时出错: {e}")
            
            # 在成功处理后，将论文 ID 添加到 checkpoint
            arxiv_ckpt.add(arxiv_obj.id)
            arxiv_ckpt_file.write(arxiv_obj.id + '\n')
            
        if len(search_results) > 0:
            logger.info(f"更新Arxiv文章 {len(search_results)} 篇")
            # common_utils.send_slack(f'更新文章 {len(search_results)} 篇')

    # 处理 Hugging Face 数据集
    hf_visitor = HFDailyPaperVisitor(output_root, dt=dt)
    create_dt = hf_visitor.datetime.strftime('%Y-%m-%d')
    ckpt_filename = os.path.join(output_root, "cache", f"ckpt_{create_dt}.txt")
    ckpt_file = open(ckpt_filename, 'a')
    ckpt = set()
    if os.path.exists(ckpt_filename):
        ckpt = set([line.strip() for line in open(ckpt_filename, 'r').readlines() if line.strip() != ''])

    with open(ckpt_filename, 'a') as ckpt_file:
        for hf_obj in tqdm(hf_visitor.paper_list, desc=create_dt):
            # if hf_obj['id'] in ckpt:
            #     continue
            arxiv_obj = arxiv_visitor.find_by_id(hf_obj['id'])

            # 日志记录替代 print
            logger.info(f"处理文章: {hf_obj['id']} 分类为: {arxiv_obj.category}")
            # 处理 Zotero
            try:
                logger.info(f"将文章插入 Zotero: {hf_obj['id']}")
                params = category_map.get(arxiv_obj.category, ["DFGZNVCM"])
                zotero_service.insert(arxiv_obj, params)
                logger.info(f"已将文章插入 Zotero: {hf_obj['id']}")
            except Exception as e:
                logger.error(f"将文章插入 Zotero 时出错: {e}")
                continue

            # 处理 Notion
            try:
                logger.info(f"将文章插入 Notion: {hf_obj['id']}")
                notion_service.insert(arxiv_obj,hf_obj)  # 插入 Notion
            except Exception as e:
                logger.error(f"将文章插入 Notion 时出错: {e}")

            # 处理 Wolai
            try:
                wolai_service.insert(arxiv_obj)
                logger.info(f"正在将文章插入我来: {hf_obj['id']}")
            except Exception as e:
                logger.error(f"将文章插入我来时出错: {e}")
                continue

            ckpt.add(hf_obj['id'])
            ckpt_file.write(hf_obj['id'])
            ckpt_file.write('\n')
    

    if len(hf_visitor.paper_list) > 0:
        logger.info(f"更新文章 {len(hf_visitor.paper_list)} 篇")
        # common_utils.send_slack(f'更新文章 {len(hf_visitor.paper_list)} 篇')


if __name__ == '__main__':
    import argparse
    from datetime import datetime, timedelta

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='ArXiv 论文搜索工具')
    parser.add_argument('--keywords', type=str, nargs='+', help='要搜索的关键字列表，可以使用括号表示嵌套')
    parser.add_argument('--categories', type=str, nargs='+', help='要搜索的分类列表，例如 cs.LG')
    parser.add_argument('--date', type=str, help='指定日期，格式为 YYYY-MM-DD')
    args = parser.parse_args()

    keywords = args.keywords
    dt = args.date
    categories = args.categories

    # 调用 main 函数
    main(dt=dt, keywords=keywords,categories=categories)
    

    # # 获取前天日期
    # start_date = datetime.now() 

    # # 往前追溯period天
    # period = 7
    # # 生成过去30天的日期，格式为 YYYY-MM-DD
    # for i in range(period):
    #     dt = (start_date - timedelta(days=i)).strftime('%Y-%m-%d')
        
    #     # 调用 main 函数，保持 keywords 和 categories 不变
    #     main(dt=dt, keywords=keywords, categories=categories)
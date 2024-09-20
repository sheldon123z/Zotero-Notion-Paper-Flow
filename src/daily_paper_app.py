"""
Modified by: Xiaodong Zheng
"""
import os
import sys
import common_utils
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from service.arxiv_visitor import ArxivVisitor
from service.hf_visotor import HFDailyPaperVisitor
from tqdm import tqdm

from service.notion_service import NotionService
from service.wolai_service import WolaiService
from service.zotero_service import ZoteroService


def main(dt=None):
    output_root = os.path.join(Path(__file__).parent.parent.resolve(), 'output')
    os.makedirs(os.path.join(output_root, 'cache'), exist_ok=True)

    hf_visitor = HFDailyPaperVisitor(output_root, dt=dt)
    create_dt = hf_visitor.datetime.strftime('%Y-%m-%d')
    ckpt_filename = os.path.join(output_root, "cache", f"ckpt_{create_dt}.txt")
    ckpt_file = open(ckpt_filename, 'a')
    ckpt = set()
    if os.path.exists(ckpt_filename):
        ckpt = set([line.strip() for line in open(ckpt_filename, 'r').readlines() if line.strip() != ''])

    arxiv_visitor = ArxivVisitor(output_dir=output_root)
    notion_service = NotionService(create_time=hf_visitor.datetime)
    wolai_service = WolaiService()
    zotero_service = ZoteroService(create_time=hf_visitor.datetime,use_proxy=True)
    for hf_obj in tqdm(hf_visitor.paper_list, desc=create_dt):
        # if hf_obj['id'] in ckpt:
        #     continue
        arxiv_obj = arxiv_visitor.find_by_id(hf_obj['id'])
        notion_service.insert(hf_obj, arxiv_obj) #插入notion
        print(arxiv_obj.category)
        
        try:
            if arxiv_obj.category == 'NLP':
                zotero_service.insert(arxiv_obj,["WXBCJ969","DFGZNVCM"])  # NLP
            elif arxiv_obj.category == 'RL':
                zotero_service.insert(arxiv_obj,["DXU9QIKA","DFGZNVCM"]) # RL
            elif arxiv_obj.category == 'MARL':
                zotero_service.insert(arxiv_obj,["8DXU5DFC","DFGZNVCM"]) # MARL
            elif arxiv_obj.category == 'MTS':
                zotero_service.insert(arxiv_obj,["JSYLDU9Z","DFGZNVCM"]) # MTS
            elif arxiv_obj.category == '多模态':
                zotero_service.insert(arxiv_obj,["H2AHAFZF","DFGZNVCM"]) # 多模态
            elif arxiv_obj.category == 'CV':
                zotero_service.insert(arxiv_obj,["H8W7XVEC","DFGZNVCM"]) # CV
            else:
                zotero_service.insert(arxiv_obj,["DFGZNVCM"])
            
        except Exception as e:
            print(e)
            continue
        try:
            wolai_service.insert(arxiv_obj)
        except Exception as e:
            print(e)
            continue
        
        # resp = wolai_service.insert(arxiv_obj) #插入我来
        # logger.info(resp)
        ckpt.add(hf_obj['id'])
        ckpt_file.write(hf_obj['id'])
        ckpt_file.write('\n')

    if len(hf_visitor.paper_list) > 0:
        common_utils.send_slack(f'更新文章{len(hf_visitor.paper_list)}篇')

if __name__ == '__main__':
    # for dt in ('2024-02-23', '2024-02-24', '2024-02-25', '2024-02-26', '2024-02-27', '2024-02-28', '2024-02-29', '2024-03-01'):
    #     main(dt)
    from datetime import datetime, timedelta

# 获取最近 10 天的日期列表，格式为 YYYY-MM-DD
    # last_10_days = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(10)]

    # for dt in last_10_days:
    #     print(dt)  # 输出日期
    #     try:
    #         main(dt)  # 调用 main 函数
    #     except Exception as e:
    #         print(f"Error processing date {dt}: {e}")
    main()

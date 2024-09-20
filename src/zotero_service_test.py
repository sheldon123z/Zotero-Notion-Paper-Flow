"""_summary_
    ZoteroService class for interacting with Zotero API
    Inseart new item to Zotero library
    Author: Xiaodong Zheng
    Created: 2024-09-20
"""
import requests
import json
import os
import common_utils
from entity.formatted_arxiv_obj import FormattedArxivObj
logger = common_utils.get_logger(__name__)
class ZoteroService:
    def __init__(self, create_time, api_key=os.environ.get('ZOTERO_API_KEY'), user_id=os.environ.get('ZOTERO_USER_ID'), use_proxy=True):
        self.api_key = api_key
        self.user_id = user_id
        self.create_time = create_time
        self.use_proxy = use_proxy
        # 初始化 item_data
        self.item_data = [
            {
                "itemType": "journalArticle",
                "title": "",
                "creators": [
                    {
                        "creatorType": "author",
                        "name": ""
                    }
                ],
                "abstractNote": "",
                "websiteTitle": "",
                "websiteType": "",
                "date": "",
                "shortTitle": "",
                "url": "",
                "accessDate": "2014-06-12T21:28:55Z",
                "language": "",
                "rights": "",
                "extra": "",
                "dateAdded": "2014-06-12T21:28:55Z",
                "dateModified": "2014-06-12T21:28:55Z",
                "tags": [],
                "collections": ["WXBCJ969"],
                "relations": {}
            }
        ]

    # 更新 title 和 url 的方法
    def update_title_and_url(self, new_title, new_url):
        logger.info(f"Updating title to: {new_title} and URL to: {new_url}")
        self.item_data[0]['title'] = new_title
        self.item_data[0]['url'] = new_url

    # 更新 creators 的方法
    def update_creators(self, new_authors):
        logger.info(f"Updating creators to: {new_authors}")
        self.item_data[0]['creators'] = [{"creatorType": "author", "name": author} for author in new_authors]

    # 更新 dateAdded 和 dateModified 的方法
    # def update_dates(self, new_date_added, new_date_modified):
    #     logger.info(f"Updating dateAdded to: {new_date_added} and dateModified to: {new_date_modified}")
    #     self.item_data[0]['dateAdded'] = new_date_added
    #     self.item_data[0]['dateModified'] = new_date_modified
        

    # 更新 dateAdded 和 dateModified 的方法
    def update_dates(self, new_date_added, new_date_modified):
        logger.info(f"Updating dateAdded to: {new_date_added} and dateModified to: {new_date_modified}")
        
        def parse_date(date_str):
            try:
                # 先尝试解析带有时间和时区的格式
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                try:
                    # 如果解析失败，则尝试解析简单的 'YYYY-MM-DD' 格式
                    return datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    logger.error(f"Date format for {date_str} is not supported")
                    return None

        # 解析 new_date_added 和 new_date_modified
        if isinstance(new_date_added, str):
            new_date_added = parse_date(new_date_added)
        if isinstance(new_date_modified, str):
            new_date_modified = parse_date(new_date_modified)

        if new_date_added and new_date_modified:
            # 格式化为 'YYYY-MM-DD hh:mm:ss'
            formatted_date_added = new_date_added.strftime('%Y-%m-%d %H:%M:%S')
            formatted_date_modified = new_date_modified.strftime('%Y-%m-%d %H:%M:%S')

            # 更新 item_data
            self.item_data[0]['dateAdded'] = formatted_date_added
            self.item_data[0]['dateModified'] = formatted_date_modified
            self.item_data[0]['accessDate'] = formatted_date_modified
        else:
            logger.error("Failed to update dates due to invalid date format.")

    # 更新其他字段的方法
    # 每个方法添加 logger.info 记录更新信息
    def update_tags(self, new_tags):
        logger.info(f"Updating tags to: {new_tags}")
        self.item_data[0]['tags'] = [{"tag": tag} for tag in new_tags]

    # 更新 accessDate 的方法
    def update_access_date(self, new_access_date):
        pass

    def update_abstract(self, new_abstract):
        logger.info(f"Updating abstractNote to: {new_abstract}")
        self.item_data[0]['abstractNote'] = new_abstract

    def update_collections(self, new_collections):
        logger.info(f"Updating collections to: {new_collections}")
        self.item_data[0]['collections'] = new_collections

    def update_website_title(self, new_website_title):
        logger.info(f"Updating websiteTitle to: {new_website_title}")
        self.item_data[0]['websiteTitle'] = new_website_title

    def update_website_type(self, new_website_type):
        logger.info(f"Updating websiteType to: {new_website_type}")
        self.item_data[0]['websiteType'] = new_website_type

    def update_short_title(self, new_short_title):
        logger.info(f"Updating shortTitle to: {new_short_title}")
        self.item_data[0]['shortTitle'] = new_short_title

    def update_language(self, new_language):
        logger.info(f"Updating language to: {new_language}")
        self.item_data[0]['language'] = new_language

    def update_rights(self, new_rights):
        logger.info(f"Updating rights to: {new_rights}")
        self.item_data[0]['rights'] = new_rights

    def update_extra(self, new_extra):
        logger.info(f"Updating extra to: {new_extra}")
        self.item_data[0]['extra'] = new_extra

    def update_relations(self, new_relations):
        logger.info(f"Updating relations to: {new_relations}")
        self.item_data[0]['relations'] = new_relations

    # 打印当前 item_data 的方法
    def get_item_data(self):
        logger.info(f"Current item_data: {self.item_data}")
        return self.item_data

    def insert(self, formatted_arxiv_obj: FormattedArxivObj):
        url = f"https://api.zotero.org/users/{self.user_id}/items"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        proxies = {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        } if self.use_proxy else None

        # 使用 formatted_arxiv_obj 更新 item_data 的各个字段
        logger.info("Inserting new item into Zotero...")
        self.update_title_and_url(formatted_arxiv_obj.title, formatted_arxiv_obj.pdf_url)
        self.update_creators(formatted_arxiv_obj.authors)
        self.update_dates(self.create_time.strftime('%Y-%m-%d'), self.create_time.strftime('%Y-%m-%d'))
        self.update_tags(formatted_arxiv_obj.tags)
        self.update_access_date(formatted_arxiv_obj.published_dt)
        self.update_abstract(formatted_arxiv_obj.summary_cn)
        self.update_collections(["WXBCJ969"])
        logger.info(f"item_data prepared for submission: {self.item_data}")

        # 进行 API 请求，捕捉可能的错误
        try:
            response = requests.post(url, headers=headers, json=self.item_data, proxies=proxies)
            response.raise_for_status()
            logger.info(response.json())
            logger.info("Item successfully created in Zotero.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create item: {e}")
            return {
                "error": "Failed to create item",
                "status_code": response.status_code if response else "N/A",
                "message": str(e),
                "details": response.text if response else "No response text"
            }
        # response = requests.post(url, headers=headers, json=self.item_data, proxies=proxies)

        # if response.status_code != 200:
        #         logger.warning(f"status_code not 200, response:")
        #         logger.warning(response.json())
        # logger.debug("send response")
        # logger.debug(response.json())
            

# Your API key and user/group ID
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from service.arxiv_visitor import ArxivVisitor
from service.hf_visotor import HFDailyPaperVisitor
from tqdm import tqdm
# Your API key and user/group ID
api_key = ""
user_id = ""

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
    zotero_service = ZoteroService(create_time=hf_visitor.datetime,api_key=api_key, user_id=user_id, use_proxy=True)

    for hf_obj in tqdm(hf_visitor.paper_list, desc=create_dt):
        # if hf_obj['id'] in ckpt:
        #     continue
        arxiv_obj = arxiv_visitor.find_by_id(hf_obj['id'])
        try:
            zotero_service.insert(arxiv_obj)
        except Exception as e:
            logger.error(f"insert error: {e}")
            # print(e)
            continue
        ckpt.add(hf_obj['id'])
        ckpt_file.write(hf_obj['id'])
        ckpt_file.write('\n')

if __name__ =='__main__':

    from datetime import datetime, timedelta
    main('2024-09-15')
    # create_dt = hf_visitor.datetime.strftime('%Y-%m-%d')
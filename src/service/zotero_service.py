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
from common_utils.json_templates import *
from entity.formatted_arxiv_obj import FormattedArxivObj
from datetime import datetime
logger = common_utils.get_logger(__name__)
class ZoteroService:
    def __init__(self, create_time, item_type="preprint", api_key=os.environ.get('ZOTERO_API_KEY'), user_id=os.environ.get('ZOTERO_USER_ID'), use_proxy=True):
        self.api_key = api_key
        self.user_id = user_id
        self.create_time = create_time
        self.use_proxy = use_proxy
        self.item_data= []
        # self.item_data = [{
        #             "itemType": "preprint",
        #             "title": "",
        #             "creators": [
        #                 {
        #                     "creatorType": "author",
        #                     "firstName": "",
        #                     "lastName": ""
        #                 }
        #             ],
        #             "abstractNote": "",
        #             "genre": "",
        #             "repository": "",
        #             "archiveID": "",
        #             "place": "",
        #             "date": "",
        #             "series": "",
        #             "seriesNumber": "",
        #             "DOI": "",
        #             "citationKey": "",
        #             "url": "",
        #             "accessDate": "",
        #             "archive": "",
        #             "archiveLocation": "",
        #             "shortTitle": "",
        #             "language": "",
        #             "libraryCatalog": "",
        #             "callNumber": "",
        #             "rights": "",
        #             "extra": "",
        #             "tags": [],
        #             "collections": [],
        #             "relations": {}
        #         }]
        self.data = self.load_json_from_directory(directory="src/common_utils/json_templates/", target_filename=item_type + ".json")
        if self.data:
            self.item_data.append(self.data)
    
    def load_json_from_directory(self, directory, target_filename):
        # 获取文件夹中所有的文件列表
        files = os.listdir(directory)
        
        # 过滤出与目标文件名匹配的文件
        json_file_path = None
        for file in files:
            if file == target_filename:
                json_file_path = os.path.join(directory, file)
                break
        
        if json_file_path:
            # 打开并加载JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                return data
        else:
            print(f"文件 {target_filename} 不存在于文件夹 {directory} 中。")
            return None
    
    # 更新 title 和 url 的方法
    def update_title_and_url(self, new_title, new_url):
        logger.info(f"更新标题为: {new_title} 和URL为: {new_url}")
        self.item_data[0]['title'] = new_title
        self.item_data[0]['url'] = new_url

    # 更新 creators 的方法
    def update_creators(self, new_authors):
        logger.info(f"更新创建者为: {new_authors}")
        self.item_data[0]['creators'] = [{"creatorType": "author", "name": author} for author in new_authors]


    # 更新 dateAdded 和 dateModified 的方法
    def update_dates(self, new_date_added, new_date_modified):
        logger.info(f"更新 dateAdded 为: {new_date_added} 和 dateModified 为: {new_date_modified}")
        
        def parse_date(date_str):
            try:
                # 先尝试解析带有时间和时区的格式
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                try:
                    # 如果解析失败，则尝试解析简单的 'YYYY-MM-DD' 格式
                    return datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    logger.error(f"日期格式 for {date_str} 不支持")
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
            formatted_date = new_date_added.strftime('%Y-%m-%d')
            # 更新 item_data
            self.item_data[0]['dateAdded'] = formatted_date_added
            self.item_data[0]['date'] = formatted_date
            self.item_data[0]['dateModified'] = formatted_date_modified
            self.item_data[0]['accessDate'] = formatted_date_modified
        else:
            logger.error("无法更新日期格式导致失败。")

    # 更新其他字段的方法
    # 每个方法添加 logger.info 记录更新信息
    def update_tags(self, new_tags, arxiv_categories):
        logger.info(f"更新标签为: {new_tags}")
        self.item_data[0]['tags'] = [{"tag": tag} for tag in new_tags]
        if arxiv_categories:
            logger.info(f"将 arxiv 分类添加到标签: {arxiv_categories}")
            sharp_tags = [{"tag":f"#{category}"} for category in arxiv_categories]
            self.item_data[0]['tags'].extend(sharp_tags)
            logger.info(f"新标签为: {self.item_data[0]['tags']}")

    # 更新 accessDate 的方法
    def update_access_date(self, new_access_date):
        pass

    def update_abstract(self, new_abstract):
        if 'abstractNote' in self.item_data[0]:
            logger.info(f"正在更新摘要为: {new_abstract}")
            self.item_data[0]['abstractNote'] = new_abstract
        else:
            logger.info("键 'abstractNote' 不存在于 item_data 中，跳过更新。")

    def update_collections(self, new_collections):
        if 'collections' in self.item_data[0]:
            logger.info(f"正在更新收藏集为: {new_collections}")
            self.item_data[0]['collections'] = [collection for collection in new_collections]
        else:
            logger.info("键 'collections' 不存在于 item_data 中，跳过更新。")

    def update_website_title(self, new_website_title):
        if 'websiteTitle' in self.item_data[0]:
            logger.info(f"正在更新网站标题为: {new_website_title}")
            self.item_data[0]['websiteTitle'] = new_website_title
        else:
            logger.info("键 'websiteTitle' 不存在于 item_data 中，跳过更新。")

    def update_website_type(self, new_website_type):
        if 'websiteType' in self.item_data[0]:
            logger.info(f"正在更新网站类型为: {new_website_type}")
            self.item_data[0]['websiteType'] = new_website_type
        else:
            logger.info("键 'websiteType' 不存在于 item_data 中，跳过更新。")

    def update_short_title(self, new_short_title):
        if 'shortTitle' in self.item_data[0]:
            logger.info(f"正在更新短标题为: {new_short_title}")
            self.item_data[0]['shortTitle'] = new_short_title
        else:
            logger.info("键 'shortTitle' 不存在于 item_data 中，跳过更新。")

    def update_language(self, new_language):
        if 'language' in self.item_data[0]:
            logger.info(f"正在更新语言为: {new_language}")
            self.item_data[0]['language'] = new_language
        else:
            logger.info("键 'language' 不存在于 item_data 中，跳过更新。")

    def update_rights(self, new_rights):
        if 'rights' in self.item_data[0]:
            logger.info(f"正在更新权限为: {new_rights}")
            self.item_data[0]['rights'] = new_rights
        else:
            logger.info("键 'rights' 不存在于 item_data 中，跳过更新。")

    def update_extra(self, new_extra):
        if 'extra' in self.item_data[0]:
            logger.info(f"正在更新附加信息为: {new_extra}")
            self.item_data[0]['extra'] = new_extra
        else:
            logger.info("键 'extra' 不存在于 item_data 中，跳过更新。")

    def update_relations(self, new_relations):
        if 'relations' in self.item_data[0]:
            logger.info(f"正在更新关系为: {new_relations}")
            self.item_data[0]['relations'] = new_relations
        else:
            logger.info("键 'relations' 不存在于 item_data 中，跳过更新。")

    def update_doi(self, new_doi):
        if 'DOI' in self.item_data[0]:
            logger.info(f"正在更新 DOI 为: {new_doi}")
            if new_doi == None:
                logger.info("本篇文章没有DOI。")
                self.item_data[0]['DOI'] = ''
            else:
                self.item_data[0]['DOI'] = new_doi
        else:
            logger.info("键 'DOI' 不存在于 item_data 中，跳过更新。")

    def update_journal_reference(self, new_journal_reference):
        if 'journalAbbreviation' in self.item_data[0]:
            logger.info(f"正在更新期刊缩写为: {new_journal_reference}")
            self.item_data[0]['journalAbbreviation'] = new_journal_reference
        else:
            logger.info("键 'journalAbbreviation' 不存在于 item_data 中，跳过更新。")

    def update_tldr(self, new_tldr, tldr_keys=('动机', '方法', '结果')):
        logger.info(f"Updating tldr to: {new_tldr}")
        
        # 检查是否有任何 key 在 new_tldr 中，并且其值不为空
        if any([key in new_tldr and new_tldr[key] != '' for key in tldr_keys]):
            for key in tldr_keys:
                if key in new_tldr and new_tldr[key] != '':
                    # 将 key 和对应的值追加到 extra 中
                    if 'extra' in self.item_data[0]:
                        self.item_data[0]['extra'] += f"\n{key}: {new_tldr[key]}"
                    else:
                        # 如果 'extra' 还不存在，初始化它
                        self.item_data[0]['extra'] = f"{key}: {new_tldr[key]}"
    
    # 打印当前 item_data 的方法
    def get_item_data(self):
        logger.info(f"Current item_data: {self.item_data[0]}")
        return self.item_data[0]

    def insert(self, formatted_arxiv_obj: FormattedArxivObj,collection=["DFGZNVCM"]):
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
        logger.info("正在将新项目插入 Zotero...")
        self.update_title_and_url(formatted_arxiv_obj.title, formatted_arxiv_obj.pdf_url)
        self.update_creators(formatted_arxiv_obj.authors)
        self.update_dates(self.create_time.strftime('%Y-%m-%d'), self.create_time.strftime('%Y-%m-%d'))
        self.update_tags(formatted_arxiv_obj.tags,formatted_arxiv_obj.arxiv_categories)
        self.update_access_date(formatted_arxiv_obj.published_dt)
        self.update_abstract(formatted_arxiv_obj.summary_cn) # 更新中文摘要
        self.update_collections(collection)
        self.update_doi(formatted_arxiv_obj.doi)
        self.update_journal_reference(formatted_arxiv_obj.journal_ref)
        self.update_tldr(formatted_arxiv_obj.tldr) # 更新 tldr, 如果存在, 也可以换成其他的字段
        logger.info(f"item_data 准备提交: {self.item_data}")

        # 进行 API 请求，捕捉可能的错误
        try:
            response = requests.post(url, headers=headers, json=self.item_data, proxies=proxies)
            response.raise_for_status()
            logger.info(response.json())
            logger.info("在 Zotero 中成功创建项目.")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"创建项目失败: {e}")
            return {
                "error": "创建项目失败",
                "status_code": response.status_code if response else "N/A",
                "message": str(e),
                "details": response.text if response else "无回复文字"
            }
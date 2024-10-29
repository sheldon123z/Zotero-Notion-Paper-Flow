"""_summary_
    Wolai class for interacting with Wolai API
    Inseart new item to Zotero library
    Author: Xiaodong Zheng
    Created: 2024-09-20
"""
import json
import os

import requests

from entity.formatted_arxiv_obj import FormattedArxivObj
import common_utils

logger = common_utils.get_logger(__name__)


class WolaiService:
    def __init__(self, token=os.environ['WOLAI_TOKEN']):
        self.token = token
        self._blocks = []

    def insert(self, formatted_arxiv_obj: FormattedArxivObj, db_id=os.environ['WOLAI_DB_ID']):
        # db加入记录
        tags = [str(tag) for tag in formatted_arxiv_obj.tags]
        category = [str(formatted_arxiv_obj.category)]

        print(f"tags{tags}")
        print(f"category: {category} type: {type(category)}")
        req_body = {
            "rows": [
                {
                    "标题": str(formatted_arxiv_obj.title),
                    "类型": ["论文"],
                    "领域": category,
                    "文章标签": tags ,
                    "阅读标签": False,
                    "AI总结": str(formatted_arxiv_obj.short_summary),
                    "首次发表时间": formatted_arxiv_obj.published_dt,
                    "作者": ", ".join(formatted_arxiv_obj.authors),
                    "PDF链接": formatted_arxiv_obj.pdf_url
                }
            ]
        }
        print(f"req_body:{req_body}")
        headers = {'Authorization': self.token}
        url = f"https://openapi.wolai.com/v1/databases/{db_id}/rows"
        logger.debug("create database row request:")
        logger.debug(json.dumps(req_body, ensure_ascii=False, indent=2))

        resp = requests.post(url, headers=headers, json=req_body)
        resp_json = resp.json()
        print(f'resp_json: {resp_json}')
        if resp.status_code != 200:
            logger.warning(f"create database row failed, resp status code: {resp.status_code}, resp: {resp_json}")

        if formatted_arxiv_obj.media_type != '':
            self._add_media(formatted_arxiv_obj.media_type, formatted_arxiv_obj.media_url)

        self._add_text("关键词: " + ', '.join(formatted_arxiv_obj.tags))
        self._add_h1('TL;DR')
        tldr_keys = ('动机', '方法', '结果')
        if any([key in formatted_arxiv_obj.tldr and formatted_arxiv_obj.tldr[key] != '' for key in tldr_keys]):
            for key in tldr_keys:
                if key in formatted_arxiv_obj.tldr and formatted_arxiv_obj.tldr[key] != '':
                    self._add_h2(key)._add_text(formatted_arxiv_obj.tldr[key])
        else:
            self._add_text(formatted_arxiv_obj.raw_tldr)
            logger.warning(f'insert raw tldr! full obj:')
            logger.warning(formatted_arxiv_obj)
        (
            self._add_h1('摘要')
            ._add_h2('原文')
            ._add_quote(formatted_arxiv_obj.summary)
            ._add_h2('中文译文')
            ._add_quote(formatted_arxiv_obj.summary_cn)
        )
        block_id = resp_json['data'][0].split('/')[-1]
        req_body = {
            "parent_id": block_id,
            "blocks": self._blocks
        }
        logger.debug("create block request:")
        logger.debug(json.dumps(req_body, ensure_ascii=False, indent=2))

        url = ' https://openapi.wolai.com/v1/blocks'
        resp = requests.post(url, headers=headers, json=req_body)
        resp_json = resp.json()
        if resp.status_code not in (200, 201):
            logger.warning(f"create block failed, resp status code: {resp.status_code}, resp: {resp_json}")
        self._blocks.clear()
        return resp_json

    def __add_header(self, level, text):
        self._blocks.append({
            "type": "heading",
            "level": level,
            "content": {
                "title": text,
                # "front_color": "red"
            },
            "text_alignment": "left"
        })
        return self

    def _add_text(self, text):
        self._blocks.append({
            "type": "text",
            "content": text,
            "text_alignment": "left"
        })
        return self

    def _add_h1(self, text):
        return self.__add_header(1, text)

    def _add_h2(self, text):
        return self.__add_header(2, text)

    def _add_h3(self, text):
        return self.__add_header(3, text)

    def _add_media(self, media_type, url):
        self._blocks.append({
            "type": media_type,
            "link": url,
        })
        return self

    def _add_quote(self, text):
        self._blocks.append({
            "type": "quote",
            "content": text,
            "text_alignment": "left"
        })
        return self

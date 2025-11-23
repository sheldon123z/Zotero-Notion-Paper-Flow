import os
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseStorage
from models.paper import Paper

logger = logging.getLogger(__name__)

class NotionStorage(BaseStorage):
    """Notion存储服务"""

    API_URL = "https://api.notion.com/v1/pages"
    API_VERSION = "2022-06-28"

    def __init__(
        self,
        db_id: str = None,
        secret: str = None,
        create_time: datetime = None,
        **kwargs
    ):
        super().__init__(create_time=create_time, **kwargs)
        self.db_id = db_id or os.environ.get('NOTION_DB_ID')
        self.secret = secret or os.environ.get('NOTION_SECRET')

        # 请求构建器
        self._req_body: Dict = {}
        self._properties: Dict = {}
        self._blocks: List = []

    def get_storage_name(self) -> str:
        return "notion"

    def is_available(self) -> bool:
        """检查Notion服务是否可用"""
        return bool(self.db_id and self.secret)

    def exists(self, paper_id: str) -> bool:
        """Notion暂不支持检查，返回False"""
        return False

    def update(self, paper_id: str, data: Dict) -> Dict:
        """Notion暂不支持更新"""
        raise NotImplementedError("Notion存储暂不支持更新操作")

    def insert(self, paper: Paper, **kwargs) -> Dict:
        """插入论文到Notion"""
        self._reset_builder()

        hf_obj = kwargs.get('hf_obj')

        # 设置数据库ID
        self._req_body['parent'] = {'database_id': self.db_id}

        # 添加属性
        self._add_property_title('标题', paper.title)
        self._add_property_date('日期', self.create_time.strftime('%Y-%m-%d'))
        self._add_property_rich_text('首次发表日期', paper.published_date.strftime('%Y-%m') if paper.published_date else '')
        self._add_property_rich_text('作者', ', '.join(paper.authors))
        self._add_property_rich_text('AI总结', paper.short_summary)
        self._add_property_select('领域', paper.category)
        self._add_property_url('PDF链接', paper.pdf_url)
        self._add_property_multi_select('标签', paper.tags)

        # 添加媒体块
        if hf_obj and hf_obj.get('media_type') and hf_obj.get('media_url'):
            self._add_media_block(hf_obj['media_type'], hf_obj['media_url'])

        # 添加内容块
        self._add_heading('TL;DR', level=1)

        tldr_keys = ('动机', '方法', '结果')
        if any(paper.tldr.get(key) for key in tldr_keys):
            for key in tldr_keys:
                if paper.tldr.get(key):
                    self._add_heading(key, level=2)
                    self._add_paragraph(paper.tldr[key])

        self._add_heading('摘要', level=1)
        self._add_heading('原文', level=2)
        self._add_paragraph(paper.summary)
        self._add_heading('中文译文', level=2)
        self._add_paragraph(paper.summary_cn)

        return self._send()

    def _reset_builder(self):
        """重置请求构建器"""
        self._req_body = {}
        self._properties = {}
        self._blocks = []

    def _add_property_title(self, column: str, content: str):
        self._properties[column] = {
            "title": [{"text": {"content": content}}]
        }

    def _add_property_rich_text(self, column: str, content: str):
        self._properties[column] = {
            "rich_text": [{"text": {"content": content}}]
        }

    def _add_property_date(self, column: str, content: str):
        self._properties[column] = {"date": {"start": content}}

    def _add_property_select(self, column: str, content: str):
        self._properties[column] = {"select": {"name": content}}

    def _add_property_multi_select(self, column: str, items: list):
        self._properties[column] = {
            "multi_select": [{"name": tag} for tag in items]
        }

    def _add_property_url(self, column: str, content: str):
        self._properties[column] = {"url": content}

    def _add_heading(self, content: str, level: int = 1):
        block_type = f"heading_{level}"
        self._blocks.append({
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        })

    def _add_paragraph(self, content: str):
        self._blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        })

    def _add_media_block(self, media_type: str, url: str):
        self._blocks.append({
            "object": "block",
            "type": media_type,
            media_type: {
                "type": "external",
                "external": {"url": url}
            }
        })

    def _send(self) -> Dict:
        """发送请求到Notion API"""
        headers = {
            'Authorization': f'Bearer {self.secret}',
            'Notion-Version': self.API_VERSION,
            'Content-Type': 'application/json'
        }

        self._req_body['properties'] = self._properties
        self._req_body['children'] = self._blocks

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=self._req_body,
            proxies=self.proxies
        )

        if response.status_code != 200:
            logger.warning(f"Notion API错误: {response.json()}")

        return response.json()

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .base import BaseStorage
from models.paper import Paper

logger = logging.getLogger(__name__)

class ZoteroItemExistsError(Exception):
    """论文已存在异常"""
    pass

class ZoteroStorage(BaseStorage):
    """Zotero存储服务"""

    API_BASE_URL = "https://api.zotero.org"

    def __init__(
        self,
        api_key: str = None,
        user_id: str = None,
        group_id: str = None,
        item_type: str = "preprint",
        library_type: str = "user",
        create_time: datetime = None,
        templates_dir: str = "src/common_utils/json_templates",
        **kwargs
    ):
        super().__init__(create_time=create_time, **kwargs)
        self.api_key = api_key or os.environ.get('ZOTERO_API_KEY')
        self.user_id = user_id or os.environ.get('ZOTERO_USER_ID')
        self.group_id = group_id or os.environ.get('ZOTERO_GROUP_ID')
        self.item_type = item_type
        self.library_type = library_type
        self.templates_dir = Path(templates_dir)

        # 加载模板
        self._item_template = self._load_template(item_type)

    def get_storage_name(self) -> str:
        return "zotero"

    def is_available(self) -> bool:
        """检查Zotero服务是否可用"""
        return bool(self.api_key and (self.user_id or self.group_id))

    def _get_api_url(self) -> str:
        """获取API URL"""
        if self.library_type == "group":
            return f"{self.API_BASE_URL}/groups/{self.group_id}/items"
        return f"{self.API_BASE_URL}/users/{self.user_id}/items"

    def _load_template(self, item_type: str) -> Dict:
        """加载Zotero项目模板"""
        template_path = self.templates_dir / f"{item_type}.json"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        logger.warning(f"模板文件不存在: {template_path}")
        return {}

    def exists(self, paper_id: str, doi: str = None, title: str = None) -> bool:
        """检查论文是否存在"""
        result = self._search_item(arxiv_id=paper_id, doi=doi, title=title)
        return result.get("exists", False)

    def _search_item(
        self,
        arxiv_id: str = None,
        doi: str = None,
        title: str = None
    ) -> Dict:
        """搜索Zotero中的项目"""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # 确定查询参数
        if doi:
            params = {'q': doi, 'qmode': 'everything', 'format': 'json'}
        elif arxiv_id:
            params = {'q': arxiv_id, 'qmode': 'everything', 'format': 'json'}
        elif title:
            params = {'q': title, 'qmode': 'title', 'format': 'json'}
        else:
            return {"exists": False, "count": 0, "items": []}

        try:
            response = requests.get(
                self._get_api_url(),
                headers=headers,
                params=params,
                proxies=self.proxies
            )
            response.raise_for_status()
            items = response.json()

            return {
                "exists": len(items) > 0,
                "count": len(items),
                "items": items
            }
        except Exception as e:
            logger.error(f"搜索Zotero项目失败: {e}")
            return {"exists": False, "count": 0, "items": []}

    def update(self, paper_id: str, data: Dict) -> Dict:
        """更新Zotero项目"""
        raise NotImplementedError("Zotero更新功能尚未实现")

    def insert(self, paper: Paper, collections: List[str] = None, **kwargs) -> Dict:
        """插入论文到Zotero"""
        collections = collections or kwargs.get('collection', ["DFGZNVCM"])

        # 检查是否存在
        if self.exists(paper.id, paper.doi, paper.title):
            raise ZoteroItemExistsError(f"论文已存在: {paper.title}")

        # 构建项目数据
        item_data = self._build_item_data(paper, collections)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self._get_api_url(),
                headers=headers,
                json=[item_data],
                proxies=self.proxies
            )
            response.raise_for_status()
            logger.info(f"成功插入到Zotero: {paper.title}")
            return response.json()
        except Exception as e:
            logger.error(f"插入Zotero失败: {e}")
            raise

    def _build_item_data(self, paper: Paper, collections: List[str]) -> Dict:
        """构建Zotero项目数据"""
        item_data = self._item_template.copy()

        # 基本信息
        item_data['title'] = paper.title
        item_data['url'] = paper.pdf_url
        item_data['archiveID'] = paper.id

        # 作者
        item_data['creators'] = [
            {"creatorType": "author", "name": author}
            for author in paper.authors
        ]

        # 日期
        date_str = self.create_time.strftime('%Y-%m-%d')
        item_data['date'] = date_str
        item_data['dateAdded'] = f"{date_str} 00:00:00"
        item_data['dateModified'] = f"{date_str} 00:00:00"

        # 标签（包含ArXiv分类）
        tags = [{"tag": tag} for tag in paper.tags]
        if paper.arxiv_categories:
            tags.extend([{"tag": f"#{cat}"} for cat in paper.arxiv_categories])
        item_data['tags'] = tags

        # 摘要（使用中文摘要）
        if 'abstractNote' in item_data:
            item_data['abstractNote'] = paper.summary_cn or paper.summary

        # 集合
        item_data['collections'] = collections

        # DOI
        if 'DOI' in item_data:
            item_data['DOI'] = paper.doi or ''

        # TLDR放入extra字段
        if paper.tldr and 'extra' in item_data:
            tldr_content = "\n".join([
                f"{key}: {value}"
                for key, value in paper.tldr.items()
                if value
            ])
            item_data['extra'] = tldr_content

        return item_data

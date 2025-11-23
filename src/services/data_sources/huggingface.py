import os
import time
import json
import logging
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

from .base import BaseDataSource
from models.paper import Paper

logger = logging.getLogger(__name__)

class HuggingFaceDataSource(BaseDataSource):
    """HuggingFace Daily Papers数据源"""

    BASE_URL = "https://huggingface.co/papers"

    def __init__(
        self,
        output_dir: str = "./output",
        proxy: str = None,
        **kwargs
    ):
        super().__init__(output_dir=output_dir, **kwargs)
        self.proxy = proxy or os.environ.get('HTTP_PROXY', 'http://127.0.0.1:7890')
        self._paper_list: List[Dict] = []
        self._datetime: Optional[datetime] = None

    def get_source_name(self) -> str:
        return "huggingface"

    @property
    def paper_list(self) -> List[Dict]:
        """获取论文列表"""
        return self._paper_list

    @property
    def fetch_datetime(self) -> Optional[datetime]:
        """获取抓取时间"""
        return self._datetime

    def fetch_papers(self, date: str = None, **kwargs) -> List[Paper]:
        """获取指定日期的论文列表"""
        url = self.BASE_URL
        if date:
            url = f"{url}?date={date}"

        self._fetch_page(url)

        # 返回Paper对象列表（基础信息，需要通过ArXiv获取详细信息）
        return [
            Paper(
                id=p['id'],
                title=p['title'],
                media_type=p.get('media_type', ''),
                media_url=p.get('media_url', '')
            )
            for p in self._paper_list
        ]

    def search(self, keywords: List[str], **kwargs) -> List[Paper]:
        """HuggingFace不支持搜索，返回空列表"""
        logger.warning("HuggingFace数据源不支持关键词搜索")
        return []

    def get_by_id(self, paper_id: str) -> Optional[Paper]:
        """通过ID获取论文（从已抓取的列表中）"""
        for p in self._paper_list:
            if p['id'] == paper_id:
                return Paper(
                    id=p['id'],
                    title=p['title'],
                    media_type=p.get('media_type', ''),
                    media_url=p.get('media_url', '')
                )
        return None

    def _fetch_page(self, url: str):
        """抓取HuggingFace页面"""
        proxies = {
            'http': self.proxy,
            'https': self.proxy,
        } if self.proxy else None

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        for attempt in range(self.max_retries):
            try:
                logger.info(f"获取HuggingFace页面: {url} (尝试 {attempt + 1}/{self.max_retries})")

                response = requests.get(url, headers=headers, proxies=proxies, timeout=30)

                if response.status_code != 200:
                    logger.warning(f"HTTP状态码: {response.status_code}")
                    continue

                self._parse_page(response.text)
                break

            except Exception as e:
                logger.warning(f"请求失败: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_wait * (attempt + 1))

        # 保存结果
        if self._datetime:
            save_path = self.output_dir / f"hf_{self._datetime.strftime('%Y-%m-%d')}.json"
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._paper_list, f, ensure_ascii=False, indent=2)

    def _parse_page(self, html: str):
        """解析页面HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # 解析日期
        time_tag = soup.select_one('time')
        if time_tag and 'datetime' in time_tag.attrs:
            self._datetime = datetime.strptime(
                time_tag.attrs['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ'
            )
        else:
            self._datetime = datetime.now()

        # 解析论文列表
        self._paper_list = []
        selectors = [
            'section.container > div > div > article',
            'article',
            'a[href^="/papers/"]'
        ]

        paper_nodes = []
        for selector in selectors:
            paper_nodes = soup.select(selector)
            if paper_nodes:
                break

        for node in paper_nodes:
            try:
                paper_info = self._parse_paper_node(node)
                if paper_info:
                    self._paper_list.append(paper_info)
            except Exception as e:
                logger.warning(f"解析论文节点失败: {e}")

        logger.info(f"找到 {len(self._paper_list)} 篇论文")

    def _parse_paper_node(self, node) -> Optional[Dict]:
        """解析单个论文节点"""
        # 查找标题链接
        title_selectors = ['h3 > a', 'a[href^="/papers/"]', '.title a']

        a_node = None
        for selector in title_selectors:
            found = node.select(selector)
            if found:
                a_node = found[0]
                break

        if not a_node:
            return None

        # 提取链接和ID
        href = a_node.attrs.get('href', '')
        if not href.startswith('http'):
            href = f"https://huggingface.co{href}" if href.startswith('/') else f"https://huggingface.co/{href}"

        paper_id = href.split('/')[-1]

        # 查找媒体
        media_type = None
        media_url = ""

        img_node = node.select('img')
        video_node = node.select('video')

        if img_node:
            media_type = 'image'
            media_url = img_node[0].attrs.get('src', '')
        elif video_node:
            media_type = 'video'
            media_url = video_node[0].attrs.get('src', '')

        return {
            'id': paper_id,
            'title': a_node.text.strip(),
            'link': href,
            'media_type': media_type or 'none',
            'media_url': media_url
        }

"""
Zotero-Notion-Paper-Flow

一个用于从HuggingFace和ArXiv抓取学术论文，
使用LLM分析后同步到Notion和Zotero的工具。
"""

__version__ = "2.0.0"
__author__ = "Xiaodong Zheng"

# 导出主要模块
from .config.settings import Settings
from .container import ServiceContainer
from .core.processor import PaperProcessor
from .models.paper import Paper

__all__ = [
    'Settings',
    'ServiceContainer',
    'PaperProcessor',
    'Paper',
]

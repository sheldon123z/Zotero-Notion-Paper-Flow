"""
 Created by luogang on 2024/2/29
"""
from dataclasses import dataclass

import arxiv


# @dataclass
# class FormattedArxivObj:
#     id: str
#     title: str
#     authors: list
#     published_dt: str
#     summary: str
#     summary_cn: str
#     short_summary: str
#     pdf_url: str
#     tldr: dict
#     raw_tldr: str
#     category: str
#     tags: list
#     arxiv_result: arxiv.Result
#     media_type: str
#     media_url: str
#     journal_ref: str
#     doi: str
#     arxiv_categories: list

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import arxiv

@dataclass
class FormattedArxivObj:
    id: Optional[str] = None  # 默认为 None
    title: Optional[str] = ""  # 默认为空字符串
    authors: List[str] = field(default_factory=list)  # 默认为空列表
    published_dt: Optional[str] = ""
    summary: Optional[str] = ""
    summary_cn: Optional[str] = ""
    short_summary: Optional[str] = ""
    pdf_url: Optional[str] = ""
    tldr: Dict[str, str] = field(default_factory=dict)  # 默认为空字典
    raw_tldr: Optional[str] = ""
    category: Optional[str] = ""
    tags: List[str] = field(default_factory=list)  # 默认为空列表
    arxiv_result: Optional[arxiv.Result] = None
    media_type: Optional[str] = ""
    media_url: Optional[str] = ""
    journal_ref: Optional[str] = ""
    doi: Optional[str] = ""
    arxiv_categories: List[str] = field(default_factory=list)  # 默认为空列表






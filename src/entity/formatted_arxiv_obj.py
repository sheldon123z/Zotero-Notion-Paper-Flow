"""
 Created by luogang on 2024/2/29
"""
from dataclasses import dataclass

import arxiv


@dataclass
class FormattedArxivObj:
    id: str
    title: str
    authors: list
    published_dt: str
    summary: str
    summary_cn: str
    short_summary: str
    pdf_url: str
    tldr: dict
    raw_tldr: str
    category: str
    tags: list
    arxiv_result: arxiv.Result
    media_type: str
    media_url: str
    journal_ref: str
    doi: str
    arxiv_categories: list


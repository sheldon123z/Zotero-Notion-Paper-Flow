"""_summary_
    Feishu (Lark) class for interacting with Feishu API
    Insert new item to Feishu Bitable (multi-dimensional table)
    Author: GitHub Copilot
    Created: 2026-01-24
"""
import os
import requests

from entity.formatted_arxiv_obj import FormattedArxivObj
import common_utils

logger = common_utils.get_logger(__name__)


class FeishuService:
    def __init__(self, app_id=None, app_secret=None):
        """
        Initialize Feishu service
        
        Args:
            app_id: Feishu app ID, defaults to FEISHU_APP_ID env var
            app_secret: Feishu app secret, defaults to FEISHU_APP_SECRET env var
        """
        self.app_id = app_id or os.environ.get('FEISHU_APP_ID')
        self.app_secret = app_secret or os.environ.get('FEISHU_APP_SECRET')
        self._access_token = None
        
        if not self.app_id or not self.app_secret:
            logger.warning("Feishu app_id or app_secret not provided")
    
    def _get_tenant_access_token(self):
        """
        Get tenant access token for API authentication
        Reference: https://open.feishu.cn/document/server-docs/authentication-management/access-token-creation-method/tenant_access_token
        """
        if self._access_token:
            return self._access_token
            
        url = "https://open.feishu.cn/open-api/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                self._access_token = result.get("tenant_access_token")
                logger.debug("Successfully obtained Feishu access token")
                return self._access_token
            else:
                logger.error(f"Failed to get Feishu access token: {result}")
                return None
        except Exception as e:
            logger.error(f"Error getting Feishu access token: {e}")
            return None
    
    def insert(self, formatted_arxiv_obj: FormattedArxivObj, app_token=None, table_id=None):
        """
        Insert paper information into Feishu Bitable
        
        Args:
            formatted_arxiv_obj: Formatted paper object
            app_token: Feishu bitable app token, defaults to FEISHU_APP_TOKEN env var
            table_id: Feishu table ID, defaults to FEISHU_TABLE_ID env var
        
        Reference: https://open.feishu.cn/document/server-docs/bitable-v1/app-table-record/create
        """
        app_token = app_token or os.environ.get('FEISHU_APP_TOKEN')
        table_id = table_id or os.environ.get('FEISHU_TABLE_ID')
        
        if not app_token or not table_id:
            logger.error("Feishu app_token or table_id not provided")
            return None
        
        access_token = self._get_tenant_access_token()
        if not access_token:
            logger.error("Cannot insert to Feishu without access token")
            return None
        
        # Prepare the record fields
        # Note: Field names should match your Feishu table column names
        fields = {
            "标题": formatted_arxiv_obj.title,
            "作者": ", ".join(formatted_arxiv_obj.authors),
            "发表日期": formatted_arxiv_obj.published_dt,
            "领域": formatted_arxiv_obj.category,
            "PDF链接": formatted_arxiv_obj.pdf_url,
            "AI总结": formatted_arxiv_obj.short_summary,
            "标签": formatted_arxiv_obj.tags,
        }
        
        # Build TL;DR content
        tldr_content = ""
        tldr_keys = ('动机', '方法', '结果')
        if any([key in formatted_arxiv_obj.tldr and formatted_arxiv_obj.tldr[key] != '' for key in tldr_keys]):
            for key in tldr_keys:
                if key in formatted_arxiv_obj.tldr and formatted_arxiv_obj.tldr[key] != '':
                    tldr_content += f"{key}: {formatted_arxiv_obj.tldr[key]}\n"
        else:
            tldr_content = formatted_arxiv_obj.raw_tldr
        
        fields["TLDR"] = tldr_content.strip()
        
        # Build abstract content (original + Chinese translation)
        abstract_content = f"原文:\n{formatted_arxiv_obj.summary}\n\n中文译文:\n{formatted_arxiv_obj.summary_cn}"
        fields["摘要"] = abstract_content
        
        # Create API request
        url = f"https://open.feishu.cn/open-api/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        body = {
            "fields": fields
        }
        
        logger.debug(f"Creating Feishu record for paper: {formatted_arxiv_obj.title}")
        
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"Successfully inserted paper to Feishu: {formatted_arxiv_obj.id}")
                return result
            else:
                logger.warning(f"Failed to insert to Feishu: {result}")
                return None
        except Exception as e:
            logger.error(f"Error inserting to Feishu: {e}")
            return None

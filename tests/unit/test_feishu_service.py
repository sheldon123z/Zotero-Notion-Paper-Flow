"""Feishu服务单元测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


class TestFeishuService:
    """飞书服务测试"""

    def test_init_with_env_vars(self):
        """测试使用环境变量初始化"""
        with patch.dict('os.environ', {
            'FEISHU_APP_ID': 'test_app_id',
            'FEISHU_APP_SECRET': 'test_app_secret'
        }):
            from service.feishu_service import FeishuService
            
            service = FeishuService()
            assert service.app_id == 'test_app_id'
            assert service.app_secret == 'test_app_secret'

    def test_init_with_params(self):
        """测试使用参数初始化"""
        from service.feishu_service import FeishuService
        
        service = FeishuService(app_id='param_app_id', app_secret='param_secret')
        assert service.app_id == 'param_app_id'
        assert service.app_secret == 'param_secret'

    @patch('service.feishu_service.requests.post')
    def test_get_tenant_access_token_success(self, mock_post):
        """测试成功获取访问令牌"""
        from service.feishu_service import FeishuService
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'code': 0,
            'tenant_access_token': 'test_token'
        }
        mock_post.return_value = mock_response
        
        service = FeishuService(app_id='test_id', app_secret='test_secret')
        token = service._get_tenant_access_token()
        
        assert token == 'test_token'
        assert service._access_token == 'test_token'
        mock_post.assert_called_once()

    @patch('service.feishu_service.requests.post')
    def test_get_tenant_access_token_failure(self, mock_post):
        """测试获取访问令牌失败"""
        from service.feishu_service import FeishuService
        
        # Mock failed response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'code': -1,
            'msg': 'authentication failed'
        }
        mock_post.return_value = mock_response
        
        service = FeishuService(app_id='test_id', app_secret='test_secret')
        token = service._get_tenant_access_token()
        
        assert token is None

    @patch('service.feishu_service.requests.post')
    def test_insert_paper_success(self, mock_post):
        """测试成功插入论文"""
        from service.feishu_service import FeishuService
        from entity.formatted_arxiv_obj import FormattedArxivObj
        
        # Mock access token request
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {
            'code': 0,
            'tenant_access_token': 'test_token'
        }
        
        # Mock insert record request
        mock_insert_response = MagicMock()
        mock_insert_response.json.return_value = {
            'code': 0,
            'data': {
                'record_id': 'test_record_id'
            }
        }
        
        mock_post.side_effect = [mock_token_response, mock_insert_response]
        
        # Create test paper object
        paper = FormattedArxivObj()
        paper.id = 'test_id'
        paper.title = 'Test Paper'
        paper.authors = ['Author 1', 'Author 2']
        paper.published_dt = '2026-01-24'
        paper.category = 'cs.LG'
        paper.pdf_url = 'https://arxiv.org/pdf/test.pdf'
        paper.short_summary = 'Test summary'
        paper.tags = ['ML', 'AI']
        paper.tldr = {'动机': 'test motivation', '方法': 'test method', '结果': 'test result'}
        paper.raw_tldr = 'raw tldr'
        paper.summary = 'Original abstract'
        paper.summary_cn = 'Chinese abstract'
        
        service = FeishuService(app_id='test_id', app_secret='test_secret')
        
        with patch.dict('os.environ', {
            'FEISHU_APP_TOKEN': 'test_app_token',
            'FEISHU_TABLE_ID': 'test_table_id'
        }):
            result = service.insert(paper)
        
        assert result is not None
        assert result['code'] == 0
        assert mock_post.call_count == 2

    @patch('service.feishu_service.requests.post')
    def test_insert_paper_no_credentials(self, mock_post):
        """测试缺少凭证时插入论文"""
        from service.feishu_service import FeishuService
        from entity.formatted_arxiv_obj import FormattedArxivObj
        
        paper = FormattedArxivObj()
        paper.id = 'test_id'
        paper.title = 'Test Paper'
        
        service = FeishuService(app_id='test_id', app_secret='test_secret')
        
        # No FEISHU_APP_TOKEN or FEISHU_TABLE_ID in environment
        result = service.insert(paper)
        
        assert result is None
        mock_post.assert_not_called()

    @patch('service.feishu_service.requests.post')
    def test_insert_paper_with_raw_tldr(self, mock_post):
        """测试使用原始TLDR插入论文"""
        from service.feishu_service import FeishuService
        from entity.formatted_arxiv_obj import FormattedArxivObj
        
        # Mock responses
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {
            'code': 0,
            'tenant_access_token': 'test_token'
        }
        
        mock_insert_response = MagicMock()
        mock_insert_response.json.return_value = {
            'code': 0,
            'data': {'record_id': 'test_record_id'}
        }
        
        mock_post.side_effect = [mock_token_response, mock_insert_response]
        
        # Create paper with raw TLDR only
        paper = FormattedArxivObj()
        paper.id = 'test_id'
        paper.title = 'Test Paper'
        paper.authors = ['Author 1']
        paper.published_dt = '2026-01-24'
        paper.category = 'cs.AI'
        paper.pdf_url = 'https://arxiv.org/pdf/test.pdf'
        paper.short_summary = 'Test summary'
        paper.tags = ['AI']
        paper.tldr = {}  # Empty structured TLDR
        paper.raw_tldr = 'This is the raw TLDR content'
        paper.summary = 'Original abstract'
        paper.summary_cn = 'Chinese abstract'
        
        service = FeishuService(app_id='test_id', app_secret='test_secret')
        
        with patch.dict('os.environ', {
            'FEISHU_APP_TOKEN': 'test_app_token',
            'FEISHU_TABLE_ID': 'test_table_id'
        }):
            result = service.insert(paper)
        
        assert result is not None
        # Verify raw_tldr was used
        call_args = mock_post.call_args_list[1]
        assert 'This is the raw TLDR content' in str(call_args)

"""LLM服务单元测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock

class TestLLMServiceFactory:
    """LLM服务工厂测试"""

    def test_create_deepseek_service(self):
        """测试创建DeepSeek服务"""
        from services.llm.factory import LLMServiceFactory
        from services.llm.deepseek import DeepSeekService

        with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test_key'}):
            service = LLMServiceFactory.create('deepseek')
            assert isinstance(service, DeepSeekService)
            assert service.get_service_name() == 'deepseek'

    def test_create_unknown_service(self):
        """测试创建未知服务抛出异常"""
        from services.llm.factory import LLMServiceFactory

        with pytest.raises(ValueError):
            LLMServiceFactory.create('unknown_service')

    def test_get_available_services(self):
        """测试获取可用服务列表"""
        from services.llm.factory import LLMServiceFactory

        services = LLMServiceFactory.get_available_services()
        assert 'deepseek' in services
        assert 'kimi' in services
        assert 'zhipu' in services


class TestBaseLLMService:
    """基础LLM服务测试"""

    def test_generate_summary_format(self, mock_llm_response):
        """测试生成摘要的格式"""
        from services.llm.deepseek import DeepSeekService

        with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test_key'}):
            service = DeepSeekService()

            # Mock chat方法
            service.chat = Mock(return_value=mock_llm_response)

            result = service.generate_summary("Test summary text")

            assert "动机" in result
            assert "方法" in result
            assert "结果" in result

    def test_generate_tags_format(self):
        """测试生成标签的格式"""
        from services.llm.deepseek import DeepSeekService

        mock_response = {
            "主要领域": "RL",
            "标签": ["test", "/unread"]
        }

        with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'test_key'}):
            service = DeepSeekService()
            service.chat = Mock(return_value=mock_response)

            result = service.generate_tags("Test summary text")

            assert "主要领域" in result
            assert "标签" in result
            assert "/unread" in result["标签"]

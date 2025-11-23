"""处理器集成测试"""
import pytest
from unittest.mock import Mock, MagicMock

class TestPaperProcessor:
    """论文处理器集成测试"""

    def test_process_papers_with_mock_services(self, mock_settings, sample_paper):
        """测试使用模拟服务处理论文"""
        from core.processor import PaperProcessor

        # 创建模拟数据源
        mock_data_source = Mock()
        mock_data_source.search.return_value = [sample_paper]

        # 创建模拟存储服务
        mock_storage = Mock()
        mock_storage.insert.return_value = {"status": "success"}
        mock_storage.exists.return_value = False

        # 创建模拟LLM服务
        mock_llm = Mock()
        mock_llm.generate_summary.return_value = {"动机": "test"}
        mock_llm.generate_tags.return_value = {"主要领域": "RL", "标签": []}

        processor = PaperProcessor(
            data_sources={"arxiv": mock_data_source},
            storages={"notion": mock_storage},
            llm_service=mock_llm
        )

        # 验证处理器可以正常初始化
        assert processor.data_sources is not None
        assert processor.storages is not None

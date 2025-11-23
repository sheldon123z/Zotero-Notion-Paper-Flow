"""pytest配置和通用fixtures"""
import pytest
import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def mock_settings():
    """模拟配置"""
    from config.settings import Settings, ServiceConfig, LLMConfig
    return Settings(
        keywords=["test"],
        categories=["cs.AI"],
        services=ServiceConfig(notion=False, zotero=False, wolai=False),
        llm=LLMConfig(service="deepseek"),
        download_pdf=False
    )

@pytest.fixture
def sample_paper():
    """示例论文数据"""
    from models.paper import Paper
    return Paper(
        id="2401.00001",
        title="Test Paper Title",
        authors=["Author One", "Author Two"],
        summary="This is a test paper summary.",
        category="RL",
        tags=["test", "/unread"]
    )

@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    return {
        "动机": "测试动机",
        "方法": "测试方法",
        "结果": "测试结果",
        "翻译": "这是一个测试摘要",
        "short_summary": "测试简介",
        "remark": "RL/Test"
    }

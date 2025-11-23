"""配置管理单元测试"""
import pytest
import json
import tempfile
from pathlib import Path

class TestSettings:
    """Settings配置类测试"""

    def test_default_settings(self):
        """测试默认配置"""
        from config.settings import Settings

        settings = Settings()
        assert settings.search_limit == 20
        assert settings.retries == 3
        assert settings.download_pdf == True

    def test_settings_from_file(self):
        """测试从文件加载配置"""
        from config.settings import Settings

        config_data = {
            "keywords": ["test_keyword"],
            "search_limit": 50
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name

        try:
            settings = Settings.from_file(temp_path)
            assert settings.keywords == ["test_keyword"]
            assert settings.search_limit == 50
        finally:
            Path(temp_path).unlink()


class TestServiceConfig:
    """服务配置测试"""

    def test_default_service_config(self):
        """测试默认服务配置"""
        from config.settings import ServiceConfig

        config = ServiceConfig()
        assert config.notion == True
        assert config.zotero == True
        assert config.wolai == False

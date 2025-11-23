import os
import json
import logging
from abc import abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

from interfaces.data_source import DataSourceInterface
from models.paper import Paper

logger = logging.getLogger(__name__)

class BaseDataSource(DataSourceInterface):
    """数据源基类"""

    def __init__(
        self,
        output_dir: str = "./output",
        cache_enabled: bool = True,
        max_retries: int = 3,
        retry_wait: int = 2
    ):
        self.output_dir = Path(output_dir)
        self.cache_dir = self.output_dir / "cache"
        self.cache_enabled = cache_enabled
        self.max_retries = max_retries
        self.retry_wait = retry_wait

        # 确保目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"

    def _load_cache(self, cache_key: str) -> Optional[Dict]:
        """加载缓存"""
        if not self.cache_enabled:
            return None

        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}")
        return None

    def _save_cache(self, cache_key: str, data: Dict):
        """保存缓存"""
        if not self.cache_enabled:
            return

        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    @abstractmethod
    def get_source_name(self) -> str:
        """获取数据源名称"""
        pass

    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """获取数据源元数据"""
        return {
            "name": self.get_source_name(),
            "cache_enabled": self.cache_enabled,
            "output_dir": str(self.output_dir)
        }

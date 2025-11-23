from typing import Dict, Type, List
from .base import BaseDataSource
from .arxiv import ArxivDataSource
from .huggingface import HuggingFaceDataSource

class DataSourceFactory:
    """数据源工厂"""

    _sources: Dict[str, Type[BaseDataSource]] = {
        'arxiv': ArxivDataSource,
        'huggingface': HuggingFaceDataSource,
        'hf': HuggingFaceDataSource,  # 别名
    }

    @classmethod
    def register(cls, name: str, source_class: Type[BaseDataSource]):
        """注册新的数据源"""
        cls._sources[name] = source_class

    @classmethod
    def create(cls, source_name: str, **kwargs) -> BaseDataSource:
        """创建数据源实例"""
        if source_name not in cls._sources:
            raise ValueError(f"未知的数据源: {source_name}，可用: {list(cls._sources.keys())}")

        return cls._sources[source_name](**kwargs)

    @classmethod
    def get_available_sources(cls) -> List[str]:
        """获取可用数据源列表"""
        return list(set(cls._sources.keys()))

"""
接口定义模块

该模块定义了系统中各种服务的抽象接口，包括：
- DataSourceInterface: 数据源接口
- StorageInterface: 存储服务接口
- LLMInterface: LLM服务接口
"""

from .data_source import DataSourceInterface
from .storage import StorageInterface
from .llm import LLMInterface

__all__ = [
    "DataSourceInterface",
    "StorageInterface",
    "LLMInterface",
]

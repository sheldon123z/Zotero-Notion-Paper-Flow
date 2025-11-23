from typing import Dict, Type, List
from .base import BaseStorage
from .notion import NotionStorage
from .zotero import ZoteroStorage

class StorageFactory:
    """存储服务工厂"""

    _storages: Dict[str, Type[BaseStorage]] = {
        'notion': NotionStorage,
        'zotero': ZoteroStorage,
    }

    @classmethod
    def register(cls, name: str, storage_class: Type[BaseStorage]):
        """注册新的存储服务"""
        cls._storages[name] = storage_class

    @classmethod
    def create(cls, storage_name: str, **kwargs) -> BaseStorage:
        """创建存储服务实例"""
        if storage_name not in cls._storages:
            raise ValueError(f"未知的存储服务: {storage_name}，可用: {list(cls._storages.keys())}")

        return cls._storages[storage_name](**kwargs)

    @classmethod
    def get_available_storages(cls) -> List[str]:
        """获取可用存储服务列表"""
        return list(cls._storages.keys())

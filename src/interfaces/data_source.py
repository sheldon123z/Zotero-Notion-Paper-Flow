"""
数据源抽象接口模块

该模块定义了数据源服务的抽象接口，所有数据源实现都必须继承此接口。
支持的数据源包括：ArXiv、Semantic Scholar、Zotero 等。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# 避免循环导入，使用 TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.paper import Paper


class DataSourceInterface(ABC):
    """
    数据源抽象接口

    所有数据源服务都必须实现此接口，提供统一的论文获取、搜索和查询功能。

    Attributes:
        name: 数据源名称
        enabled: 是否启用
    """

    name: str = "base"
    enabled: bool = True

    @abstractmethod
    def fetch_papers(
        self,
        categories: Optional[List[str]] = None,
        date: Optional[str] = None,
        limit: int = 20,
        **kwargs: Any
    ) -> List["Paper"]:
        """
        获取论文列表

        从数据源获取指定条件的论文列表。

        Args:
            categories: 论文分类列表，如 ["cs.LG", "cs.AI"]
            date: 日期筛选，格式为 "YYYY-MM-DD" 或 "YYYY-MM"
            limit: 返回结果数量限制
            **kwargs: 其他数据源特定参数

        Returns:
            论文列表

        Raises:
            ConnectionError: 连接数据源失败
            ValueError: 参数无效
        """
        pass

    @abstractmethod
    def search(
        self,
        keywords: List[str],
        categories: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 20,
        **kwargs: Any
    ) -> List["Paper"]:
        """
        搜索论文

        根据关键词和其他条件搜索论文。

        Args:
            keywords: 搜索关键词列表
            categories: 论文分类列表
            date_from: 起始日期，格式为 "YYYY-MM-DD"
            date_to: 结束日期，格式为 "YYYY-MM-DD"
            limit: 返回结果数量限制
            **kwargs: 其他数据源特定参数

        Returns:
            匹配的论文列表

        Raises:
            ConnectionError: 连接数据源失败
            ValueError: 参数无效
        """
        pass

    @abstractmethod
    def get_by_id(self, paper_id: str) -> Optional["Paper"]:
        """
        通过ID获取论文

        根据论文唯一标识符获取论文详细信息。

        Args:
            paper_id: 论文唯一标识符（如 ArXiv ID、DOI 等）

        Returns:
            论文对象，如果不存在则返回 None

        Raises:
            ConnectionError: 连接数据源失败
            ValueError: ID 格式无效
        """
        pass

    def is_available(self) -> bool:
        """
        检查数据源是否可用

        验证数据源服务是否正常运行，可用于健康检查。

        Returns:
            数据源是否可用
        """
        return self.enabled

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取数据源元数据

        返回数据源的基本信息，包括名称、版本、支持的功能等。

        Returns:
            包含数据源元数据的字典
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "type": self.__class__.__name__,
        }

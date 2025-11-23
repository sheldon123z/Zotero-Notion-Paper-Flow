"""
存储服务抽象接口模块

该模块定义了存储服务的抽象接口，所有存储实现都必须继承此接口。
支持的存储服务包括：Notion、Zotero、Wolai、本地文件系统等。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# 避免循环导入，使用 TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.paper import Paper


class StorageInterface(ABC):
    """
    存储服务抽象接口

    所有存储服务都必须实现此接口，提供统一的论文存储、查询和更新功能。

    Attributes:
        name: 存储服务名称
        enabled: 是否启用
    """

    name: str = "base"
    enabled: bool = True

    @abstractmethod
    def insert(self, paper: "Paper", **kwargs: Any) -> Dict[str, Any]:
        """
        插入论文

        将论文数据插入到存储服务中。

        Args:
            paper: 论文对象
            **kwargs: 其他存储特定参数（如 Notion 的 database_id 等）

        Returns:
            包含插入结果的字典，通常包含：
            - success: 是否成功
            - id: 存储服务中的记录 ID
            - url: 记录的访问 URL（如果有）
            - message: 详细信息

        Raises:
            ConnectionError: 连接存储服务失败
            ValueError: 数据无效
            PermissionError: 权限不足
        """
        pass

    @abstractmethod
    def exists(self, paper_id: str) -> bool:
        """
        检查论文是否存在

        检查指定 ID 的论文是否已存在于存储服务中。

        Args:
            paper_id: 论文唯一标识符

        Returns:
            论文是否存在

        Raises:
            ConnectionError: 连接存储服务失败
        """
        pass

    @abstractmethod
    def update(self, paper_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新论文

        更新存储服务中指定论文的数据。

        Args:
            paper_id: 论文唯一标识符
            data: 要更新的数据字典

        Returns:
            包含更新结果的字典，通常包含：
            - success: 是否成功
            - id: 存储服务中的记录 ID
            - message: 详细信息

        Raises:
            ConnectionError: 连接存储服务失败
            ValueError: 数据无效
            KeyError: 论文不存在
        """
        pass

    def delete(self, paper_id: str) -> Dict[str, Any]:
        """
        删除论文

        从存储服务中删除指定论文。

        Args:
            paper_id: 论文唯一标识符

        Returns:
            包含删除结果的字典

        Raises:
            NotImplementedError: 存储服务不支持删除操作
        """
        raise NotImplementedError(f"{self.name} 存储服务不支持删除操作")

    def get(self, paper_id: str) -> Optional["Paper"]:
        """
        获取论文

        从存储服务中获取指定论文的详细信息。

        Args:
            paper_id: 论文唯一标识符

        Returns:
            论文对象，如果不存在则返回 None

        Raises:
            NotImplementedError: 存储服务不支持获取操作
        """
        raise NotImplementedError(f"{self.name} 存储服务不支持获取操作")

    def query(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        **kwargs: Any
    ) -> List["Paper"]:
        """
        查询论文

        根据条件从存储服务中查询论文。

        Args:
            filters: 查询过滤条件
            limit: 返回结果数量限制
            **kwargs: 其他查询参数

        Returns:
            匹配的论文列表

        Raises:
            NotImplementedError: 存储服务不支持查询操作
        """
        raise NotImplementedError(f"{self.name} 存储服务不支持查询操作")

    def batch_insert(
        self,
        papers: List["Paper"],
        skip_existing: bool = True,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        批量插入论文

        将多篇论文批量插入到存储服务中。

        Args:
            papers: 论文对象列表
            skip_existing: 是否跳过已存在的论文
            **kwargs: 其他存储特定参数

        Returns:
            包含批量插入结果的字典，通常包含：
            - success_count: 成功插入数量
            - skip_count: 跳过数量
            - fail_count: 失败数量
            - results: 各论文的详细结果
        """
        results: List[Dict[str, Any]] = []
        success_count = 0
        skip_count = 0
        fail_count = 0

        for paper in papers:
            try:
                if skip_existing and self.exists(paper.id):
                    skip_count += 1
                    results.append({
                        "id": paper.id,
                        "status": "skipped",
                        "message": "论文已存在"
                    })
                    continue

                result = self.insert(paper, **kwargs)
                if result.get("success"):
                    success_count += 1
                    results.append({
                        "id": paper.id,
                        "status": "success",
                        "result": result
                    })
                else:
                    fail_count += 1
                    results.append({
                        "id": paper.id,
                        "status": "failed",
                        "result": result
                    })
            except Exception as e:
                fail_count += 1
                results.append({
                    "id": paper.id,
                    "status": "error",
                    "message": str(e)
                })

        return {
            "success_count": success_count,
            "skip_count": skip_count,
            "fail_count": fail_count,
            "total": len(papers),
            "results": results
        }

    def is_available(self) -> bool:
        """
        检查存储服务是否可用

        验证存储服务是否正常运行，可用于健康检查。

        Returns:
            存储服务是否可用
        """
        return self.enabled

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取存储服务元数据

        返回存储服务的基本信息。

        Returns:
            包含存储服务元数据的字典
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "type": self.__class__.__name__,
        }

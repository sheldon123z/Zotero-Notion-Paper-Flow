import logging
from abc import abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from interfaces.storage import StorageInterface
from models.paper import Paper

logger = logging.getLogger(__name__)

class BaseStorage(StorageInterface):
    """存储服务基类"""

    def __init__(
        self,
        create_time: datetime = None,
        use_proxy: bool = True,
        proxy_url: str = "http://127.0.0.1:7890"
    ):
        self.create_time = create_time or datetime.now()
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url

    @property
    def proxies(self) -> Optional[Dict[str, str]]:
        """获取代理配置"""
        if self.use_proxy:
            return {
                'http': self.proxy_url,
                'https': self.proxy_url,
            }
        return None

    @abstractmethod
    def get_storage_name(self) -> str:
        """获取存储服务名称"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass

    def batch_insert(self, papers: List[Paper], **kwargs) -> Dict[str, Any]:
        """批量插入论文"""
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        for paper in papers:
            try:
                if self.exists(paper.id):
                    results["skipped"].append(paper.id)
                    continue

                result = self.insert(paper, **kwargs)
                results["success"].append(paper.id)
            except Exception as e:
                logger.error(f"插入论文失败 {paper.id}: {e}")
                results["failed"].append({"id": paper.id, "error": str(e)})

        return results

"""
依赖注入容器模块

该模块实现了服务的依赖注入容器，用于管理和获取各种服务实例。
采用单例模式确保服务实例的复用。
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from .config.settings import Settings
from .interfaces.data_source import DataSourceInterface
from .interfaces.llm import LLMInterface
from .interfaces.storage import StorageInterface

logger = logging.getLogger(__name__)

# 泛型类型变量
T = TypeVar("T")


class ServiceNotRegisteredError(Exception):
    """服务未注册异常"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"服务 '{service_name}' 未注册")


class ServiceInitializationError(Exception):
    """服务初始化异常"""

    def __init__(self, service_name: str, cause: Exception):
        self.service_name = service_name
        self.cause = cause
        super().__init__(f"服务 '{service_name}' 初始化失败: {cause}")


class ServiceContainer:
    """
    服务依赖注入容器

    管理应用程序中各种服务的生命周期，提供服务的注册、获取和销毁功能。
    采用工厂模式和单例模式，确保服务的延迟初始化和实例复用。

    Attributes:
        settings: 应用配置
    """

    def __init__(self, settings: Settings):
        """
        初始化服务容器

        Args:
            settings: 应用配置实例
        """
        self.settings = settings
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[Settings], Any]] = {}
        self._service_types: Dict[str, Type] = {}

        # 分类存储
        self._data_source_names: List[str] = []
        self._storage_names: List[str] = []
        self._llm_names: List[str] = []

    def register(
        self,
        name: str,
        factory: Callable[[Settings], T],
        service_type: Optional[Type] = None
    ) -> "ServiceContainer":
        """
        注册服务工厂

        注册一个服务工厂函数，当首次获取服务时会调用该工厂创建实例。

        Args:
            name: 服务名称
            factory: 服务工厂函数，接收 Settings 参数并返回服务实例
            service_type: 服务类型（用于类型检查和分类）

        Returns:
            返回 self 以支持链式调用

        Example:
            >>> container.register("arxiv", ArxivDataSource)
            >>> container.register("notion", lambda s: NotionStorage(s.notion))
        """
        self._factories[name] = factory
        if service_type:
            self._service_types[name] = service_type

        # 根据服务类型分类
        if service_type:
            if issubclass(service_type, DataSourceInterface):
                self._data_source_names.append(name)
            elif issubclass(service_type, StorageInterface):
                self._storage_names.append(name)
            elif issubclass(service_type, LLMInterface):
                self._llm_names.append(name)

        logger.debug(f"已注册服务: {name}")
        return self

    def register_instance(self, name: str, instance: Any) -> "ServiceContainer":
        """
        注册服务实例

        直接注册一个已创建的服务实例。

        Args:
            name: 服务名称
            instance: 服务实例

        Returns:
            返回 self 以支持链式调用
        """
        self._services[name] = instance

        # 根据实例类型分类
        if isinstance(instance, DataSourceInterface):
            self._data_source_names.append(name)
        elif isinstance(instance, StorageInterface):
            self._storage_names.append(name)
        elif isinstance(instance, LLMInterface):
            self._llm_names.append(name)

        logger.debug(f"已注册服务实例: {name}")
        return self

    def get(self, name: str) -> Any:
        """
        获取服务实例（单例模式）

        首次调用时会通过工厂函数创建服务实例，后续调用返回已创建的实例。

        Args:
            name: 服务名称

        Returns:
            服务实例

        Raises:
            ServiceNotRegisteredError: 服务未注册
            ServiceInitializationError: 服务初始化失败
        """
        # 如果实例已存在，直接返回
        if name in self._services:
            return self._services[name]

        # 如果工厂不存在，抛出异常
        if name not in self._factories:
            raise ServiceNotRegisteredError(name)

        # 使用工厂创建实例
        try:
            logger.debug(f"正在初始化服务: {name}")
            instance = self._factories[name](self.settings)
            self._services[name] = instance
            logger.info(f"服务已初始化: {name}")
            return instance
        except Exception as e:
            logger.error(f"服务初始化失败: {name}, 错误: {e}")
            raise ServiceInitializationError(name, e) from e

    def get_optional(self, name: str) -> Optional[Any]:
        """
        获取可选服务实例

        如果服务不存在或初始化失败，返回 None 而不是抛出异常。

        Args:
            name: 服务名称

        Returns:
            服务实例或 None
        """
        try:
            return self.get(name)
        except (ServiceNotRegisteredError, ServiceInitializationError):
            return None

    def has(self, name: str) -> bool:
        """
        检查服务是否已注册

        Args:
            name: 服务名称

        Returns:
            服务是否已注册
        """
        return name in self._factories or name in self._services

    def get_llm(self) -> LLMInterface:
        """
        获取LLM服务

        获取当前配置的LLM服务实例。

        Returns:
            LLM服务实例

        Raises:
            ServiceNotRegisteredError: LLM服务未注册
        """
        llm_service = self.settings.llm.service
        if self.has(llm_service):
            return self.get(llm_service)

        # 尝试获取默认 LLM 服务
        if self._llm_names:
            return self.get(self._llm_names[0])

        raise ServiceNotRegisteredError("llm")

    def get_data_sources(self) -> Dict[str, DataSourceInterface]:
        """
        获取所有启用的数据源

        根据配置返回所有启用的数据源服务。

        Returns:
            数据源服务字典，键为服务名称
        """
        sources: Dict[str, DataSourceInterface] = {}

        for name in self._data_source_names:
            # 检查服务是否在配置中启用
            service_enabled = getattr(self.settings.services, name, True)
            if not service_enabled:
                continue

            try:
                source = self.get(name)
                if source.is_available():
                    sources[name] = source
            except ServiceInitializationError as e:
                logger.warning(f"数据源 {name} 初始化失败: {e}")

        return sources

    def get_storages(self) -> Dict[str, StorageInterface]:
        """
        获取所有启用的存储服务

        根据配置返回所有启用的存储服务。

        Returns:
            存储服务字典，键为服务名称
        """
        storages: Dict[str, StorageInterface] = {}

        for name in self._storage_names:
            # 检查服务是否在配置中启用
            service_enabled = getattr(self.settings.services, name, True)
            if not service_enabled:
                continue

            try:
                storage = self.get(name)
                if storage.is_available():
                    storages[name] = storage
            except ServiceInitializationError as e:
                logger.warning(f"存储服务 {name} 初始化失败: {e}")

        return storages

    def get_data_source(self, name: str) -> DataSourceInterface:
        """
        获取指定数据源

        Args:
            name: 数据源名称

        Returns:
            数据源服务实例

        Raises:
            ServiceNotRegisteredError: 数据源未注册
        """
        if name not in self._data_source_names:
            raise ServiceNotRegisteredError(f"data_source:{name}")
        return self.get(name)

    def get_storage(self, name: str) -> StorageInterface:
        """
        获取指定存储服务

        Args:
            name: 存储服务名称

        Returns:
            存储服务实例

        Raises:
            ServiceNotRegisteredError: 存储服务未注册
        """
        if name not in self._storage_names:
            raise ServiceNotRegisteredError(f"storage:{name}")
        return self.get(name)

    def dispose(self, name: str) -> None:
        """
        销毁服务实例

        释放指定服务的资源。

        Args:
            name: 服务名称
        """
        if name in self._services:
            instance = self._services.pop(name)
            # 如果服务实现了 close 或 dispose 方法，调用它
            if hasattr(instance, "close"):
                instance.close()
            elif hasattr(instance, "dispose"):
                instance.dispose()
            logger.debug(f"服务已销毁: {name}")

    def dispose_all(self) -> None:
        """
        销毁所有服务实例

        释放所有已创建服务的资源。
        """
        for name in list(self._services.keys()):
            self.dispose(name)
        logger.info("所有服务已销毁")

    def reset(self) -> None:
        """
        重置容器

        销毁所有服务实例并清空注册的工厂。
        """
        self.dispose_all()
        self._factories.clear()
        self._service_types.clear()
        self._data_source_names.clear()
        self._storage_names.clear()
        self._llm_names.clear()
        logger.info("服务容器已重置")

    def get_status(self) -> Dict[str, Any]:
        """
        获取容器状态

        返回容器中所有服务的状态信息。

        Returns:
            包含容器状态的字典
        """
        return {
            "registered_factories": list(self._factories.keys()),
            "initialized_services": list(self._services.keys()),
            "data_sources": self._data_source_names,
            "storages": self._storage_names,
            "llm_services": self._llm_names,
        }

    def __enter__(self) -> "ServiceContainer":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器出口，自动销毁所有服务"""
        self.dispose_all()


def create_container(settings: Optional[Settings] = None) -> ServiceContainer:
    """
    创建服务容器的便捷函数

    Args:
        settings: 应用配置，如果为 None 则从环境变量加载

    Returns:
        配置好的服务容器实例
    """
    if settings is None:
        settings = Settings.from_env()

    return ServiceContainer(settings)

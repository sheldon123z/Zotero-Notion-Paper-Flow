from typing import Dict, Type, Optional
from .base import BaseLLMService
from .deepseek import DeepSeekService
from .kimi import KimiService
from .zhipu import ZhipuService

class LLMServiceFactory:
    """LLM服务工厂"""

    _services: Dict[str, Type[BaseLLMService]] = {
        'deepseek': DeepSeekService,
        'kimi': KimiService,
        'zhipu': ZhipuService,
    }

    @classmethod
    def register(cls, name: str, service_class: Type[BaseLLMService]):
        """注册新的LLM服务"""
        cls._services[name] = service_class

    @classmethod
    def create(
        cls,
        service_name: str = 'deepseek',
        **kwargs
    ) -> BaseLLMService:
        """创建LLM服务实例"""
        if service_name not in cls._services:
            raise ValueError(f"未知的LLM服务: {service_name}，可用服务: {list(cls._services.keys())}")

        service_class = cls._services[service_name]
        return service_class(**kwargs)

    @classmethod
    def get_available_services(cls) -> list:
        """获取可用的服务列表"""
        return list(cls._services.keys())

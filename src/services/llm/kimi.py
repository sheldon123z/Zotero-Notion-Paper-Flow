import os
from .base import BaseLLMService

class KimiService(BaseLLMService):
    """Kimi (Moonshot) LLM服务"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model_name: str = None,
        **kwargs
    ):
        super().__init__(
            api_key=api_key or os.environ.get('KIMI_API_KEY'),
            base_url=base_url or os.environ.get('KIMI_URL', 'https://api.moonshot.cn/v1'),
            model_name=model_name or os.environ.get('KIMI_MODEL', 'moonshot-v1-8k'),
            **kwargs
        )

    def get_service_name(self) -> str:
        return "kimi"

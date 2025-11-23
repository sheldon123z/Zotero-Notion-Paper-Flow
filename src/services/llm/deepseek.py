import os
from .base import BaseLLMService

class DeepSeekService(BaseLLMService):
    """DeepSeek LLM服务"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model_name: str = None,
        **kwargs
    ):
        super().__init__(
            api_key=api_key or os.environ.get('DEEPSEEK_API_KEY'),
            base_url=base_url or os.environ.get('DEEPSEEK_URL', 'https://api.deepseek.com/v1'),
            model_name=model_name or os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat'),
            **kwargs
        )

    def get_service_name(self) -> str:
        return "deepseek"

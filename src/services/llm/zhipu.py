import os
from .base import BaseLLMService

class ZhipuService(BaseLLMService):
    """智谱 LLM服务"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model_name: str = None,
        **kwargs
    ):
        super().__init__(
            api_key=api_key or os.environ.get('ZHIPU_API_KEY'),
            base_url=base_url or os.environ.get('ZHIPU_URL', 'https://open.bigmodel.cn/api/paas/v4/'),
            model_name=model_name or os.environ.get('ZHIPU_MODEL', 'glm-4'),
            **kwargs
        )

    def get_service_name(self) -> str:
        return "zhipu"

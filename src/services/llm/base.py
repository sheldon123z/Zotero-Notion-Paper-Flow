import os
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class BaseLLMService(ABC):
    """LLM服务基类"""

    MAX_RETRIES = 3

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model_name: str = None,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """懒加载OpenAI客户端"""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    def chat(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0,
        retry_count: int = None
    ) -> Any:
        """发送对话请求，带重试机制"""
        if retry_count is None:
            retry_count = self.MAX_RETRIES

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        last_error = None
        for attempt in range(retry_count):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": response_format},
                    timeout=self.timeout
                )

                content = resp.choices[0].message.content
                if response_format == "json_object":
                    return json.loads(content)
                return content

            except Exception as e:
                last_error = e
                logger.warning(f"LLM请求失败 (尝试 {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    sleep_time = (attempt + 1) * 2
                    time.sleep(sleep_time)

        logger.error(f"LLM请求全部失败: {last_error}")
        return "" if response_format == "text" else {}

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return "你是人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。"

    def generate_summary(self, text: str) -> Dict[str, str]:
        """生成论文摘要的TLDR"""
        prompt = f'''下面这段话（<summary></summary>之间的部分）是一篇论文的摘要。
请基于摘要信息总结论文的动机、方法、结果、remark、翻译、short_summary等信息，
其中remark请你用不超过15个英文字符总结该文章的领域，如果有算法请将算法放到前面，
如"LLM/强化学习"，或"RL/多智能体"等，其中"翻译"将整个摘要内容使用中文进行翻译，
"short_summary"部分则是使用中文根据翻译结果进行不超过50字的主题简介，
注意不要使用任何的markdown格式标点符号，也不要写任何的公式。
需要特别注意，除了remark部分其他所有地方请使用中文表述，并以 **JSON** 格式输出，
格式如下：
{{
    "动机": "xxx",
    "方法": "xxx",
    "结果": "xxx",
    "翻译": "xxx",
    "short_summary": "xxx",
    "remark": "xxx"
}}
如果某一项不存在，请输出空字符串：
<summary>{text}</summary>'''

        result = self.chat(prompt, response_format="json_object")
        if not result:
            return {
                "动机": "", "方法": "", "结果": "",
                "翻译": "", "short_summary": "", "remark": ""
            }
        return result

    def generate_tags(self, text: str) -> Dict[str, Any]:
        """生成论文标签"""
        prompt = f"""以下是论文摘要内容：
{text}

请参考论文摘要内容，判断该论文的主要研究领域（例如RL、MTS、NLP、多模态、CV、MARL、LLM等）
填写在"主要领域"键后，请你尽量使用英文专业名词的简写。
同时根据摘要内容总结出最多10个高度概括文章主题的tags，以list的形式填写在"标签"键后，
并在最后一定加入一个"/unread"标签。
请你一定注意，"主要领域" 只能有一个，"标签" 内容的数量则可以有多个，
并使用以下**JSON**格式回复：
{{
    "主要领域": "RL",
    "标签": ["reinforcement-learning", "optimization", "/unread"]
}}"""

        result = self.chat(prompt, response_format="json_object")
        if not result:
            return {"主要领域": "ML", "标签": ["/unread"]}
        return result

    @abstractmethod
    def get_service_name(self) -> str:
        """获取服务名称"""
        pass

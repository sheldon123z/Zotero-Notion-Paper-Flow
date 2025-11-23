"""
LLM服务抽象接口模块

该模块定义了LLM服务的抽象接口，采用策略模式设计。
支持的LLM服务包括：DeepSeek、OpenAI、Claude、本地模型等。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMInterface(ABC):
    """
    LLM服务抽象接口

    所有LLM服务都必须实现此接口，提供统一的对话、摘要生成和标签生成功能。
    采用策略模式，允许在运行时切换不同的LLM服务实现。

    Attributes:
        name: LLM服务名称
        model: 使用的模型名称
        enabled: 是否启用
    """

    name: str = "base"
    model: str = ""
    enabled: bool = True

    @abstractmethod
    def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        发送对话请求

        向LLM发送单轮对话请求并获取响应。

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词，用于设定LLM的角色和行为
            temperature: 温度参数，控制输出的随机性，范围 0-2
            max_tokens: 最大生成token数量
            **kwargs: 其他LLM特定参数

        Returns:
            LLM的响应文本

        Raises:
            ConnectionError: 连接LLM服务失败
            ValueError: 参数无效
            RuntimeError: LLM服务返回错误
        """
        pass

    @abstractmethod
    def generate_summary(
        self,
        text: str,
        language: str = "zh",
        max_length: Optional[int] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        生成摘要

        为论文或文本生成摘要。

        Args:
            text: 原始文本（通常是论文摘要或全文）
            language: 输出语言，"zh" 为中文，"en" 为英文
            max_length: 摘要最大长度（字符数）
            **kwargs: 其他参数

        Returns:
            包含摘要信息的字典：
            - summary: 生成的摘要
            - short_summary: 简短摘要（一句话总结）
            - keywords: 提取的关键词列表
            - success: 是否成功
            - error: 错误信息（如果有）

        Raises:
            ConnectionError: 连接LLM服务失败
            ValueError: 输入文本无效
        """
        pass

    @abstractmethod
    def generate_tags(
        self,
        text: str,
        existing_tags: Optional[List[str]] = None,
        max_tags: int = 5,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        生成标签

        为论文或文本生成分类标签。

        Args:
            text: 原始文本（通常是论文标题和摘要）
            existing_tags: 现有标签列表，用于参考或匹配
            max_tags: 最大标签数量
            **kwargs: 其他参数

        Returns:
            包含标签信息的字典：
            - tags: 生成的标签列表
            - categories: 分类列表（如果有）
            - confidence: 置信度分数（如果有）
            - success: 是否成功
            - error: 错误信息（如果有）

        Raises:
            ConnectionError: 连接LLM服务失败
            ValueError: 输入文本无效
        """
        pass

    def chat_with_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        多轮对话

        支持上下文的多轮对话。

        Args:
            messages: 对话历史列表，每条消息包含 "role" 和 "content"
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大生成token数量
            **kwargs: 其他LLM特定参数

        Returns:
            LLM的响应文本

        Raises:
            NotImplementedError: 不支持多轮对话
        """
        raise NotImplementedError(f"{self.name} 不支持多轮对话")

    def generate_tldr(
        self,
        text: str,
        language: str = "zh",
        **kwargs: Any
    ) -> Dict[str, str]:
        """
        生成TLDR（太长不看）摘要

        生成一句话的简短总结。

        Args:
            text: 原始文本
            language: 输出语言
            **kwargs: 其他参数

        Returns:
            包含TLDR的字典：
            - tldr_zh: 中文TLDR
            - tldr_en: 英文TLDR
        """
        summary_result = self.generate_summary(text, language=language, max_length=100, **kwargs)
        return {
            "tldr_zh": summary_result.get("short_summary", ""),
            "tldr_en": ""
        }

    def batch_process(
        self,
        texts: List[str],
        operation: str = "summary",
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        批量处理

        对多个文本进行批量处理。

        Args:
            texts: 文本列表
            operation: 操作类型，"summary" 或 "tags"
            **kwargs: 其他参数

        Returns:
            处理结果列表
        """
        results: List[Dict[str, Any]] = []

        for text in texts:
            try:
                if operation == "summary":
                    result = self.generate_summary(text, **kwargs)
                elif operation == "tags":
                    result = self.generate_tags(text, **kwargs)
                else:
                    result = {"error": f"不支持的操作类型: {operation}"}
                results.append(result)
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e)
                })

        return results

    def is_available(self) -> bool:
        """
        检查LLM服务是否可用

        验证LLM服务是否正常运行，可用于健康检查。

        Returns:
            LLM服务是否可用
        """
        return self.enabled

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取LLM服务元数据

        返回LLM服务的基本信息。

        Returns:
            包含LLM服务元数据的字典
        """
        return {
            "name": self.name,
            "model": self.model,
            "enabled": self.enabled,
            "type": self.__class__.__name__,
        }

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量

        粗略估算文本的token数量，用于控制输入长度。

        Args:
            text: 输入文本

        Returns:
            估算的token数量
        """
        # 简单估算：中文约1字=1.5token，英文约4字符=1token
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars / 4)

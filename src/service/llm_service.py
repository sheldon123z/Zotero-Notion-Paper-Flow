"""
 Modified by Xiaodong Zheng on 2024/9/20
"""
import os
import time
import openai
import json
import logging
import common_utils
import random
import requests
from requests.exceptions import Timeout, ConnectionError
from openai import OpenAI
MAX_RETRIES = 3

logger = common_utils.get_logger(__name__)
def chat(prompt, retry_count=MAX_RETRIES-1, service="deepseek", response_format="text", **kwargs):
    # 从 kwargs 中获取 API 相关参数，如果没有提供则使用环境变量中的默认值
    api_key = kwargs.get('api_key', os.environ.get('DEFAULT_API_KEY'))
    base_url = kwargs.get('base_url', os.environ.get('DEFAULT_BASE_URL'))
    model_name = kwargs.get('model_name', os.environ.get("DEFAULT_MODEL_NAME"))

    # 设置特定服务的参数
    if service == 'kimi':
        api_key = os.environ.get('KIMI_API_KEY', api_key)
        base_url = os.environ.get('KIMI_URL',base_url)
        model_name = os.environ.get('KIMI_MODEL',model_name)
    elif service == 'deepseek':
        api_key = os.environ.get('DEEPSEEK_API_KEY', api_key)
        base_url = os.environ.get('DEEPSEEK_URL',base_url) # deepseek 只有这个api可以输出8K
        model_name = os.environ.get('DEEPSEEK_MODEL',model_name)
    elif service == 'zhipu':
        api_key = os.environ.get('ZHIPU_API_KEY', api_key)
        base_url = os.environ.get('ZHIPU_URL',base_url)
        model_name = os.environ.get('ZHIPU_MODEL',model_name)
    elif service not in ['kimi', 'deepseek','zhipu']:
        # 自定义服务时，检查必需的参数
        if not api_key:
            raise ValueError("缺少 'api_key'")
        if not base_url:
            raise ValueError("缺少 'base_url'")
        if not model_name:
            raise ValueError("缺少 'model_name'")
    else:
        raise Exception(f"未知或缺失的大模型服务: {service}")

    # 创建 OpenAI 客户端
    client = OpenAI(api_key=api_key, base_url=base_url)

    messages = [
        {"role": "system", "content": "你是人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。"},
        {"role": "user", "content": prompt}
    ]
    
    def do_request():
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0,
                response_format={"type": f"{response_format}"} ,
                timeout=30
            )
            if response_format == "json_object":
                content = json.loads(resp.choices[0].message.content)
                return content
            else:   
                return resp.choices[0].message.content
        except requests.exceptions.Timeout as e:
            logger.error(f"请求超时: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {e}")
            raise
    
    while retry_count > 0:
        try:
            return do_request()
        except Exception as e:
            sleeping_seconds = (MAX_RETRIES - retry_count) * 2
            retry_count -= 1
            logger.warning(f"{e} sleeping {sleeping_seconds}s, prompt: {prompt}")
            time.sleep(sleeping_seconds)
    return ""

    # logger.error("所有尝试均失败，返回空字符串")
    # return ""  # 如果所有重试都失败，返回空字符串


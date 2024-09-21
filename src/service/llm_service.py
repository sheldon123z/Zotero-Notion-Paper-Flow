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

logger = common_utils.get_logger(__name__)
def chat(prompt, retry_count=6, service="kimi", response_format="text", **kwargs):
    # 从 kwargs 中获取 API 相关参数，如果没有提供则使用环境变量中的默认值
    api_key = kwargs.get('api_key', os.environ.get('DEFAULT_API_KEY'))
    base_url = kwargs.get('base_url', os.environ.get('DEFAULT_BASE_URL'))
    model_name = kwargs.get('model_name', os.environ.get("DEFAULT_MODEL_NAME"))

    # 设置特定服务的参数
    if service == 'kimi':
        api_key = os.environ.get('KIMI_API_KEY', api_key)
        base_url = "https://api.moonshot.cn/v1"
        model_name = 'moonshot-v1-8k'
    elif service == 'deepseek':
        api_key = os.environ.get('DEEPSEEK_API_KEY', api_key)
        base_url = "https://api.deepseek.cn/v1"
        model_name = 'deepseek-chat'
    elif service not in ['kimi', 'deepseek']:
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
                temperature=0.2,
                response_format={"type": f"{response_format}"} ,
                timeout=15
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
    # return do_request()
    # for attempt in range(retry_count):
    #     try:
    #         return do_request()  # 成功时直接返回结果
    #     except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
    #         # 使用指数退避算法设置重试间隔，最长10秒
    #         sleeping_seconds = min((2 ** attempt) * 3 + random.uniform(0, 2), 10)            
    #         truncated_prompt = (prompt[:50] + '...') if len(prompt) > 50 else prompt
    #         logger.warning(f"Attempt {attempt + 1}/{retry_count}: {e}, sleeping {sleeping_seconds}s, prompt: {truncated_prompt}")
    #         time.sleep(sleeping_seconds)  # 等待指定秒数后再重试
    #     except requests.exceptions.HTTPError as e:
    #         logger.error(f"HTTP 错误，停止重试: {e}")
    #         break
    #     except Exception as e:
    #         logger.error(f"未处理的异常: {e}, 不再进行重试")
    #         break
    while retry_count > 0:
        try:
            return do_request()
        except Exception as e:
            sleeping_seconds = (4 - retry_count) * 2
            retry_count -= 1
            logger.warning(f"{e} sleeping {sleeping_seconds}s, prompt: {prompt}")
            time.sleep(sleeping_seconds)
    return ""

    # logger.error("所有尝试均失败，返回空字符串")
    # return ""  # 如果所有重试都失败，返回空字符串

# def function_call_chat(summary, retry_count=3, service='deepseek'):

#     if service == 'kimi':
#         api_key = os.environ['KIMI_API_KEY']
#         base_url = "https://api.moonshot.cn/v1"
#         model_name='moonshot-v1-8k'
#     elif service == 'deepseek':
#         api_key = os.environ['DEEPSEEK_API_KEY']
#         base_url = "https://api.deepseek.cn/v1"
#         model_name='deepseek-chat'
#     else:
#         raise Exception(f"Unknown service: {service}")
    
#     client = OpenAI(
#         # api_key=os.environ['KIMI_API_KEY'],
#         # base_url=os.environ['KIMI_URL'],
#         api_key=api_key,
#         base_url=base_url,
#     )
    
#     system_prompt = f"""
#                 你是一个人工智能科研助手，负责回答用户提出的各种问题。你专长与总结论文摘要，并根据摘要
#                 能够给出主要内容提炼和文章标签。
#                 """
#     user_prompt = f"""
#                 以下是论文摘要内容：\n {summary}\n

#                 请参考论文摘要内容，判断该论文的主要研究领域（例如强化学习RL、MTS、NLP、多模态、CV、MARL、LLM等）请你尽量使用英文专业名词的简写，
#                 并总结出最多6个高度概括文章主题的标签。
#                 请根据论文摘要灵活确定"主要领域"和"标签"的内容，注意，“主要领域”
#                 只能有一个，并使用以下JSON格式回复：
#                 {{
#                   "主要领域": "LLM",
#                   "标签": [
#                     "instruction-tuning",
#                     "language models",
#                     "training data selection",
#                     "learning percentage",
#                     "data hardness",
#                     "model sizes",
#                     "Reinforcement Learning"
#                   ]
#                 }}
#                 """
#     messages = [{"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt}]            
#     completion = client.chat.completions.create(
#         model=model_name,
#         messages=messages,
#         temperature=0.1,
#         response_format={"type": "json_object"}, # <-- 使用 response_format 参数指定输出格式为 json_object
#     )
#     content = json.loads(completion.choices[0].message.content)
    
#     return content

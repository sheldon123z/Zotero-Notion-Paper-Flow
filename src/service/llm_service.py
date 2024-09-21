"""
 Modified by Xiaodong Zheng on 2024/9/20
"""
import os
import time
import openai
import json

from openai import OpenAI

import common_utils

logger = common_utils.get_logger(__name__)


def chat(prompt, retry_count=3, service='kimi',response_type='text'):
    client = OpenAI(
        api_key=os.environ['KIMI_API_KEY'],
        base_url="https://api.moonshot.cn/v1",
    )
    model_name = 'moonshot-v1-8k'
    messages = [
        {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。"},
        {"role": "user", "content": prompt}
    ]

    def do_request():
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.6,
            response_format ={"type": f"{response_type}"},
            
        )
        return resp.choices[0].message.content

    while retry_count > 0:
        try:
            return do_request()
        except Exception as e:
            sleeping_seconds = (4 - retry_count) * 2
            retry_count -= 1
            logger.warning(f"{e} sleeping {sleeping_seconds}s, prompt: {prompt}")
            time.sleep(sleeping_seconds)
    return ""


def function_call_chat(summary, retry_count=3, model_name='deepseek-chat'):
    client = OpenAI(
        # api_key=os.environ['KIMI_API_KEY'],
        # base_url=os.environ['KIMI_URL'],
        api_key=os.environ['DEEPSEEK_API_KEY'],
        base_url=os.environ['DEEPSEEK_URL'],
    )
    
    system_prompt = f"""
                你是智能客服，负责回答用户提出的各种问题。请参考论文摘要内容，判断该论文的主要研究领域（例如强化学习RL、MTS、NLP、多模态、CV、MARL、LLM等）请你尽量使用英文专业名词的简写，并总结出最多6个高度概括文章主题的标签。请根据论文摘要灵活确定"主要领域"和"标签"的内容，注意，“主要领域”只能有一个，并使用以下JSON格式回复：
                {{
                  "主要领域": "LLM",
                  "标签": [
                    "instruction-tuning",
                    "language models",
                    "training data selection",
                    "learning percentage",
                    "data hardness",
                    "model sizes",
                    "Reinforcement Learning"
                  ]
                }}

                以下是论文摘要内容：\n {summary}
                """
    user_prompt = "Which is the longest river in the world? The Nile River."
    messages = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]            
    completion = client.chat.completions.create(
        model=model_name,
        # messages=[
        #     {"role": "system",
        #      "content": "你是 deepseekchat提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。deepseek 为专有名词，不可翻译成其他语言。"},
        #     {"role": "system", "content": system_prompt}, # <-- 将附带输出格式的 system prompt 提交给 Kimi
        #     {"role": "user", "content": "你好，我叫李雷，1+1等于多少？"}
        # ],
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"}, # <-- 使用 response_format 参数指定输出格式为 json_object
    )
    content = json.loads(completion.choices[0].message.content)
    
    return content

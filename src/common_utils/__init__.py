"""
通用工具模块
"""
import logging
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(name)s] [%(filename)s(%(lineno)d)] [%(levelname)s] %(message)s"
    )
    return logging.getLogger(name)

logger = get_logger(__name__)

def send_slack(msg: str, channel_id: str = '每日论文'):
    """发送Slack消息"""
    try:
        api_key = os.environ.get('SLACK_API_KEY')
        if not api_key:
            logger.warning("SLACK_API_KEY 未设置，跳过发送Slack消息")
            return None

        client = WebClient(token=api_key)
        result = client.chat_postMessage(
            channel=channel_id,
            text=msg,
            mrkdwn=True
        )
        logger.info(f"Slack消息发送成功: {result}")
        return result
    except SlackApiError as e:
        logger.error(f"发送Slack消息失败: {e}")
        return None
    except Exception as e:
        logger.error(f"Slack发送异常: {e}")
        return None

# 导出
__all__ = ['get_logger', 'send_slack', 'logger']

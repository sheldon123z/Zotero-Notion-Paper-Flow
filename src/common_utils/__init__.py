"""
 Created by luogang on 2024/3/1
"""
import logging
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def get_logger(name):
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(name)s] [%(filename)s(%(lineno)d)] [%(levelname)s] %(message)s")
    return logging.getLogger(name)


logger = get_logger(__name__)


def send_slack(msg, channel_id='每日论文'):
    try:
        client = WebClient(token=os.environ['SLACK_API_KEY'])
        # Call the chat.postMessage method using the WebClient
        result = client.chat_postMessage(
            channel=channel_id,
            text=msg,
            mrkdwn=True
        )
        logger.info(result)
    except SlackApiError as e:
        logger.error(f"Error posting message: {e}")

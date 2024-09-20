"""
 Modified by Xiaodong Zheng on 2024/9/20
"""
import json
import os

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import common_utils

logger = common_utils.get_logger(__name__)


class HFDailyPaperVisitor:
    def __init__(self, output_dir, url='https://huggingface.co/papers', dt=None):
        if dt is not None:
            url = url + f'?date={dt}'
        self._url = url
        self.datetime = None
        self.paper_list: list = []
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self._init()

    def _init(self):
        proxies = {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890',
        }
        daily_paper_page = requests.get(
            self._url,
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Content-Type': 'text/html; charset=utf-8',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            },
            proxies=proxies
        )
        soup = BeautifulSoup(daily_paper_page.text, 'html.parser')
        # 2024-02-28T06:48:32.919Z
        dt = soup.select_one('time').attrs['datetime']
        # [<a class="cursor-pointer" href="/papers/2402.17764">The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits</a>,
        # <a class="cursor-pointer" href="/papers/2402.17485">EMO: Emote Portrait Alive - Generating Expressive Portrait Videos with Audio2Video Diffusion Model under Weak Conditions</a>,
        # <a class="cursor-pointer" href="/papers/2402.17177">Sora: A Review on Background, Technology, Limitations, and Opportunities of Large Vision Models</a>,
        # <a class="cursor-pointer" href="/papers/2402.17412">DiffuseKronA: A Parameter Efficient Fine-tuning Method for Personalized Diffusion Model</a>]
        parent_nodes = soup.select('section.container > div > div > article')
        for p_node in parent_nodes:
            a_node = p_node.select('div > div > div.w-full > h3 > a')[0]
            media_node = p_node.select('a > img')
            media_type = 'image'
            if len(media_node) == 0:
                media_node = p_node.select('video')
                media_type = 'video'
            if len(media_node) > 0:
                media_node = media_node[0]
            self.paper_list.append({
                'link': a_node.attrs['href'],
                'id': a_node.attrs['href'].split('/')[-1],
                'title': a_node.text.strip(),
                'media_type': media_type,
                'media_url': media_node.attrs['src'] if 'src' in media_node.attrs else ''
            })
        self.datetime = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')

        logger.info(f"paper list size: {len(self.paper_list)}")
        logger.info(f"datetime {self.datetime}")

        save_filename = os.path.join(self.output_dir, f"hf_{self.datetime.strftime('%Y-%m-%d')}.json")
        logger.info(f"saving to {save_filename}")

        json.dump(
            self.paper_list,
            open(save_filename, 'w'),
            ensure_ascii=False,
            indent=True
        )

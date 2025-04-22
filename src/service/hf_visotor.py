"""
Modified by Xiaodong Zheng on 2025/4/22
添加错误处理和网站结构适应性
"""
import json
import os
import time
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
        # 设置代理，如果环境变量中没有设置，默认使用本地代理
        proxy_url = os.environ.get('HTTP_PROXY', 'http://127.0.0.1:7890')
        proxies = {
            'http': proxy_url,
            'https': proxy_url,
        }
        
        # 设置最大重试次数和等待时间
        max_retries = 3
        retry_wait = 2
        
        # 添加重试逻辑
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试获取HuggingFace Papers页面: {self._url} (尝试 {attempt+1}/{max_retries})")
                daily_paper_page = requests.get(
                    self._url,
                    headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Content-Type': 'text/html; charset=utf-8',
                        'Accept-Encoding': 'gzip, deflate, br, zstd',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                    },
                    proxies=proxies,
                    timeout=30  # 设置超时时间
                )
                
                # 检查响应状态
                if daily_paper_page.status_code != 200:
                    logger.warning(f"HTTP请求失败: 状态码 {daily_paper_page.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_wait)
                        retry_wait *= 2  # 指数退避
                        continue
                    else:
                        logger.error("达到最大重试次数，使用空列表")
                        self.datetime = datetime.now()
                        break
                
                # 解析HTML
                soup = BeautifulSoup(daily_paper_page.text, 'html.parser')
                
                # 尝试查找时间标签
                time_tag = soup.select_one('time')
                if time_tag and 'datetime' in time_tag.attrs:
                    dt = time_tag.attrs['datetime']
                    self.datetime = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.%fZ')
                    logger.info(f"找到日期: {self.datetime}")
                else:
                    # 如果找不到time标签，尝试查找其他可能包含日期的元素
                    logger.warning("未找到 <time> 标签或缺少 datetime 属性，使用当前时间")
                    self.datetime = datetime.now()
                
                # 增强文章查找逻辑，尝试多种选择器
                paper_sections = []
                selectors = [
                    'section.container > div > div > article',  # 原始选择器
                    'article',  # 简化的选择器
                    '.paper-card',  # 可能的类选择器
                    '.papers-list > div'  # 可能的列表选择器
                ]
                
                for selector in selectors:
                    paper_sections = soup.select(selector)
                    if paper_sections:
                        logger.info(f"使用选择器 '{selector}' 找到 {len(paper_sections)} 篇论文")
                        break
                
                # 处理每个论文部分
                for p_node in paper_sections:
                    try:
                        # 尝试多种标题选择器
                        title_selectors = [
                            'div > div > div.w-full > h3 > a',  # 原始选择器
                            'h3 > a',  # 简化选择器
                            'a.paper-title',  # 可能的类选择器
                            '.title a',  # 可能的嵌套选择器
                            'a[href^="/papers/"]'  # 基于href模式的选择器
                        ]
                        
                        a_node = None
                        for selector in title_selectors:
                            a_nodes = p_node.select(selector)
                            if a_nodes:
                                a_node = a_nodes[0]
                                break
                        
                        if not a_node:
                            logger.warning(f"无法找到论文标题链接，跳过")
                            continue
                        
                        # 确保链接是完整的
                        paper_link = a_node.attrs['href']
                        if not paper_link.startswith('http'):
                            # 添加域名前缀如果是相对链接
                            if paper_link.startswith('/'):
                                paper_link = f"https://huggingface.co{paper_link}"
                            else:
                                paper_link = f"https://huggingface.co/{paper_link}"
                        
                        # 从链接中提取论文ID
                        paper_id = paper_link.split('/')[-1]
                        
                        # 查找媒体(图片或视频)
                        media_type = None
                        media_url = ""
                        
                        # 尝试查找图片
                        media_node = p_node.select('a > img')
                        if media_node:
                            media_type = 'image'
                            media_node = media_node[0]
                        else:
                            # 尝试查找视频
                            media_node = p_node.select('video')
                            if media_node:
                                media_type = 'video'
                                media_node = media_node[0]
                            else:
                                # 尝试其他可能的图片选择器
                                media_node = p_node.select('img')
                                if media_node:
                                    media_type = 'image'
                                    media_node = media_node[0]
                        
                        # 如果找到媒体节点并且有src属性
                        if media_node and 'src' in media_node.attrs:
                            media_url = media_node.attrs['src']
                        
                        # 添加论文信息到列表
                        paper_info = {
                            'link': paper_link,
                            'id': paper_id,
                            'title': a_node.text.strip(),
                            'media_type': media_type if media_type else 'none',
                            'media_url': media_url
                        }
                        
                        self.paper_list.append(paper_info)
                        logger.debug(f"添加论文: {paper_info['id']} - {paper_info['title']}")
                    
                    except Exception as e:
                        logger.warning(f"处理论文时出错: {str(e)}")
                        continue
                
                # 成功处理，跳出重试循环
                break
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_wait} 秒后重试...")
                    time.sleep(retry_wait)
                    retry_wait *= 2  # 指数退避
                else:
                    logger.error("达到最大重试次数，使用空列表和当前时间")
                    self.datetime = datetime.now()
            
            except Exception as e:
                logger.error(f"解析HuggingFace页面时发生未预期错误: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_wait} 秒后重试...")
                    time.sleep(retry_wait)
                    retry_wait *= 2
                else:
                    logger.error("达到最大重试次数，使用空列表和当前时间")
                    self.datetime = datetime.now()
        
        # 日志输出
        logger.info(f"找到论文: {len(self.paper_list)} 篇")
        logger.info(f"日期: {self.datetime}")

        # 保存到文件
        save_filename = os.path.join(self.output_dir, f"hf_{self.datetime.strftime('%Y-%m-%d')}.json")
        logger.info(f"保存到文件: {save_filename}")

        json.dump(
            self.paper_list,
            open(save_filename, 'w'),
            ensure_ascii=False,
            indent=True
        )
"""
Modified by Xiaodong Zheng on 2025/4/22
增强ArXiv查询功能和错误处理
"""
import json
import os
import pickle
import re
import copy
import sys
import time
from typing import Union, List
from urllib.request import urlretrieve

import arxiv

import common_utils
from entity.formatted_arxiv_obj import FormattedArxivObj
from service import llm_service

logger = common_utils.get_logger(__name__)

class ArxivVisitor:
    def __init__(self, output_dir, page_size=10, disable_cache=False):
        self.cache_dir = os.path.join(output_dir, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.client = arxiv.Client(page_size=page_size)
        self.max_retries = 3
        self.retry_wait = 2

    def _process_tldr(self, summary, cache_obj, cache_filename):
        logger.info(f"处理论文TLDR: {cache_obj['id']}")

        keys = ('动机', '方法', '结果', 'remark')
        
        if 'tldr' in cache_obj and all([key in cache_obj['tldr'] and cache_obj['tldr'][key].strip() != '' for key in keys]):
            logger.info(f"从缓存找到TLDR")
            return
        # 检查是否有缓存
        if 'raw_tldr' in cache_obj and cache_obj['raw_tldr'].strip() != '':
            try:
                tldr = json.loads(cache_obj['raw_tldr'])
            except json.JSONDecodeError:
                logger.warning(f"解析raw_tldr JSON失败，重新处理")
                tldr = self._generate_tldr(summary)
                cache_obj['raw_tldr'] = json.dumps(tldr)
        else:
            tldr = self._generate_tldr(summary)
            cache_obj['raw_tldr'] = json.dumps(tldr) # 保存成字符串格式
            
        if 'tldr' not in cache_obj:
            cache_obj['tldr'] = {}
        cache_obj['tldr'].update(tldr)
        
        for key in keys:
            if key not in cache_obj['tldr']:
                logger.warning(f"{key} 不在tldr中")
                cache_obj['tldr'][key] = ''
                
        if '翻译' in cache_obj['tldr']:
            cache_obj['summary_cn'] = cache_obj['tldr']['翻译']
        if 'short_summary' in cache_obj['tldr']:
            cache_obj['short_summary'] = cache_obj['tldr']['short_summary']
            
        try:
            json.dump(cache_obj, open(cache_filename, 'w'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存文件时出错: {e}")
            # 创建备份路径
            backup_filename = cache_filename + ".backup"
            logger.info(f"尝试保存到备份文件: {backup_filename}")
            json.dump(cache_obj, open(backup_filename, 'w'), ensure_ascii=False, indent=2)

    def _generate_tldr(self, summary):
        """使用LLM生成摘要的TLDR"""
        logger.info("生成论文TLDR")
        
        prmpt = f'''下面这段话（<summary></summary>之间的部分）是一篇论文的摘要。
        请基于摘要信息总结论文的动机、方法、结果、remark、翻译、short_summary等信息，, 其中remark请你用不超过15个英文字符总结
        该文章的领域,如果有算法请将算法放到前面，如"LLM/强化学习"，或"RL/多智能体"等，其中"翻译"将整个摘要内容使用中文进行翻译，
        "short_summary"部分则是使用中文根据翻译结果进行不超过50字的主题简介,注意不要使用任何的markdown格式标点符号，也不要写任何的公式。
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
        如果某一项不存在，请输出空字符串，请认真回答，
        如果回答的好我会给你很多小费：\n<summary>{summary}</summary>'''
        
        # 添加重试逻辑
        for attempt in range(self.max_retries):
            try:
                tldr = llm_service.chat(
                    prompt=prmpt,
                    response_format='json_object' 
                )
                return tldr
            except Exception as e:
                logger.error(f"LLM调用出错 (尝试 {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"等待 {self.retry_wait} 秒后重试...")
                    time.sleep(self.retry_wait)
                    self.retry_wait *= 2  # 指数退避
                else:
                    logger.error("达到最大重试次数，返回空的TLDR")
                    return {
                        "动机": "",
                        "方法": "",
                        "结果": "",
                        "翻译": "",
                        "short_summary": "",
                        "remark": ""
                    }

    def _process_tag_info(self, summary, cache_obj, cache_filename):
        logger.info(f"处理论文标签: {cache_obj['id']}")

        keys = ('主要领域', '标签')
        if 'tag_info' in cache_obj and all([key in cache_obj['tag_info'] for key in keys]):
            logger.info(f"从缓存找到标签信息")
            return
            
        # 尝试加载或生成标签信息
        if 'tag_info_raw' in cache_obj and cache_obj['tag_info_raw'].strip() != '':
            try:
                tag_info = json.loads(cache_obj['tag_info_raw'])
            except json.JSONDecodeError:
                logger.warning(f"解析tag_info_raw JSON失败，重新处理")
                tag_info = self._generate_tag_info(summary)
                cache_obj['tag_info_raw'] = json.dumps(tag_info)
        else:
            tag_info = self._generate_tag_info(summary)
            cache_obj['tag_info_raw'] = json.dumps(tag_info)
            
        if 'tag_info' not in cache_obj:
            cache_obj['tag_info'] = {}

        # 确保tag_info是字典类型
        if isinstance(tag_info, dict):
            cache_obj['tag_info'].update(tag_info)
            
            # 确保标签列表包含/unread
            if '标签' in cache_obj['tag_info'] and isinstance(cache_obj['tag_info']['标签'], list):
                if "/unread" not in cache_obj['tag_info']['标签']:
                    cache_obj['tag_info']['标签'].append("/unread")
        else:
            logger.error(f"tag_info不是字典类型: {type(tag_info)}")
            cache_obj['tag_info'] = {
                '主要领域': 'RL' if 'reinforcement' in summary.lower() else 'NLP', 
                '标签': ['/unread']
            }

        try:
            json.dump(cache_obj, open(cache_filename, 'w'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存文件时出错: {e}")
            backup_filename = cache_filename + ".backup"
            logger.info(f"尝试保存到备份文件: {backup_filename}")
            json.dump(cache_obj, open(backup_filename, 'w'), ensure_ascii=False, indent=2)

    def _generate_tag_info(self, summary):
        """使用LLM生成标签信息"""
        logger.info(f"生成论文标签")
        
        prompt = f"""
                    以下是论文摘要内容：\n {summary}\n

                    请参考论文摘要内容，判断该论文的主要研究领域（例如RL、MTS、NLP、多模态、CV、MARL、LLM等）概括的结果
                    填写在"主要领域"键后，请你尽量使用英文专业名词的简写。
                    同时根据摘要内容总结出最多10个高度概括文章主题的tags,以list的形式填写在"标签"键后，并在最后一定加入一个"/unread"标签。
                    请你一定注意，"主要领域" 只能有一个，"标签" 内容的数量则可以有多个，
                    并使用以下**JSON**格式回复：
                    {{
                    "主要领域": "RL",
                    "标签": [
                        "reinforcement-learning",
                        "power-system",
                        "optimization",
                        "energy",
                        "/unread"
                    ]
                    }}
                    """
                    
        # 添加重试逻辑
        for attempt in range(self.max_retries):
            try:
                tag_info = llm_service.chat(
                    prompt=prompt,
                    service="deepseek",
                    response_format="json_object",
                    temperature=0.1
                )
                return tag_info
            except Exception as e:
                logger.error(f"LLM调用出错 (尝试 {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    logger.info(f"等待 {self.retry_wait} 秒后重试...")
                    time.sleep(self.retry_wait)
                    self.retry_wait *= 2  # 指数退避
                else:
                    logger.error("达到最大重试次数，返回默认标签")
                    return {
                        "主要领域": "RL" if "reinforcement" in summary.lower() else "NLP",
                        "标签": ["research", "/unread"]
                    }

    def _post_process(self, arxiv_result, hf_obj=None):
        """对ArXiv结果进行后处理，生成摘要、标签等信息"""
        summary = arxiv_result.summary.replace('\n', ' ').replace('  ', ' ')
        _id = arxiv_result.entry_id.split('/')[-1]
        cache_obj = {
            'id': _id,
            'title': arxiv_result.title,
            'pdf_url': arxiv_result.pdf_url
        }
        if hf_obj is not None:
            cache_obj['media_type'] = hf_obj['media_type']
            cache_obj['media_url'] = hf_obj['media_url']

        cache_filename = os.path.join(self.cache_dir, f"{_id}.json")
        if os.path.exists(cache_filename):
            logger.info(f'找到缓存文件 {cache_filename}, 正在加载...')
            try:
                with open(cache_filename, 'r', encoding='utf-8') as f:
                    cache_obj = json.load(f)
                logger.info('缓存内容加载成功')
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"读取缓存文件出错: {e}")
                logger.info("使用新的缓存对象")

        # 处理TLDR和标签
        self._process_tldr(summary, cache_obj, cache_filename)
        self._process_tag_info(summary, cache_obj, cache_filename)

        # 创建格式化对象
        ret = FormattedArxivObj(
            id=_id,
            title=arxiv_result.title,
            authors=[author.name for author in arxiv_result.authors],
            published_dt=arxiv_result.published.strftime('%Y-%m'),
            summary=summary,
            
            # 使用 .get() 方法避免 KeyError
            summary_cn=cache_obj.get('summary_cn', ''),
            short_summary=cache_obj.get('short_summary', ''),
            pdf_url=arxiv_result.pdf_url,
            
            tldr=cache_obj.get('tldr', {}),
            raw_tldr=cache_obj.get('raw_tldr', ''),
            
            # 安全获取 'tag_info' 中的 '主要领域' 和 '标签'
            category=cache_obj.get('tag_info', {}).get('主要领域', ''),
            tags=cache_obj.get('tag_info', {}).get('标签', []),
            
            arxiv_result=arxiv_result,
            
            # 处理 hf_obj 为 None 的情况
            media_type='' if hf_obj is None else hf_obj.get('media_type', ''),
            media_url='' if hf_obj is None else hf_obj.get('media_url', ''),
            
            journal_ref=arxiv_result.journal_ref if hasattr(arxiv_result, 'journal_ref') else None,
            doi=arxiv_result.doi if hasattr(arxiv_result, 'doi') else None,
            arxiv_categories=arxiv_result.categories if hasattr(arxiv_result, 'categories') else []
        )
        
        logger.info(f'保存缓存到 {cache_filename}')
        try:
            json.dump(cache_obj, open(cache_filename, 'w'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存文件时出错: {e}")
            backup_filename = cache_filename + ".backup"
            logger.info(f"尝试保存到备份文件: {backup_filename}")
            json.dump(cache_obj, open(backup_filename, 'w'), ensure_ascii=False, indent=2)
            
        return ret

    def find_by_id(self, id_or_idlist, hf_obj=None, format_result=True) -> Union[FormattedArxivObj, arxiv.Result]:
        """通过ID查找论文"""
        cache_filename = os.path.join(self.cache_dir, f'{id_or_idlist}.pkl')
        
        # 尝试从缓存加载
        if os.path.exists(cache_filename):
            logger.info(f"缓存命中: {cache_filename}")
            try:
                with open(cache_filename, 'rb') as f:
                    result = pickle.load(f)
            except Exception as e:
                logger.error(f"读取缓存出错: {e}，重新获取数据")
                result = self._fetch_arxiv_result(id_or_idlist)
        else:
            result = self._fetch_arxiv_result(id_or_idlist)
            
        # 保存到缓存
        try:
            with open(cache_filename, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            logger.error(f"保存缓存文件时出错: {e}")
            
        logger.info(f"标题: {result.title}")
        logger.info(f"作者: {', '.join(author.name for author in result.authors)}")
        logger.info(f"发布日期: {result.published.strftime('%Y-%m')}")
        
        return self._post_process(result, hf_obj) if format_result else result
        
    def _fetch_arxiv_result(self, id_or_idlist):
        """从ArXiv API获取论文数据，包含重试机制"""
        logger.info(f"从ArXiv获取论文: {id_or_idlist}")
        
        # 准备ID列表
        if isinstance(id_or_idlist, list):
            id_list = id_or_idlist
        else:
            id_list = [id_or_idlist]
            
        # 添加重试逻辑
        retry_count = 0
        max_retries = self.max_retries
        retry_wait = self.retry_wait
        
        while retry_count < max_retries:
            try:
                search = arxiv.Search(id_list=id_list)
                results = list(self.client.results(search))
                
                if not results:
                    raise Exception(f"ArXiv没有返回结果: {id_list}")
                    
                return results[0]  # 返回第一个结果
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"ArXiv API请求失败 (尝试 {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"等待 {retry_wait} 秒后重试...")
                    time.sleep(retry_wait)
                    retry_wait *= 2  # 指数退避
                else:
                    logger.error(f"达到最大重试次数，抛出异常")
                    raise

    def smart_find(self, title_or_id, format_result=False):
        """
        根据标题或论文id自动查找
        :param title_or_id:
        :param format_result:
        :return:
        """
        if re.match('\d{4}.*', title_or_id) is not None:
            logger.info('使用find_by_id函数')
            return self.find_by_id(title_or_id, format_result=format_result)
        logger.info('使用search_by_title函数')
        return self.search_by_title(title_or_id, format_result=format_result)

    def search_by_title(self, title, limit=10, format_result=True) -> Union[List[FormattedArxivObj], List[arxiv.Result]]:
        """通过标题搜索论文"""
        data = []
        
        logger.info(f"通过标题搜索论文: '{title}'")
        
        # 添加重试逻辑
        retry_count = 0
        max_retries = self.max_retries
        retry_wait = self.retry_wait
        
        while retry_count < max_retries:
            try:
                search = arxiv.Search(query=f'ti:"{title}"', max_results=limit)
                search_results = self.client.results(search)
                
                for result in search_results:
                    logger.info(f"标题: {result.title}")
                    logger.info(f"作者: {', '.join(author.name for author in result.authors)}")
                    logger.info(f"发布日期: {result.published.strftime('%Y-%m')}")
                    data.append(result)
                    if len(data) >= limit:
                        break
                        
                break  # 成功获取结果，跳出重试循环
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"ArXiv API请求失败 (尝试 {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"等待 {retry_wait} 秒后重试...")
                    time.sleep(retry_wait)
                    retry_wait *= 2  # 指数退避
                else:
                    logger.error(f"达到最大重试次数，返回空列表")
        
        return [self._post_process(item) for item in data] if format_result else data

    @classmethod
    def download_pdf(cls, obj: Union[FormattedArxivObj, arxiv.Result], save_dir: str):
        """下载论文PDF"""
        # 两种类都有这个属性
        title = obj.title
        filename = f"{title}.pdf"
        
        # 移除文件名中的非法字符
        for ch in ('?', '/', ':', '\\', '*', '"', '<', '>', '|'):
            filename = filename.replace(ch, '_')
            
        # 防止文件名过长
        if len(filename) > 150:
            filename = filename[:147] + "..."
            
        path = os.path.join(save_dir, filename)
        
        # 添加重试逻辑
        max_retries = 3
        retry_wait = 2
        
        for attempt in range(max_retries):
            try:
                written_path, _ = urlretrieve(obj.pdf_url, path)
                logger.info(f"论文 '{title}' 已下载到 {written_path}")
                return written_path
            except Exception as e:
                logger.warning(f"下载PDF失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_wait} 秒后重试...")
                    time.sleep(retry_wait)
                    retry_wait *= 2  # 指数退避
                else:
                    logger.error(f"达到最大重试次数，下载失败")
                    raise

    def search_by_keywords(self, keywords, categories=None, limit=10, format_result=True) -> Union[List[FormattedArxivObj], List[arxiv.Result]]:
        """通过关键词和分类搜索论文"""
        data = []

        # 构建查询字符串
        query_parts = []

        # 处理关键词
        if keywords:
            if isinstance(keywords, list):
                # 如果关键字是列表，构建一个查询，确保所有关键字都存在
                keyword_query_parts = []
                for keyword in keywords:
                    if isinstance(keyword, list):
                        # 处理嵌套的关键字列表，使用 OR 连接
                        sub_parts = [f'(ti:"{kw}" OR abs:"{kw}")' for kw in keyword]
                        keyword_query_parts.append('(' + ' OR '.join(sub_parts) + ')')
                    else:
                        keyword_query_parts.append(f'(ti:"{keyword}" OR abs:"{keyword}")')
                query_parts.append(' AND '.join(keyword_query_parts))
            else:
                # 如果关键字是字符串，在标题或摘要中搜索该短语
                query_parts.append(f'(ti:"{keywords}" OR abs:"{keywords}")')

        # 处理分类
        if categories:
            if isinstance(categories, list):
                # 修正分类格式: 直接列出多个分类
                category_query = ' OR '.join([f'cat:{cat}' for cat in categories])
                query_parts.append('(' + category_query + ')')
            else:
                # 如果分类是字符串
                query_parts.append(f'cat:{categories}')

        # 将所有查询部分组合在一起
        query = ' AND '.join(query_parts)

        logger.info(f"构建的查询：{query}")

        # 添加重试逻辑
        retry_count = 0
        max_retries = self.max_retries
        retry_wait = self.retry_wait
        
        while retry_count < max_retries:
            try:
                search = arxiv.Search(
                    query=query,
                    max_results=limit,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )
                
                search_results = self.client.results(search)
                for result in search_results:
                    logger.info(f"标题：{result.title}")
                    logger.info(f"作者：{', '.join(author.name for author in result.authors)}")
                    logger.info(f"发布日期：{result.published.strftime('%Y-%m')}")
                    data.append(result)
                    if len(data) >= limit:
                        break
                        
                break  # 成功获取结果，跳出重试循环
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"ArXiv API请求失败 (尝试 {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"等待 {retry_wait} 秒后重试...")
                    time.sleep(retry_wait)
                    retry_wait *= 2  # 指数退避
                else:
                    logger.error(f"达到最大重试次数，返回空列表")
        
        return [self._post_process(item) for item in data] if format_result else data
"""
 Modified by Xiaodong Zheng on 2024/9/20
"""
import json
import os
import pickle
import re
import copy
import sys
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

    def _process_tldr(self, summary, cache_obj, cache_filename):
        logger.info(f"processing tldr for {cache_obj['id']}")

        keys = ('动机', '方法', '结果', 'remark')
        
        if 'tldr' in cache_obj and all([key in cache_obj['tldr'] and cache_obj['tldr'][key].strip() != '' for key in keys]):
            logger.info(f"processing tldr found cache")
            return
        # 检查是否有缓存
        if 'raw_tldr' in cache_obj and cache_obj['raw_tldr'].strip() != '':
            tldr = json.loads(cache_obj['raw_tldr'])
        else:
            prmpt = f'''下面这段话（<summary></summary>之间的部分）是一篇论文的摘要。
            请基于摘要信息总结论文的动机、方法、结果、remark、翻译、short_summary等信息，, 其中remark请你用不超过15个英文字符总结
            该文章的领域,如果有算法请将算法放到前面，如"LQR/多智能体控制"，其中“翻译”将整个摘要内容使用中文进行翻译，
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
            tldr = llm_service.chat(
                prompt=prmpt,
                response_format='json_object' 
                )
            cache_obj['raw_tldr'] = json.dumps(tldr) # 保存成字符串格式
        if 'tldr' not in cache_obj:
            cache_obj['tldr'] = {}
        cache_obj['tldr'].update(tldr)
        for key in keys:
            if key not in cache_obj['tldr']:
                logger.warning(f"{key} not in tldr")
                cache_obj['tldr'][key] = ''
                
        if '翻译' in cache_obj['tldr']:
            cache_obj['summary_cn'] = cache_obj['tldr']['翻译']
        if 'short_summary' in cache_obj['tldr']:
            cache_obj['short_summary'] = cache_obj['tldr']['short_summary']
        json.dump(cache_obj, open(cache_filename, 'w'), ensure_ascii=False, indent=2)

    def _process_summary(self, summary, cache_obj, cache_filename):
        logger.info(f"processing summary for {cache_obj['id']}")
        if 'summary_cn' in cache_obj:
            logger.info(f"processing summary found cache")
            return
        prompt = f"""这段话是一篇论文的摘要，请你使用中文进行翻译：\n{summary}"""
        summary_cn = llm_service.chat(prompt=prompt)
        cache_obj['summary_cn'] = summary_cn
        json.dump(cache_obj, open(cache_filename, 'w'), ensure_ascii=False, indent=2)
        
    # def _process_short_summary(self, summary, cache_obj, cache_filename):
    #     logger.info(f"processing short summary for {cache_obj['id']}")
    #     if 'short_summary' in cache_obj:
    #         logger.info(f"processing short summary found cache")
    #         return
        
    #     # 调用 llm_service.chat，返回的可能是列表或其他格式，确保转换为字符串
    #     prompt = f"""这段话是一篇论文的摘要，请你使用中文用进行不超过50字的主题简介,
    #                                      注意不要使用任何的markdown格式标点符号，
    #                                      也不要写任何的公式：\n {summary} \n"""
    #     short_summary = llm_service.chat(prompt=prompt)
        
    #     # 将结果保存到缓存对象并写入文件
    #     cache_obj['short_summary'] = short_summary
    #     json.dump(cache_obj, open(cache_filename, 'w'), ensure_ascii=False, indent=2)

    def _process_tag_info(self, summary, cache_obj, cache_filename):
        logger.info(f"processing tag info for {cache_obj['id']}")

        keys = ('主要领域', '标签')
        if 'tag_info' in cache_obj and all([key in cache_obj['tag_info'] for key in keys]):
            logger.info(f"processing tags info found cache")
            return
        # ```json
        # {
        #   "主要领域": "NLP",
        #   "标签": [
        #     "instruction-tuning",
        #     "language models",
        #     "training data selection",
        #     "learning percentage",
        #     "data hardness",
        #     "model sizes",
        #     "OPT",
        #     "Llama-2"
        #   ]
        # }
        # ```
        if 'tag_info_raw' in cache_obj and cache_obj['tag_info_raw'].strip() != '':
            tag_info = cache_obj['tag_info_raw']
        else:
            prompt = f"""
                        以下是论文摘要内容：\n {summary}\n

                        请参考论文摘要内容，判断该论文的主要研究领域（例如RL、MTS、NLP、多模态、CV、MARL、LLM等）概括的结果
                        填写在"主要领域"键后，请你尽量使用英文专业名词的简写。
                        同时根据摘要内容总结出最多10个高度概括文章主题的tags,以list的形式填写在"标签"键后，并在最后一定加入一个"/unread"标签。
                        请你一定注意，"主要领域" 只能有一个，"标签" 内容的数量则可以有多个，
                        并使用以下**JSON**格式回复：
                        {{
                        "主要领域": "LLM",
                        "标签": [
                            "instruction-tuning",
                            "language models",
                            "training data selection",
                            "learning percentage",
                            "data hardness",
                            "Reinforcement Learning",
                            "/unread",
                        ]
                        }}
                        """
            # 调用大模型
            tag_info =llm_service.chat(prompt,service="kimi",response_format="json_object",temperature=0.1)
            # 将结果保存到缓存对象并写入文件
            cache_obj['tag_info_raw'] = json.dumps(tag_info)
            
        if 'tag_info' not in cache_obj:
            cache_obj['tag_info'] = {}

        print(f"taginfo is : ############# {type(tag_info)}")
        #更新cache_obj['tag_info']
        cache_obj['tag_info'].update(tag_info)
        # print(f"taginfo is : ############# {cache_obj['tag_info']}")

        json.dump(cache_obj, open(cache_filename, 'w'), ensure_ascii=False, indent=2)

    def _post_process(self, arxiv_result, hf_obj=None):
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
            logger.info(f'找到缓存 {cache_filename}, 加载中 ...')
            cache_obj = json.load(open(cache_filename))
            logger.info('缓存内容为：')
            logger.info(json.dumps(cache_obj, ensure_ascii=False, indent=2))

        self._process_tldr(summary, cache_obj, cache_filename)
        # self._process_summary(summary, cache_obj, cache_filename)
        # self._process_short_summary(summary,cache_obj, cache_filename)
        self._process_tag_info(summary, cache_obj, cache_filename)

        ret = FormattedArxivObj(
            id=_id,
            title=arxiv_result.title,
            authors=[author.name for author in arxiv_result.authors],
            published_dt=arxiv_result.published.strftime('%Y-%m'),
            summary=summary,
            
            # 使用 .get() 方法避免 KeyError
            summary_cn=cache_obj.get('summary_cn', ''),  # 缺少时返回空字符串
            short_summary=cache_obj.get('short_summary', ''),  # 缺少时返回空字符串
            pdf_url=arxiv_result.pdf_url,
            
            tldr=cache_obj.get('tldr', {}),  # 缺少时返回空字典
            raw_tldr=cache_obj.get('raw_tldr', ''),  # 缺少时返回空字符串
            
            # 安全获取 'tag_info' 中的 '主要领域' 和 '标签'
            category=cache_obj.get('tag_info', {}).get('主要领域', ''),  # 缺少时返回空字符串
            tags=cache_obj.get('tag_info', {}).get('标签', []),  # 缺少时返回空列表
            
            arxiv_result=arxiv_result,
            
            # 处理 hf_obj 为 None 的情况
            media_type='' if hf_obj is None else hf_obj.get('media_type', ''),
            media_url='' if hf_obj is None else hf_obj.get('media_url', ''),
            
            journal_ref=arxiv_result.journal_ref,
            doi=arxiv_result.doi,
            arxiv_categories=arxiv_result.categories
        )
        logger.info(f'saving cache_obj to {cache_filename}')
        json.dump(cache_obj, open(cache_filename, 'w'), ensure_ascii=False, indent=2)
        return ret

    def find_by_hf_obj(self, hf_obj):
        return self.find_by_id(hf_obj['id'], hf_obj)

    def find_by_id(self, id_or_idlist, hf_obj=None, format_result=True) -> Union[FormattedArxivObj, arxiv.Result]:
        cache_filename = os.path.join(self.cache_dir, f'{id_or_idlist}.pkl')
        if os.path.exists(cache_filename):
            logger.info(f"find_by_id cache hit at {cache_filename}")
            result = pickle.load(open(cache_filename, 'rb'))
        else:
            result = next(self.client.results(arxiv.Search(id_list=id_or_idlist if isinstance(id_or_idlist, list) else [id_or_idlist])))
        # result = next(self.client.results(arxiv.Search(id_list=id_or_idlist if isinstance(id_or_idlist, list) else [id_or_idlist])))
        pickle.dump(result, open(cache_filename, 'wb'))
        logger.info(f"Title: {result.title}")
        logger.info(f"Authors: {', '.join(author.name for author in result.authors)}")
        logger.info(f"Publish Date: {result.published.strftime('%Y-%m')}")
        return self._post_process(result, hf_obj) if format_result else result

    def smart_find(self, title_or_id, format_result=False):
        """
        根据标题或论文id自动查找
        :param title_or_id:
        :param format_result:
        :return:
        """
        if re.match('\d{4}.*', title_or_id) is not None:
            logger.info('using find_by_id function')
            return self.find_by_id(title_or_id, format_result=format_result)
        logger.info('using search_by_title function')
        return self.search_by_title(title_or_id, format_result=format_result)

    def search_by_title(self, title, limit=10, format_result=True) -> Union[List[FormattedArxivObj], List[arxiv.Result]]:
        data = []
        ret = {}
        search = arxiv.Search(query=f'ti:"{title}"')
        search_results = self.client.results(search)
        for result in search_results:
            logger.info(f"Title: {result.title}")
            logger.info(f"Authors: {', '.join(author.name for author in result.authors)}")
            logger.info(f"Publish Date: {result.published.strftime('%Y-%m')}")
            data.append(result)
            if len(data) >= limit:
                break
        return [self._post_process(item) for item in data] if format_result else data

    @classmethod
    def download_pdf(cls, obj: Union[FormattedArxivObj, arxiv.Result], save_dir: str):
        # 两种类都有这个属性
        title = obj.title
        filename = f"{title}.pdf"
        for ch in ('?', '/', ':', '\\'):
            filename = filename.replace(ch, '_')
        # arxiv_result.download_pdf(save_dir, filename=filename)
        path = os.path.join(save_dir, filename)
        written_path, _ = urlretrieve(obj.pdf_url, path)
        logger.info(f"{title} downloaded to {written_path}")

    # 通过关键字查询

    def search_by_keywords(self, keywords, categories=None, limit=10, format_result=True) -> Union[List[FormattedArxivObj], List[arxiv.Result]]:
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
                # 如果分类是列表，使用 OR 连接
                category_query = ' OR '.join([f'cat:{cat}' for cat in categories])
                query_parts.append('(' + category_query + ')')
            else:
                # 如果分类是字符串
                query_parts.append(f'cat:{categories}')

        # 将所有查询部分组合在一起
        query = ' AND '.join(query_parts)

        logger.info(f"构建的查询：{query}")

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
        return [self._post_process(item) for item in data] if format_result else data
    

if __name__ == '__main__':
    print(__file__)

    
    
    
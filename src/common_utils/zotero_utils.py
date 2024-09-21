# 获取特定zotero项目类型的模板JSON数据

import requests
import json

def get_new_item_template(item_type):
    """
    根据给定的itemType发送GET请求，获取模板JSON数据。
    该模板仅限于创建新的Zotero项目使用的data部分
    
    参数:
        item_type (str): 需要查询的项目类型（如 'book'）。
    
    返回:
        dict: 服务器返回的JSON数据。
    """
    # 定义API的URL，使用传入的itemType参数
    url = f'http://api.zotero.org/items/new?itemType={item_type}'
    
    # 定义请求头部，设置 If-Modified-Since
    headers = {
        'If-Modified-Since': 'Mon, 14 Mar 2011 22:30:17 GMT'
    }

    # 发送GET请求
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            # 将JSON数据写入文件
            filename = f'./json_templates/{item_type}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=4)
            print(f"数据已保存到 {filename}")
            return True
        except Exception as e:
            print(f"保存文件时发生错误：{e}")
            return False
    else:
        print(f"请求失败，状态码：{response.status_code}")
        return False

# # 使用示例
# item_type = 'book'
# item_template = get_item_template(item_type)

item_types ={
        "annotation": "注释",
        "artwork": "艺术品",
        "attachment": "附件",
        "audioRecording": "音频",
        "bill": "法案",
        "blogPost": "博客帖子",
        "book": "图书",
        "bookSection": "图书章节",
        "case": "司法案例",
        "computerProgram": "软件",
        "conferencePaper": "会议论文",
        "dataset": "数据集",
        "dictionaryEntry": "词条",
        "document": "文档",
        "email": "电子邮件",
        "encyclopediaArticle": "百科条目",
        "film": "电影",
        "forumPost": "论坛帖子",
        "hearing": "听证会",
        "instantMessage": "即时消息",
        "interview": "采访稿",
        "journalArticle": "期刊文章",
        "letter": "信件",
        "magazineArticle": "杂志文章",
        "manuscript": "手稿",
        "map": "地图",
        "newspaperArticle": "报纸文章",
        "note": "笔记",
        "patent": "专利",
        "podcast": "播客",
        "preprint": "预印本",
        "presentation": "演示文档",
        "radioBroadcast": "电台广播",
        "report": "报告",
        "standard": "标准",
        "statute": "法律",
        "thesis": "学位论文",
        "tvBroadcast": "电视广播",
        "videoRecording": "视频",
        "webpage": "网页"
      }

for item_type in item_types.keys():
    item_template = get_new_item_template(item_type)

# print(item_template)
"""
Modified by: Xiaodong Zheng
"""
import os
from pathlib import Path

from flask import Flask, jsonify, request

import sys

sys.path.append('')

import common_utils
from service.arxiv_visitor import ArxivVisitor
from service.wolai_service import WolaiService
import threading


app = Flask(__name__)

logger = common_utils.get_logger(__name__)

TOKEN= os.environ['WOLAI_TOKEN'] 

output_root = os.path.join(Path(__file__).parent.parent.resolve(), 'output')
os.makedirs(os.path.join(output_root, 'cache'), exist_ok=True)
arxiv_visitor = ArxivVisitor(output_dir=output_root)


@app.route('/api/papers', methods=['GET'])
def search():
    token = request.args.get('token', '')
    if token != TOKEN:
        return {'msg': 'token invalid!'}

    query = request.args.get('query', '')
    query = query.strip()
    if query == '':
        return jsonify({'msg': 'query required!'})
    result = arxiv_visitor.smart_find(query, format_result=False)
    if isinstance(result, list):
        return jsonify(
            {
                'msg': 'success',
                'papers': [{
                    "id": item.entry_id.split('/')[-1],
                    "title": item.title,
                    "authors": ', '.join(author.name for author in item.authors),
                    "publish_dt": item.published.strftime('%Y-%m')
                } for item in result]
            })
    return jsonify({
        'msg': "success",
        'papers': [{
            "id": result.entry_id.split('/')[-1],
            "title": result.title,
            "authors": ', '.join(author.name for author in result.authors),
            "publish_dt": result.published.strftime('%Y-%m')
        }]
    })


def async_download(entry_id, retry_count=3):
    logger.info('async thread started!')
    formatted_arxiv_obj = arxiv_visitor.find_by_id(entry_id, format_result=True)
    wolai_service = WolaiService()

    os.makedirs('papers', exist_ok=True)

    def do_download():
        arxiv_visitor.download_pdf(formatted_arxiv_obj, 'Papers')
        resp = wolai_service.insert(formatted_arxiv_obj)
        logger.info(resp)
        common_utils.send_slack(f'论文《{formatted_arxiv_obj.title}》下载完成！', '深度学习研究')

    while retry_count > 0:
        try:
            do_download()
            return
        except Exception as e:
            logger.error(e)
            retry_count -= 1

    common_utils.send_slack(f'论文《{formatted_arxiv_obj.title}》下载失败, {e}', '深度学习研究')


@app.route('/api/papers/<entry_id>/basic_info', methods=['GET'])
def get_basic_info(entry_id):
    token = request.args.get('token', '')
    if token != TOKEN:
        return {'msg': 'token invalid!'}

    result = arxiv_visitor.find_by_id(entry_id, format_result=False)
    return jsonify({
        'msg': "success",
        'paper': {
            "id": result.entry_id.split('/')[-1],
            "title": result.title,
            "authors": ', '.join(author.name for author in result.authors),
            "publish_dt": result.published.strftime('%Y-%m'),
            "summary": result.summary
        }
    })


@app.route('/api/papers/<entry_id>/details', methods=['GET'])
def get_details(entry_id):
    token = request.args.get('token', '')
    if token != TOKEN:
        return {'msg': 'token invalid!'}

    result = arxiv_visitor.find_by_id(entry_id, format_result=True)
    return jsonify({
        'msg': "success",
        'paper': {
            "id": result.id,
            "title": result.title,
            "authors": result.authors,
            "publish_dt": result.published_dt,
            "summary": result.summary,
            "summary_cn": result.summary_cn,
            "动机": result.tldr.get('动机', ''),
            "方法": result.tldr.get("方法", ''),
            "结果": result.tldr.get('结果', ''),
            "category": result.category,
            "tags": result.tags
        }
    })


@app.route('/api/papers/<entry_id>/download', methods=['GET'])
def download(entry_id):
    token = request.args.get('token', '')
    if token != TOKEN:
        return {'msg': 'token invalid!'}

    thread = threading.Thread(target=async_download, args=(entry_id,))
    thread.start()

    return jsonify({
        'msg': "success"
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)

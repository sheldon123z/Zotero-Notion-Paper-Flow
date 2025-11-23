#!/usr/bin/env python3
"""
命令行工具入口
"""
import click
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import main as run_main, setup_logging, PROJECT_ROOT
from config.settings import Settings
from services.llm import LLMServiceFactory

logger = setup_logging()

@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Zotero-Notion-Paper-Flow 命令行工具"""
    pass

@cli.command()
@click.option('--keywords', '-k', multiple=True, help='搜索关键词')
@click.option('--categories', '-c', multiple=True, help='ArXiv分类')
@click.option('--limit', '-l', default=10, help='搜索结果限制')
@click.option('--date', '-d', help='指定日期 (YYYY-MM-DD)')
@click.option('--days', type=int, help='处理过去N天')
@click.option('--config', type=click.Path(exists=True), help='配置文件')
@click.option('--download-pdf/--no-download-pdf', default=False, help='是否下载PDF')
@click.option('--no-hf', is_flag=True, help='跳过HuggingFace')
@click.option('--no-arxiv', is_flag=True, help='跳过ArXiv搜索')
def run(**kwargs):
    """运行论文抓取和同步"""
    # 转换参数格式并调用main
    import argparse
    args = argparse.Namespace(**kwargs)

    # 调用主函数逻辑
    click.echo("开始运行论文抓取...")
    run_main()

@cli.command()
@click.option('--service', '-s', default='deepseek',
              type=click.Choice(['deepseek', 'kimi', 'zhipu']),
              help='LLM服务')
@click.argument('text')
def summarize(service, text):
    """使用LLM生成摘要"""
    try:
        llm = LLMServiceFactory.create(service)
        result = llm.generate_summary(text)

        click.echo("\n=== 摘要结果 ===")
        for key, value in result.items():
            if value:
                click.echo(f"{key}: {value}")
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)

@cli.command()
def list_services():
    """列出可用的服务"""
    from services.llm import LLMServiceFactory
    from services.data_sources import DataSourceFactory
    from services.storage import StorageFactory

    click.echo("\n=== LLM服务 ===")
    for service in LLMServiceFactory.get_available_services():
        click.echo(f"  - {service}")

    click.echo("\n=== 数据源 ===")
    for source in DataSourceFactory.get_available_sources():
        click.echo(f"  - {source}")

    click.echo("\n=== 存储服务 ===")
    for storage in StorageFactory.get_available_storages():
        click.echo(f"  - {storage}")

@cli.command()
@click.argument('config_path', type=click.Path())
def init_config(config_path):
    """生成默认配置文件"""
    import json

    default_config = {
        "keywords": ["reinforcement learning"],
        "categories": ["cs.LG", "cs.AI"],
        "date": None,
        "proxy": "http://127.0.0.1:7890",
        "services": {
            "notion": True,
            "zotero": True,
            "wolai": False
        },
        "llm": {
            "service": "deepseek"
        },
        "download_pdf": False,
        "pdf_dir": "papers/pdf",
        "search_limit": 20,
        "retries": 3,
        "category_map": {
            "RL": ["DXU9QIKA", "DFGZNVCM"],
            "NLP": ["WXBCJ969", "DFGZNVCM"],
            "LLM": ["WXBCJ969", "DFGZNVCM"]
        },
        "default_category": ["DFGZNVCM"]
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)

    click.echo(f"配置文件已生成: {config_path}")

if __name__ == '__main__':
    cli()

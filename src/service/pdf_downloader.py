def download_paper_pdfs(arxiv_ids, output_dir=None, arxiv_visitor=None):
    """
    下载指定论文ID的PDF文件
    
    参数:
        arxiv_ids: 字符串或字符串列表，包含ArXiv论文ID
        output_dir: 字符串，PDF保存目录，默认为'output/papers'
        arxiv_visitor: ArxivVisitor实例，如果为None则创建新实例
        
    返回:
        成功下载的PDF文件路径列表
    """
    import os
    import logging
    from pathlib import Path
    import traceback
    
    logger = logging.getLogger(__name__)
    
    # 确保arxiv_ids是列表形式
    if isinstance(arxiv_ids, str):
        arxiv_ids = [arxiv_ids]
    
    # 设置默认输出目录
    if output_dir is None:
        project_root = Path(__file__).parent.parent.resolve()
        output_dir = os.path.join(project_root, 'output', 'papers')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 如果没有提供ArxivVisitor实例，创建一个新的
    if arxiv_visitor is None:
        from service.arxiv_visitor import ArxivVisitor
        arxiv_visitor = ArxivVisitor(output_dir=os.path.join(project_root, 'output'))
    
    # 存储成功下载的PDF路径
    downloaded_paths = []
    
    # 遍历论文ID列表
    for paper_id in arxiv_ids:
        try:
            logger.info(f"获取论文信息: {paper_id}")
            # 获取论文信息
            paper_obj = arxiv_visitor.find_by_id(paper_id, format_result=False)
            
            logger.info(f"开始下载PDF: {paper_id}, 标题: {paper_obj.title}")
            # 下载PDF
            pdf_path = arxiv_visitor.download_pdf(paper_obj, output_dir)
            
            logger.info(f"PDF下载成功: {pdf_path}")
            downloaded_paths.append(pdf_path)
            
        except Exception as e:
            logger.error(f"下载PDF时出错 ({paper_id}): {e}")
            logger.debug(traceback.format_exc())
    
    return downloaded_paths
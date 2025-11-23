"""
服务模块 - 已弃用，请使用 src/services/

此模块保留用于向后兼容，所有类已重定向到兼容层。
"""
import warnings

warnings.warn(
    "src/service 模块已弃用，请使用 src/services/",
    DeprecationWarning,
    stacklevel=2
)

# 从兼容层导入
from compat import (
    ArxivVisitor,
    HFDailyPaperVisitor,
    NotionService,
    ZoteroService,
    ZoteroItemExistsError,
)

# 保持旧的导入路径工作
__all__ = [
    'ArxivVisitor',
    'HFDailyPaperVisitor',
    'NotionService',
    'ZoteroService',
    'ZoteroItemExistsError',
]

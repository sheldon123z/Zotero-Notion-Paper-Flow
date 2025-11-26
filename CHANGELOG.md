# 更新日志 | Changelog

本文档记录项目的所有重要更改。

All notable changes to this project will be documented in this file.

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### 计划中 | Planned
- Ollama 本地模型支持
- 微信通知功能
- Google Scholar 数据源
- 高级学科分类

---

## [2.0.0] - 2025-04-22

### 新增 | Added
- **新架构**: 引入依赖注入和接口抽象
  - `ServiceContainer` 管理服务实例
  - `DataSourceInterface`、`StorageInterface`、`LLMInterface` 抽象接口
  - 策略模式支持 LLM 服务动态切换
  - 工厂模式创建各类服务
- **配置管理**: 使用 `Settings` dataclass 管理配置
- **新服务实现**:
  - `services/llm/`: Kimi、DeepSeek、Zhipu LLM 服务
  - `services/data_sources/`: ArXiv、HuggingFace 数据源
  - `services/storage/`: Notion、Zotero 存储服务
- **新数据模型**: `models/paper.py` 替代旧的 `FormattedArxivObj`
- **CLI 工具**: 新增 `cli.py` 命令行接口
- **兼容层**: `compat.py` 支持旧代码平滑迁移
- **迁移指南**: `MIGRATION.md` 详细说明架构迁移步骤
- **CI/CD**: GitHub Actions 工作流
  - 代码风格检查 (Ruff, Flake8)
  - 类型检查 (mypy)
  - 单元测试 (多 Python 版本)
  - 测试覆盖率报告
  - 安全漏洞扫描 (Safety, Bandit)

### 变更 | Changed
- 重构项目目录结构
- 统一日志记录格式
- 改进错误处理和重试机制

### 文档 | Documentation
- 新增英文 README (`README_EN.md`)
- 新增贡献指南 (`CONTRIBUTING.md`)
- 新增架构文档 (`docs/architecture.md`)
- 新增 API 文档 (`docs/api.md`)
- 新增故障排除指南 (`docs/troubleshooting.md`)

---

## [1.5.0] - 2025-04-21

### 新增 | Added
- arXiv 分类搜索功能
- 按分类文件夹插入 Zotero
- `category_map` 配置支持论文分类到 Zotero Collection 的映射
- 配置文件 `config.json` 支持

### 变更 | Changed
- 增强命令行参数解析
- 改进 PDF 下载功能

---

## [1.4.0] - 2025-02-15

### 新增 | Added
- Wolai API 集成
- 论文标签自动生成
- 中文摘要翻译功能

### 修复 | Fixed
- 修复 Notion API 速率限制问题
- 修复论文重复处理问题

---

## [1.3.0] - 2024-12-01

### 新增 | Added
- Zotero API 集成
- 论文 Extra 字段 LLM 智能总结
- Slack 通知功能

### 变更 | Changed
- 重构 LLM 服务支持多提供商

---

## [1.2.0] - 2024-10-15

### 新增 | Added
- HuggingFace Daily Papers 页面解析
- 论文截图支持
- 检查点机制避免重复处理

---

## [1.1.0] - 2024-09-20

### 新增 | Added
- LLM 摘要解析 (动机、方法、结果)
- 论文 TLDR 生成
- Notion 详情页自动创建

### 变更 | Changed
- 重构 ArxivVisitor 类

---

## [1.0.0] - 2024-08-01

### 新增 | Added
- 初始版本发布
- arXiv API 集成
- Notion API 集成
- 基础命令行界面
- 定时调度支持

---

## 版本说明 | Version Notes

### 主版本号 (Major)
- 不兼容的 API 修改

### 次版本号 (Minor)
- 新增功能（向后兼容）

### 修订号 (Patch)
- Bug 修复（向后兼容）

---

[Unreleased]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v1.5.0...v2.0.0
[1.5.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/releases/tag/v1.0.0

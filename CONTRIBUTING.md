# 贡献指南 | Contributing Guide

[中文](#中文) | [English](#english)

---

## 中文

感谢您对 Zotero-Notion-Paper-Flow 项目的关注！我们欢迎各种形式的贡献。

### 如何贡献

#### 报告问题

如果您发现了 bug 或有功能建议，请通过 [GitHub Issues](https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/issues) 提交：

1. **搜索现有 Issue**：在创建新 Issue 之前，请先搜索是否已有类似问题
2. **提供详细信息**：
   - 问题描述
   - 复现步骤
   - 期望行为 vs 实际行为
   - 运行环境（OS、Python 版本等）
   - 相关日志或截图

#### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Zotero-Notion-Paper-Flow.git
   cd Zotero-Notion-Paper-Flow
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-fix-name
   ```

3. **安装开发依赖**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov ruff mypy
   ```

4. **进行修改**
   - 遵循项目的代码风格
   - 添加必要的测试
   - 更新相关文档

5. **运行测试**
   ```bash
   # 运行所有测试
   pytest tests/ -v

   # 运行代码风格检查
   ruff check src/

   # 运行类型检查
   mypy src/ --ignore-missing-imports
   ```

6. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   # 或
   git commit -m "fix: 修复问题描述"
   ```

7. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   然后在 GitHub 上创建 Pull Request。

### 代码规范

#### Python 代码风格

- 遵循 PEP 8 规范
- 使用有意义的变量名和函数名
- 添加适当的类型注解
- 为公共函数和类添加文档字符串

```python
def process_paper(paper_id: str, options: dict = None) -> FormattedArxivObj:
    """
    处理单篇论文。

    Args:
        paper_id: arXiv 论文 ID
        options: 可选的处理选项

    Returns:
        FormattedArxivObj: 格式化的论文对象

    Raises:
        ValueError: 当 paper_id 格式无效时
    """
    pass
```

#### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整（不影响功能）
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: 添加 Ollama 本地模型支持
fix: 修复 Zotero 重复插入问题
docs: 更新 API 文档
```

### 项目结构

添加新功能时，请遵循现有的项目结构：

```
src/
├── services/           # 服务实现
│   ├── llm/           # LLM 服务
│   ├── data_sources/  # 数据源
│   └── storage/       # 存储服务
├── interfaces/        # 抽象接口
├── models/           # 数据模型
└── config/          # 配置管理
```

#### 添加新的 LLM 服务

1. 在 `src/services/llm/` 下创建新文件
2. 继承 `BaseLLMService` 类
3. 在工厂类中注册新服务

```python
# src/services/llm/my_llm.py
from .base import BaseLLMService

class MyLLMService(BaseLLMService):
    def get_service_name(self) -> str:
        return "my_llm"

    def chat(self, prompt: str, **kwargs) -> str:
        # 实现聊天逻辑
        pass
```

#### 添加新的数据源

1. 在 `src/services/data_sources/` 下创建新文件
2. 继承 `BaseDataSource` 类
3. 实现必要的方法

### 测试指南

- 为新功能编写单元测试
- 测试文件放在 `tests/` 目录下
- 使用 pytest 框架
- 目标：保持代码覆盖率 > 70%

```python
# tests/unit/test_my_feature.py
import pytest
from src.services.llm.my_llm import MyLLMService

def test_my_llm_service():
    service = MyLLMService()
    assert service.get_service_name() == "my_llm"
```

### 文档贡献

- 文档使用 Markdown 格式
- 中英文文档都需要更新
- API 文档在 `docs/api.md`
- 确保示例代码可以正常运行

---

## English

Thank you for your interest in Zotero-Notion-Paper-Flow! We welcome all forms of contributions.

### How to Contribute

#### Reporting Issues

If you find a bug or have a feature suggestion, please submit via [GitHub Issues](https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/issues):

1. **Search existing issues** before creating a new one
2. **Provide detailed information**:
   - Problem description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, Python version, etc.)
   - Relevant logs or screenshots

#### Submitting Code

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Zotero-Notion-Paper-Flow.git
   cd Zotero-Notion-Paper-Flow
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov ruff mypy
   ```

4. **Make your changes**
   - Follow the project's code style
   - Add necessary tests
   - Update relevant documentation

5. **Run tests**
   ```bash
   # Run all tests
   pytest tests/ -v

   # Run linting
   ruff check src/

   # Run type checking
   mypy src/ --ignore-missing-imports
   ```

6. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

### Code Standards

#### Python Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add appropriate type annotations
- Include docstrings for public functions and classes

#### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `style:` Code formatting (no functional changes)
- `refactor:` Code refactoring
- `test:` Test related
- `chore:` Build/tooling related

### Testing Guidelines

- Write unit tests for new features
- Place test files in `tests/` directory
- Use pytest framework
- Target: maintain code coverage > 70%

### Documentation Contributions

- Documentation uses Markdown format
- Update both Chinese and English docs when applicable
- API documentation is in `docs/api.md`
- Ensure example code runs correctly

---

## 行为准则 | Code of Conduct

请在参与本项目时保持友善和尊重。我们致力于创建一个开放、包容的社区。

Please be kind and respectful when participating in this project. We are committed to creating an open and inclusive community.

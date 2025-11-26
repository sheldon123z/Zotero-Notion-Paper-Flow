# 故障排除指南 | Troubleshooting Guide

本文档列出常见问题及其解决方案。

## 目录

- [安装问题](#安装问题)
- [API 连接问题](#api-连接问题)
- [LLM 服务问题](#llm-服务问题)
- [数据源问题](#数据源问题)
- [存储服务问题](#存储服务问题)
- [代理问题](#代理问题)
- [日志和调试](#日志和调试)

---

## 安装问题

### 依赖安装失败

**问题**: `pip install -r requirements.txt` 失败

**解决方案**:

1. 确保 Python 版本 >= 3.9
   ```bash
   python --version
   ```

2. 升级 pip
   ```bash
   pip install --upgrade pip
   ```

3. 使用国内镜像 (中国用户)
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

4. 如果特定包安装失败，尝试单独安装
   ```bash
   pip install arxiv
   pip install openai
   ```

### 模块导入错误

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:

1. 确保在项目根目录运行
   ```bash
   cd /path/to/Zotero-Notion-Paper-Flow
   ```

2. 安装项目包
   ```bash
   pip install -e .
   ```

3. 检查 PYTHONPATH
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

---

## API 连接问题

### 连接超时

**问题**: `requests.exceptions.Timeout` 或 `Connection timed out`

**解决方案**:

1. 检查网络连接
   ```bash
   ping api.deepseek.com
   ping api.notion.com
   ```

2. 配置代理 (如果在中国大陆)
   ```bash
   export HTTP_PROXY="http://127.0.0.1:7890"
   export HTTPS_PROXY="http://127.0.0.1:7890"
   ```

3. 增加超时时间
   在 `config.json` 中设置:
   ```json
   {
       "retries": 5
   }
   ```

### SSL 证书错误

**问题**: `SSLError` 或 `CERTIFICATE_VERIFY_FAILED`

**解决方案**:

1. 更新 certifi
   ```bash
   pip install --upgrade certifi
   ```

2. 临时禁用 SSL 验证 (不推荐用于生产)
   ```python
   import ssl
   ssl._create_default_https_context = ssl._create_unverified_context
   ```

---

## LLM 服务问题

### API Key 无效

**问题**: `401 Unauthorized` 或 `Invalid API Key`

**解决方案**:

1. 检查环境变量是否正确设置
   ```bash
   echo $DEEPSEEK_API_KEY
   echo $KIMI_API_KEY
   ```

2. 确认 API Key 没有过期

3. 检查 API Key 是否有足够的配额

### 速率限制

**问题**: `429 Too Many Requests` 或 `Rate limit exceeded`

**解决方案**:

1. 减少并发请求
2. 增加请求间隔
3. 在 `config.json` 中减少 `search_limit`
   ```json
   {
       "search_limit": 5
   }
   ```

### JSON 解析错误

**问题**: LLM 返回的 JSON 格式不正确

**解决方案**:

1. 检查日志中的原始响应
2. 重新运行，LLM 可能会给出正确格式
3. 清除缓存后重试
   ```bash
   rm -rf output/cache/*.json
   ```

### 模型不存在

**问题**: `Model not found` 或 `Invalid model`

**解决方案**:

检查模型名称是否正确:
```bash
# DeepSeek
export DEEPSEEK_MODEL="deepseek-chat"

# Kimi
export KIMI_MODEL="moonshot-v1-8k"

# Zhipu
export ZHIPU_MODEL="glm-4"
```

---

## 数据源问题

### arXiv API 错误

**问题**: arXiv 搜索返回空结果或报错

**解决方案**:

1. 检查查询语法
   ```python
   # 正确的分类格式
   categories = ["cs.LG", "cs.AI"]  # 不是 ["csLG", "csAI"]
   ```

2. 检查网络连接到 arxiv.org

3. 等待一段时间后重试 (arXiv 可能有临时限制)

### HuggingFace 页面解析失败

**问题**: 无法获取 HuggingFace Daily Papers

**解决方案**:

1. 检查日期格式
   ```bash
   # 正确格式
   --date 2025-04-21
   ```

2. 确认该日期有论文发布

3. HuggingFace 页面结构可能已更改，检查最新版本

### 论文 ID 无效

**问题**: `ArXiv没有返回结果: xxx`

**解决方案**:

1. 检查论文 ID 格式
   ```
   正确: 2401.00001
   错误: 2401.00001v1, arxiv:2401.00001
   ```

2. 确认论文确实存在于 arXiv

---

## 存储服务问题

### Notion 插入失败

**问题**: Notion API 返回 400 或 404 错误

**解决方案**:

1. 检查 Database ID 是否正确
   ```
   从 Notion URL 获取:
   https://notion.so/xxx?v=yyy
   其中 xxx 就是 Database ID
   ```

2. 确认 Integration 已连接到数据库
   - 打开 Notion 数据库
   - 点击右上角 "..."
   - 选择 "Connect to" -> 你的 Integration

3. 检查数据库属性是否匹配
   - 需要有 "标题"、"日期"、"领域" 等属性

### Zotero 重复插入

**问题**: `ZoteroItemExistsError: 论文已经存在`

**解决方案**:

这是正常行为，系统会自动跳过已存在的论文。如果需要强制更新:

1. 在 Zotero 中手动删除该条目
2. 或者修改代码跳过检查 (不推荐)

### Zotero Collection ID 无效

**问题**: 论文无法插入到指定的 Collection

**解决方案**:

1. 获取正确的 Collection ID:
   - 在 Zotero 网页版中打开 Collection
   - 从 URL 获取 ID: `https://www.zotero.org/xxx/collections/COLLECTION_ID`

2. 更新 `config.json` 中的 `category_map`:
   ```json
   {
       "category_map": {
           "NLP": ["YOUR_COLLECTION_ID"],
           "RL": ["YOUR_COLLECTION_ID_2"]
       }
   }
   ```

### Wolai 认证失败

**问题**: Wolai API 返回认证错误

**解决方案**:

检查所有 Wolai 环境变量:
```bash
export WOLAI_APP_ID="your-app-id"
export WOLAI_APP_SECRETE="your-app-secret"  # 注意拼写
export WOLAI_TOKEN="your-token"
export WOLAI_DB_ID="your-db-id"
```

---

## 代理问题

### 代理连接失败

**问题**: `ProxyError` 或 `Cannot connect to proxy`

**解决方案**:

1. 检查代理服务是否运行
   ```bash
   curl -x http://127.0.0.1:7890 https://www.google.com
   ```

2. 确认代理地址和端口正确

3. 如果不需要代理，在配置中禁用:
   ```json
   {
       "proxy": ""
   }
   ```

   或在代码中:
   ```python
   service = NotionService(create_time=datetime.now(), use_proxy=False)
   ```

### 部分服务需要代理

**问题**: 某些 API 需要代理，某些不需要

**解决方案**:

目前代理配置是全局的。如果需要精细控制，可以修改各服务的 `use_proxy` 参数:

```python
notion_service = NotionService(create_time=datetime.now(), use_proxy=True)
zotero_service = ZoteroService(create_time=datetime.now(), use_proxy=False)
```

---

## 日志和调试

### 查看日志

日志文件位置: `logs/daily_paper_YYYYMMDD.log`

```bash
# 查看最新日志
tail -f logs/daily_paper_$(date +%Y%m%d).log

# 查看错误日志
grep "ERROR" logs/daily_paper_*.log
```

### 启用调试模式

在代码中设置日志级别:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 检查缓存

缓存文件位置: `output/cache/`

```bash
# 查看缓存文件
ls -la output/cache/

# 查看特定论文的缓存
cat output/cache/2401.00001.json

# 清除所有缓存
rm -rf output/cache/*
```

### 检查检查点

检查点文件位置: `output/cache/ckpt_*.txt` 和 `output/cache/arxiv_ckpt.txt`

```bash
# 查看已处理的论文
cat output/cache/arxiv_ckpt.txt

# 如果需要重新处理某篇论文，从检查点中删除其 ID
```

---

## 常见错误信息

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `KeyError: 'NOTION_SECRET'` | 环境变量未设置 | 设置环境变量或在 config.json 中禁用 Notion |
| `JSONDecodeError` | LLM 返回非 JSON 格式 | 重试或清除缓存 |
| `Connection refused` | 服务未启动或端口错误 | 检查代理或 API 服务 |
| `Permission denied` | 文件权限问题 | 检查目录写权限 |
| `Max retries exceeded` | 网络不稳定或 API 限制 | 稍后重试或检查网络 |

---

## 获取帮助

如果以上方案都无法解决问题:

1. 查看 [GitHub Issues](https://github.com/sheldon123z/Zotero-Notion-Paper-Flow/issues) 是否有类似问题

2. 提交新的 Issue，包含:
   - 错误信息和完整堆栈跟踪
   - 运行命令
   - Python 版本和操作系统
   - 相关日志

3. 参考 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解如何贡献修复

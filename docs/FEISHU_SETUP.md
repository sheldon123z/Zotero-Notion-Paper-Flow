# Feishu (飞书/Lark) 集成指南

本文档介绍如何配置飞书多维表格集成，使项目能够将论文信息自动同步到飞书。

## 前置条件

- 拥有飞书账号
- 已加入飞书企业或组织（个人版也可）

## 配置步骤

### 1. 创建飞书自建应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 点击"创建企业自建应用"
3. 填写应用基本信息：
   - 应用名称：例如 "论文管理助手"
   - 应用描述：简要描述应用用途
   - 上传应用图标（可选）

### 2. 获取应用凭证

1. 在应用管理页面，进入"凭证与基础信息"页面
2. 记录以下信息：
   - **App ID**：格式为 `cli_xxxxxxxxxx`
   - **App Secret**：点击"查看"并记录完整密钥

### 3. 配置应用权限

1. 进入应用的"权限管理"页面
2. 搜索并添加以下权限：
   - `bitable:app` - 查看、评论、编辑和管理多维表格
   - `bitable:app:readonly` - 获取多维表格信息（可选，建议开启）
3. 点击"保存"

### 4. 创建多维表格

1. 在飞书中创建一个新的多维表格（Bitable）
2. 创建表格时，建议包含以下字段（列）：
   - **标题** (文本)
   - **作者** (文本)
   - **发表日期** (文本/日期)
   - **领域** (文本/单选)
   - **PDF链接** (URL)
   - **AI总结** (文本)
   - **标签** (多选)
   - **TLDR** (文本)
   - **摘要** (文本)

> **注意**：字段名称必须与上述名称完全一致，否则需要修改 `src/service/feishu_service.py` 中的字段映射。

### 5. 获取表格标识符

#### 获取 App Token

1. 打开创建的多维表格
2. 查看浏览器地址栏的 URL，格式类似：
   ```
   https://example.feishu.cn/base/bascnxxxxxxxxxxxxxx?table=tblxxxxxxxxxxxxxx
   ```
3. 其中 `bascnxxxxxxxxxxxxxx` 就是 **App Token**

#### 获取 Table ID

1. 在多维表格中，点击要使用的数据表标签
2. 查看浏览器地址栏的 URL，格式类似：
   ```
   https://example.feishu.cn/base/bascnxxxxxxxxxxxxxx?table=tblxxxxxxxxxxxxxx
   ```
3. 其中 `tblxxxxxxxxxxxxxx` 就是 **Table ID**

### 6. 授予应用访问权限

1. 在多维表格右上角，点击"设置"图标
2. 选择"应用权限"
3. 搜索并添加刚才创建的应用
4. 授予"可管理"权限

### 7. 配置环境变量

将获取的信息配置到环境变量或启动脚本中：

```bash
export FEISHU_APP_ID="cli_xxxxxxxxxx"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_APP_TOKEN="bascnxxxxxxxxxxxxxx"
export FEISHU_TABLE_ID="tblxxxxxxxxxxxxxx"
```

或在 `bin/start_daily_paper_app_example.sh` 中修改相应配置。

### 8. 启用 Feishu 服务

在 `config.json` 中启用飞书服务：

```json
{
  "services": {
    "notion": true,
    "zotero": false,
    "wolai": false,
    "feishu": true
  }
}
```

或在桌面应用的"服务设置"页面中勾选"飞书 (Feishu/Lark)"。

## 使用桌面应用配置

如果使用桌面应用，可以通过图形界面进行配置：

1. 启动桌面应用
2. 进入"API 密钥配置"标签页
3. 找到"飞书 (Feishu/Lark) 配置"部分
4. 填写：
   - App ID
   - App Secret
   - Bitable App Token
   - Table ID
5. 点击"测试连接"验证配置
6. 进入"服务设置"标签页
7. 在"同步目标"中勾选"飞书 (Feishu/Lark)"
8. 保存配置

## 验证配置

运行以下命令测试配置是否正确：

```bash
python src/daily_paper_app.py --keywords "test" --limit 1
```

如果配置正确，你应该能在日志中看到类似以下内容：

```
插入到飞书: arxiv_id
成功插入到飞书: arxiv_id
```

检查飞书多维表格，应该能看到新增的论文记录。

## 常见问题

### 1. 提示 "Failed to get Feishu access token"

**原因**：App ID 或 App Secret 不正确。

**解决方法**：
- 检查 App ID 和 App Secret 是否正确复制
- 确认应用未被停用或删除

### 2. 提示 "Feishu app_token or table_id not provided"

**原因**：未配置 App Token 或 Table ID 环境变量。

**解决方法**：
- 确认已设置 `FEISHU_APP_TOKEN` 和 `FEISHU_TABLE_ID` 环境变量
- 或在调用 `insert()` 方法时显式传递这些参数

### 3. 插入数据失败，提示权限错误

**原因**：应用权限不足或未授权访问表格。

**解决方法**：
- 检查应用是否有 `bitable:app` 权限
- 确认已在多维表格设置中添加该应用
- 确认授予了"可管理"权限

### 4. 字段不匹配错误

**原因**：表格字段名称与代码中的字段名不一致。

**解决方法**：
- 确保表格字段名称与本文档"创建多维表格"部分描述的名称完全一致
- 或修改 `src/service/feishu_service.py` 中的字段映射以匹配你的表格结构

## 高级配置

### 自定义字段映射

如果需要使用不同的字段名称，可以修改 `src/service/feishu_service.py` 中的 `insert` 方法：

```python
fields = {
    "你的标题字段名": formatted_arxiv_obj.title,
    "你的作者字段名": ", ".join(formatted_arxiv_obj.authors),
    # ... 其他字段
}
```

### 使用企业版权限

如果使用飞书企业版，可以配置更细粒度的权限控制：
- 使用部门级别的访问控制
- 配置数据行级权限
- 启用审计日志

## 参考资料

- [飞书开放平台文档](https://open.feishu.cn/document/home/index)
- [多维表格 API 文档](https://open.feishu.cn/document/server-docs/bitable-v1/overview)
- [应用权限说明](https://open.feishu.cn/document/server-docs/authentication-management/access-token-creation-method/tenant_access_token)

## 技术支持

如遇到其他问题，请：
1. 查看项目 GitHub Issues
2. 查阅飞书开放平台文档
3. 在项目仓库提交新 Issue

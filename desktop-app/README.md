# Paper Flow Desktop

Zotero-Notion-Paper-Flow 桌面配置管理工具，支持 macOS 和 Windows。

## 功能特性

- **API 密钥管理**：安全配置 Notion、LLM、Zotero 等服务的 API 密钥
- **搜索配置**：设置关键词、ArXiv 分类、论文数量限制等
- **服务开关**：灵活启用/禁用各个集成服务
- **运行控制**：一键启动/停止论文抓取任务
- **实时日志**：查看任务执行日志
- **跨平台**：支持 macOS、Windows、Linux

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.8+
- 已安装项目 Python 依赖 (`pip install -r requirements.txt`)

### 安装依赖

```bash
cd desktop-app
npm install
```

### 开发模式运行

```bash
npm run dev
```

### 生产模式运行

```bash
npm start
```

### 构建安装包

```bash
# macOS
npm run build:mac

# Windows
npm run build:win

# Linux
npm run build:linux

# 全平台
npm run build
```

构建产物在 `dist/` 目录下。

## 配置说明

### API 密钥配置

所有 API 密钥安全存储在本地，不会上传到任何服务器。

| 服务 | 必需 | 说明 |
|------|------|------|
| Notion | 是 | 需要 Secret 和 Database ID |
| LLM (Kimi/DeepSeek) | 是 | 至少配置一个 LLM 服务 |
| Zotero | 否 | 需要 API Key 和 User ID |
| Wolai | 否 | 需要 Token 和 Database ID |
| Slack | 否 | 用于消息通知 |

### 搜索配置

- **关键词**：每行一个关键词，逗号分隔表示 OR 逻辑
- **ArXiv 分类**：选择感兴趣的论文分类
- **论文数量**：每次最多处理的论文数
- **PDF 下载**：是否下载论文 PDF

### 服务设置

- 选择论文来源（ArXiv、HuggingFace）
- 选择同步目标（Notion、Zotero、Wolai）

## 项目结构

```
desktop-app/
├── main.js           # Electron 主进程
├── preload.js        # 预加载脚本
├── package.json      # 项目配置
├── renderer/         # 渲染进程（前端）
│   ├── index.html
│   ├── styles.css
│   └── renderer.js
└── assets/           # 资源文件
    └── icon.png
```

## 开发说明

### 技术栈

- Electron 28
- 原生 HTML/CSS/JavaScript
- electron-store（配置存储）

### 调试

开发模式下自动打开 DevTools：

```bash
npm run dev
```

### 打包配置

打包配置在 `package.json` 的 `build` 字段中，支持：

- macOS: DMG, ZIP
- Windows: NSIS 安装程序, Portable
- Linux: AppImage, DEB

## 常见问题

### Python 找不到

确保 Python 3 已安装并添加到系统 PATH。

### 启动失败

检查是否已安装项目依赖：

```bash
cd ..
pip install -r requirements.txt
```

### 权限问题

macOS 用户可能需要在系统偏好设置中允许应用运行。

## License

MIT

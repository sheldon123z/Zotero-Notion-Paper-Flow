# Desktop App Bug Fixes

## 修复日期：2025-12-02

本文档记录了对 desktop-app 的 bug 修复和改进。

## 修复的 Bug

### 1. ✅ 日志文件路径不匹配

**问题描述**：
- 桌面应用期望的日志文件名：`YYYY-MM-DD.log`
- Python 后端实际生成的日志文件名：`daily_paper_YYYYMMDD.log`
- 导致 `read-log-file` 功能无法找到日志文件

**修复位置**：`main.js` 第 337-340 行

**修复内容**：
```javascript
// 修复前
const logFile = path.join(logsDir, `${date}.log`);

// 修复后
const formattedDate = date.replace(/-/g, '');
const logFile = path.join(logsDir, `daily_paper_${formattedDate}.log`);
```

---

### 2. ✅ Zotero 配置字段名错误

**问题描述**：
- 桌面应用使用：`ZOTERO_GROUP_ID`
- Python 后端期望：`ZOTERO_LIBRARY_ID`
- 导致 Zotero 配置无法正确传递到后端

**修复位置**：
- `main.js` 第 126 行（默认配置）
- `main.js` 第 308-309 行（配置验证）

**修复内容**：
```javascript
// 修复前
ZOTERO_GROUP_ID: '',

// 修复后
ZOTERO_LIBRARY_ID: '',
```

---

### 3. ✅ 定时任务与手动任务冲突

**问题描述**：
- 定时任务和手动任务可能同时运行
- 没有检查 `pythonProcess` 状态
- 可能导致资源冲突和意外行为

**修复位置**：`main.js` 第 528-539 行

**修复内容**：
```javascript
// 在定时任务开始前检查手动任务状态
if (pythonProcess) {
  console.log('检测到手动任务正在运行，跳过此次定时任务');
  schedulerStatus.lastResult = '跳过（手动任务运行中）';
  
  // 重新调度下次任务
  const schedulerConfig = store.get('schedulerConfig', {});
  if (schedulerConfig.enabled) {
    startScheduler(schedulerConfig);
  }
  return;
}
```

---

### 4. ✅ 环境变量空字符串覆盖问题

**问题描述**：
- 当配置值为空字符串时，也会覆盖系统环境变量
- 导致系统环境变量被意外清空

**修复位置**：
- `main.js` 第 203-207 行（手动任务）
- `main.js` 第 558-562 行（定时任务）

**修复内容**：
```javascript
// 修复前
Object.keys(envConfig).forEach(key => {
  if (envConfig[key]) {
    env[key] = envConfig[key];
  }
});

// 修复后
Object.keys(envConfig).forEach(key => {
  // 只有当配置值不为空字符串时才覆盖环境变量
  if (envConfig[key] && envConfig[key].trim() !== '') {
    env[key] = envConfig[key];
  }
});
```

---

### 5. ✅ 定时任务进程变量命名改进

**问题描述**：
- 原代码使用 `process_child` 作为变量名
- 改为 `scheduledProcess` 更符合语义

**修复位置**：`main.js` 第 565 行

**修复内容**：
```javascript
// 修复前
const process_child = spawn('python3', args, {...});

// 修复后
const scheduledProcess = spawn('python3', args, {...});
```

---

### 6. ✅ 错误提示信息改进

**问题描述**：
- 任务冲突时的错误提示不够详细

**修复位置**：`main.js` 第 153 行

**修复内容**：
```javascript
// 修复前
reject(new Error('已有任务在运行中'));

// 修复后
reject(new Error('已有任务在运行中，请等待当前任务完成'));
```

---

### 7. ✅ Zotero 配置验证增强

**问题描述**：
- 配置验证缺少 `ZOTERO_LIBRARY_ID` 检查

**修复位置**：`main.js` 第 308-310 行

**修复内容**：
```javascript
if (!config.env.ZOTERO_LIBRARY_ID) {
  errors.push('Zotero Library ID 未配置');
}
```

---

### 8. ✅ 定时任务错误日志增强

**问题描述**：
- 定时任务失败时没有记录输出日志

**修复位置**：`main.js` 第 570-578, 591 行

**修复内容**：
```javascript
// 记录定时任务的输出
let output = '';
scheduledProcess.stdout.on('data', (data) => {
  output += data.toString();
});

scheduledProcess.stderr.on('data', (data) => {
  output += data.toString();
});

// 失败时输出日志
console.error('定时任务失败输出:', output);
```

---

### 9. ✅ 定时任务错误后重新调度

**问题描述**：
- 定时任务出错后不会重新调度
- 导致定时任务停止工作

**修复位置**：
- `main.js` 第 605-609 行（进程错误）
- `main.js` 第 616-620 行（异常捕获）

**修复内容**：
```javascript
// 即使出错也要重新调度
const schedulerConfig = store.get('schedulerConfig', {});
if (schedulerConfig.enabled) {
  startScheduler(schedulerConfig);
}
```

---

## 新增功能

### 1. ✨ Python 环境检测

**功能描述**：
- 检查 Python 3 是否安装
- 检查 Python 版本
- 检查必需的依赖包是否安装
- 列出缺失的包

**实现位置**：
- `main.js` 第 644-694 行（后端实现）
- `preload.js` 第 44 行（API 暴露）

**使用方法**：
```javascript
const result = await window.electronAPI.checkPythonEnv();

if (result.success) {
  console.log('Python 版本:', result.python);
  if (result.hasMissingPackages) {
    console.log('缺失的包:', result.missingPackages);
  }
} else {
  console.error('Python 环境检查失败:', result.message);
}
```

---

## 测试建议

### 1. 日志文件读取测试
```bash
# 1. 运行 Python 脚本生成日志
python src/daily_paper_app.py --limit 1

# 2. 在桌面应用中尝试读取今天的日志
# 验证日志能否正常显示
```

### 2. Zotero 配置测试
```bash
# 1. 在桌面应用中配置 Zotero
# 2. 运行任务
# 3. 检查 Zotero 中是否成功添加论文
```

### 3. 定时任务冲突测试
```bash
# 1. 启动定时任务（设置为 1 分钟后执行）
# 2. 在定时任务触发前手动运行任务
# 3. 验证定时任务是否正确跳过
# 4. 验证下次定时任务是否正常调度
```

### 4. Python 环境检测测试
```bash
# 在桌面应用启动时或设置页面调用
# 验证能否正确检测 Python 版本和依赖包
```

---

## 后续优化建议

### 1. 添加重试机制
当 Python 脚本失败时，自动重试 1-2 次

### 2. 实现进度条
- Python 脚本输出结构化的进度信息
- 桌面应用解析并显示进度条

### 3. 增加更多状态指示
- 运行中/暂停/完成/失败等状态
- 显示当前处理的论文数量

### 4. 配置备份和恢复
- 自动备份配置
- 支持配置版本管理

### 5. 日志查看器增强
- 支持日志搜索和过滤
- 支持日志高亮显示
- 支持实时日志滚动

---

## 版本信息

- **修复版本**: 1.0.1
- **修复日期**: 2025-12-02
- **修复文件**: `main.js`, `preload.js`
- **影响范围**: Desktop App 与 Python 后端交互

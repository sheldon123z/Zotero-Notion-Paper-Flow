const { app, BrowserWindow, ipcMain, dialog, shell, Notification } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const Store = require('electron-store');

// 配置存储
const store = new Store();

let mainWindow;
let pythonProcess = null;
let schedulerTimer = null;
let schedulerStatus = {
  enabled: false,
  nextRun: null,
  lastRun: null,
  lastResult: null
};

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'assets/icon.png')
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));

  // 开发模式下打开开发者工具
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// IPC 处理器

// 获取配置
ipcMain.handle('get-config', async () => {
  try {
    const projectRoot = path.resolve(__dirname, '..');
    const configPath = path.join(projectRoot, 'config.json');

    if (fs.existsSync(configPath)) {
      const configData = fs.readFileSync(configPath, 'utf-8');
      return JSON.parse(configData);
    }

    // 返回默认配置
    return {
      keywords: [],
      categories: [],
      date: null,
      proxy: "",
      services: {
        notion: true,
        zotero: false,
        wolai: false
      },
      download_pdf: true,
      pdf_dir: "papers",
      search_limit: 10,
      retries: 3,
      category_map: {},
      default_category: []
    };
  } catch (error) {
    console.error('读取配置失败:', error);
    throw error;
  }
});

// 保存配置到 config.json
ipcMain.handle('save-config', async (event, config) => {
  try {
    const projectRoot = path.resolve(__dirname, '..');
    const configPath = path.join(projectRoot, 'config.json');

    fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8');
    return { success: true };
  } catch (error) {
    console.error('保存配置失败:', error);
    throw error;
  }
});

// 获取环境变量配置
ipcMain.handle('get-env-config', async () => {
  return store.get('envConfig', {
    NOTION_SECRET: '',
    NOTION_DB_ID: '',
    KIMI_API_KEY: '',
    KIMI_URL: 'https://api.moonshot.cn/v1',
    DEEPSEEK_API_KEY: '',
    DEEPSEEK_URL: 'https://api.deepseek.com',
    ZOTERO_API_KEY: '',
    ZOTERO_USER_ID: '',
    ZOTERO_GROUP_ID: '',
    WOLAI_TOKEN: '',
    WOLAI_DB_ID: '',
    SLACK_API_KEY: '',
    HTTP_PROXY: '',
    HTTPS_PROXY: '',
    DEFAULT_API_KEY: '',
    DEFAULT_BASE_URL: '',
    DEFAULT_MODEL_NAME: ''
  });
});

// 保存环境变量配置
ipcMain.handle('save-env-config', async (event, envConfig) => {
  try {
    store.set('envConfig', envConfig);
    return { success: true };
  } catch (error) {
    console.error('保存环境变量配置失败:', error);
    throw error;
  }
});

// 运行 Python 脚本
ipcMain.handle('run-python-script', async (event, options) => {
  return new Promise((resolve, reject) => {
    if (pythonProcess) {
      reject(new Error('已有任务在运行中'));
      return;
    }

    const projectRoot = path.resolve(__dirname, '..');
    const scriptPath = path.join(projectRoot, 'src/daily_paper_app.py');

    // 构建命令行参数
    const args = [scriptPath];

    if (options.keywords && options.keywords.length > 0) {
      args.push('--keywords', ...options.keywords);
    }

    if (options.categories && options.categories.length > 0) {
      args.push('--categories', ...options.categories);
    }

    if (options.date) {
      args.push('--date', options.date);
    }

    if (options.days) {
      args.push('--days', options.days.toString());
    }

    if (options.limit) {
      args.push('--limit', options.limit.toString());
    }

    if (options.downloadPdf) {
      args.push('--download-pdf');
    }

    if (options.pdfDir) {
      args.push('--pdf-dir', options.pdfDir);
    }

    if (options.noArxiv) {
      args.push('--no-arxiv');
    }

    if (options.noHf) {
      args.push('--no-hf');
    }

    // 设置环境变量
    const env = { ...process.env };
    const envConfig = store.get('envConfig', {});

    Object.keys(envConfig).forEach(key => {
      if (envConfig[key]) {
        env[key] = envConfig[key];
      }
    });

    // 启动 Python 进程
    pythonProcess = spawn('python3', args, {
      cwd: projectRoot,
      env: env
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      const text = data.toString();
      output += text;
      // 实时发送日志到渲染进程
      mainWindow.webContents.send('python-log', { type: 'info', message: text });
    });

    pythonProcess.stderr.on('data', (data) => {
      const text = data.toString();
      errorOutput += text;
      mainWindow.webContents.send('python-log', { type: 'error', message: text });
    });

    pythonProcess.on('close', (code) => {
      pythonProcess = null;
      mainWindow.webContents.send('python-finished', { code, output, errorOutput });

      if (code === 0) {
        resolve({ success: true, output });
      } else {
        reject(new Error(`进程退出，代码: ${code}\n${errorOutput}`));
      }
    });

    pythonProcess.on('error', (error) => {
      pythonProcess = null;
      mainWindow.webContents.send('python-error', { error: error.message });
      reject(error);
    });
  });
});

// 停止 Python 脚本
ipcMain.handle('stop-python-script', async () => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
    pythonProcess = null;
    return { success: true };
  }
  return { success: false, message: '没有运行中的任务' };
});

// 获取运行状态
ipcMain.handle('get-running-status', async () => {
  return { isRunning: pythonProcess !== null };
});

// 选择目录
ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });

  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

// 验证配置
ipcMain.handle('validate-config', async (event, config) => {
  const errors = [];

  // 检查必需的环境变量
  if (config.services.notion) {
    if (!config.env.NOTION_SECRET) {
      errors.push('Notion Secret 未配置');
    }
    if (!config.env.NOTION_DB_ID) {
      errors.push('Notion Database ID 未配置');
    }
  }

  // 检查 LLM 配置（至少需要一个）
  const hasKimi = config.env.KIMI_API_KEY && config.env.KIMI_URL;
  const hasDeepseek = config.env.DEEPSEEK_API_KEY && config.env.DEEPSEEK_URL;
  const hasCustom = config.env.DEFAULT_API_KEY && config.env.DEFAULT_BASE_URL;

  if (!hasKimi && !hasDeepseek && !hasCustom) {
    errors.push('至少需要配置一个 LLM 服务（Kimi/DeepSeek/自定义）');
  }

  if (config.services.zotero) {
    if (!config.env.ZOTERO_API_KEY) {
      errors.push('Zotero API Key 未配置');
    }
    if (!config.env.ZOTERO_USER_ID) {
      errors.push('Zotero User ID 未配置');
    }
  }

  if (config.services.wolai) {
    if (!config.env.WOLAI_TOKEN) {
      errors.push('Wolai Token 未配置');
    }
    if (!config.env.WOLAI_DB_ID) {
      errors.push('Wolai Database ID 未配置');
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
});

// 读取日志文件
ipcMain.handle('read-log-file', async (event, date) => {
  try {
    const projectRoot = path.resolve(__dirname, '..');
    const logsDir = path.join(projectRoot, 'logs');

    if (!date) {
      date = new Date().toISOString().split('T')[0];
    }

    const logFile = path.join(logsDir, `${date}.log`);

    if (fs.existsSync(logFile)) {
      const content = fs.readFileSync(logFile, 'utf-8');
      return { success: true, content };
    }

    return { success: false, message: '日志文件不存在' };
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// 获取已处理论文列表
ipcMain.handle('get-processed-papers', async () => {
  try {
    const projectRoot = path.resolve(__dirname, '..');
    const cacheDir = path.join(projectRoot, 'output/cache');

    if (!fs.existsSync(cacheDir)) {
      return [];
    }

    const files = fs.readdirSync(cacheDir);
    const papers = [];

    files.forEach(file => {
      if (file.endsWith('.json')) {
        try {
          const content = fs.readFileSync(path.join(cacheDir, file), 'utf-8');
          const data = JSON.parse(content);
          if (Array.isArray(data)) {
            papers.push(...data);
          } else if (data) {
            papers.push(data);
          }
        } catch (e) {
          console.error(`读取文件失败: ${file}`, e);
        }
      }
    });

    // 按日期排序，最新的在前
    papers.sort((a, b) => {
      const dateA = new Date(a.published || a.date || 0);
      const dateB = new Date(b.published || b.date || 0);
      return dateB - dateA;
    });

    return papers;
  } catch (error) {
    console.error('获取已处理论文失败:', error);
    return [];
  }
});

// ==================== 定时任务功能 ====================

// 获取定时任务配置
ipcMain.handle('get-scheduler-config', async () => {
  return store.get('schedulerConfig', {
    enabled: false,
    type: 'daily',
    dailyTime: '08:00',
    weeklyTime: '08:00',
    weekdays: [1, 2, 3, 4, 5],
    intervalValue: 6,
    intervalUnit: 'hours',
    days: 1,
    limit: 20,
    downloadPdf: true,
    notify: true,
    autoStart: false,
    runInBackground: false
  });
});

// 保存定时任务配置
ipcMain.handle('save-scheduler-config', async (event, config) => {
  try {
    store.set('schedulerConfig', config);

    // 更新定时任务
    if (config.enabled) {
      startScheduler(config);
    } else {
      stopScheduler();
    }

    // 处理开机自启动
    if (config.autoStart !== undefined) {
      app.setLoginItemSettings({
        openAtLogin: config.autoStart,
        openAsHidden: config.runInBackground
      });
    }

    return { success: true };
  } catch (error) {
    console.error('保存定时任务配置失败:', error);
    throw error;
  }
});

// 获取定时任务状态
ipcMain.handle('get-scheduler-status', async () => {
  return schedulerStatus;
});

// 启动定时任务
function startScheduler(config) {
  stopScheduler();

  schedulerStatus.enabled = true;
  const nextRunTime = calculateNextRunTime(config);
  schedulerStatus.nextRun = nextRunTime ? formatDateTime(nextRunTime) : null;

  if (!nextRunTime) {
    return;
  }

  const delay = nextRunTime.getTime() - Date.now();

  schedulerTimer = setTimeout(() => {
    runScheduledTask(config);
  }, Math.max(0, delay));

  console.log(`定时任务已启动，下次运行: ${schedulerStatus.nextRun}`);
}

// 停止定时任务
function stopScheduler() {
  if (schedulerTimer) {
    clearTimeout(schedulerTimer);
    schedulerTimer = null;
  }
  schedulerStatus.enabled = false;
  schedulerStatus.nextRun = null;
}

// 计算下次运行时间
function calculateNextRunTime(config) {
  const now = new Date();

  if (config.type === 'daily') {
    const [hours, minutes] = config.dailyTime.split(':').map(Number);
    const next = new Date(now);
    next.setHours(hours, minutes, 0, 0);

    if (next <= now) {
      next.setDate(next.getDate() + 1);
    }
    return next;

  } else if (config.type === 'weekly') {
    const [hours, minutes] = config.weeklyTime.split(':').map(Number);
    const weekdays = config.weekdays || [];

    if (weekdays.length === 0) {
      return null;
    }

    for (let i = 0; i < 7; i++) {
      const next = new Date(now);
      next.setDate(next.getDate() + i);
      next.setHours(hours, minutes, 0, 0);

      if (weekdays.includes(next.getDay()) && next > now) {
        return next;
      }
    }
    return null;

  } else if (config.type === 'interval') {
    const value = config.intervalValue || 6;
    const unit = config.intervalUnit || 'hours';
    const ms = unit === 'hours' ? value * 60 * 60 * 1000 : value * 60 * 1000;

    return new Date(now.getTime() + ms);
  }

  return null;
}

// 运行定时任务
async function runScheduledTask(config) {
  console.log('开始运行定时任务...');
  schedulerStatus.lastRun = formatDateTime(new Date());

  try {
    const projectRoot = path.resolve(__dirname, '..');
    const scriptPath = path.join(projectRoot, 'src/daily_paper_app.py');

    const args = [scriptPath];
    args.push('--days', (config.days || 1).toString());
    args.push('--limit', (config.limit || 20).toString());

    if (config.downloadPdf) {
      args.push('--download-pdf');
    }

    // 设置环境变量
    const env = { ...process.env };
    const envConfig = store.get('envConfig', {});
    Object.keys(envConfig).forEach(key => {
      if (envConfig[key]) {
        env[key] = envConfig[key];
      }
    });

    const process_child = spawn('python3', args, {
      cwd: projectRoot,
      env: env
    });

    process_child.on('close', (code) => {
      if (code === 0) {
        schedulerStatus.lastResult = '成功';
        if (config.notify) {
          showNotification('Paper Flow', '定时任务执行成功');
        }
      } else {
        schedulerStatus.lastResult = `失败 (代码: ${code})`;
        if (config.notify) {
          showNotification('Paper Flow', `定时任务执行失败 (代码: ${code})`);
        }
      }

      // 重新调度下次任务
      const schedulerConfig = store.get('schedulerConfig', {});
      if (schedulerConfig.enabled) {
        startScheduler(schedulerConfig);
      }
    });

    process_child.on('error', (error) => {
      schedulerStatus.lastResult = `错误: ${error.message}`;
      console.error('定时任务执行错误:', error);
    });

  } catch (error) {
    schedulerStatus.lastResult = `错误: ${error.message}`;
    console.error('定时任务执行错误:', error);
  }
}

// 显示系统通知
function showNotification(title, body) {
  if (Notification.isSupported()) {
    new Notification({ title, body }).show();
  }
}

// 格式化日期时间
function formatDateTime(date) {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// ==================== 系统功能 ====================

// 打开外部链接
ipcMain.handle('open-external', async (event, url) => {
  try {
    await shell.openExternal(url);
    return { success: true };
  } catch (error) {
    console.error('打开外部链接失败:', error);
    throw error;
  }
});

// 设置开机自启动
ipcMain.handle('set-auto-start', async (event, enable) => {
  try {
    app.setLoginItemSettings({
      openAtLogin: enable
    });
    return { success: true };
  } catch (error) {
    console.error('设置开机自启动失败:', error);
    throw error;
  }
});

// 获取开机自启动状态
ipcMain.handle('get-auto-start-status', async () => {
  const settings = app.getLoginItemSettings();
  return { enabled: settings.openAtLogin };
});

// ==================== API 连接测试 ====================

ipcMain.handle('test-connection', async (event, service, config) => {
  const https = require('https');
  const http = require('http');

  return new Promise((resolve) => {
    try {
      if (service === 'notion') {
        testNotionConnection(config, resolve);
      } else if (service === 'llm') {
        testLLMConnection(config, resolve);
      } else if (service === 'zotero') {
        testZoteroConnection(config, resolve);
      } else if (service === 'wolai') {
        testWolaiConnection(config, resolve);
      } else {
        resolve({ success: false, message: '未知服务' });
      }
    } catch (error) {
      resolve({ success: false, message: error.message });
    }
  });
});

function testNotionConnection(config, resolve) {
  if (!config.NOTION_SECRET) {
    resolve({ success: false, message: 'Notion Secret 未配置' });
    return;
  }

  const https = require('https');
  const options = {
    hostname: 'api.notion.com',
    path: '/v1/users/me',
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${config.NOTION_SECRET}`,
      'Notion-Version': '2022-06-28'
    },
    timeout: 10000
  };

  const req = https.request(options, (res) => {
    if (res.statusCode === 200) {
      resolve({ success: true });
    } else {
      resolve({ success: false, message: `HTTP ${res.statusCode}` });
    }
  });

  req.on('error', (e) => {
    resolve({ success: false, message: e.message });
  });

  req.on('timeout', () => {
    req.destroy();
    resolve({ success: false, message: '连接超时' });
  });

  req.end();
}

function testLLMConnection(config, resolve) {
  const https = require('https');

  // 优先测试 Kimi
  if (config.KIMI_API_KEY && config.KIMI_URL) {
    testOpenAICompatible(config.KIMI_URL, config.KIMI_API_KEY, resolve);
  } else if (config.DEEPSEEK_API_KEY && config.DEEPSEEK_URL) {
    testOpenAICompatible(config.DEEPSEEK_URL, config.DEEPSEEK_API_KEY, resolve);
  } else if (config.DEFAULT_API_KEY && config.DEFAULT_BASE_URL) {
    testOpenAICompatible(config.DEFAULT_BASE_URL, config.DEFAULT_API_KEY, resolve);
  } else {
    resolve({ success: false, message: 'LLM API 未配置' });
  }
}

function testOpenAICompatible(baseUrl, apiKey, resolve) {
  const https = require('https');
  const url = new URL(baseUrl);

  const options = {
    hostname: url.hostname,
    port: url.port || 443,
    path: (url.pathname.endsWith('/') ? url.pathname : url.pathname + '/') + 'models',
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${apiKey}`
    },
    timeout: 10000
  };

  const req = https.request(options, (res) => {
    if (res.statusCode === 200) {
      resolve({ success: true });
    } else {
      resolve({ success: false, message: `HTTP ${res.statusCode}` });
    }
  });

  req.on('error', (e) => {
    resolve({ success: false, message: e.message });
  });

  req.on('timeout', () => {
    req.destroy();
    resolve({ success: false, message: '连接超时' });
  });

  req.end();
}

function testZoteroConnection(config, resolve) {
  if (!config.ZOTERO_API_KEY || !config.ZOTERO_USER_ID) {
    resolve({ success: false, message: 'Zotero API Key 或 User ID 未配置' });
    return;
  }

  const https = require('https');
  const options = {
    hostname: 'api.zotero.org',
    path: `/users/${config.ZOTERO_USER_ID}/items?limit=1`,
    method: 'GET',
    headers: {
      'Zotero-API-Key': config.ZOTERO_API_KEY
    },
    timeout: 10000
  };

  const req = https.request(options, (res) => {
    if (res.statusCode === 200) {
      resolve({ success: true });
    } else {
      resolve({ success: false, message: `HTTP ${res.statusCode}` });
    }
  });

  req.on('error', (e) => {
    resolve({ success: false, message: e.message });
  });

  req.on('timeout', () => {
    req.destroy();
    resolve({ success: false, message: '连接超时' });
  });

  req.end();
}

function testWolaiConnection(config, resolve) {
  if (!config.WOLAI_TOKEN) {
    resolve({ success: false, message: 'Wolai Token 未配置' });
    return;
  }

  const https = require('https');
  const options = {
    hostname: 'openapi.wolai.com',
    path: '/v1/token',
    method: 'GET',
    headers: {
      'Authorization': config.WOLAI_TOKEN
    },
    timeout: 10000
  };

  const req = https.request(options, (res) => {
    if (res.statusCode === 200) {
      resolve({ success: true });
    } else {
      resolve({ success: false, message: `HTTP ${res.statusCode}` });
    }
  });

  req.on('error', (e) => {
    resolve({ success: false, message: e.message });
  });

  req.on('timeout', () => {
    req.destroy();
    resolve({ success: false, message: '连接超时' });
  });

  req.end();
}

// ==================== 配置导入/导出 ====================

ipcMain.handle('export-config', async (event, configData) => {
  try {
    const result = await dialog.showSaveDialog(mainWindow, {
      title: '导出配置',
      defaultPath: `paper-flow-config-${new Date().toISOString().slice(0, 10)}.json`,
      filters: [
        { name: 'JSON 文件', extensions: ['json'] }
      ]
    });

    if (!result.canceled && result.filePath) {
      fs.writeFileSync(result.filePath, JSON.stringify(configData, null, 2), 'utf-8');
      return { success: true };
    }

    return { success: false, canceled: true };
  } catch (error) {
    console.error('导出配置失败:', error);
    return { success: false, message: error.message };
  }
});

ipcMain.handle('import-config', async () => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      title: '导入配置',
      filters: [
        { name: 'JSON 文件', extensions: ['json'] }
      ],
      properties: ['openFile']
    });

    if (!result.canceled && result.filePaths.length > 0) {
      const content = fs.readFileSync(result.filePaths[0], 'utf-8');
      const data = JSON.parse(content);

      // 验证配置格式
      if (!data.version || !data.envConfig) {
        return { success: false, message: '无效的配置文件格式' };
      }

      return { success: true, data };
    }

    return { success: false, canceled: true };
  } catch (error) {
    console.error('导入配置失败:', error);
    return { success: false, message: error.message };
  }
});

// 应用启动时恢复定时任务
app.whenReady().then(() => {
  createWindow();

  // 恢复定时任务
  const schedulerConfig = store.get('schedulerConfig', {});
  if (schedulerConfig.enabled) {
    startScheduler(schedulerConfig);
  }
});

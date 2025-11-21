const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const Store = require('electron-store');

// 配置存储
const store = new Store();

let mainWindow;
let pythonProcess = null;

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

app.whenReady().then(createWindow);

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
          papers.push(...data);
        } catch (e) {
          console.error(`读取文件失败: ${file}`, e);
        }
      }
    });

    return papers;
  } catch (error) {
    console.error('获取已处理论文失败:', error);
    return [];
  }
});

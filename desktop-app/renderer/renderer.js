// Paper Flow Desktop App - 渲染进程

// ArXiv 分类列表
const ARXIV_CATEGORIES = [
  { code: 'cs.AI', name: '人工智能' },
  { code: 'cs.LG', name: '机器学习' },
  { code: 'cs.CL', name: '自然语言处理' },
  { code: 'cs.CV', name: '计算机视觉' },
  { code: 'cs.NE', name: '神经网络' },
  { code: 'cs.RO', name: '机器人学' },
  { code: 'cs.IR', name: '信息检索' },
  { code: 'cs.HC', name: '人机交互' },
  { code: 'cs.SE', name: '软件工程' },
  { code: 'cs.DC', name: '分布式计算' },
  { code: 'cs.CR', name: '密码学与安全' },
  { code: 'cs.DB', name: '数据库' },
  { code: 'stat.ML', name: '统计机器学习' },
  { code: 'eess.AS', name: '音频语音处理' },
  { code: 'eess.IV', name: '图像视频处理' },
  { code: 'eess.SY', name: '系统与控制' },
  { code: 'math.OC', name: '优化与控制' },
  { code: 'physics.comp-ph', name: '计算物理' },
  { code: 'q-bio.NC', name: '神经科学' },
  { code: 'quant-ph', name: '量子物理' }
];

// 全局状态
let config = {};
let envConfig = {};
let isRunning = false;

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
  initNavigation();
  initCategoryGrid();
  await loadConfig();
  await loadEnvConfig();
  await checkRunningStatus();
  initEventListeners();
  setupPythonLogListener();
});

// 初始化导航
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  const tabContents = document.querySelectorAll('.tab-content');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const tabId = item.dataset.tab;

      // 更新导航状态
      navItems.forEach(nav => nav.classList.remove('active'));
      item.classList.add('active');

      // 切换内容
      tabContents.forEach(content => {
        content.classList.remove('active');
        if (content.id === tabId) {
          content.classList.add('active');
        }
      });
    });
  });
}

// 初始化分类网格
function initCategoryGrid() {
  const grid = document.getElementById('categoryGrid');
  grid.innerHTML = ARXIV_CATEGORIES.map(cat => `
    <label class="category-item">
      <input type="checkbox" value="${cat.code}" class="category-checkbox">
      <span>
        <span class="category-name">${cat.name}</span>
        <span class="category-code">${cat.code}</span>
      </span>
    </label>
  `).join('');
}

// 加载配置
async function loadConfig() {
  try {
    config = await window.electronAPI.getConfig();
    applyConfigToUI();
  } catch (error) {
    showToast('加载配置失败: ' + error.message, 'error');
  }
}

// 加载环境变量配置
async function loadEnvConfig() {
  try {
    envConfig = await window.electronAPI.getEnvConfig();
    applyEnvConfigToUI();
  } catch (error) {
    showToast('加载环境变量配置失败: ' + error.message, 'error');
  }
}

// 应用配置到 UI
function applyConfigToUI() {
  // 关键词
  if (config.keywords && config.keywords.length > 0) {
    const keywordsText = config.keywords.map(kw => {
      if (Array.isArray(kw)) {
        return kw.join(', ');
      }
      return kw;
    }).join('\n');
    document.getElementById('keywords').value = keywordsText;
  }

  // 分类
  if (config.categories && config.categories.length > 0) {
    document.querySelectorAll('.category-checkbox').forEach(cb => {
      cb.checked = config.categories.includes(cb.value);
    });
  }

  // 搜索限制
  if (config.search_limit) {
    document.getElementById('searchLimit').value = config.search_limit;
  }
  if (config.retries) {
    document.getElementById('retries').value = config.retries;
  }

  // PDF 设置
  document.getElementById('downloadPdf').checked = config.download_pdf !== false;
  if (config.pdf_dir) {
    document.getElementById('pdfDir').value = config.pdf_dir;
  }

  // 服务开关
  if (config.services) {
    document.getElementById('enableNotion').checked = config.services.notion !== false;
    document.getElementById('enableZotero').checked = config.services.zotero === true;
    document.getElementById('enableWolai').checked = config.services.wolai === true;
    updateZoteroCategoriesVisibility();
  }

  // Zotero 分类映射
  if (config.category_map) {
    renderCategoryMap();
  }
}

// 应用环境变量配置到 UI
function applyEnvConfigToUI() {
  document.getElementById('notionSecret').value = envConfig.NOTION_SECRET || '';
  document.getElementById('notionDbId').value = envConfig.NOTION_DB_ID || '';
  document.getElementById('kimiApiKey').value = envConfig.KIMI_API_KEY || '';
  document.getElementById('kimiUrl').value = envConfig.KIMI_URL || 'https://api.moonshot.cn/v1';
  document.getElementById('deepseekApiKey').value = envConfig.DEEPSEEK_API_KEY || '';
  document.getElementById('deepseekUrl').value = envConfig.DEEPSEEK_URL || 'https://api.deepseek.com';
  document.getElementById('zoteroApiKey').value = envConfig.ZOTERO_API_KEY || '';
  document.getElementById('zoteroUserId').value = envConfig.ZOTERO_USER_ID || '';
  document.getElementById('zoteroGroupId').value = envConfig.ZOTERO_GROUP_ID || '';
  document.getElementById('wolaiToken').value = envConfig.WOLAI_TOKEN || '';
  document.getElementById('wolaiDbId').value = envConfig.WOLAI_DB_ID || '';
  document.getElementById('slackApiKey').value = envConfig.SLACK_API_KEY || '';
  document.getElementById('httpProxy').value = envConfig.HTTP_PROXY || '';
  document.getElementById('httpsProxy').value = envConfig.HTTPS_PROXY || '';
  document.getElementById('defaultApiKey').value = envConfig.DEFAULT_API_KEY || '';
  document.getElementById('defaultBaseUrl').value = envConfig.DEFAULT_BASE_URL || '';
  document.getElementById('defaultModelName').value = envConfig.DEFAULT_MODEL_NAME || '';
}

// 从 UI 收集环境变量配置
function collectEnvConfigFromUI() {
  return {
    NOTION_SECRET: document.getElementById('notionSecret').value.trim(),
    NOTION_DB_ID: document.getElementById('notionDbId').value.trim(),
    KIMI_API_KEY: document.getElementById('kimiApiKey').value.trim(),
    KIMI_URL: document.getElementById('kimiUrl').value.trim(),
    DEEPSEEK_API_KEY: document.getElementById('deepseekApiKey').value.trim(),
    DEEPSEEK_URL: document.getElementById('deepseekUrl').value.trim(),
    ZOTERO_API_KEY: document.getElementById('zoteroApiKey').value.trim(),
    ZOTERO_USER_ID: document.getElementById('zoteroUserId').value.trim(),
    ZOTERO_GROUP_ID: document.getElementById('zoteroGroupId').value.trim(),
    WOLAI_TOKEN: document.getElementById('wolaiToken').value.trim(),
    WOLAI_DB_ID: document.getElementById('wolaiDbId').value.trim(),
    SLACK_API_KEY: document.getElementById('slackApiKey').value.trim(),
    HTTP_PROXY: document.getElementById('httpProxy').value.trim(),
    HTTPS_PROXY: document.getElementById('httpsProxy').value.trim(),
    DEFAULT_API_KEY: document.getElementById('defaultApiKey').value.trim(),
    DEFAULT_BASE_URL: document.getElementById('defaultBaseUrl').value.trim(),
    DEFAULT_MODEL_NAME: document.getElementById('defaultModelName').value.trim()
  };
}

// 从 UI 收集搜索配置
function collectSearchConfigFromUI() {
  // 解析关键词
  const keywordsText = document.getElementById('keywords').value.trim();
  const keywords = keywordsText.split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
    .map(line => {
      if (line.includes(',')) {
        return line.split(',').map(k => k.trim()).filter(k => k.length > 0);
      }
      return line;
    });

  // 收集选中的分类
  const categories = [];
  document.querySelectorAll('.category-checkbox:checked').forEach(cb => {
    categories.push(cb.value);
  });

  return {
    keywords,
    categories,
    search_limit: parseInt(document.getElementById('searchLimit').value) || 10,
    retries: parseInt(document.getElementById('retries').value) || 3,
    download_pdf: document.getElementById('downloadPdf').checked,
    pdf_dir: document.getElementById('pdfDir').value.trim() || 'papers'
  };
}

// 从 UI 收集服务配置
function collectServiceConfigFromUI() {
  return {
    services: {
      notion: document.getElementById('enableNotion').checked,
      zotero: document.getElementById('enableZotero').checked,
      wolai: document.getElementById('enableWolai').checked
    }
  };
}

// 初始化事件监听器
function initEventListeners() {
  // 保存环境变量配置
  document.getElementById('saveEnvConfig').addEventListener('click', async () => {
    const newEnvConfig = collectEnvConfigFromUI();
    try {
      await window.electronAPI.saveEnvConfig(newEnvConfig);
      envConfig = newEnvConfig;
      showToast('API 密钥配置已保存', 'success');
    } catch (error) {
      showToast('保存失败: ' + error.message, 'error');
    }
  });

  // 保存搜索配置
  document.getElementById('saveSearchConfig').addEventListener('click', async () => {
    const searchConfig = collectSearchConfigFromUI();
    try {
      config = { ...config, ...searchConfig };
      await window.electronAPI.saveConfig(config);
      showToast('搜索配置已保存', 'success');
    } catch (error) {
      showToast('保存失败: ' + error.message, 'error');
    }
  });

  // 保存服务配置
  document.getElementById('saveServiceConfig').addEventListener('click', async () => {
    const serviceConfig = collectServiceConfigFromUI();
    try {
      config = { ...config, ...serviceConfig };
      await window.electronAPI.saveConfig(config);
      showToast('服务配置已保存', 'success');
    } catch (error) {
      showToast('保存失败: ' + error.message, 'error');
    }
  });

  // 选择 PDF 目录
  document.getElementById('selectPdfDir').addEventListener('click', async () => {
    const dir = await window.electronAPI.selectDirectory();
    if (dir) {
      document.getElementById('pdfDir').value = dir;
    }
  });

  // Zotero 开关
  document.getElementById('enableZotero').addEventListener('change', updateZoteroCategoriesVisibility);

  // 添加分类映射
  document.getElementById('addCategoryMap').addEventListener('click', addCategoryMapItem);

  // 开始运行
  document.getElementById('startRun').addEventListener('click', startRun);

  // 停止运行
  document.getElementById('stopRun').addEventListener('click', stopRun);

  // 加载日志
  document.getElementById('loadLog').addEventListener('click', loadHistoryLog);

  // 设置默认日期
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('logDate').value = today;

  // 论文来源开关
  document.getElementById('enableArxiv').addEventListener('change', updateSourceConfig);
  document.getElementById('enableHf').addEventListener('change', updateSourceConfig);
}

// 更新 Zotero 分类显示
function updateZoteroCategoriesVisibility() {
  const zoteroEnabled = document.getElementById('enableZotero').checked;
  document.getElementById('zoteroCategories').style.display = zoteroEnabled ? 'block' : 'none';
}

// 渲染分类映射
function renderCategoryMap() {
  const container = document.getElementById('categoryMapContainer');
  container.innerHTML = '';

  if (config.category_map) {
    Object.entries(config.category_map).forEach(([tag, ids]) => {
      addCategoryMapItemWithData(tag, Array.isArray(ids) ? ids.join(', ') : ids);
    });
  }
}

// 添加分类映射项
function addCategoryMapItem() {
  addCategoryMapItemWithData('', '');
}

function addCategoryMapItemWithData(tag, ids) {
  const container = document.getElementById('categoryMapContainer');
  const item = document.createElement('div');
  item.className = 'category-map-item';
  item.innerHTML = `
    <input type="text" class="map-tag" placeholder="标签名称 (如: NLP)" value="${tag}">
    <input type="text" class="map-ids" placeholder="Zotero 分类 ID (逗号分隔)" value="${ids}">
    <button class="remove-btn" title="删除">×</button>
  `;

  item.querySelector('.remove-btn').addEventListener('click', () => {
    item.remove();
  });

  container.appendChild(item);
}

// 更新数据源配置
function updateSourceConfig() {
  config.noArxiv = !document.getElementById('enableArxiv').checked;
  config.noHf = !document.getElementById('enableHf').checked;
}

// 检查运行状态
async function checkRunningStatus() {
  try {
    const status = await window.electronAPI.getRunningStatus();
    updateRunningUI(status.isRunning);
  } catch (error) {
    console.error('检查运行状态失败:', error);
  }
}

// 更新运行 UI
function updateRunningUI(running) {
  isRunning = running;
  const startBtn = document.getElementById('startRun');
  const stopBtn = document.getElementById('stopRun');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  startBtn.disabled = running;
  stopBtn.disabled = !running;

  if (running) {
    statusDot.className = 'status-dot running';
    statusText.textContent = '运行中...';
  } else {
    statusDot.className = 'status-dot';
    statusText.textContent = '就绪';
  }
}

// 设置 Python 日志监听
function setupPythonLogListener() {
  window.electronAPI.onPythonLog((data) => {
    appendLog(data.message, data.type);
  });

  window.electronAPI.onPythonFinished((data) => {
    updateRunningUI(false);
    if (data.code === 0) {
      showToast('任务完成', 'success');
      appendLog('\n=== 任务完成 ===\n', 'success');
    } else {
      showToast('任务异常退出', 'error');
      appendLog('\n=== 任务异常退出 (代码: ' + data.code + ') ===\n', 'error');
    }
  });

  window.electronAPI.onPythonError((data) => {
    updateRunningUI(false);
    showToast('任务出错: ' + data.error, 'error');
    appendLog('\n错误: ' + data.error + '\n', 'error');
  });
}

// 追加日志
function appendLog(message, type = 'info') {
  const logContainer = document.getElementById('realtimeLog');

  // 清除占位符
  const placeholder = logContainer.querySelector('.log-placeholder');
  if (placeholder) {
    placeholder.remove();
  }

  const line = document.createElement('div');
  line.className = `log-line ${type}`;
  line.textContent = message;
  logContainer.appendChild(line);

  // 滚动到底部
  logContainer.scrollTop = logContainer.scrollHeight;
}

// 清除日志
function clearLog() {
  const logContainer = document.getElementById('realtimeLog');
  logContainer.innerHTML = '<div class="log-placeholder">点击"开始运行"后，日志将在此显示...</div>';
}

// 开始运行
async function startRun() {
  if (isRunning) return;

  // 先验证配置
  const validationConfig = {
    services: {
      notion: document.getElementById('enableNotion').checked,
      zotero: document.getElementById('enableZotero').checked,
      wolai: document.getElementById('enableWolai').checked
    },
    env: collectEnvConfigFromUI()
  };

  try {
    const validation = await window.electronAPI.validateConfig(validationConfig);
    if (!validation.valid) {
      showToast('配置验证失败:\n' + validation.errors.join('\n'), 'error');
      return;
    }
  } catch (error) {
    showToast('配置验证出错: ' + error.message, 'error');
    return;
  }

  // 清除旧日志
  clearLog();
  appendLog('=== 开始运行 ===\n', 'info');

  // 收集运行选项
  const options = {
    keywords: config.keywords || [],
    categories: config.categories || [],
    date: document.getElementById('runDate').value || null,
    days: parseInt(document.getElementById('runDays').value) || 1,
    limit: parseInt(document.getElementById('runLimit').value) || 10,
    downloadPdf: document.getElementById('runDownloadPdf').checked,
    pdfDir: config.pdf_dir || 'papers',
    noArxiv: document.getElementById('runNoArxiv').checked,
    noHf: document.getElementById('runNoHf').checked
  };

  updateRunningUI(true);

  try {
    await window.electronAPI.runPythonScript(options);
  } catch (error) {
    updateRunningUI(false);
    showToast('启动失败: ' + error.message, 'error');
    appendLog('\n启动失败: ' + error.message + '\n', 'error');
  }
}

// 停止运行
async function stopRun() {
  if (!isRunning) return;

  try {
    await window.electronAPI.stopPythonScript();
    appendLog('\n=== 用户停止任务 ===\n', 'warning');
    showToast('任务已停止', 'warning');
  } catch (error) {
    showToast('停止失败: ' + error.message, 'error');
  }
}

// 加载历史日志
async function loadHistoryLog() {
  const date = document.getElementById('logDate').value;
  const logContainer = document.getElementById('historyLog');

  if (!date) {
    showToast('请选择日期', 'warning');
    return;
  }

  try {
    const result = await window.electronAPI.readLogFile(date);
    if (result.success) {
      logContainer.innerHTML = '';
      const content = document.createElement('pre');
      content.textContent = result.content;
      content.style.margin = '0';
      logContainer.appendChild(content);
    } else {
      logContainer.innerHTML = `<div class="log-placeholder">${result.message}</div>`;
    }
  } catch (error) {
    showToast('加载日志失败: ' + error.message, 'error');
  }
}

// Toast 通知
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  // 3秒后自动移除
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

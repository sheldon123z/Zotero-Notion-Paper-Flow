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

// 初始化 - 移动到文件末尾统一处理

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
  // 初始化密码显示切换
  initPasswordToggles();

  // 初始化测试连接按钮
  initTestButtons();

  // 初始化配置导入/导出
  initConfigIO();

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

// ==================== 论文管理功能 ====================

let allPapers = [];
let filteredPapers = [];
let currentPage = 1;
const papersPerPage = 10;

// 初始化论文管理
async function initPapersTab() {
  await loadPapers();
  initPaperEventListeners();
}

// 加载论文数据
async function loadPapers() {
  try {
    allPapers = await window.electronAPI.getProcessedPapers();
    filteredPapers = [...allPapers];
    updatePaperStats();
    updateCategoryFilter();
    renderPapers();
  } catch (error) {
    console.error('加载论文失败:', error);
    document.getElementById('paperList').innerHTML =
      '<div class="paper-placeholder">加载论文失败，请稍后重试</div>';
  }
}

// 更新统计信息
function updatePaperStats() {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

  const todayPapers = allPapers.filter(p => {
    const date = new Date(p.published || p.date || p.created_at);
    return date >= today;
  });

  const weekPapers = allPapers.filter(p => {
    const date = new Date(p.published || p.date || p.created_at);
    return date >= weekAgo;
  });

  const categories = new Set();
  allPapers.forEach(p => {
    if (p.categories) {
      (Array.isArray(p.categories) ? p.categories : [p.categories]).forEach(c => categories.add(c));
    }
  });

  document.getElementById('totalPapers').textContent = allPapers.length;
  document.getElementById('todayPapers').textContent = todayPapers.length;
  document.getElementById('weekPapers').textContent = weekPapers.length;
  document.getElementById('categoriesCount').textContent = categories.size;
}

// 更新分类筛选器
function updateCategoryFilter() {
  const categories = new Set();
  allPapers.forEach(p => {
    if (p.categories) {
      (Array.isArray(p.categories) ? p.categories : [p.categories]).forEach(c => categories.add(c));
    }
  });

  const select = document.getElementById('paperCategoryFilter');
  select.innerHTML = '<option value="">全部分类</option>';
  Array.from(categories).sort().forEach(cat => {
    const option = document.createElement('option');
    option.value = cat;
    option.textContent = cat;
    select.appendChild(option);
  });
}

// 筛选论文
function filterPapers() {
  const searchText = document.getElementById('paperSearch').value.toLowerCase();
  const categoryFilter = document.getElementById('paperCategoryFilter').value;
  const dateFilter = document.getElementById('paperDateFilter').value;

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  filteredPapers = allPapers.filter(paper => {
    // 文本搜索
    if (searchText) {
      const title = (paper.title || '').toLowerCase();
      const authors = (Array.isArray(paper.authors) ? paper.authors.join(' ') : (paper.authors || '')).toLowerCase();
      const summary = (paper.summary || paper.abstract || '').toLowerCase();
      if (!title.includes(searchText) && !authors.includes(searchText) && !summary.includes(searchText)) {
        return false;
      }
    }

    // 分类筛选
    if (categoryFilter) {
      const cats = Array.isArray(paper.categories) ? paper.categories : [paper.categories];
      if (!cats.includes(categoryFilter)) {
        return false;
      }
    }

    // 日期筛选
    if (dateFilter) {
      const paperDate = new Date(paper.published || paper.date || paper.created_at);
      if (dateFilter === 'today' && paperDate < today) {
        return false;
      } else if (dateFilter === 'week') {
        const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
        if (paperDate < weekAgo) return false;
      } else if (dateFilter === 'month') {
        const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
        if (paperDate < monthAgo) return false;
      }
    }

    return true;
  });

  currentPage = 1;
  renderPapers();
}

// 渲染论文列表
function renderPapers() {
  const container = document.getElementById('paperList');

  if (filteredPapers.length === 0) {
    container.innerHTML = '<div class="paper-placeholder">没有找到论文</div>';
    renderPagination();
    return;
  }

  const start = (currentPage - 1) * papersPerPage;
  const end = start + papersPerPage;
  const pagePapers = filteredPapers.slice(start, end);

  container.innerHTML = pagePapers.map(paper => {
    const title = paper.title || '无标题';
    const authors = Array.isArray(paper.authors)
      ? paper.authors.slice(0, 3).join(', ') + (paper.authors.length > 3 ? ' 等' : '')
      : (paper.authors || '未知作者');
    const date = paper.published || paper.date || '';
    const summary = paper.tldr || paper.summary || paper.abstract || '';
    const categories = Array.isArray(paper.categories) ? paper.categories : (paper.categories ? [paper.categories] : []);
    const tags = Array.isArray(paper.tags) ? paper.tags : (paper.tags ? [paper.tags] : []);
    const arxivId = paper.id || paper.arxiv_id || '';
    const arxivUrl = arxivId ? `https://arxiv.org/abs/${arxivId.replace('arxiv:', '')}` : '';
    const pdfUrl = paper.pdf_url || (arxivId ? `https://arxiv.org/pdf/${arxivId.replace('arxiv:', '')}.pdf` : '');

    return `
      <div class="paper-item">
        <div class="paper-title">
          ${arxivUrl ? `<a href="#" data-url="${arxivUrl}">${title}</a>` : title}
        </div>
        <div class="paper-meta">
          <span class="paper-meta-item">👤 ${authors}</span>
          ${date ? `<span class="paper-meta-item">📅 ${formatDate(date)}</span>` : ''}
          ${arxivId ? `<span class="paper-meta-item">📑 ${arxivId}</span>` : ''}
        </div>
        ${summary ? `<div class="paper-summary">${summary}</div>` : ''}
        <div class="paper-tags">
          ${categories.map(c => `<span class="paper-tag category">${c}</span>`).join('')}
          ${tags.slice(0, 5).map(t => `<span class="paper-tag">${t}</span>`).join('')}
        </div>
        <div class="paper-actions">
          ${arxivUrl ? `<button class="btn btn-secondary" data-url="${arxivUrl}">打开 ArXiv</button>` : ''}
          ${pdfUrl ? `<button class="btn btn-secondary" data-url="${pdfUrl}">查看 PDF</button>` : ''}
        </div>
      </div>
    `;
  }).join('');

  // 绑定链接点击事件
  container.querySelectorAll('[data-url]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      window.electronAPI.openExternal(el.dataset.url);
    });
  });

  renderPagination();
}

// 渲染分页
function renderPagination() {
  const container = document.getElementById('pagination');
  const totalPages = Math.ceil(filteredPapers.length / papersPerPage);

  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }

  let html = `
    <button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">‹</button>
  `;

  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
      html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
    } else if (i === currentPage - 3 || i === currentPage + 3) {
      html += `<span class="pagination-info">...</span>`;
    }
  }

  html += `
    <button class="pagination-btn" ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">›</button>
  `;

  container.innerHTML = html;

  container.querySelectorAll('.pagination-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const page = parseInt(btn.dataset.page);
      if (page >= 1 && page <= totalPages) {
        currentPage = page;
        renderPapers();
      }
    });
  });
}

// 格式化日期
function formatDate(dateStr) {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
  } catch {
    return dateStr;
  }
}

// 初始化论文事件监听
function initPaperEventListeners() {
  document.getElementById('paperSearch').addEventListener('input', debounce(filterPapers, 300));
  document.getElementById('paperCategoryFilter').addEventListener('change', filterPapers);
  document.getElementById('paperDateFilter').addEventListener('change', filterPapers);
  document.getElementById('refreshPapers').addEventListener('click', loadPapers);
}

// 防抖函数
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// ==================== 定时任务功能 ====================

let schedulerConfig = {};

// 初始化定时任务
async function initSchedulerTab() {
  await loadSchedulerConfig();
  initSchedulerEventListeners();
}

// 加载定时任务配置
async function loadSchedulerConfig() {
  try {
    schedulerConfig = await window.electronAPI.getSchedulerConfig();
    applySchedulerConfigToUI();
  } catch (error) {
    console.error('加载定时任务配置失败:', error);
  }
}

// 应用定时任务配置到 UI
function applySchedulerConfigToUI() {
  document.getElementById('enableScheduler').checked = schedulerConfig.enabled || false;

  // 运行频率
  const scheduleType = schedulerConfig.type || 'daily';
  document.querySelectorAll('input[name="scheduleType"]').forEach(radio => {
    radio.checked = radio.value === scheduleType;
  });
  updateScheduleOptionsVisibility(scheduleType);

  // 每天配置
  document.getElementById('dailyTime').value = schedulerConfig.dailyTime || '08:00';

  // 每周配置
  document.getElementById('weeklyTime').value = schedulerConfig.weeklyTime || '08:00';
  const weekdays = schedulerConfig.weekdays || [];
  document.querySelectorAll('#weeklyOptions input[type="checkbox"]').forEach(cb => {
    cb.checked = weekdays.includes(parseInt(cb.value));
  });

  // 间隔配置
  document.getElementById('intervalValue').value = schedulerConfig.intervalValue || 6;
  document.getElementById('intervalUnit').value = schedulerConfig.intervalUnit || 'hours';

  // 任务设置
  document.getElementById('scheduleDays').value = schedulerConfig.days || 1;
  document.getElementById('scheduleLimit').value = schedulerConfig.limit || 20;
  document.getElementById('scheduleDownloadPdf').checked = schedulerConfig.downloadPdf !== false;
  document.getElementById('scheduleNotify').checked = schedulerConfig.notify !== false;

  // 系统设置
  document.getElementById('autoStart').checked = schedulerConfig.autoStart || false;
  document.getElementById('runInBackground').checked = schedulerConfig.runInBackground || false;

  // 更新状态显示
  updateSchedulerStatus();
}

// 从 UI 收集定时任务配置
function collectSchedulerConfigFromUI() {
  const scheduleType = document.querySelector('input[name="scheduleType"]:checked').value;

  const weekdays = [];
  document.querySelectorAll('#weeklyOptions input[type="checkbox"]:checked').forEach(cb => {
    weekdays.push(parseInt(cb.value));
  });

  return {
    enabled: document.getElementById('enableScheduler').checked,
    type: scheduleType,
    dailyTime: document.getElementById('dailyTime').value,
    weeklyTime: document.getElementById('weeklyTime').value,
    weekdays: weekdays,
    intervalValue: parseInt(document.getElementById('intervalValue').value) || 6,
    intervalUnit: document.getElementById('intervalUnit').value,
    days: parseInt(document.getElementById('scheduleDays').value) || 1,
    limit: parseInt(document.getElementById('scheduleLimit').value) || 20,
    downloadPdf: document.getElementById('scheduleDownloadPdf').checked,
    notify: document.getElementById('scheduleNotify').checked,
    autoStart: document.getElementById('autoStart').checked,
    runInBackground: document.getElementById('runInBackground').checked
  };
}

// 更新定时任务选项显示
function updateScheduleOptionsVisibility(type) {
  document.getElementById('dailyOptions').style.display = type === 'daily' ? 'block' : 'none';
  document.getElementById('weeklyOptions').style.display = type === 'weekly' ? 'block' : 'none';
  document.getElementById('intervalOptions').style.display = type === 'interval' ? 'block' : 'none';
}

// 更新定时任务状态
async function updateSchedulerStatus() {
  try {
    const status = await window.electronAPI.getSchedulerStatus();

    const statusEl = document.getElementById('schedulerStatus');
    statusEl.textContent = status.enabled ? '运行中' : '未启用';
    statusEl.className = `status-value ${status.enabled ? 'active' : 'inactive'}`;

    document.getElementById('nextRunTime').textContent = status.nextRun || '-';
    document.getElementById('lastRunTime').textContent = status.lastRun || '-';
    document.getElementById('lastRunResult').textContent = status.lastResult || '-';
  } catch (error) {
    console.error('获取定时任务状态失败:', error);
  }
}

// 初始化定时任务事件监听
function initSchedulerEventListeners() {
  // 运行频率切换
  document.querySelectorAll('input[name="scheduleType"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      updateScheduleOptionsVisibility(e.target.value);
    });
  });

  // 保存配置
  document.getElementById('saveSchedulerConfig').addEventListener('click', async () => {
    const newConfig = collectSchedulerConfigFromUI();
    try {
      await window.electronAPI.saveSchedulerConfig(newConfig);
      schedulerConfig = newConfig;
      await updateSchedulerStatus();
      showToast('定时任务配置已保存', 'success');
    } catch (error) {
      showToast('保存失败: ' + error.message, 'error');
    }
  });

  // 立即运行
  document.getElementById('runSchedulerNow').addEventListener('click', async () => {
    showToast('正在启动任务...', 'info');
    // 切换到运行标签页
    document.querySelector('[data-tab="run"]').click();
    // 触发运行
    document.getElementById('startRun').click();
  });
}

// ==================== 密码显示/隐藏切换 ====================

function initPasswordToggles() {
  document.querySelectorAll('.password-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.target;
      const input = document.getElementById(targetId);

      if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '🔒';
        btn.classList.add('visible');
      } else {
        input.type = 'password';
        btn.textContent = '👁';
        btn.classList.remove('visible');
      }
    });
  });
}

// ==================== API 连接测试 ====================

function initTestButtons() {
  document.querySelectorAll('.test-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const service = btn.dataset.service;
      await testServiceConnection(service, btn);
    });
  });
}

async function testServiceConnection(service, btn) {
  const originalText = btn.textContent;
  btn.textContent = '测试中...';
  btn.classList.add('testing');
  btn.classList.remove('success', 'error');

  try {
    const envData = collectEnvConfigFromUI();
    const result = await window.electronAPI.testConnection(service, envData);

    if (result.success) {
      btn.textContent = '连接成功';
      btn.classList.add('success');
      showToast(`${getServiceName(service)} 连接成功`, 'success');
    } else {
      btn.textContent = '连接失败';
      btn.classList.add('error');
      showToast(`${getServiceName(service)} 连接失败: ${result.message}`, 'error');
    }
  } catch (error) {
    btn.textContent = '连接失败';
    btn.classList.add('error');
    showToast(`测试失败: ${error.message}`, 'error');
  }

  // 3秒后恢复按钮状态
  setTimeout(() => {
    btn.textContent = originalText;
    btn.classList.remove('testing', 'success', 'error');
  }, 3000);
}

function getServiceName(service) {
  const names = {
    notion: 'Notion',
    llm: 'LLM',
    zotero: 'Zotero',
    wolai: '我来'
  };
  return names[service] || service;
}

// ==================== 配置导入/导出 ====================

function initConfigIO() {
  document.getElementById('exportConfig').addEventListener('click', exportConfig);
  document.getElementById('importConfig').addEventListener('click', importConfig);
}

async function exportConfig() {
  try {
    const envData = collectEnvConfigFromUI();
    const configData = {
      version: '1.0',
      exportDate: new Date().toISOString(),
      envConfig: envData,
      searchConfig: config
    };

    const result = await window.electronAPI.exportConfig(configData);
    if (result.success) {
      showToast('配置已导出', 'success');
    }
  } catch (error) {
    showToast('导出失败: ' + error.message, 'error');
  }
}

async function importConfig() {
  try {
    const result = await window.electronAPI.importConfig();

    if (result.success && result.data) {
      const importedData = result.data;

      // 应用导入的环境变量配置
      if (importedData.envConfig) {
        await window.electronAPI.saveEnvConfig(importedData.envConfig);
        envConfig = importedData.envConfig;
        applyEnvConfigToUI();
      }

      // 应用导入的搜索配置
      if (importedData.searchConfig) {
        config = { ...config, ...importedData.searchConfig };
        await window.electronAPI.saveConfig(config);
        applyConfigToUI();
      }

      showToast('配置已导入', 'success');
    } else if (result.canceled) {
      // 用户取消，不显示消息
    } else {
      showToast('导入失败: ' + (result.message || '未知错误'), 'error');
    }
  } catch (error) {
    showToast('导入失败: ' + error.message, 'error');
  }
}

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', async () => {
  initNavigation();
  initCategoryGrid();
  await loadConfig();
  await loadEnvConfig();
  await checkRunningStatus();
  initEventListeners();
  setupPythonLogListener();

  // 初始化论文管理和定时任务
  await initPapersTab();
  await initSchedulerTab();
});

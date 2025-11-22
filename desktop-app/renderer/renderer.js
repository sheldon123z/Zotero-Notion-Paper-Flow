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

// ==================== 国际化 (i18n) ====================

const i18n = {
  zh: {
    darkMode: '深色模式',
    lightMode: '浅色模式',
    ready: '就绪',
    running: '运行中...',
    'nav.logs': '日志',
    'nav.advanced': '高级设置',
    'logs.title': '历史日志',
    'logs.desc': '查看历史运行日志和运行记录',
    'logs.runHistory': '运行历史',
    'logs.clearHistory': '清空历史',
    'logs.noHistory': '暂无运行记录',
    'logs.selectDate': '选择日期',
    'logs.loadLog': '加载日志',
    'logs.exportLog': '导出日志',
    'logs.logPlaceholder': '选择日期后，日志将在此显示...',
    'advanced.title': '高级设置',
    'advanced.desc': '自定义 Prompt 模板、Webhook 通知等高级功能',
    'advanced.promptTemplates': 'LLM Prompt 模板',
    'advanced.promptHelp': '自定义 LLM 分析论文时使用的 Prompt 模板',
    'advanced.templateSummary': '摘要生成',
    'advanced.templateTranslation': '标题翻译',
    'advanced.templateKeywords': '关键词提取',
    'advanced.availableVars': '可用变量：',
    'advanced.saveTemplate': '保存模板',
    'advanced.resetTemplate': '恢复默认',
    'advanced.webhookTitle': 'Webhook 通知',
    'advanced.addWebhook': '+ 添加',
    'advanced.webhookHelp': '配置 Webhook URL 接收任务完成通知',
    'advanced.saveWebhooks': '保存 Webhook 配置',
    'advanced.testWebhook': '发送测试通知',
    'advanced.updateTitle': '软件更新',
    'advanced.autoUpdate': '自动检查更新',
    'advanced.autoUpdateDesc': '启动时自动检查新版本',
    'advanced.checkNow': '立即检查更新',
    'advanced.shortcuts': '快捷键',
    'advanced.shortcutsHelp': '按 ? 键可随时查看快捷键列表',
    'shortcuts.run': '开始运行',
    'shortcuts.stop': '停止任务',
    'shortcuts.save': '保存配置',
    'shortcuts.theme': '切换主题',
    'shortcuts.help': '显示快捷键',
    'update.available': '发现新版本可用！',
    'update.later': '稍后提醒',
    'update.download': '立即更新',
    'wizard.title': '欢迎使用 Paper Flow',
    'wizard.prev': '上一步',
    'wizard.next': '下一步',
    'wizard.skip': '跳过',
    'wizard.done': '完成',
    'toast.configSaved': '配置已保存',
    'toast.exportSuccess': '导出成功',
    'toast.webhookTestSent': '测试通知已发送'
  },
  en: {
    darkMode: 'Dark Mode',
    lightMode: 'Light Mode',
    ready: 'Ready',
    running: 'Running...',
    'nav.logs': 'Logs',
    'nav.advanced': 'Advanced',
    'logs.title': 'History Logs',
    'logs.desc': 'View history logs and run records',
    'logs.runHistory': 'Run History',
    'logs.clearHistory': 'Clear History',
    'logs.noHistory': 'No run records yet',
    'logs.selectDate': 'Select Date',
    'logs.loadLog': 'Load Log',
    'logs.exportLog': 'Export Log',
    'logs.logPlaceholder': 'Select a date to view logs...',
    'advanced.title': 'Advanced Settings',
    'advanced.desc': 'Custom Prompt templates, Webhook notifications and more',
    'advanced.promptTemplates': 'LLM Prompt Templates',
    'advanced.promptHelp': 'Customize prompts used by LLM for paper analysis',
    'advanced.templateSummary': 'Summary',
    'advanced.templateTranslation': 'Translation',
    'advanced.templateKeywords': 'Keywords',
    'advanced.availableVars': 'Available variables:',
    'advanced.saveTemplate': 'Save Template',
    'advanced.resetTemplate': 'Reset to Default',
    'advanced.webhookTitle': 'Webhook Notifications',
    'advanced.addWebhook': '+ Add',
    'advanced.webhookHelp': 'Configure Webhook URLs to receive task notifications',
    'advanced.saveWebhooks': 'Save Webhooks',
    'advanced.testWebhook': 'Send Test',
    'advanced.updateTitle': 'Software Updates',
    'advanced.autoUpdate': 'Auto-check Updates',
    'advanced.autoUpdateDesc': 'Check for updates on startup',
    'advanced.checkNow': 'Check Now',
    'advanced.shortcuts': 'Keyboard Shortcuts',
    'advanced.shortcutsHelp': 'Press ? to view shortcuts anytime',
    'shortcuts.run': 'Start Run',
    'shortcuts.stop': 'Stop Task',
    'shortcuts.save': 'Save Config',
    'shortcuts.theme': 'Toggle Theme',
    'shortcuts.help': 'Show Shortcuts',
    'update.available': 'New version available!',
    'update.later': 'Later',
    'update.download': 'Update Now',
    'wizard.title': 'Welcome to Paper Flow',
    'wizard.prev': 'Previous',
    'wizard.next': 'Next',
    'wizard.skip': 'Skip',
    'wizard.done': 'Done',
    'toast.configSaved': 'Config saved',
    'toast.exportSuccess': 'Export successful',
    'toast.webhookTestSent': 'Test notification sent'
  }
};

let currentLang = 'zh';

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('paperflow-lang', lang);

  // Update all elements with data-i18n attribute
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (i18n[lang][key]) {
      el.textContent = i18n[lang][key];
    }
  });

  // Update language buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
}

function t(key) {
  return i18n[currentLang][key] || key;
}

// ==================== 主题切换 ====================

function initTheme() {
  const savedTheme = localStorage.getItem('paperflow-theme') || 'light';
  setTheme(savedTheme);

  document.getElementById('themeToggle').addEventListener('click', () => {
    const currentTheme = document.documentElement.dataset.theme || 'light';
    setTheme(currentTheme === 'light' ? 'dark' : 'light');
  });
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('paperflow-theme', theme);

  const themeToggle = document.getElementById('themeToggle');
  const themeIcon = themeToggle.querySelector('.theme-icon');
  const themeText = themeToggle.querySelector('[data-i18n]');

  if (theme === 'dark') {
    themeIcon.textContent = '☀️';
    themeText.dataset.i18n = 'lightMode';
    themeText.textContent = t('lightMode');
  } else {
    themeIcon.textContent = '🌙';
    themeText.dataset.i18n = 'darkMode';
    themeText.textContent = t('darkMode');
  }
}

// ==================== 快捷键支持 ====================

function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const modifier = isMac ? e.metaKey : e.ctrlKey;

    // ? - 显示快捷键提示
    if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
      toggleShortcutHint();
      return;
    }

    // Ctrl/Cmd + R - 开始运行
    if (modifier && e.key === 'r') {
      e.preventDefault();
      if (!isRunning) {
        document.getElementById('startRun').click();
      }
      return;
    }

    // Ctrl/Cmd + S - 停止任务 (无 shift)
    if (modifier && e.key === 's' && !e.shiftKey) {
      e.preventDefault();
      if (isRunning) {
        document.getElementById('stopRun').click();
      }
      return;
    }

    // Ctrl/Cmd + Shift + S - 保存配置
    if (modifier && e.key === 'S' && e.shiftKey) {
      e.preventDefault();
      // 保存当前标签页的配置
      const activeTab = document.querySelector('.tab-content.active');
      if (activeTab) {
        const saveBtn = activeTab.querySelector('[id^="save"]');
        if (saveBtn) saveBtn.click();
      }
      return;
    }

    // Ctrl/Cmd + T - 切换主题
    if (modifier && e.key === 't') {
      e.preventDefault();
      document.getElementById('themeToggle').click();
      return;
    }

    // Escape - 关闭快捷键提示
    if (e.key === 'Escape') {
      document.getElementById('shortcutHint').classList.remove('visible');
      document.getElementById('wizardModal').classList.remove('active');
    }
  });
}

function toggleShortcutHint() {
  const hint = document.getElementById('shortcutHint');
  hint.classList.toggle('visible');

  // 3秒后自动隐藏
  if (hint.classList.contains('visible')) {
    setTimeout(() => {
      hint.classList.remove('visible');
    }, 5000);
  }
}

// ==================== 新手引导向导 ====================

const wizardSteps = [
  {
    icon: '👋',
    title: '欢迎使用 Paper Flow',
    titleEn: 'Welcome to Paper Flow',
    description: 'Paper Flow 是一个自动化论文管理工具，帮助您自动抓取、分析和整理学术论文。',
    descriptionEn: 'Paper Flow is an automated paper management tool that helps you fetch, analyze, and organize academic papers.'
  },
  {
    icon: '🔑',
    title: '配置 API 密钥',
    titleEn: 'Configure API Keys',
    description: '首先需要配置 Notion 和 LLM 服务的 API 密钥。点击侧边栏的"API 密钥"标签开始配置。',
    descriptionEn: 'First, configure your Notion and LLM API keys. Click "API Keys" in the sidebar to start.'
  },
  {
    icon: '🔍',
    title: '设置搜索条件',
    titleEn: 'Set Search Criteria',
    description: '在"搜索配置"中设置您感兴趣的关键词和 ArXiv 分类，系统将自动抓取相关论文。',
    descriptionEn: 'Set your keywords and ArXiv categories in "Search Config". The system will fetch relevant papers automatically.'
  },
  {
    icon: '🚀',
    title: '开始使用',
    titleEn: 'Get Started',
    description: '配置完成后，点击"运行"标签页启动论文抓取任务。您也可以在"定时任务"中设置自动运行计划。',
    descriptionEn: 'After configuration, click "Run" to start fetching papers. You can also set up scheduled tasks in "Scheduler".'
  }
];

let currentWizardStep = 0;

function initWizard() {
  const isFirstTime = !localStorage.getItem('paperflow-wizard-completed');

  if (isFirstTime) {
    setTimeout(() => {
      showWizard();
    }, 500);
  }

  document.getElementById('closeWizard').addEventListener('click', closeWizard);
  document.getElementById('wizardPrev').addEventListener('click', prevWizardStep);
  document.getElementById('wizardNext').addEventListener('click', nextWizardStep);

  // 点击 overlay 关闭
  document.getElementById('wizardModal').addEventListener('click', (e) => {
    if (e.target.id === 'wizardModal') {
      closeWizard();
    }
  });
}

function showWizard() {
  currentWizardStep = 0;
  updateWizardContent();
  document.getElementById('wizardModal').classList.add('active');
}

function closeWizard() {
  document.getElementById('wizardModal').classList.remove('active');
  localStorage.setItem('paperflow-wizard-completed', 'true');
}

function updateWizardContent() {
  const step = wizardSteps[currentWizardStep];
  const content = document.getElementById('wizardContent');

  const title = currentLang === 'en' ? step.titleEn : step.title;
  const description = currentLang === 'en' ? step.descriptionEn : step.description;

  content.innerHTML = `
    <div class="wizard-icon">${step.icon}</div>
    <div class="wizard-title">${title}</div>
    <div class="wizard-description">${description}</div>
  `;

  // 更新步骤指示器
  document.querySelectorAll('.wizard-step').forEach((el, i) => {
    el.classList.remove('active', 'completed');
    if (i < currentWizardStep) {
      el.classList.add('completed');
    } else if (i === currentWizardStep) {
      el.classList.add('active');
    }
  });

  // 更新按钮
  const prevBtn = document.getElementById('wizardPrev');
  const nextBtn = document.getElementById('wizardNext');

  prevBtn.style.visibility = currentWizardStep === 0 ? 'hidden' : 'visible';

  if (currentWizardStep === wizardSteps.length - 1) {
    nextBtn.textContent = t('wizard.done');
  } else {
    nextBtn.textContent = t('wizard.next');
  }
}

function prevWizardStep() {
  if (currentWizardStep > 0) {
    currentWizardStep--;
    updateWizardContent();
  }
}

function nextWizardStep() {
  if (currentWizardStep < wizardSteps.length - 1) {
    currentWizardStep++;
    updateWizardContent();
  } else {
    closeWizard();
  }
}

// ==================== 运行历史 ====================

let runHistory = [];

async function initRunHistory() {
  runHistory = await window.electronAPI.getRunHistory();
  renderRunHistory();

  document.getElementById('clearHistory').addEventListener('click', clearRunHistory);
}

function renderRunHistory() {
  const container = document.getElementById('historyList');

  if (!runHistory || runHistory.length === 0) {
    container.innerHTML = `<div class="paper-placeholder">${t('logs.noHistory')}</div>`;
    return;
  }

  container.innerHTML = runHistory.slice(0, 20).map(item => `
    <div class="history-item">
      <div class="history-status ${item.status}"></div>
      <div class="history-info">
        <div class="history-time">${formatDateTime(new Date(item.startTime))}</div>
        <div class="history-detail">
          ${item.papersProcessed || 0} 篇论文 · ${item.duration || '-'}
        </div>
      </div>
      <div class="history-actions">
        <button class="btn btn-sm btn-secondary" onclick="viewHistoryLog('${item.logFile}')">查看日志</button>
      </div>
    </div>
  `).join('');
}

async function clearRunHistory() {
  if (confirm(currentLang === 'en' ? 'Clear all run history?' : '确定要清空所有运行历史吗？')) {
    await window.electronAPI.clearRunHistory();
    runHistory = [];
    renderRunHistory();
    showToast(currentLang === 'en' ? 'History cleared' : '历史已清空', 'success');
  }
}

function addRunHistoryEntry(entry) {
  runHistory.unshift(entry);
  renderRunHistory();
  window.electronAPI.saveRunHistory(runHistory);
}

function viewHistoryLog(logFile) {
  // 加载并显示特定日志
  document.getElementById('logDate').value = logFile;
  loadHistoryLog();
}

// ==================== 日志导出 ====================

async function initLogExport() {
  document.getElementById('exportLog').addEventListener('click', exportCurrentLog);
}

async function exportCurrentLog() {
  const logContainer = document.getElementById('historyLog');
  const content = logContainer.textContent;

  if (!content || content.includes('选择日期后')) {
    showToast(currentLang === 'en' ? 'No log to export' : '没有可导出的日志', 'warning');
    return;
  }

  const date = document.getElementById('logDate').value || new Date().toISOString().slice(0, 10);

  try {
    const result = await window.electronAPI.exportLog({
      content,
      filename: `paper-flow-log-${date}.txt`
    });

    if (result.success) {
      showToast(t('toast.exportSuccess'), 'success');
    }
  } catch (error) {
    showToast('Export failed: ' + error.message, 'error');
  }
}

// ==================== LLM Prompt 模板 ====================

const defaultPromptTemplates = {
  summary: `请分析以下论文并生成简洁的中文摘要：

标题：{title}
摘要：{abstract}
作者：{authors}
分类：{categories}

请用 2-3 句话概括论文的核心贡献和主要方法。`,
  translation: `请将以下英文论文标题翻译成中文，保持学术准确性：

{title}`,
  keywords: `请从以下论文中提取 5-8 个关键词：

标题：{title}
摘要：{abstract}

请以逗号分隔输出关键词。`
};

let promptTemplates = { ...defaultPromptTemplates };
let currentTemplateType = 'summary';

async function initPromptTemplates() {
  // 加载保存的模板
  const saved = await window.electronAPI.getPromptTemplates();
  if (saved) {
    promptTemplates = { ...defaultPromptTemplates, ...saved };
  }

  // 初始化 UI
  document.getElementById('promptTemplate').value = promptTemplates[currentTemplateType];

  // 模板类型切换
  document.querySelectorAll('.template-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      document.querySelectorAll('.template-tag').forEach(t => t.classList.remove('active'));
      tag.classList.add('active');
      currentTemplateType = tag.dataset.template;
      document.getElementById('promptTemplate').value = promptTemplates[currentTemplateType];
    });
  });

  // 变量点击插入
  document.querySelectorAll('.variable-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      const textarea = document.getElementById('promptTemplate');
      const varText = tag.dataset.var;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = textarea.value;
      textarea.value = text.substring(0, start) + varText + text.substring(end);
      textarea.focus();
      textarea.setSelectionRange(start + varText.length, start + varText.length);
    });
  });

  // 保存按钮
  document.getElementById('savePromptTemplate').addEventListener('click', async () => {
    promptTemplates[currentTemplateType] = document.getElementById('promptTemplate').value;
    await window.electronAPI.savePromptTemplates(promptTemplates);
    showToast(t('toast.configSaved'), 'success');
  });

  // 重置按钮
  document.getElementById('resetPromptTemplate').addEventListener('click', () => {
    promptTemplates[currentTemplateType] = defaultPromptTemplates[currentTemplateType];
    document.getElementById('promptTemplate').value = promptTemplates[currentTemplateType];
    showToast(currentLang === 'en' ? 'Reset to default' : '已恢复默认', 'success');
  });
}

// ==================== Webhook 配置 ====================

let webhooks = [];

async function initWebhooks() {
  webhooks = await window.electronAPI.getWebhooks() || [];
  renderWebhooks();

  document.getElementById('addWebhook').addEventListener('click', addWebhook);
  document.getElementById('saveWebhooks').addEventListener('click', saveWebhooks);
  document.getElementById('testWebhook').addEventListener('click', testWebhook);
}

function renderWebhooks() {
  const container = document.getElementById('webhookList');

  if (webhooks.length === 0) {
    container.innerHTML = `<div class="paper-placeholder">点击"+ 添加"创建第一个 Webhook</div>`;
    return;
  }

  container.innerHTML = webhooks.map((webhook, index) => `
    <div class="webhook-item" data-index="${index}">
      <div class="form-group flex-grow">
        <input type="text" class="webhook-url" value="${webhook.url}" placeholder="https://your-webhook-url.com">
      </div>
      <div class="form-group">
        <div class="webhook-events">
          <label class="webhook-event-label">
            <input type="checkbox" class="webhook-event" value="success" ${webhook.events?.includes('success') ? 'checked' : ''}>
            <span>成功</span>
          </label>
          <label class="webhook-event-label">
            <input type="checkbox" class="webhook-event" value="error" ${webhook.events?.includes('error') ? 'checked' : ''}>
            <span>失败</span>
          </label>
        </div>
      </div>
      <button class="btn btn-sm btn-danger" onclick="removeWebhook(${index})">删除</button>
    </div>
  `).join('');
}

function addWebhook() {
  webhooks.push({ url: '', events: ['success', 'error'] });
  renderWebhooks();
}

function removeWebhook(index) {
  webhooks.splice(index, 1);
  renderWebhooks();
}

async function saveWebhooks() {
  // 收集表单数据
  const items = document.querySelectorAll('.webhook-item');
  webhooks = Array.from(items).map(item => ({
    url: item.querySelector('.webhook-url').value.trim(),
    events: Array.from(item.querySelectorAll('.webhook-event:checked')).map(cb => cb.value)
  })).filter(w => w.url);

  await window.electronAPI.saveWebhooks(webhooks);
  showToast(t('toast.configSaved'), 'success');
}

async function testWebhook() {
  if (webhooks.length === 0 || !webhooks[0].url) {
    showToast(currentLang === 'en' ? 'Please add a webhook first' : '请先添加 Webhook', 'warning');
    return;
  }

  const result = await window.electronAPI.testWebhook(webhooks[0].url);
  if (result.success) {
    showToast(t('toast.webhookTestSent'), 'success');
  } else {
    showToast('Test failed: ' + result.message, 'error');
  }
}

// ==================== 自动更新 ====================

async function initAutoUpdate() {
  // 获取当前版本
  const version = await window.electronAPI.getAppVersion();
  document.getElementById('currentVersion').textContent = `当前版本: v${version}`;

  // 检查更新设置
  const autoCheck = localStorage.getItem('paperflow-auto-update') !== 'false';
  document.getElementById('autoCheckUpdate').checked = autoCheck;

  document.getElementById('autoCheckUpdate').addEventListener('change', (e) => {
    localStorage.setItem('paperflow-auto-update', e.target.checked);
  });

  document.getElementById('checkUpdate').addEventListener('click', checkForUpdates);
  document.getElementById('dismissUpdate').addEventListener('click', () => {
    document.getElementById('updateBanner').classList.remove('visible');
  });
  document.getElementById('downloadUpdate').addEventListener('click', downloadUpdate);

  // 启动时检查更新
  if (autoCheck) {
    setTimeout(checkForUpdates, 3000);
  }
}

async function checkForUpdates() {
  const btn = document.getElementById('checkUpdate');
  btn.textContent = currentLang === 'en' ? 'Checking...' : '检查中...';
  btn.disabled = true;

  try {
    const result = await window.electronAPI.checkForUpdates();

    if (result.hasUpdate) {
      document.getElementById('updateMessage').textContent =
        currentLang === 'en'
          ? `New version ${result.version} available!`
          : `发现新版本 ${result.version}！`;
      document.getElementById('updateBanner').classList.add('visible');
    } else {
      showToast(currentLang === 'en' ? 'You are up to date!' : '已是最新版本', 'success');
    }
  } catch (error) {
    showToast('Check failed: ' + error.message, 'error');
  }

  btn.textContent = t('advanced.checkNow');
  btn.disabled = false;
}

async function downloadUpdate() {
  await window.electronAPI.downloadUpdate();
}

// ==================== 语言切换初始化 ====================

function initLanguageSwitch() {
  const savedLang = localStorage.getItem('paperflow-lang') || 'zh';
  setLanguage(savedLang);

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      setLanguage(btn.dataset.lang);
    });
  });
}

// ==================== 格式化日期时间 ====================

function formatDateTime(date) {
  return date.toLocaleString(currentLang === 'en' ? 'en-US' : 'zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', async () => {
  // 基础初始化
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

  // 初始化高级功能
  initTheme();
  initLanguageSwitch();
  initKeyboardShortcuts();
  initWizard();
  await initRunHistory();
  initLogExport();
  await initPromptTemplates();
  await initWebhooks();
  await initAutoUpdate();
});

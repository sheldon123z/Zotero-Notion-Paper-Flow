const { contextBridge, ipcRenderer, shell } = require('electron');

// 安全地暴露 API 到渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 配置管理
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  getEnvConfig: () => ipcRenderer.invoke('get-env-config'),
  saveEnvConfig: (envConfig) => ipcRenderer.invoke('save-env-config', envConfig),
  validateConfig: (config) => ipcRenderer.invoke('validate-config', config),

  // 运行控制
  runPythonScript: (options) => ipcRenderer.invoke('run-python-script', options),
  stopPythonScript: () => ipcRenderer.invoke('stop-python-script'),
  getRunningStatus: () => ipcRenderer.invoke('get-running-status'),

  // 日志
  onPythonLog: (callback) => {
    ipcRenderer.on('python-log', (event, data) => callback(data));
  },
  onPythonFinished: (callback) => {
    ipcRenderer.on('python-finished', (event, data) => callback(data));
  },
  onPythonError: (callback) => {
    ipcRenderer.on('python-error', (event, data) => callback(data));
  },
  removePythonListeners: () => {
    ipcRenderer.removeAllListeners('python-log');
    ipcRenderer.removeAllListeners('python-finished');
    ipcRenderer.removeAllListeners('python-error');
  },

  // 文件操作
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  readLogFile: (date) => ipcRenderer.invoke('read-log-file', date),
  getProcessedPapers: () => ipcRenderer.invoke('get-processed-papers'),

  // 定时任务
  getSchedulerConfig: () => ipcRenderer.invoke('get-scheduler-config'),
  saveSchedulerConfig: (config) => ipcRenderer.invoke('save-scheduler-config', config),
  getSchedulerStatus: () => ipcRenderer.invoke('get-scheduler-status'),

  // 系统功能
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  setAutoStart: (enable) => ipcRenderer.invoke('set-auto-start', enable),
  getAutoStartStatus: () => ipcRenderer.invoke('get-auto-start-status'),
});

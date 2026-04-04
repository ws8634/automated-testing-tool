import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// 规则管理 API
export const rulesApi = {
  // 获取规则列表
  list: (params) => api.get('/rules', { params }),
  // 获取规则详情
  get: (id) => api.get(`/rules/${id}`),
  // 创建规则
  create: (data) => api.post('/rules', data),
  // 更新规则
  update: (id, data) => api.patch(`/rules/${id}`, data),
  // 删除规则
  delete: (id) => api.delete(`/rules/${id}`),
  // 获取分类
  categories: () => api.get('/rules/categories'),
  // 获取风险等级
  severities: () => api.get('/rules/severities'),
}

// 扫描 API
export const scansApi = {
  // 创建扫描任务
  create: (data) => api.post('/scans', data),
  // 获取任务列表
  list: (params) => api.get('/scans/tasks', { params }),
  // 获取任务结果
  get: (id) => api.get(`/scans/tasks/${id}`),
  // 删除任务
  delete: (id) => api.delete(`/scans/tasks/${id}`),
  // 保存任务结果为报告
  saveReport: (id) => api.post(`/scans/tasks/${id}/save-report`),
}

// 报告 API
export const reportsApi = {
  // 获取报告列表
  list: (params) => api.get('/reports', { params }),
  // 获取报告详情
  get: (id) => api.get(`/reports/${id}`),
  // 获取报告 HTML
  getHtml: (id) => api.get(`/reports/${id}/html`),
  // 保存报告
  save: (data) => api.post('/reports/save', data),
  // 删除报告
  delete: (id) => api.delete(`/reports/${id}`),
  // 导出报告
  export: (id, format = 'html') => api.get(`/reports/${id}/export?format=${format}`),
}

// 统计 API
export const statsApi = {
  // 获取统计信息
  get: () => api.get('/stats'),
  // 获取趋势
  trends: (days) => api.get('/stats/trends', { params: { days } }),
  // 获取 Dashboard 数据
  dashboard: () => api.get('/stats/dashboard'),
}

export default api

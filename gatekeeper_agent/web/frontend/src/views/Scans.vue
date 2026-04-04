<template>
  <div class="scans-page">
    <!-- 操作栏 -->
    <el-card class="action-card">
      <el-row justify="space-between" align="middle">
        <el-col>
          <h3>扫描任务管理</h3>
        </el-col>
        <el-col style="text-align: right;">
          <el-button type="primary" @click="handleCreateScan">
            <el-icon><Plus /></el-icon>
            新建扫描
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 任务列表 -->
    <el-card class="tasks-card">
      <el-table v-loading="loading" :data="tasks" style="width: 100%">
        <el-table-column prop="task_id" label="任务ID" width="280">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewDetail(row)">
              {{ row.task_id.substring(0, 8) }}...
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" effect="dark">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetail(row)">查看</el-button>
            <el-button 
              v-if="row.status === 'completed'" 
              link 
              type="success" 
              @click="handleSaveReport(row)"
            >
              保存报告
            </el-button>
            <el-button link type="danger" @click="handleDeleteTask(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 扫描结果对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="扫描结果"
      width="900px"
      destroy-on-close
    >
      <div v-if="currentResult" class="scan-result">
        <!-- 统计 -->
        <el-row :gutter="20" class="result-stats">
          <el-col :span="4">
            <div class="stat-box">
              <div class="stat-num">{{ currentResult.summary?.total_files || 0 }}</div>
              <div class="stat-label">文件数</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-box fatal">
              <div class="stat-num">{{ currentResult.summary?.fatal_count || 0 }}</div>
              <div class="stat-label">Fatal</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-box error">
              <div class="stat-num">{{ currentResult.summary?.error_count || 0 }}</div>
              <div class="stat-label">Error</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-box warning">
              <div class="stat-num">{{ currentResult.summary?.warning_count || 0 }}</div>
              <div class="stat-label">Warning</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-box info">
              <div class="stat-num">{{ currentResult.summary?.info_count || 0 }}</div>
              <div class="stat-label">Info</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="stat-box" :class="{ danger: currentResult.has_blocking_violations }">
              <div class="stat-num">
                <el-icon v-if="currentResult.has_blocking_violations" color="#dc3545" size="24">
                  <CircleClose />
                </el-icon>
                <el-icon v-else color="#28a745" size="24"><CircleCheck /></el-icon>
              </div>
              <div class="stat-label">{{ currentResult.has_blocking_violations ? '有阻断' : '通过' }}</div>
            </div>
          </el-col>
        </el-row>

        <!-- 违规列表 -->
        <div v-if="currentResult.violations?.length" class="violations-section">
          <h4>违规详情 ({{ currentResult.violations.length }})</h4>
          <el-collapse>
            <el-collapse-item
              v-for="(v, index) in currentResult.violations"
              :key="index"
              :title="`${v.rule_name} - ${v.file_path || 'N/A'}:${v.location?.line_number || 0}`"
            >
              <div class="violation-detail">
                <p><strong>规则ID:</strong> {{ v.rule_id }}</p>
                <p><strong>风险等级:</strong> 
                  <el-tag :type="getSeverityType(v.severity)" size="small" effect="dark">
                    {{ v.severity.toUpperCase() }}
                  </el-tag>
                </p>
                <p><strong>分类:</strong> {{ v.category }}</p>
                <p><strong>描述:</strong> {{ v.message }}</p>
                <div v-if="v.matched_content" class="code-block">
                  <pre>{{ v.matched_content }}</pre>
                </div>
                <div v-if="v.suggested_fix" class="suggested-fix">
                  <strong>修复建议:</strong>
                  <pre>{{ v.suggested_fix }}</pre>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <el-empty v-else description="未发现违规项，代码审核通过！" />

        <!-- 操作按钮 -->
        <div v-if="currentTask?.status === 'completed'" class="dialog-actions">
          <el-button type="success" @click="saveReportFromDialog">
            <el-icon><Document /></el-icon>
            保存报告
          </el-button>
          <el-button @click="resultDialogVisible = false">关闭</el-button>
        </div>
      </div>

      <div v-else-if="currentTask?.status === 'pending'" class="status-pending">
        <el-icon class="loading-icon" size="48" color="#667eea"><Loading /></el-icon>
        <p>扫描任务等待中...</p>
      </div>

      <div v-else-if="currentTask?.status === 'running'" class="status-running">
        <el-icon class="loading-icon" size="48" color="#667eea"><Loading /></el-icon>
        <p>正在扫描中...</p>
      </div>

      <div v-else-if="currentTask?.status === 'failed'" class="status-failed">
        <el-icon size="48" color="#dc3545"><CircleClose /></el-icon>
        <p>扫描失败</p>
        <p class="error-message">{{ currentTask.error }}</p>
      </div>
    </el-dialog>

    <!-- 新建扫描对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建扫描任务"
      width="500px"
    >
      <el-form :model="newScan" label-width="100px">
        <el-form-item label="扫描类型">
          <el-select v-model="newScan.scan_type" style="width: 100%">
            <el-option label="暂存区 (Staged)" value="staged" />
            <el-option label="Git Diff" value="diff" />
            <el-option label="目录扫描" value="directory" />
            <el-option label="单个文件" value="file" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标路径">
          <el-input v-model="newScan.target" placeholder="输入路径，如: /home/wangsen/programe/ds-mcdonald/" />
        </el-form-item>
        <el-form-item v-if="newScan.scan_type === 'diff'" label="源分支">
          <el-input v-model="newScan.source" placeholder="可选，用于Git Diff" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCreate" :loading="creating">开始扫描</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { scansApi } from '../api'

const route = useRoute()

const loading = ref(false)
const tasks = ref([])
const resultDialogVisible = ref(false)
const createDialogVisible = ref(false)
const creating = ref(false)
const currentTask = ref(null)
const currentResult = ref(null)
const newScan = ref({
  scan_type: 'staged',
  target: '.',
  source: ''
})

let pollTimer = null

// 获取任务列表
const fetchTasks = async () => {
  try {
    const res = await scansApi.list({ limit: 20 })
    tasks.value = res
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

// 获取任务结果
const fetchTaskResult = async (taskId) => {
  try {
    const res = await scansApi.get(taskId)
    currentTask.value = res
    if (res.status === 'completed') {
      currentResult.value = res.result
    }
    return res.status
  } catch (error) {
    ElMessage.error('获取扫描结果失败')
    return 'failed'
  }
}

// 查看详情
const handleViewDetail = async (row) => {
  resultDialogVisible.value = true
  currentTask.value = row
  currentResult.value = null
  
  const status = await fetchTaskResult(row.task_id)
  
  // 如果任务还在进行中，轮询结果
  if (status === 'pending' || status === 'running') {
    startPolling(row.task_id)
  }
}

// 轮询结果
const startPolling = (taskId) => {
  stopPolling()
  pollTimer = setInterval(async () => {
    const status = await fetchTaskResult(taskId)
    if (status === 'completed' || status === 'failed') {
      stopPolling()
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 创建扫描
const handleCreateScan = () => {
  createDialogVisible.value = true
}

const confirmCreate = async () => {
  creating.value = true
  try {
    const res = await scansApi.create(newScan.value)
    ElMessage.success('扫描任务已创建')
    createDialogVisible.value = false
    fetchTasks()
    // 自动打开结果查看
    handleViewDetail({ task_id: res.task_id, status: 'pending', created_at: new Date().toISOString() })
  } catch (error) {
    ElMessage.error(error.message || '创建失败')
  } finally {
    creating.value = false
  }
}

// 删除任务
const handleDeleteTask = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个扫描任务吗？', '确认删除', { type: 'warning' })
    await scansApi.delete(row.task_id)
    ElMessage.success('任务已删除')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 保存报告
const handleSaveReport = async (row) => {
  try {
    const res = await scansApi.saveReport(row.task_id)
    ElMessage.success(`报告已保存: ${res.report_id}`)
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  }
}

// 从对话框保存报告
const saveReportFromDialog = async () => {
  if (!currentTask.value) return
  try {
    const res = await scansApi.saveReport(currentTask.value.task_id)
    ElMessage.success(`报告已保存: ${res.report_id}`)
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  }
}

// 状态样式
const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const labels = {
    pending: '等待中',
    running: '扫描中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

// 风险等级样式
const getSeverityType = (severity) => {
  const types = {
    fatal: 'danger',
    error: 'warning',
    warning: '',
    info: 'info'
  }
  return types[severity] || ''
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchTasks()
  
  // 如果 URL 带有 action=create 参数，自动打开新建对话框
  if (route.query.action === 'create') {
    handleCreateScan()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.scans-page {
  padding-bottom: 24px;
}

.action-card {
  margin-bottom: 20px;
}

.action-card h3 {
  margin: 0;
  color: #303133;
}

.result-stats {
  margin-bottom: 24px;
}

.stat-box {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.stat-box.fatal {
  background: rgba(220, 53, 69, 0.1);
}

.stat-box.fatal .stat-num {
  color: #dc3545;
}

.stat-box.error {
  background: rgba(253, 126, 20, 0.1);
}

.stat-box.error .stat-num {
  color: #fd7e14;
}

.stat-box.warning {
  background: rgba(255, 193, 7, 0.1);
}

.stat-box.warning .stat-num {
  color: #ffc107;
}

.stat-box.info {
  background: rgba(23, 162, 184, 0.1);
}

.stat-box.info .stat-num {
  color: #17a2b8;
}

.stat-box.danger {
  background: rgba(220, 53, 69, 0.1);
}

.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.violations-section {
  margin-top: 24px;
}

.violations-section h4 {
  margin-bottom: 16px;
  color: #303133;
}

.violation-detail {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.violation-detail p {
  margin: 8px 0;
  color: #606266;
}

.code-block, .suggested-fix {
  margin-top: 12px;
  background: #2d2d2d;
  color: #f8f8f2;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.code-block pre, .suggested-fix pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.suggested-fix {
  background: #d4edda;
  color: #155724;
}

.status-pending, .status-running, .status-failed {
  text-align: center;
  padding: 40px;
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-message {
  color: #dc3545;
  margin-top: 16px;
  padding: 12px;
  background: #f8d7da;
  border-radius: 4px;
}

.dialog-actions {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

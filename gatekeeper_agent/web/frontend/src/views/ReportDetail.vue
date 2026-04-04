<template>
  <div class="report-detail">
    <div class="page-header">
      <el-button link @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        返回报告列表
      </el-button>
      <span class="page-title">报告详情</span>
    </div>

    <el-card v-loading="loading" class="detail-card">
      <template v-if="report">
        <div class="report-header">
          <div class="report-title">
            <h2>扫描报告</h2>
            <el-tag v-if="report.has_blocking" type="danger" effect="dark">有阻断性违规</el-tag>
            <el-tag v-else type="success" effect="dark">审核通过</el-tag>
          </div>
          <div class="report-actions">
            <el-button type="primary" @click="refreshReport">刷新</el-button>
          </div>
        </div>

        <el-descriptions :column="3" border class="report-info">
          <el-descriptions-item label="报告ID">{{ report.report_id }}</el-descriptions-item>
          <el-descriptions-item label="扫描ID">{{ report.scan_id }}</el-descriptions-item>
          <el-descriptions-item label="生成时间">{{ formatTime(report.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="扫描文件">{{ report.total_files }} 个</el-descriptions-item>
          <el-descriptions-item label="总违规数">{{ report.total_violations }} 个</el-descriptions-item>
          <el-descriptions-item label="来源">{{ report.source_type || 'Git Staged' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 违规统计 -->
        <div class="stats-section">
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-card fatal">
                <div class="stat-value">{{ report.fatal_count || 0 }}</div>
                <div class="stat-label">Fatal</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card error">
                <div class="stat-value">{{ report.error_count || 0 }}</div>
                <div class="stat-label">Error</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card warning">
                <div class="stat-value">{{ report.warning_count || 0 }}</div>
                <div class="stat-label">Warning</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card info">
                <div class="stat-value">{{ report.info_count || 0 }}</div>
                <div class="stat-label">Info</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 违规详情 -->
        <div v-if="report.violations?.length" class="violations-section">
          <h3>违规详情</h3>
          <el-timeline>
            <el-timeline-item
              v-for="(v, index) in report.violations"
              :key="index"
              :type="getTimelineType(v.severity)"
              :color="getSeverityColor(v.severity)"
            >
              <el-card class="violation-card">
                <template #header>
                  <div class="violation-header">
                    <span class="violation-title">{{ v.rule_name }}</span>
                    <el-tag :type="getSeverityType(v.severity)" size="small" effect="dark">
                      {{ v.severity.toUpperCase() }}
                    </el-tag>
                  </div>
                </template>
                <div class="violation-content">
                  <p><strong>规则ID:</strong> {{ v.rule_id }}</p>
                  <p><strong>分类:</strong> {{ v.category }}</p>
                  <p><strong>文件:</strong> {{ v.file_path || 'N/A' }}:{{ v.location?.line_number || 0 }}</p>
                  <p class="violation-message">{{ v.message }}</p>
                  <div v-if="v.matched_content" class="code-block">
                    <div class="code-header">违规代码</div>
                    <pre>{{ v.matched_content }}</pre>
                  </div>
                  <div v-if="v.suggested_fix" class="suggested-fix">
                    <div class="fix-header">修复建议</div>
                    <pre>{{ v.suggested_fix }}</pre>
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>

        <el-empty v-else description="未发现违规项，代码审核通过！" />
      </template>

      <el-empty v-else description="报告不存在或已删除" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { reportsApi } from '../api'

const route = useRoute()
const loading = ref(false)
const report = ref(null)

// 获取报告详情
const fetchReport = async () => {
  loading.value = true
  try {
    const res = await reportsApi.get(route.params.id)
    report.value = res
  } catch (error) {
    ElMessage.error('获取报告详情失败')
  } finally {
    loading.value = false
  }
}

// 刷新报告
const refreshReport = () => {
  fetchReport()
}

// 返回按钮处理
const handleBack = () => {
  router.push('/reports')
}

// 获取时间线类型
const getTimelineType = (severity) => {
  const types = {
    fatal: 'danger',
    error: 'warning',
    warning: 'primary',
    info: 'info'
  }
  return types[severity] || 'info'
}

// 获取风险等级样式
const getSeverityType = (severity) => {
  const types = {
    fatal: 'danger',
    error: 'warning',
    warning: '',
    info: 'info'
  }
  return types[severity] || ''
}

const getSeverityColor = (severity) => {
  const colors = {
    fatal: '#dc3545',
    error: '#fd7e14',
    warning: '#ffc107',
    info: '#17a2b8'
  }
  return colors[severity] || '#909399'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
.report-detail {
  padding-bottom: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 12px 0;
  border-bottom: 1px solid #e4e7ed;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.detail-card {
  margin-top: 20px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.report-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.report-title h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.report-info {
  margin-bottom: 24px;
}

.stats-section {
  margin: 24px 0;
}

.stat-card {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.stat-card.fatal {
  background: rgba(220, 53, 69, 0.1);
}

.stat-card.fatal .stat-value {
  color: #dc3545;
}

.stat-card.error {
  background: rgba(253, 126, 20, 0.1);
}

.stat-card.error .stat-value {
  color: #fd7e14;
}

.stat-card.warning {
  background: rgba(255, 193, 7, 0.1);
}

.stat-card.warning .stat-value {
  color: #ffc107;
}

.stat-card.info {
  background: rgba(23, 162, 184, 0.1);
}

.stat-card.info .stat-value {
  color: #17a2b8;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.violations-section {
  margin-top: 32px;
}

.violations-section h3 {
  font-size: 18px;
  color: #303133;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.violation-card {
  margin-bottom: 16px;
}

.violation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.violation-title {
  font-weight: 600;
  color: #303133;
}

.violation-content p {
  margin: 8px 0;
  color: #606266;
}

.violation-message {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin: 12px 0;
}

.code-block, .suggested-fix {
  margin-top: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.code-header, .fix-header {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.code-block {
  background: #2d2d2d;
}

.code-header {
  background: #1a1a1a;
  color: #f8f8f2;
}

.code-block pre {
  margin: 0;
  padding: 16px;
  color: #f8f8f2;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
}

.suggested-fix {
  background: #d4edda;
}

.fix-header {
  background: #c3e6cb;
  color: #155724;
}

.suggested-fix pre {
  margin: 0;
  padding: 16px;
  color: #155724;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
}
</style>

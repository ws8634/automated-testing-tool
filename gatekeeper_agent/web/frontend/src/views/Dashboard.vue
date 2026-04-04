<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: rgba(102, 126, 234, 0.1); color: #667eea;">
            <el-icon size="24"><Collection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.rules?.total || 0 }}</div>
            <div class="stat-label">规则总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: rgba(220, 53, 69, 0.1); color: #dc3545;">
            <el-icon size="24"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" style="color: #dc3545;">{{ stats.rules?.by_severity?.fatal || 0 }}</div>
            <div class="stat-label">Fatal 规则</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: rgba(253, 126, 20, 0.1); color: #fd7e14;">
            <el-icon size="24"><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" style="color: #fd7e14;">{{ stats.rules?.by_severity?.error || 0 }}</div>
            <div class="stat-label">Error 规则</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: rgba(40, 167, 69, 0.1); color: #28a745;">
            <el-icon size="24"><DocumentChecked /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value" style="color: #28a745;">{{ stats.scans?.total_scans || 0 }}</div>
            <div class="stat-label">扫描次数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分类统计 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>规则分类分布</span>
            </div>
          </template>
          <div class="category-list">
            <div v-for="(count, category) in stats.rules?.by_category" :key="category" class="category-item">
              <div class="category-label">
                <el-tag :type="getCategoryType(category)" size="small">{{ category }}</el-tag>
              </div>
              <el-progress 
                :percentage="getCategoryPercentage(count)" 
                :color="getCategoryColor(category)"
                :show-text="false"
              />
              <div class="category-count">{{ count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>风险等级分布</span>
            </div>
          </template>
          <div class="severity-chart">
            <div v-for="(count, severity) in stats.rules?.by_severity" :key="severity" class="severity-item">
              <div class="severity-info">
                <span :class="`severity-badge ${severity}`">{{ severity.toUpperCase() }}</span>
                <span class="severity-count">{{ count }} 条规则</span>
              </div>
              <div class="severity-bar">
                <div 
                  class="severity-fill" 
                  :style="{ 
                    width: getSeverityPercentage(count) + '%',
                    background: getSeverityColor(severity)
                  }"
                />
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快速操作 -->
    <el-card class="quick-actions">
      <template #header>
        <div class="card-header">
          <span>快速操作</span>
        </div>
      </template>
      <div class="actions">
        <el-button type="primary" size="large" @click="$router.push('/rules')">
          <el-icon><Collection /></el-icon>
          管理规则
        </el-button>
        <el-button type="success" size="large" @click="handleScan">
          <el-icon><Search /></el-icon>
          执行扫描
        </el-button>
        <el-button type="info" size="large" @click="$router.push('/reports')">
          <el-icon><Document /></el-icon>
          查看报告
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { statsApi, scansApi } from '../api'

const router = useRouter()
const stats = ref({
  rules: { total: 0, builtin: 0, custom: 0, by_category: {}, by_severity: {} },
  scans: { total_scans: 0, total_violations: 0, blocking_violations: 0 }
})

const totalRules = ref(0)

// 获取统计数据
const fetchStats = async () => {
  try {
    const res = await statsApi.dashboard()
    stats.value = res
    totalRules.value = res.rules?.total || 1
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  }
}

// 获取分类样式
const getCategoryType = (category) => {
  const types = {
    security: 'danger',
    business: 'warning',
    performance: 'success',
    ai_hallucination: 'info',
    style: ''
  }
  return types[category] || ''
}

const getCategoryColor = (category) => {
  const colors = {
    security: '#dc3545',
    business: '#fd7e14',
    performance: '#28a745',
    ai_hallucination: '#17a2b8',
    style: '#6c757d'
  }
  return colors[category] || '#667eea'
}

const getCategoryPercentage = (count) => {
  return Math.round((count / totalRules.value) * 100)
}

// 获取风险等级样式
const getSeverityColor = (severity) => {
  const colors = {
    fatal: '#dc3545',
    error: '#fd7e14',
    warning: '#ffc107',
    info: '#17a2b8'
  }
  return colors[severity] || '#667eea'
}

const getSeverityPercentage = (count) => {
  return Math.round((count / totalRules.value) * 100)
}

// 执行扫描 - 跳转到扫描任务页面
const handleScan = () => {
  router.push('/scans?action=create')
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard {
  padding-bottom: 24px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 8px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.charts-row {
  margin-bottom: 20px;
}

.card-header {
  font-weight: 600;
  color: #303133;
}

.category-list {
  padding: 10px 0;
}

.category-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.category-label {
  width: 100px;
  flex-shrink: 0;
}

.category-item :deep(.el-progress) {
  flex: 1;
  margin: 0 16px;
}

.category-count {
  width: 40px;
  text-align: right;
  font-weight: 600;
  color: #606266;
}

.severity-chart {
  padding: 10px 0;
}

.severity-item {
  margin-bottom: 20px;
}

.severity-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.severity-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.severity-badge.fatal {
  background: #dc3545;
}

.severity-badge.error {
  background: #fd7e14;
}

.severity-badge.warning {
  background: #ffc107;
  color: #333;
}

.severity-badge.info {
  background: #17a2b8;
}

.severity-count {
  font-size: 14px;
  color: #909399;
}

.severity-bar {
  height: 8px;
  background: #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.severity-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.quick-actions {
  margin-top: 20px;
}

.actions {
  display: flex;
  gap: 16px;
  padding: 20px 0;
}

.actions .el-button {
  flex: 1;
  height: 48px;
}
</style>

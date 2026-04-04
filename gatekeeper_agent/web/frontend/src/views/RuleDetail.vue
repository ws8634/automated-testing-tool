<template>
  <div class="rule-detail">
    <div class="page-header">
      <el-button link @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        返回规则列表
      </el-button>
      <span class="page-title">规则详情</span>
    </div>

    <el-card v-loading="loading" class="detail-card">
      <template v-if="rule">
        <div class="rule-header">
          <div class="rule-title">
            <h2>{{ rule.name }}</h2>
            <el-tag v-if="rule.is_builtin" type="info" effect="plain">内置规则</el-tag>
            <el-tag v-else type="success" effect="plain">自定义规则</el-tag>
          </div>
          <div class="rule-actions">
            <el-switch
              v-model="rule.enabled"
              :disabled="rule.is_builtin"
              active-text="启用"
              inactive-text="禁用"
              @change="handleStatusChange"
            />
          </div>
        </div>

        <el-descriptions :column="2" border class="rule-info">
          <el-descriptions-item label="规则ID">{{ rule.rule_id }}</el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag :type="getCategoryType(rule.category)" size="small">
              {{ rule.category }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag :type="getSeverityType(rule.severity)" size="small" effect="dark">
              {{ rule.severity.toUpperCase() }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="版本">{{ rule.metadata?.version || '1.0' }}</el-descriptions-item>
          <el-descriptions-item label="作者">{{ rule.metadata?.author || 'system' }}</el-descriptions-item>
          <el-descriptions-item label="标签">
            <el-tag
              v-for="tag in rule.metadata?.tags || []"
              :key="tag"
              size="small"
              style="margin-right: 8px;"
            >
              {{ tag }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="section">
          <h3>规则描述</h3>
          <p class="description">{{ rule.description }}</p>
        </div>

        <div v-if="yamlContent" class="section">
          <h3>YAML 配置</h3>
          <pre class="yaml-content"><code>{{ yamlContent }}</code></pre>
        </div>

        <div v-if="!rule.is_builtin" class="section actions">
          <el-button type="danger" @click="handleDelete">删除规则</el-button>
        </div>
      </template>

      <el-empty v-else description="规则不存在或已删除" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { rulesApi } from '../api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const rule = ref(null)
const yamlContent = ref('')

// 获取规则详情
const fetchRule = async () => {
  loading.value = true
  try {
    const res = await rulesApi.get(route.params.id)
    rule.value = res.rule
    yamlContent.value = res.yaml_content || ''
  } catch (error) {
    ElMessage.error('获取规则详情失败')
  } finally {
    loading.value = false
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

// 获取等级样式
const getSeverityType = (severity) => {
  const types = {
    fatal: 'danger',
    error: 'warning',
    warning: '',
    info: 'info'
  }
  return types[severity] || ''
}

// 状态变更
const handleStatusChange = async (val) => {
  try {
    await rulesApi.update(rule.value.rule_id, { enabled: val })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    rule.value.enabled = !val
  }
}

// 返回按钮处理
const handleBack = () => {
  router.push('/rules')
}

// 删除规则
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除规则 "${rule.value.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await rulesApi.delete(rule.value.rule_id)
    ElMessage.success('删除成功')
    router.back()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchRule()
})
</script>

<style scoped>
.rule-detail {
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

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.rule-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rule-title h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.rule-info {
  margin-bottom: 24px;
}

.section {
  margin-top: 24px;
}

.section h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.description {
  color: #606266;
  line-height: 1.8;
  font-size: 14px;
}

.yaml-content {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  color: #303133;
}

.actions {
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}
</style>

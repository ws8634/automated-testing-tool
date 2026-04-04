<template>
  <div class="rules-page">
    <!-- 搜索和过滤 -->
    <el-card class="filter-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索规则名称、ID或描述"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterCategory" placeholder="全部分类" clearable @change="handleSearch">
            <el-option
              v-for="cat in categories"
              :key="cat.value"
              :label="cat.label"
              :value="cat.value"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterSeverity" placeholder="全部等级" clearable @change="handleSearch">
            <el-option
              v-for="sev in severities"
              :key="sev.value"
              :label="sev.label"
              :value="sev.value"
            />
          </el-select>
        </el-col>
        <el-col :span="8" style="text-align: right;">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建规则
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 规则列表 -->
    <el-card class="rules-card">
      <el-table
        v-loading="loading"
        :data="rules"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="rule_id" label="规则ID" width="180" />
        <el-table-column prop="name" label="规则名称" min-width="200">
          <template #default="{ row }">
            <div class="rule-name">
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_builtin" size="small" type="info" effect="plain">内置</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)" size="small">
              {{ row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small" effect="dark">
              {{ row.severity.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              :disabled="row.is_builtin"
              @change="(val) => handleStatusChange(row, val)"
              @click.stop
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleView(row)">查看</el-button>
            <el-button 
              v-if="!row.is_builtin" 
              link 
              type="danger" 
              @click.stop="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新建规则对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建规则"
      width="800px"
      destroy-on-close
    >
      <el-form :model="newRule" label-width="100px">
        <el-form-item label="规则ID" required>
          <el-input v-model="newRule.rule_id" placeholder="如: business-custom-001" />
        </el-form-item>
        <el-form-item label="规则名称" required>
          <el-input v-model="newRule.name" placeholder="规则名称" />
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="newRule.category" placeholder="选择分类">
            <el-option
              v-for="cat in categories"
              :key="cat.value"
              :label="cat.label"
              :value="cat.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级" required>
          <el-select v-model="newRule.severity" placeholder="选择等级">
            <el-option
              v-for="sev in severities"
              :key="sev.value"
              :label="sev.label"
              :value="sev.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" required>
          <el-input v-model="newRule.description" type="textarea" :rows="2" placeholder="规则描述" />
        </el-form-item>
        <el-form-item label="YAML配置" required>
          <el-input
            v-model="newRule.yaml_content"
            type="textarea"
            :rows="15"
            placeholder="规则YAML配置"
            class="yaml-editor"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { rulesApi } from '../api'

const router = useRouter()
const loading = ref(false)
const rules = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 过滤条件
const searchQuery = ref('')
const filterCategory = ref('')
const filterSeverity = ref('')

// 选项
const categories = ref([])
const severities = ref([])

// 新建规则
const createDialogVisible = ref(false)
const creating = ref(false)
const newRule = ref({
  rule_id: '',
  name: '',
  category: '',
  severity: '',
  description: '',
  yaml_content: `rule_id: ""
name: ""
severity: error
category: business
description: ""
enabled: true
triggers:
  - pattern: ""
    language: ["python"]
    file_pattern: ["*.py"]
violation_response:
  block_commit: true
  message: ""
  suggested_fix: ""
metadata:
  version: "1.0"
  author: "custom"
  tags: []
`
})

// 获取规则列表
const fetchRules = async () => {
  loading.value = true
  try {
    const res = await rulesApi.list({
      search: searchQuery.value,
      category: filterCategory.value,
      severity: filterSeverity.value,
    })
    rules.value = res.rules
    total.value = res.total
  } catch (error) {
    ElMessage.error('获取规则列表失败')
  } finally {
    loading.value = false
  }
}

// 获取选项
const fetchOptions = async () => {
  try {
    const [catRes, sevRes] = await Promise.all([
      rulesApi.categories(),
      rulesApi.severities()
    ])
    categories.value = catRes
    severities.value = sevRes
  } catch (error) {
    console.error('获取选项失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchRules()
}

// 分页
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchRules()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchRules()
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
const handleStatusChange = async (row, val) => {
  try {
    await rulesApi.update(row.rule_id, { enabled: val })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    row.enabled = !val
  }
}

// 查看规则
const handleView = (row) => {
  router.push(`/rules/${row.rule_id}`)
}

// 点击行
const handleRowClick = (row) => {
  router.push(`/rules/${row.rule_id}`)
}

// 删除规则
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除规则 "${row.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await rulesApi.delete(row.rule_id)
    ElMessage.success('删除成功')
    fetchRules()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 新建规则
const handleCreate = () => {
  createDialogVisible.value = true
}

const confirmCreate = async () => {
  if (!newRule.value.rule_id || !newRule.value.name) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  creating.value = true
  try {
    await rulesApi.create(newRule.value)
    ElMessage.success('规则创建成功')
    createDialogVisible.value = false
    fetchRules()
  } catch (error) {
    ElMessage.error(error.message || '创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  fetchRules()
  fetchOptions()
})
</script>

<style scoped>
.rules-page {
  padding-bottom: 24px;
}

.filter-card {
  margin-bottom: 20px;
}

.rules-card {
  min-height: 500px;
}

.rule-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.yaml-editor :deep(.el-textarea__inner) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
}
</style>

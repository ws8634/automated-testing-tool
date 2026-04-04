<template>
  <div class="reports-page">
    <el-card class="filter-card">
      <el-row justify="space-between" align="middle">
        <el-col>
          <h3>扫描报告中心</h3>
        </el-col>
        <el-col style="text-align: right;">
          <el-radio-group v-model="filterType" @change="handleFilterChange">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="blocking">有阻断</el-radio-button>
            <el-radio-button label="clean">无违规</el-radio-button>
          </el-radio-group>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="reports-card">
      <el-table v-loading="loading" :data="reports" style="width: 100%">
        <el-table-column prop="report_id" label="报告ID" width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="handleView(row)">
              {{ row.report_id }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="scan_id" label="扫描ID" width="180" />
        <el-table-column prop="created_at" label="生成时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_files" label="文件数" width="100" />
        <el-table-column label="违规统计" width="250">
          <template #default="{ row }">
            <div class="violation-stats">
              <el-tag v-if="row.fatal_count > 0" type="danger" size="small" effect="dark">
                Fatal: {{ row.fatal_count }}
              </el-tag>
              <el-tag v-if="row.error_count > 0" type="warning" size="small" effect="dark">
                Error: {{ row.error_count }}
              </el-tag>
              <el-tag v-if="row.warning_count > 0" type="info" size="small">
                Warning: {{ row.warning_count }}
              </el-tag>
              <span v-if="row.total_violations === 0" class="clean-text">✅ 无违规</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="has_blocking" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.has_blocking" type="danger" effect="dark">阻断</el-tag>
            <el-tag v-else type="success" effect="dark">通过</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看</el-button>
            <el-button link type="success" @click="handleExport(row)">导出</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { reportsApi } from '../api'

const router = useRouter()
const loading = ref(false)
const reports = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterType = ref('all')

// 获取报告列表
const fetchReports = async () => {
  loading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
    }
    
    if (filterType.value === 'blocking') {
      params.has_blocking = true
    } else if (filterType.value === 'clean') {
      params.has_blocking = false
    }
    
    const res = await reportsApi.list(params)
    reports.value = res.reports
    total.value = res.total
  } catch (error) {
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
}

// 过滤变更
const handleFilterChange = () => {
  currentPage.value = 1
  fetchReports()
}

// 分页
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchReports()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchReports()
}

// 查看报告
const handleView = (row) => {
  router.push(`/reports/${row.report_id}`)
}

// 删除报告
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个报告吗？', '确认删除', { type: 'warning' })
    await reportsApi.delete(row.report_id)
    ElMessage.success('报告已删除')
    fetchReports()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 导出报告
const handleExport = async (row) => {
  try {
    const res = await reportsApi.export(row.report_id, 'html')
    // 创建下载链接
    const blob = new Blob([res.content || res], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report-${row.report_id}.html`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('报告导出成功')
  } catch (error) {
    ElMessage.error(error.message || '导出失败')
  }
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.reports-page {
  padding-bottom: 24px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-card h3 {
  margin: 0;
  color: #303133;
}

.violation-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.clean-text {
  color: #28a745;
  font-size: 14px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

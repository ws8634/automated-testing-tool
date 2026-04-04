<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon size="28" color="#667eea"><Lock /></el-icon>
        <span class="logo-text">Gatekeeper</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#1a1a2e"
        text-color="#a0a3bd"
        active-text-color="#667eea"
        @select="handleMenuSelect"
      >
        <el-menu-item v-for="route in menuRoutes" :key="route.path" :index="route.path">
          <el-icon>
            <component :is="route.meta.icon" />
          </el-icon>
          <span>{{ route.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h2>{{ $route.meta.title }}</h2>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="handleScan">
            <el-icon><Search /></el-icon>
            立即扫描
          </el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { scansApi } from '../api'

const route = useRoute()
const router = useRouter()

// 当前激活的菜单（处理子路由情况）
const activeMenu = computed(() => {
  const path = route.path
  // 如果是详情页，返回父路由路径
  if (path.startsWith('/rules/')) return '/rules'
  if (path.startsWith('/reports/')) return '/reports'
  return path
})

// 菜单路由
const menuRoutes = computed(() => {
  const layoutRoute = router.getRoutes().find(r => r.name === 'Layout')
  return layoutRoute?.children?.filter(r => !r.meta?.hidden) || []
})

// 菜单选择处理 - 使用 replace 避免历史记录问题
const handleMenuSelect = (index) => {
  // 确保使用绝对路径，避免相对路径拼接
  const targetPath = index.startsWith('/') ? index : '/' + index
  router.replace(targetPath)
}

// 立即扫描 - 跳转到扫描任务页面并打开新建对话框
const handleScan = () => {
  router.push('/scans?action=create')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background: #1a1a2e;
  color: #fff;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.sidebar-menu {
  border-right: none;
  padding-top: 16px;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
  margin: 4px 12px;
  border-radius: 8px;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(102, 126, 234, 0.1);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: rgba(102, 126, 234, 0.15);
}

.header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.main-content {
  background: #f5f7fa;
  padding: 24px;
  overflow-y: auto;
}
</style>

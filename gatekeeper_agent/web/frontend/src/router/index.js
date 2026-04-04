import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: 'Dashboard', icon: 'DataLine' }
      },
      {
        path: 'rules',
        name: 'Rules',
        component: () => import('../views/Rules.vue'),
        meta: { title: '规则管理', icon: 'Collection' }
      },
      {
        path: 'rules/:id',
        name: 'RuleDetail',
        component: () => import('../views/RuleDetail.vue'),
        meta: { title: '规则详情', hidden: true }
      },
      {
        path: 'scans',
        name: 'Scans',
        component: () => import('../views/Scans.vue'),
        meta: { title: '扫描任务', icon: 'Search' }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('../views/Reports.vue'),
        meta: { title: '报告中心', icon: 'Document' }
      },
      {
        path: 'reports/:id',
        name: 'ReportDetail',
        component: () => import('../views/ReportDetail.vue'),
        meta: { title: '报告详情', hidden: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

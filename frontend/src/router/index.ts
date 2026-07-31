import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/jobs/JobList.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { title: '注册', public: true },
  },
  {
    path: '/jobs',
    name: 'jobs',
    component: () => import('@/views/jobs/JobList.vue'),
    meta: { title: '岗位列表' },
  },
  {
    path: '/jobs/:id',
    name: 'jobDetail',
    component: () => import('@/views/jobs/JobDetail.vue'),
    meta: { title: '岗位详情' },
  },
  {
    path: '/resume',
    name: 'resume',
    component: () => import('@/views/resume/ResumeGenerator.vue'),
    meta: { title: '简历制作', requiresAuth: true },
  },
  {
    path: '/resume/generate',
    name: 'resumeGenerate',
    component: () => import('@/views/resume/ResumeGenerator.vue'),
    meta: { title: 'AI简历生成', requiresAuth: true },
  },
  {
    path: '/settings/ai',
    name: 'aiSettings',
    component: () => import('@/views/settings/AISettings.vue'),
    meta: { title: 'AI 设置', requiresAuth: true },
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: () => import('@/views/analysis/IndustryAnalysis.vue'),
    meta: { title: '行业分析' },
  },
  {
    path: '/interview',
    name: 'interview',
    component: () => import('@/views/interview/InterviewTips.vue'),
    meta: { title: '面试技巧' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/profile/Profile.vue'),
    meta: { title: '个人中心', requiresAuth: true },
  },
  {
    path: '/profile/favorites',
    name: 'favorites',
    component: () => import('@/views/profile/Favorites.vue'),
    meta: { title: '我的收藏', requiresAuth: true },
  },
  {
    path: '/feedback',
    name: 'feedback',
    component: () => import('@/views/Feedback.vue'),
    meta: { title: '反馈' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// 全局前置守卫
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || '秋招助手'} - 秋招助手`

  const authStore = useAuthStore()

  // 需要登录的页面
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router

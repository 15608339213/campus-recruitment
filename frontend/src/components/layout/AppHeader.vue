<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  NLayoutHeader,
  NMenu,
  NButton,
  NDropdown,
  NAvatar,
  NSpace,
  NIcon,
  NInput,
} from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { h } from 'vue'
import {
  HomeOutline,
  BriefcaseOutline,
  DocumentTextOutline,
  AnalyticsOutline,
  PersonOutline,
  ChatbubbleEllipsesOutline,
  LogOutOutline,
  SettingsOutline,
  HeartOutline,
  SearchOutline,
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const renderIcon = (icon: typeof HomeOutline) => {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = computed<MenuOption[]>(() => [
  {
    label: '首页',
    key: 'home',
    icon: renderIcon(HomeOutline),
  },
  {
    label: '岗位',
    key: 'jobs',
    icon: renderIcon(BriefcaseOutline),
  },
  {
    label: '简历',
    key: 'resume',
    icon: renderIcon(DocumentTextOutline),
  },
  {
    label: '行业分析',
    key: 'analysis',
    icon: renderIcon(AnalyticsOutline),
  },
  {
    label: '反馈',
    key: 'feedback',
    icon: renderIcon(ChatbubbleEllipsesOutline),
  },
])

const activeKey = computed(() => {
  const path = route.path
  if (path === '/') return 'home'
  if (path.startsWith('/jobs')) return 'jobs'
  if (path.startsWith('/resume')) return 'resume'
  if (path.startsWith('/analysis')) return 'analysis'
  if (path.startsWith('/feedback')) return 'feedback'
  if (path.startsWith('/profile')) return 'profile'
  return 'home'
})

function handleMenuSelect(key: string) {
  const routeMap: Record<string, string> = {
    home: '/',
    jobs: '/jobs',
    resume: '/resume',
    analysis: '/analysis',
    feedback: '/feedback',
  }
  router.push(routeMap[key] || '/')
}

function handleSearch(value: string) {
  if (value.trim()) {
    router.push({ path: '/jobs', query: { keyword: value.trim() } })
  }
}

function goToLogin() {
  router.push('/login')
}

function goToRegister() {
  router.push('/register')
}

const userMenuOptions = computed<MenuOption[]>(() => [
  {
    label: '个人中心',
    key: 'profile',
    icon: renderIcon(PersonOutline),
  },
  {
    label: '我的收藏',
    key: 'favorites',
    icon: renderIcon(HeartOutline),
  },
  {
    type: 'divider',
    key: 'd1',
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: renderIcon(LogOutOutline),
  },
])

function handleUserMenuSelect(key: string) {
  switch (key) {
    case 'profile':
      router.push('/profile')
      break
    case 'favorites':
      router.push('/profile/favorites')
      break
    case 'logout':
      authStore.logout()
      router.push('/')
      break
  }
}
</script>

<template>
  <n-layout-header class="app-header" bordered>
    <div class="header-inner">
      <!-- Logo -->
      <div class="logo" @click="router.push('/')">
        <div class="logo-icon">秋</div>
        <span class="logo-text">秋招助手</span>
      </div>

      <!-- 导航菜单 -->
      <div class="nav-menu">
        <n-menu
          mode="horizontal"
          :options="menuOptions"
          :value="activeKey"
          @update:value="handleMenuSelect"
        />
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <n-input
          placeholder="搜索岗位、公司..."
          clearable
          round
          @keyup.enter="handleSearch(($event.target as HTMLInputElement).value)"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>
      </div>

      <!-- 用户区域 -->
      <div class="user-area">
        <template v-if="authStore.isLoggedIn">
          <n-dropdown :options="userMenuOptions" trigger="click" @select="handleUserMenuSelect">
            <div class="user-info">
              <n-avatar
                round
                size="small"
                :src="authStore.user?.avatar_url"
                style="background-color: var(--app-primary)"
              >
                {{ authStore.nickname.charAt(0).toUpperCase() }}
              </n-avatar>
              <span class="user-name">{{ authStore.nickname }}</span>
            </div>
          </n-dropdown>
        </template>
        <template v-else>
          <n-space>
            <n-button text @click="goToLogin">登录</n-button>
            <n-button type="primary" @click="goToRegister">注册</n-button>
          </n-space>
        </template>
      </div>
    </div>
  </n-layout-header>
</template>

<style scoped>
.app-header {
  height: 64px;
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--app-header-bg);
  backdrop-filter: blur(12px);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.header-inner {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 24px;
  gap: 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex-shrink: 0;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
}

.nav-menu {
  flex-shrink: 0;
}

.search-box {
  flex: 1;
  max-width: 300px;
}

.user-area {
  flex-shrink: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 20px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f0f5ff;
}

.user-name {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
}
</style>

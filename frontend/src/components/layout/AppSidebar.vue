<script setup lang="ts">
import { computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { NMenu, NIcon } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  HomeOutline,
  BriefcaseOutline,
  DocumentTextOutline,
  AnalyticsOutline,
  PersonCircleOutline,
  ChatbubbleEllipsesOutline,
  HeartOutline,
  StarOutline,
  SchoolOutline,
  SettingsOutline,
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const renderIcon = (icon: typeof HomeOutline) => {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = computed<MenuOption[]>(() => {
  const base: MenuOption[] = [
    {
      label: '首页',
      key: '/',
      icon: renderIcon(HomeOutline),
    },
    {
      label: '岗位列表',
      key: '/jobs',
      icon: renderIcon(BriefcaseOutline),
    },
    {
      label: 'AI 简历生成',
      key: '/resume',
      icon: renderIcon(DocumentTextOutline),
    },
    {
      label: '行业分析',
      key: '/analysis',
      icon: renderIcon(AnalyticsOutline),
    },
    {
      label: '面试技巧',
      key: '/interview',
      icon: renderIcon(SchoolOutline),
    },
    {
      label: 'AI 设置',
      key: '/settings/ai',
      icon: renderIcon(SettingsOutline),
    },
  ]

  if (authStore.isLoggedIn) {
    base.push(
      {
        label: '个人中心',
        key: '/profile',
        icon: renderIcon(PersonCircleOutline),
        children: [
          {
            label: '我的资料',
            key: '/profile',
            icon: renderIcon(PersonCircleOutline),
          },
          {
            label: '我的收藏',
            key: '/profile/favorites',
            icon: renderIcon(HeartOutline),
          },
        ],
      } as MenuOption,
    )
  }

  base.push({
    label: '意见反馈',
    key: '/feedback',
    icon: renderIcon(ChatbubbleEllipsesOutline),
  })

  return base
})

const activeKey = computed(() => {
  return route.path
})

function handleMenuSelect(key: string) {
  router.push(key)
}
</script>

<template>
  <aside class="app-sidebar">
    <div class="sidebar-header">
      <n-icon size="20" color="#2563eb">
        <StarOutline />
      </n-icon>
      <span class="sidebar-title">功能导航</span>
    </div>
    <n-menu
      :options="menuOptions"
      :value="activeKey"
      :indent="18"
      :collapsed-width="64"
      :collapsed-icon-size="22"
      @update:value="handleMenuSelect"
    />
    <div class="sidebar-footer" v-if="!authStore.isLoggedIn">
      <p class="footer-text">登录后体验完整功能</p>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--app-sidebar-bg);
  border-right: 1px solid var(--app-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 20px 12px;
  font-size: 14px;
  font-weight: 600;
  color: #6b7280;
}

.sidebar-title {
  letter-spacing: 0.5px;
}

.sidebar-footer {
  margin-top: auto;
  padding: 16px 20px;
  border-top: 1px solid var(--app-border);
}

.footer-text {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
  text-align: center;
}

:deep(.n-menu .n-menu-item-content--selected) {
  background-color: #eff6ff;
  color: var(--app-primary);
}

:deep(.n-menu .n-menu-item-content--selected::before) {
  background-color: #eff6ff;
}
</style>

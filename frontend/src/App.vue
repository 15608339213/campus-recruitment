<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  NMessageProvider,
  NDialogProvider,
  NConfigProvider,
  NLoadingBarProvider,
  zhCN,
  dateZhCN,
  lightTheme,
} from 'naive-ui'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const route = useRoute()

// 登录/注册页面不显示布局
const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register'
})
</script>

<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN" :theme="lightTheme">
    <n-loading-bar-provider>
      <n-message-provider>
        <n-dialog-provider>
          <div class="app-container">
            <!-- 认证页面：无布局 -->
            <template v-if="isAuthPage">
              <router-view v-slot="{ Component }">
                <transition name="fade" mode="out-in">
                  <component :is="Component" />
                </transition>
              </router-view>
            </template>

            <!-- 主应用布局 -->
            <template v-else>
              <AppHeader />
              <div class="app-body">
                <AppSidebar />
                <main class="app-main">
                  <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                      <component :is="Component" />
                    </transition>
                  </router-view>
                </main>
              </div>
            </template>
          </div>
        </n-dialog-provider>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background-color: var(--app-bg, #f5f7fa);
}
</style>

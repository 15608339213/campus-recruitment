<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NSpace,
  NIcon,
  NDivider,
  useMessage,
} from 'naive-ui'
import { MailOutline, LockClosedOutline, LogoGithub } from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const message = useMessage()

const loading = ref(false)
const githubLoading = ref(false)

const formRef = ref()
const formModel = reactive({
  email: '',
  password: '',
})

const rules = {
  email: {
    required: true,
    message: '请输入邮箱地址',
    trigger: ['blur', 'input'],
  },
  password: {
    required: true,
    message: '请输入密码',
    trigger: ['blur', 'input'],
  },
}

async function handleLogin() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authStore.login(formModel.email, formModel.password)
    message.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (error: any) {
    message.error(error.message || '登录失败，请检查邮箱和密码')
  } finally {
    loading.value = false
  }
}

async function handleGithubLogin() {
  githubLoading.value = true
  try {
    // 在实际应用中，这里会重定向到 GitHub OAuth 授权页面
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID
    if (clientId) {
      const redirectUri = `${window.location.origin}/login`
      const githubOAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=user:email`
      window.location.href = githubOAuthUrl
    } else {
      message.info('GitHub OAuth 尚未配置，请使用邮箱登录')
    }
  } finally {
    githubLoading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-bg">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <div class="auth-card-wrapper">
      <n-card class="auth-card" :bordered="false" size="large">
        <div class="auth-header">
          <div class="logo-icon">秋</div>
          <h1 class="auth-title">欢迎回来</h1>
          <p class="auth-subtitle">登录秋招助手，开启你的求职之旅</p>
        </div>

        <n-form
          ref="formRef"
          :model="formModel"
          :rules="rules"
          size="large"
          label-placement="top"
          @keyup.enter="handleLogin"
        >
          <n-form-item label="邮箱" path="email">
            <n-input
              v-model:value="formModel.email"
              placeholder="请输入邮箱地址"
              clearable
            >
              <template #prefix>
                <n-icon :component="MailOutline" />
              </template>
            </n-input>
          </n-form-item>

          <n-form-item label="密码" path="password">
            <n-input
              v-model:value="formModel.password"
              type="password"
              show-password-on="click"
              placeholder="请输入密码"
              clearable
            >
              <template #prefix>
                <n-icon :component="LockClosedOutline" />
              </template>
            </n-input>
          </n-form-item>

          <n-button
            type="primary"
            block
            size="large"
            :loading="loading"
            @click="handleLogin"
            style="margin-top: 8px"
          >
            登录
          </n-button>
        </n-form>

        <n-divider style="margin: 24px 0">其他登录方式</n-divider>

        <n-button
          block
          size="large"
          :loading="githubLoading"
          @click="handleGithubLogin"
          style="background: #24292e; color: white; border: none"
        >
          <template #icon>
            <n-icon :component="LogoGithub" />
          </template>
          使用 GitHub 登录
        </n-button>

        <div class="auth-footer">
          <span>还没有账号？</span>
          <n-button text type="primary" @click="router.push('/register')">立即注册</n-button>
        </div>
      </n-card>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 50%, #60a5fa 100%);
  position: relative;
  overflow: hidden;
}

.auth-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}

.bg-circle-1 {
  width: 500px;
  height: 500px;
  top: -150px;
  right: -100px;
}

.bg-circle-2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: -80px;
}

.bg-circle-3 {
  width: 300px;
  height: 300px;
  top: 50%;
  left: 60%;
  background: rgba(255, 255, 255, 0.05);
}

.auth-card-wrapper {
  position: relative;
  z-index: 1;
  width: 420px;
  max-width: 90vw;
}

.auth-card {
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  margin: 0 auto 16px;
}

.auth-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px;
}

.auth-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #6b7280;
}
</style>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NIcon,
  NDivider,
  NSpace,
  useMessage,
} from 'naive-ui'
import {
  MailOutline,
  LockClosedOutline,
  PersonOutline,
  SchoolOutline,
  LogoGithub,
} from '@vicons/ionicons5'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

const loading = ref(false)
const githubLoading = ref(false)

const formRef = ref()
const formModel = reactive({
  email: '',
  password: '',
  confirmPassword: '',
  nickname: '',
  eduEmail: '',
})

function validateEmail(rule: unknown, value: string) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!value) {
    return new Error('请输入邮箱地址')
  }
  if (!emailRegex.test(value)) {
    return new Error('请输入有效的邮箱地址')
  }
  return true
}

function validateEduEmail(_rule: unknown, value: string) {
  if (!value) return true
  const eduRegex = /^[^\s@]+@[^\s@]+\.edu\.cn$/
  if (!eduRegex.test(value)) {
    return new Error('教育邮箱需以 .edu.cn 结尾')
  }
  return true
}

function validatePassword(_rule: unknown, value: string) {
  if (!value) {
    return new Error('请输入密码')
  }
  if (value.length < 6) {
    return new Error('密码长度至少6位')
  }
  return true
}

function validateConfirmPassword(_rule: unknown, value: string) {
  if (!value) {
    return new Error('请确认密码')
  }
  if (value !== formModel.password) {
    return new Error('两次输入的密码不一致')
  }
  return true
}

const rules = {
  email: {
    required: true,
    validator: validateEmail,
    trigger: ['blur', 'input'],
  },
  password: {
    required: true,
    validator: validatePassword,
    trigger: ['blur', 'input'],
  },
  confirmPassword: {
    required: true,
    validator: validateConfirmPassword,
    trigger: ['blur', 'input'],
  },
  eduEmail: {
    validator: validateEduEmail,
    trigger: ['blur'],
  },
}

async function handleRegister() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await authStore.register(formModel.email, formModel.password, formModel.nickname || undefined)
    message.success('注册成功，欢迎加入秋招助手')
    router.push('/')
  } catch (error: any) {
    message.error(error.message || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function handleGithubRegister() {
  githubLoading.value = true
  try {
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID
    if (clientId) {
      const redirectUri = `${window.location.origin}/register`
      const githubOAuthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=user:email`
      window.location.href = githubOAuthUrl
    } else {
      message.info('GitHub OAuth 尚未配置，请使用邮箱注册')
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
          <h1 class="auth-title">创建账号</h1>
          <p class="auth-subtitle">注册秋招助手，获取专属求职服务</p>
        </div>

        <n-form
          ref="formRef"
          :model="formModel"
          :rules="rules"
          size="large"
          label-placement="top"
          @keyup.enter="handleRegister"
        >
          <n-form-item label="昵称" path="nickname">
            <n-input
              v-model:value="formModel.nickname"
              placeholder="请输入昵称（选填）"
              clearable
            >
              <template #prefix>
                <n-icon :component="PersonOutline" />
              </template>
            </n-input>
          </n-form-item>

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
              placeholder="请输入密码（至少6位）"
              clearable
            >
              <template #prefix>
                <n-icon :component="LockClosedOutline" />
              </template>
            </n-input>
          </n-form-item>

          <n-form-item label="确认密码" path="confirmPassword">
            <n-input
              v-model:value="formModel.confirmPassword"
              type="password"
              show-password-on="click"
              placeholder="请再次输入密码"
              clearable
            >
              <template #prefix>
                <n-icon :component="LockClosedOutline" />
              </template>
            </n-input>
          </n-form-item>

          <n-form-item label="教育邮箱（选填）" path="eduEmail">
            <n-input
              v-model:value="formModel.eduEmail"
              placeholder="输入 .edu.cn 邮箱可获学生认证"
              clearable
            >
              <template #prefix>
                <n-icon :component="SchoolOutline" />
              </template>
            </n-input>
          </n-form-item>

          <n-button
            type="primary"
            block
            size="large"
            :loading="loading"
            @click="handleRegister"
            style="margin-top: 8px"
          >
            注册
          </n-button>
        </n-form>

        <n-divider style="margin: 24px 0">其他注册方式</n-divider>

        <n-button
          block
          size="large"
          :loading="githubLoading"
          @click="handleGithubRegister"
          style="background: #24292e; color: white; border: none"
        >
          <template #icon>
            <n-icon :component="LogoGithub" />
          </template>
          使用 GitHub 注册
        </n-button>

        <div class="auth-footer">
          <span>已有账号？</span>
          <n-button text type="primary" @click="router.push('/login')">立即登录</n-button>
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
  padding: 40px 0;
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
  margin-bottom: 28px;
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

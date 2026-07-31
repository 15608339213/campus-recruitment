import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, UserProfile } from '@/types'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const user = ref<User | null>(
    (() => {
      const stored = localStorage.getItem('user_info')
      try {
        return stored ? JSON.parse(stored) : null
      } catch {
        return null
      }
    })()
  )
  const profile = ref<UserProfile | null>(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || 'user')
  const isVerifiedStudent = computed(() => user.value?.role === 'verified_student')
  const nickname = computed(() => user.value?.nickname || user.value?.email || '游客')

  // 方法
  async function login(email: string, password: string) {
    const res = await authApi.login({ email, password })
    token.value = res.access_token
    user.value = res.user
    if (res.user.profile) {
      profile.value = res.user.profile
    }
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('user_info', JSON.stringify(res.user))
    return res
  }

  async function register(email: string, password: string, nickname?: string) {
    const res = await authApi.register({ email, password, nickname })
    // 注册成功后自动登录
    const loginRes = await authApi.login({ email, password })
    token.value = loginRes.access_token
    user.value = loginRes.user
    if (loginRes.user.profile) {
      profile.value = loginRes.user.profile
    }
    localStorage.setItem('access_token', loginRes.access_token)
    localStorage.setItem('user_info', JSON.stringify(loginRes.user))
    return loginRes
  }

  async function fetchCurrentUser() {
    try {
      const res = await authApi.getCurrentUser()
      user.value = res
      if (res.profile) {
        profile.value = res.profile
      }
      localStorage.setItem('user_info', JSON.stringify(res))
      return res
    } catch {
      logout()
      return null
    }
  }

  async function loginWithGithub(code: string) {
    const res = await authApi.githubOAuthCallback(code)
    token.value = res.access_token
    user.value = res.user
    if (res.user.profile) {
      profile.value = res.user.profile
    }
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('user_info', JSON.stringify(res.user))
    return res
  }

  function logout() {
    token.value = ''
    user.value = null
    profile.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
  }

  async function updateUserProfile(data: Partial<UserProfile>) {
    const res = await authApi.updateProfile(data)
    user.value = res
    if (res.profile) {
      profile.value = res.profile
    }
    localStorage.setItem('user_info', JSON.stringify(res))
    return res
  }

  return {
    token,
    user,
    profile,
    isLoggedIn,
    userRole,
    isVerifiedStudent,
    nickname,
    login,
    register,
    fetchCurrentUser,
    loginWithGithub,
    logout,
    updateUserProfile,
  }
})

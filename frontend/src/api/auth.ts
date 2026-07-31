import { http } from './request'
import type { User, AuthResponse, UserProfile } from '@/types'

// 用户注册
export function register(data: {
  email: string
  password: string
  nickname?: string
}) {
  return http.post<{ message: string; detail?: string }>('/auth/register', data)
}

// 用户登录
export function login(data: {
  email: string
  password: string
}) {
  return http.post<AuthResponse>('/auth/login', data)
}

// 获取当前用户信息
export function getCurrentUser() {
  return http.get<User>('/auth/me')
}

// 更新用户资料
export function updateProfile(data: Partial<UserProfile>) {
  return http.put<User>('/auth/me', data)
}

// GitHub OAuth 获取授权URL
export function getGithubOAuthUrl() {
  return http.get<{ url: string }>('/auth/oauth/github')
}

// GitHub OAuth 回调
export function githubOAuthCallback(code: string) {
  return http.get<AuthResponse>('/auth/oauth/github/callback', { params: { code } })
}

// 退出登录
export function logout() {
  return http.post<{ message: string }>('/auth/logout')
}

// 验证邮箱
export function verifyEmail(data: { email: string; code: string }) {
  return http.post<{ message: string }>('/auth/verify-email', data)
}

// 重新发送验证码
export function resendVerification(email: string) {
  return http.post<{ message: string }>('/auth/resend-verification', null, {
    params: { email },
  })
}

// 发送教育邮箱验证码
export function sendEduVerifyCode(data: { edu_email: string }) {
  return http.post<{ message: string; detail?: string }>('/auth/edu-verify-code', data)
}

// 验证教育邮箱
export function verifyEduEmail(data: { edu_email: string; code: string }) {
  return http.post<{ verified: boolean; message: string }>('/auth/verify-edu-email', data)
}

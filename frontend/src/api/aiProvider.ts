import { http } from './request'

// ===== 类型定义 =====
export interface BuiltinProvider {
  id: string
  name: string
  base_url: string
  models: string[]
  default_model: string
  website: string
  description: string
}

export interface AIProviderConfig {
  id: number
  provider_id: string
  display_name: string
  api_key_masked: string
  base_url: string
  model: string
  is_active: boolean
  last_tested: string | null
  last_test_ok: boolean | null
  created_at: string
  updated_at: string
}

export interface AIProviderListResponse {
  items: AIProviderConfig[]
  total: number
}

export interface CreateProviderData {
  provider_id: string
  display_name: string
  api_key: string
  base_url: string
  model: string
  is_active?: boolean
}

export interface UpdateProviderData {
  display_name?: string
  api_key?: string
  base_url?: string
  model?: string
  is_active?: boolean
}

export interface TestConnectionData {
  api_key: string
  base_url: string
  model: string
}

export interface TestConnectionResult {
  success: boolean
  message: string
  response?: string
}

// ===== API 请求 =====
export function getBuiltinProviders() {
  return http.get<BuiltinProvider[]>('/ai-providers/builtin')
}

export function getMyProviders() {
  return http.get<AIProviderListResponse>('/ai-providers')
}

export function createProvider(data: CreateProviderData) {
  return http.post<AIProviderConfig>('/ai-providers', data)
}

export function updateProvider(id: number, data: UpdateProviderData) {
  return http.put<AIProviderConfig>(`/ai-providers/${id}`, data)
}

export function deleteProvider(id: number) {
  return http.delete(`/ai-providers/${id}`)
}

export function testConnection(data: TestConnectionData) {
  return http.post<TestConnectionResult>('/ai-providers/test', data)
}

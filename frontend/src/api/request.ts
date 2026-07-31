import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const request: AxiosInstance = axios.create({
  baseURL,
  timeout: 30000,
  withCredentials: true, // 允许携带 cookie
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动添加 token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data
    // 如果返回的是文件流，直接返回
    if (response.config.responseType === 'blob') {
      return response as unknown as AxiosResponse
    }
    // 业务逻辑错误
    if (res.code && res.code !== 200 && res.code !== 0) {
      console.error('API Error:', res.message)
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res as unknown as AxiosResponse
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      switch (status) {
        case 401: {
          // token 过期或未授权，清除登录状态并跳转登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('user_info')
          const currentPath = window.location.pathname
          if (currentPath !== '/login' && currentPath !== '/register') {
            window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`
          }
          break
        }
        case 403:
          console.error('没有权限访问该资源')
          break
        case 404:
          console.error('请求的资源不存在')
          break
        case 500:
          console.error('服务器内部错误')
          break
        default:
          console.error(`请求错误: ${status}`)
      }
    } else if (error.code === 'ECONNABORTED') {
      console.error('请求超时，请检查网络连接')
    } else {
      console.error('网络异常，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

// 封装请求方法
export const http = {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return request.get(url, config) as unknown as Promise<T>
  },
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return request.post(url, data, config) as unknown as Promise<T>
  },
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return request.put(url, data, config) as unknown as Promise<T>
  },
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return request.delete(url, config) as unknown as Promise<T>
  },
  download(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return request.get(url, { ...config, responseType: 'blob' }) as unknown as Promise<AxiosResponse>
  },
}

export default request

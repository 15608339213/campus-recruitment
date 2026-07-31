import { http } from './request'
import type { Feedback, FeedbackCategory } from '@/types'

// 提交反馈
export function submitFeedback(data: {
  category: FeedbackCategory
  content: string
}) {
  return http.post<Feedback>('/feedback', data)
}

// 获取我的反馈列表
export function getFeedbackList(params?: {
  page?: number
  page_size?: number
}) {
  const queryParams: Record<string, unknown> = {}
  if (params?.page) queryParams.skip = (params.page - 1) * (params.page_size || 10)
  if (params?.page_size) queryParams.limit = params.page_size
  return http.get<{
    items: Feedback[]
    total: number
  }>('/feedback/me', { params: queryParams })
}

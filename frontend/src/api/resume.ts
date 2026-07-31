import { http } from './request'
import type { Resume, ResumeGenerateRequest, ResumeContent } from '@/types'

// AI 生成简历
export function generateResume(data: ResumeGenerateRequest) {
  return http.post<Resume>('/resume/generate', data)
}

// 获取简历列表
export function getResumeList(params?: { page?: number; page_size?: number }) {
  return http.get<{ items: Resume[]; total: number }>('/resume', { params })
}

// 获取简历详情
export function getResumeDetail(id: number) {
  return http.get<Resume>(`/resume/${id}`)
}

// 下载简历 PDF
export function downloadResumePdf(id: number) {
  return http.download(`/resume/${id}/pdf`)
}

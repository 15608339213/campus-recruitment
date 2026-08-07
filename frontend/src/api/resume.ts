import { http } from './request'
import type { Resume, ResumeGenerateRequest, ResumeContent, ResumeTemplate } from '@/types'

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

// ===== 简历模板 =====

// 获取模板列表
export function getTemplates(params?: { category?: string; style?: string }) {
  return http.get<{ items: ResumeTemplate[]; total: number }>('/resume/templates', { params })
}

// 获取单个模板详情
export function getTemplateById(id: number) {
  return http.get<ResumeTemplate>(`/resume/templates/${id}`)
}

// ===== 简历分析 =====

export interface ResumeAnalysisResult {
  id: number
  ats_score: number | null
  skills_matched: string[] | null
  missing_keywords: string[] | null
  suggestions: { title: string; detail: string }[] | null
  created_at: string
}

// AI 分析简历
export function analyzeResume(data: { resume_text: string; target_job_category?: string }) {
  return http.post<ResumeAnalysisResult>('/resume/analyze', data)
}

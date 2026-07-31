import { http } from './request'
import type { AnalysisStats } from '@/types'

// 获取行业分析统计数据
export function getAnalysisStats(params?: {
  range?: string
  job_type?: string
}) {
  return http.get<AnalysisStats>('/analysis/stats', { params })
}

// 获取薪资分布详情
export function getSalaryDistribution(params?: {
  job_category?: string
  location?: string
}) {
  return http.get('/analysis/salary', { params })
}

// 获取个人职业推荐
export function getCareerRecommendation() {
  return http.get<{
    major: string
    industry_stats: { industries: { category: string; job_count: number; avg_salary_max: number }[] }
    recommendation: { recommended_industries: { name: string; match_score: number; reason: string }[]; summary: string }
  }>('/analysis/recommend')
}

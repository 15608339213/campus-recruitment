import { http } from './request'
import type { Job, JobListResponse, JobFilter } from '@/types'

// 获取岗位列表（带筛选和分页）
export function getJobList(params: Partial<JobFilter>) {
  const queryParams: Record<string, unknown> = {
    skip: ((params.page || 1) - 1) * (params.page_size || 10),
    limit: params.page_size || 10,
  }
  if (params.keyword) queryParams.keyword = params.keyword
  if (params.company_type) queryParams.company_type = params.company_type
  if (params.location) queryParams.location = params.location
  if (params.industry) queryParams.job_category = params.industry
  if (params.job_type) queryParams.job_type = params.job_type
  if (params.degree_required) queryParams.degree_required = params.degree_required
  if (params.salary_min) queryParams.salary_min = params.salary_min
  if (params.salary_max) queryParams.salary_max = params.salary_max
  if (params.sort_by) queryParams.sort_by = params.sort_by
  return http.get<JobListResponse>('/jobs', { params: queryParams })
}

// 获取岗位详情
export function getJobDetail(id: number | string) {
  return http.get<Job>(`/jobs/${id}`)
}

// 获取筛选选项（从岗位数据中提取）
export function getFilterOptions() {
  return http.get<{
    industries: string[]
    locations: string[]
    company_types: string[]
    degrees: string[]
  }>('/jobs/meta')
}

// 收藏岗位
export function favoriteJob(jobId: number) {
  return http.post(`/jobs/${jobId}/favorite`)
}

// 取消收藏
export function unfavoriteJob(jobId: number) {
  return http.delete(`/jobs/${jobId}/favorite`)
}

// 获取用户收藏列表
export function getFavoriteJobs(params?: { page?: number; page_size?: number }) {
  const queryParams: Record<string, unknown> = {}
  if (params?.page) queryParams.skip = (params.page - 1) * (params.page_size || 10)
  if (params?.page_size) queryParams.limit = params.page_size
  return http.get<JobListResponse>('/jobs/favorites/me', { params: queryParams })
}

// 获取所有标签
export function getAllTags() {
  return http.get<{ id: number; tag: string }[]>('/jobs/tags/all')
}

import type { Job, DegreeRequired, CompanyType, JobType } from '@/types'

/**
 * 格式化日期
 */
export function formatDate(dateStr: string | undefined | null, format: string = 'YYYY-MM-DD'): string {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return '未知'

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
}

/**
 * 格式化薪资
 */
export function formatSalary(min: number, max: number, unit: string): string {
  if (!min && !max) return '面议'
  const unitLabel = unit === 'month' ? 'K/月' : unit === 'year' ? '万/年' : unit
  if (min && max) {
    return `${min}-${max}${unitLabel}`
  }
  return `${min || max}${unitLabel}`
}

/**
 * 获取薪资范围标签颜色
 */
export function getSalaryColor(min: number, max: number): 'success' | 'warning' | 'error' | 'info' {
  const avg = (min + max) / 2
  if (avg >= 20) return 'error'
  if (avg >= 10) return 'warning'
  if (avg >= 5) return 'success'
  return 'info'
}

/**
 * 格式化企业类型
 */
export function formatCompanyType(type: CompanyType): string {
  const map: Record<CompanyType, string> = {
    '国企': '国企',
    '民企': '民企',
    '外企': '外企',
    '事业单位': '事业单位',
    '合资': '合资',
  }
  return map[type] || type
}

/**
 * 获取企业类型标签颜色
 */
export function getCompanyTypeColor(type: CompanyType): 'success' | 'warning' | 'error' | 'info' | 'default' {
  const map: Record<CompanyType, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
    '国企': 'error',
    '民企': 'success',
    '外企': 'info',
    '事业单位': 'warning',
    '合资': 'default',
  }
  return map[type] || 'default'
}

/**
 * 格式化学历要求
 */
export function formatDegree(degree: DegreeRequired): string {
  return degree || '不限'
}

/**
 * 格式化岗位类型
 */
export function formatJobType(type: JobType): string {
  const map: Record<JobType, string> = {
    '校招': '校园招聘',
    '实习': '实习',
    '社招': '社会招聘',
  }
  return map[type] || type
}

/**
 * 获取岗位类型标签颜色
 */
export function getJobTypeColor(type: JobType): 'success' | 'warning' | 'error' | 'info' {
  const map: Record<JobType, 'success' | 'warning' | 'error' | 'info'> = {
    '校招': 'info',
    '实习': 'success',
    '社招': 'warning',
  }
  return map[type] || 'info'
}

/**
 * 计算距截止日期的剩余天数
 */
export function getDaysLeft(endDate: string | undefined): number | null {
  if (!endDate) return null
  const end = new Date(endDate)
  if (isNaN(end.getTime())) return null
  const now = new Date()
  const diff = end.getTime() - now.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

/**
 * 格式化剩余天数
 */
export function formatDaysLeft(endDate: string | undefined): string {
  const days = getDaysLeft(endDate)
  if (days === null) return '未知'
  if (days < 0) return '已截止'
  if (days === 0) return '今天截止'
  if (days <= 3) return `还剩${days}天`
  return `还剩${days}天`
}

/**
 * 获取剩余天数标签类型
 */
export function getDaysLeftType(endDate: string | undefined): 'error' | 'warning' | 'success' | 'default' {
  const days = getDaysLeft(endDate)
  if (days === null || days < 0) return 'default'
  if (days <= 3) return 'error'
  if (days <= 7) return 'warning'
  return 'success'
}

/**
 * 截断文本
 */
export function truncate(text: string, length: number): string {
  if (!text) return ''
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}

/**
 * 获取岗位卡片标签
 */
export function getJobTags(job: Job): string[] {
  const tags: string[] = []
  if (job.tags && job.tags.length > 0) {
    tags.push(...job.tags.slice(0, 4))
  }
  return tags
}

/**
 * 格式化数字（千分位）
 */
export function formatNumber(num: number | undefined | null): string {
  if (num === undefined || num === null || isNaN(num)) return '0'
  return num.toLocaleString('zh-CN')
}

/**
 * 格式化平均薪资（元转 K/月）
 */
export function formatAvgSalary(avgSalary: number | undefined | null): string {
  if (!avgSalary || isNaN(avgSalary)) return '面议'
  if (avgSalary >= 1000) {
    return `${(avgSalary / 1000).toFixed(1)}K/月`
  }
  return `${Math.round(avgSalary)}元/月`
}

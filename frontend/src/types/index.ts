// 用户相关类型
export interface User {
  id: number
  email: string
  nickname: string
  role: 'user' | 'verified_student' | 'admin'
  is_active?: boolean
  is_verified?: boolean
  oauth_provider?: string | null
  created_at?: string
  avatar_url?: string
  profile?: UserProfile | null
}

export interface UserProfile {
  user_id?: number
  edu_email?: string
  edu_verified: boolean
  school?: string
  major?: string
  graduation_year?: number
  phone?: string
  bio?: string
  avatar_url?: string
  skills: string[]
  experience: ExperienceItem[]
  projects: ProjectItem[]
  experience_json?: any
  projects_json?: any
  updated_at?: string
}

export interface ExperienceItem {
  id?: number
  company: string
  position: string
  start_date: string
  end_date: string
  description: string
}

export interface ProjectItem {
  id?: number
  name: string
  role: string
  description: string
  url?: string
}

// 岗位相关类型
export interface Job {
  id: number
  title: string
  company: string
  company_type: CompanyType
  location: string
  salary_min: number
  salary_max: number
  salary_unit: string
  start_date: string
  end_date: string
  job_category: string
  job_type: JobType
  degree_required: DegreeRequired
  description_html: string
  source_url: string
  source_repo?: string
  apply_url?: string
  apply_email?: string
  poster_url?: string
  source_verified?: boolean
  source_platform?: string
  view_count?: number
  apply_count?: number
  tags: string[]
  is_active: boolean
  created_at: string
  is_favorited?: boolean
}

export type CompanyType = '国企' | '民企' | '外企' | '事业单位' | '合资'
export type JobType = '校招' | '实习' | '社招'
export type DegreeRequired = '不限' | '大专' | '本科' | '硕士' | '博士'

export interface JobFilter {
  keyword?: string
  industry?: string
  company_type?: CompanyType | ''
  location?: string
  salary_min?: number
  salary_max?: number
  degree_required?: DegreeRequired | ''
  job_type?: JobType | ''
  sort_by?: 'latest' | 'deadline' | 'salary'
  page?: number
  page_size?: number
}

export interface JobListResponse {
  items: Job[]
  total: number
  page: number
  page_size: number
}

// 简历相关类型
export interface Resume {
  id: number
  user_id: number
  target_job_id?: number
  target_job_title?: string
  customized_content: ResumeContent
  pdf_url?: string
  version: number
  created_at: string
}

export interface ResumeContent {
  basic_info: {
    name: string
    phone: string
    email: string
    location?: string
  }
  education: {
    school: string
    major: string
    degree: string
    graduation_year: string
  }[]
  experience: ExperienceItem[]
  projects: ProjectItem[]
  skills: string[]
  self_evaluation: string
}

export interface ResumeGenerateRequest {
  target_job_id?: number
  target_job_title?: string
  personal_experience: string
  skills: string[]
  projects: ProjectItem[]
}

// 分析相关类型
export interface AnalysisStats {
  total_jobs: number
  avg_salary: number
  daily_avg_jobs: number
  active_industries: number
  trend_data: TrendPoint[]
  industry_distribution: CategoryData[]
  company_type_distribution: CategoryData[]
  region_distribution: CategoryData[]
  salary_by_industry: SalaryData[]
  top_companies: TopCompany[]
}

export interface TrendPoint {
  date: string
  jobs: number
}

export interface CategoryData {
  name: string
  value: number
}

export interface SalaryData {
  industry: string
  avg_salary: number
  min_salary: number
  max_salary: number
}

export interface TopCompany {
  company: string
  industry: string
  company_type: string
  jobs: number
  salary_avg: number
}

// 反馈相关类型
export interface Feedback {
  id?: number
  category: FeedbackCategory
  content: string
  status?: 'pending' | 'processing' | 'resolved' | 'closed'
  admin_reply?: string
  created_at?: string
}

export type FeedbackCategory = 'bug' | 'suggestion' | 'complaint' | 'praise' | 'other'

// 通用 API 响应
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// 简历模板
export interface ResumeTemplate {
  id: number
  name: string
  category: string
  description: string | null
  html_structure: string
  css_rules: string
  style_tags: string | null
  supported_sections: string | null
  color_themes: string | null
  preview_url: string | null
  is_builtin: boolean
  is_public: boolean
  downloads: number
  created_at: string
}

// 登录/注册响应
export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in?: number
  user: User
}

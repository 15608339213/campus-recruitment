import { http } from './request'

// ===== 类型定义 =====
export interface InterviewTip {
  id: number
  job_category: string
  content_markdown: string
  updated_at: string
}

export interface InterviewTipListResponse {
  items: InterviewTip[]
  total: number
}

export interface Question {
  id: number
  job_category: string
  question: string
  answer?: string
  question_type?: string
  difficulty?: string
  company?: string
  source?: string
  updated_at: string
}

export interface QuestionCreate {
  job_category: string
  question: string
  answer?: string
  question_type?: string
  difficulty?: string
  company?: string
  source?: string
}

export interface QuestionListResponse {
  items: Question[]
  total: number
  skip: number
  limit: number
}

export interface CategoryInfo {
  categories: string[]
  counts: Record<string, number>
}

// ===== API 函数 =====

// 获取所有面试技巧
export function getAllTips() {
  return http.get<InterviewTipListResponse>('/interview/tips')
}

// 按岗位类别获取面试技巧
export function getTipByCategory(category: string) {
  return http.get<InterviewTip>(`/interview/tips/${encodeURIComponent(category)}`)
}

// 获取题库列表
export function getQuestionList(params: {
  job_category?: string
  question_type?: string
  difficulty?: string
  company?: string
  page?: number
  page_size?: number
}) {
  const queryParams: Record<string, unknown> = {
    skip: ((params.page || 1) - 1) * (params.page_size || 20),
    limit: params.page_size || 20,
  }
  if (params.job_category) queryParams.job_category = params.job_category
  if (params.question_type) queryParams.question_type = params.question_type
  if (params.difficulty) queryParams.difficulty = params.difficulty
  if (params.company) queryParams.company = params.company
  return http.get<QuestionListResponse>('/interview/questions', { params: queryParams })
}

// 获取题目详情
export function getQuestionDetail(id: number) {
  return http.get<Question>(`/interview/questions/${id}`)
}

// 获取所有有数据的岗位类别
export function getCategories() {
  return http.get<CategoryInfo>('/interview/categories')
}

// 创建题目
export function createQuestion(data: QuestionCreate) {
  return http.post<Question>('/interview/questions', data)
}

// 更新题目
export function updateQuestion(id: number, data: Partial<QuestionCreate>) {
  return http.put<Question>(`/interview/questions/${id}`, data)
}

// 删除题目
export function deleteQuestion(id: number) {
  return http.delete(`/interview/questions/${id}`)
}

// 批量导入题目
export function batchImportQuestions(questions: QuestionCreate[]) {
  return http.post<{ success_count: number; failed_count: number; errors?: string[] }>(
    '/interview/questions/batch',
    questions
  )
}

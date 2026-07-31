import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Job, JobFilter, JobListResponse } from '@/types'
import * as jobApi from '@/api/job'

export const useJobStore = defineStore('job', () => {
  // 状态
  const jobs = ref<Job[]>([])
  const total = ref(0)
  const loading = ref(false)
  const favorites = ref<Set<number>>(new Set())

  // 筛选条件
  const filter = ref<JobFilter>({
    keyword: '',
    industry: '',
    company_type: '',
    location: '',
    salary_min: undefined,
    salary_max: undefined,
    degree_required: '',
    job_type: '',
    sort_by: 'latest',
    page: 1,
    page_size: 10,
  })

  // 筛选选项
  const filterOptions = ref<{
    industries: string[]
    company_types: string[]
    locations: string[]
    degrees: string[]
  }>({
    industries: [],
    company_types: [],
    locations: [],
    degrees: [],
  })

  // 计算属性
  const totalPages = computed(() => Math.ceil(total.value / (filter.value.page_size || 10)))

  // 方法
  async function fetchJobs() {
    loading.value = true
    try {
      const res: JobListResponse = await jobApi.getJobList(filter.value)
      jobs.value = res.items
      total.value = res.total
    } catch (error) {
      console.error('获取岗位列表失败:', error)
      jobs.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  async function fetchJobDetail(id: number | string): Promise<Job | null> {
    try {
      return await jobApi.getJobDetail(id)
    } catch (error) {
      console.error('获取岗位详情失败:', error)
      return null
    }
  }

  async function fetchFilterOptions() {
    try {
      const res = await jobApi.getFilterOptions()
      filterOptions.value = res
    } catch (error) {
      console.error('获取筛选选项失败:', error)
    }
  }

  async function toggleFavorite(job: Job) {
    try {
      if (job.is_favorited) {
        await jobApi.unfavoriteJob(job.id)
        job.is_favorited = false
        favorites.value.delete(job.id)
      } else {
        await jobApi.favoriteJob(job.id)
        job.is_favorited = true
        favorites.value.add(job.id)
      }
    } catch (error) {
      console.error('收藏操作失败:', error)
    }
  }

  async function fetchFavorites() {
    loading.value = true
    try {
      const res = await jobApi.getFavoriteJobs()
      jobs.value = res.items
      total.value = res.total
    } catch (error) {
      console.error('获取收藏列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  function updateFilter(newFilter: Partial<JobFilter>) {
    filter.value = { ...filter.value, ...newFilter, page: 1 }
    fetchJobs()
  }

  function resetFilter() {
    filter.value = {
      keyword: '',
      industry: '',
      company_type: '',
      location: '',
      salary_min: undefined,
      salary_max: undefined,
      degree_required: '',
      job_type: '',
      sort_by: 'latest',
      page: 1,
      page_size: 10,
    }
    fetchJobs()
  }

  function changePage(page: number) {
    filter.value.page = page
    fetchJobs()
  }

  return {
    jobs,
    total,
    loading,
    favorites,
    filter,
    filterOptions,
    totalPages,
    fetchJobs,
    fetchJobDetail,
    fetchFilterOptions,
    toggleFavorite,
    fetchFavorites,
    updateFilter,
    resetFilter,
    changePage,
  }
})

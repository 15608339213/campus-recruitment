<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useJobStore } from '@/stores/job'
import { useAuthStore } from '@/stores/auth'
import {
  NCard,
  NButton,
  NTag,
  NSpace,
  NSelect,
  NInput,
  NEmpty,
  NSpin,
  NPagination,
  NIcon,
  NRadioGroup,
  NRadio,
  NCollapse,
  NCollapseItem,
  NDivider,
  useMessage,
} from 'naive-ui'
import {
  LocationOutline,
  CalendarOutline,
  CashOutline,
  HeartOutline,
  Heart,
  BriefcaseOutline,
  RefreshOutline,
  TimeOutline,
} from '@vicons/ionicons5'
import type { Job } from '@/types'
import {
  formatSalary,
  formatCompanyType,
  getCompanyTypeColor,
  formatDegree,
  formatJobType,
  getJobTypeColor,
  formatDate,
  formatDaysLeft,
  getDaysLeftType,
} from '@/utils/format'

const router = useRouter()
const route = useRoute()
const jobStore = useJobStore()
const authStore = useAuthStore()
const message = useMessage()

// 排序选项
const sortOptions = [
  { label: '最新发布', value: 'latest' },
  { label: '截止时间', value: 'deadline' },
  { label: '薪资最高', value: 'salary_desc' },
]

// 学历选项
const degreeOptions = [
  { label: '不限', value: '' },
  { label: '大专', value: '大专' },
  { label: '本科', value: '本科' },
  { label: '硕士', value: '硕士' },
  { label: '博士', value: '博士' },
]

// 企业类型选项
const companyTypeOptions = [
  { label: '不限', value: '' },
  { label: '国企', value: '国企' },
  { label: '民企', value: '民企' },
  { label: '外企', value: '外企' },
  { label: '事业单位', value: '事业单位' },
  { label: '合资', value: '合资' },
]

// 岗位类型
const jobTypeOptions = [
  { label: '不限', value: '' },
  { label: '校招', value: '校招' },
  { label: '实习', value: '实习' },
  { label: '社招', value: '社招' },
]

// 薪资范围
const salaryRanges = [
  { label: '不限', value: '' },
  { label: '5K以下', value: '0-5' },
  { label: '5-10K', value: '5-10' },
  { label: '10-20K', value: '10-20' },
  { label: '20-30K', value: '20-30' },
  { label: '30K以上', value: '30-100' },
]

const selectedSalaryRange = ref('')

function handleSalaryRangeChange(value: string) {
  selectedSalaryRange.value = value
  if (value) {
    const [min, max] = value.split('-').map(Number)
    jobStore.updateFilter({ salary_min: min, salary_max: max })
  } else {
    jobStore.updateFilter({ salary_min: undefined, salary_max: undefined })
  }
}

function goToDetail(job: Job) {
  router.push(`/jobs/${job.id}`)
}

async function handleFavorite(job: Job) {
  if (!authStore.isLoggedIn) {
    message.warning('请先登录后再收藏')
    router.push('/login')
    return
  }
  await jobStore.toggleFavorite(job)
  message.success(job.is_favorited ? '已收藏' : '已取消收藏')
}

function handleSortChange(value: string) {
  jobStore.updateFilter({ sort_by: value as 'latest' | 'deadline' | 'salary' })
}

function handlePageChange(page: number) {
  jobStore.changePage(page)
}

function handleReset() {
  selectedSalaryRange.value = ''
  jobStore.resetFilter()
}

function handleIndustryChange(value: string) {
  jobStore.updateFilter({ industry: value })
}

function handleLocationChange(value: string) {
  jobStore.updateFilter({ location: value })
}

// 从 URL 获取搜索关键词
watch(
  () => route.query.keyword,
  (keyword) => {
    if (keyword) {
      jobStore.updateFilter({ keyword: keyword as string })
    }
  },
  { immediate: true }
)

onMounted(() => {
  jobStore.fetchFilterOptions()
  jobStore.fetchJobs()
})
</script>

<template>
  <div class="job-list-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <n-icon size="24" color="#2563eb"><BriefcaseOutline /></n-icon>
        岗位列表
      </h1>
      <p class="page-desc">共找到 {{ jobStore.total }} 个岗位</p>
    </div>

    <div class="job-list-layout">
      <!-- 筛选侧边栏 -->
      <div class="filter-sidebar">
        <n-card title="筛选条件" :bordered="false" size="small">
          <template #header-extra>
            <n-button text size="small" @click="handleReset">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              重置
            </n-button>
          </template>

          <n-space vertical size="large">
            <!-- 搜索关键词 -->
            <div>
              <p class="filter-label">关键词搜索</p>
              <n-input
                :value="jobStore.filter.keyword"
                placeholder="搜索岗位或公司"
                clearable
                @update:value="(v) => jobStore.updateFilter({ keyword: v })"
              />
            </div>

            <!-- 行业类别 -->
            <div>
              <p class="filter-label">行业类别</p>
              <n-select
                :value="jobStore.filter.industry"
                :options="[
                  { label: '不限', value: '' },
                  ...jobStore.filterOptions.industries.map((i) => ({ label: i, value: i })),
                ]"
                placeholder="选择行业"
                clearable
                @update:value="handleIndustryChange"
              />
            </div>

            <!-- 企业类型 -->
            <div>
              <p class="filter-label">企业类型</p>
              <n-radio-group
                :value="jobStore.filter.company_type"
                @update:value="(v) => jobStore.updateFilter({ company_type: v as any })"
              >
                <n-space>
                  <n-radio
                    v-for="opt in companyTypeOptions"
                    :key="opt.value"
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </n-radio>
                </n-space>
              </n-radio-group>
            </div>

            <!-- 地点 -->
            <div>
              <p class="filter-label">工作地点</p>
              <n-select
                :value="jobStore.filter.location"
                :options="[
                  { label: '不限', value: '' },
                  ...jobStore.filterOptions.locations.map((l) => ({ label: l, value: l })),
                ]"
                placeholder="选择城市"
                clearable
                filterable
                @update:value="handleLocationChange"
              />
            </div>

            <!-- 薪资范围 -->
            <div>
              <p class="filter-label">薪资范围</p>
              <n-radio-group
                :value="selectedSalaryRange"
                @update:value="handleSalaryRangeChange"
              >
                <n-space>
                  <n-radio
                    v-for="opt in salaryRanges"
                    :key="opt.value"
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </n-radio>
                </n-space>
              </n-radio-group>
            </div>

            <!-- 学历要求 -->
            <div>
              <p class="filter-label">学历要求</p>
              <n-select
                :value="jobStore.filter.degree_required"
                :options="degreeOptions"
                placeholder="选择学历"
                clearable
                @update:value="(v) => jobStore.updateFilter({ degree_required: v as any })"
              />
            </div>

            <!-- 岗位类型 -->
            <div>
              <p class="filter-label">岗位类型</p>
              <n-radio-group
                :value="jobStore.filter.job_type"
                @update:value="(v) => jobStore.updateFilter({ job_type: v as any })"
              >
                <n-space>
                  <n-radio
                    v-for="opt in jobTypeOptions"
                    :key="opt.value"
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </n-radio>
                </n-space>
              </n-radio-group>
            </div>
          </n-space>
        </n-card>
      </div>

      <!-- 岗位列表 -->
      <div class="job-list-main">
        <!-- 排序栏 -->
        <div class="sort-bar">
          <n-space align="center">
            <span class="sort-label">排序方式：</span>
            <n-select
              :value="jobStore.filter.sort_by"
              :options="sortOptions"
              style="width: 160px"
              @update:value="handleSortChange"
            />
          </n-space>
        </div>

        <!-- 加载中 -->
        <div v-if="jobStore.loading" class="loading-wrapper">
          <n-spin size="large" />
        </div>

        <!-- 空状态 -->
        <n-empty
          v-else-if="jobStore.jobs.length === 0"
          description="暂无符合条件的岗位"
          style="padding: 80px 0"
        >
          <template #extra>
            <n-button type="primary" @click="handleReset">清除筛选条件</n-button>
          </template>
        </n-empty>

        <!-- 岗位卡片列表 -->
        <div v-else class="job-cards">
          <n-card
            v-for="job in jobStore.jobs"
            :key="job.id"
            class="job-card"
            :bordered="false"
            hoverable
            @click="goToDetail(job)"
          >
            <div class="job-card-content">
              <!-- 左侧主体 -->
              <div class="job-card-main">
                <div class="job-card-header">
                  <h3 class="job-title">{{ job.title }}</h3>
                  <n-tag
                    :type="getJobTypeColor(job.job_type)"
                    size="small"
                    round
                  >
                    {{ formatJobType(job.job_type) }}
                  </n-tag>
                </div>

                <div class="job-company">
                  <span class="company-name">{{ job.company }}</span>
                  <n-tag
                    :type="getCompanyTypeColor(job.company_type)"
                    size="tiny"
                    round
                    :bordered="false"
                  >
                    {{ formatCompanyType(job.company_type) }}
                  </n-tag>
                </div>

                <div class="job-meta">
                  <span class="meta-item">
                    <n-icon size="14"><CashOutline /></n-icon>
                    {{ formatSalary(job.salary_min, job.salary_max, job.salary_unit) }}
                  </span>
                  <span class="meta-item">
                    <n-icon size="14"><LocationOutline /></n-icon>
                    {{ job.location || '地点未知' }}
                  </span>
                  <span class="meta-item">
                    <n-icon size="14"><BriefcaseOutline /></n-icon>
                    {{ formatDegree(job.degree_required) }}
                  </span>
                  <span class="meta-item deadline">
                    <n-icon size="14"><TimeOutline /></n-icon>
                    <n-tag :type="getDaysLeftType(job.end_date)" size="tiny" :bordered="false">
                      {{ formatDaysLeft(job.end_date) }}
                    </n-tag>
                  </span>
                </div>

                <div class="job-tags" v-if="job.tags && job.tags.length">
                  <n-tag
                    v-for="tag in job.tags.slice(0, 4)"
                    :key="tag"
                    size="small"
                    type="info"
                    :bordered="false"
                    round
                  >
                    {{ tag }}
                  </n-tag>
                </div>
              </div>

              <!-- 右侧操作 -->
              <div class="job-card-actions">
                <n-button
                  quaternary
                  circle
                  @click.stop="handleFavorite(job)"
                >
                  <template #icon>
                    <n-icon
                      :color="job.is_favorited ? '#ef4444' : '#9ca3af'"
                      :component="job.is_favorited ? Heart : HeartOutline"
                    />
                  </template>
                </n-button>
                <n-button
                  type="primary"
                  size="small"
                  ghost
                  @click.stop="goToDetail(job)"
                >
                  查看详情
                </n-button>
              </div>
            </div>
          </n-card>
        </div>

        <!-- 分页 -->
        <div class="pagination-wrapper" v-if="!jobStore.loading && jobStore.jobs.length > 0">
          <n-pagination
            :page="jobStore.filter.page || 1"
            :page-size="jobStore.filter.page_size || 10"
            :item-count="jobStore.total"
            show-quick-jumper
            @update:page="handlePageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.job-list-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px;
}

.page-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.job-list-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.filter-sidebar {
  width: 260px;
  flex-shrink: 0;
  position: sticky;
  top: 88px;
}

.filter-label {
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  margin: 0 0 8px;
}

.job-list-main {
  flex: 1;
  min-width: 0;
}

.sort-bar {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.sort-label {
  font-size: 14px;
  color: #6b7280;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.job-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.job-card {
  cursor: pointer;
  border-radius: 8px;
}

.job-card-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.job-card-main {
  flex: 1;
  min-width: 0;
}

.job-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.job-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.job-company {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.company-name {
  font-size: 14px;
  color: #4b5563;
  font-weight: 500;
}

.job-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6b7280;
}

.deadline {
  gap: 6px;
}

.job-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.job-card-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-bottom: 24px;
}

@media (max-width: 768px) {
  .job-list-layout {
    flex-direction: column;
  }

  .filter-sidebar {
    width: 100%;
    position: static;
  }
}
</style>

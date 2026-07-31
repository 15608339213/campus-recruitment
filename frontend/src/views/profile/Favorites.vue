<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useJobStore } from '@/stores/job'
import {
  NCard,
  NButton,
  NTag,
  NSpace,
  NIcon,
  NEmpty,
  NSpin,
  NPagination,
  useMessage,
} from 'naive-ui'
import {
  HeartOutline,
  Heart,
  LocationOutline,
  CashOutline,
  TimeOutline,
  BriefcaseOutline,
} from '@vicons/ionicons5'
import type { Job } from '@/types'
import {
  formatSalary,
  formatCompanyType,
  getCompanyTypeColor,
  formatDegree,
  formatDaysLeft,
  getDaysLeftType,
} from '@/utils/format'

const router = useRouter()
const jobStore = useJobStore()
const message = useMessage()

onMounted(() => {
  jobStore.fetchFavorites()
})

function goToDetail(job: Job) {
  router.push(`/jobs/${job.id}`)
}

async function handleUnfavorite(job: Job) {
  await jobStore.toggleFavorite(job)
  message.success('已取消收藏')
  // 重新获取列表
  jobStore.fetchFavorites()
}

function handlePageChange(page: number) {
  jobStore.changePage(page)
}
</script>

<template>
  <div class="favorites-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <n-icon size="24" color="#2563eb"><HeartOutline /></n-icon>
        我的收藏
      </h1>
      <p class="page-desc">共收藏 {{ jobStore.total }} 个岗位</p>
    </div>

    <!-- 加载中 -->
    <div v-if="jobStore.loading" class="loading-wrapper">
      <n-spin size="large" />
    </div>

    <!-- 空状态 -->
    <n-empty
      v-else-if="jobStore.jobs.length === 0"
      description="还没有收藏任何岗位"
      style="padding: 80px 0"
    >
      <template #extra>
        <n-button type="primary" @click="router.push('/jobs')">去浏览岗位</n-button>
      </template>
    </n-empty>

    <!-- 收藏列表 -->
    <div v-else class="favorite-list">
      <n-card
        v-for="job in jobStore.jobs"
        :key="job.id"
        class="job-card"
        :bordered="false"
        hoverable
        @click="goToDetail(job)"
      >
        <div class="job-card-content">
          <div class="job-card-main">
            <div class="job-card-header">
              <h3 class="job-title">{{ job.title }}</h3>
              <n-tag :type="getCompanyTypeColor(job.company_type)" size="tiny" round :bordered="false">
                {{ formatCompanyType(job.company_type) }}
              </n-tag>
            </div>

            <div class="job-company">
              <span class="company-name">{{ job.company }}</span>
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

          <div class="job-card-actions">
            <n-button
              type="error"
              size="small"
              ghost
              @click.stop="handleUnfavorite(job)"
            >
              <template #icon>
                <n-icon :component="Heart" />
              </template>
              取消收藏
            </n-button>
            <n-button type="primary" size="small" ghost @click.stop="goToDetail(job)">
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
        :page-count="jobStore.totalPages"
        :page-size="jobStore.filter.page_size || 10"
        :item-count="jobStore.total"
        show-quick-jumper
        @update:page="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.favorites-page {
  max-width: 900px;
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

.loading-wrapper {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.favorite-list {
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
</style>

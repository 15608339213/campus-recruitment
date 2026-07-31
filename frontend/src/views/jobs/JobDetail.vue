<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useJobStore } from '@/stores/job'
import { useAuthStore } from '@/stores/auth'
import {
  NCard,
  NButton,
  NTag,
  NSpace,
  NIcon,
  NSpin,
  NEmpty,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  NAlert,
  useMessage,
} from 'naive-ui'
import {
  ArrowBackOutline,
  LocationOutline,
  CashOutline,
  CalendarOutline,
  BriefcaseOutline,
  HeartOutline,
  Heart,
  SchoolOutline,
  LinkOutline,
  TimeOutline,
  AlertCircleOutline,
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

const route = useRoute()
const router = useRouter()
const jobStore = useJobStore()
const authStore = useAuthStore()
const message = useMessage()

const job = ref<Job | null>(null)
const loading = ref(true)

const jobId = computed(() => route.params.id as string)

onMounted(async () => {
  loading.value = true
  job.value = await jobStore.fetchJobDetail(jobId.value)
  loading.value = false
})

function goBack() {
  router.back()
}

async function handleFavorite() {
  if (!job.value) return
  if (!authStore.isLoggedIn) {
    message.warning('请先登录后再收藏')
    router.push('/login')
    return
  }
  await jobStore.toggleFavorite(job.value)
  message.success(job.value.is_favorited ? '已收藏' : '已取消收藏')
}

function goToSource() {
  if (job.value?.source_url) {
    window.open(job.value.source_url, '_blank')
  }
}

function goToResume() {
  if (job.value) {
    router.push({ path: '/resume/generate', query: { job_id: job.value.id.toString() } })
  }
}
</script>

<template>
  <div class="job-detail-page">
    <!-- 返回按钮 -->
    <div class="back-bar">
      <n-button text @click="goBack">
        <template #icon>
          <n-icon><ArrowBackOutline /></n-icon>
        </template>
        返回列表
      </n-button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrapper">
      <n-spin size="large" />
    </div>

    <!-- 空状态 -->
    <n-empty
      v-else-if="!job"
      description="岗位不存在或已下架"
      style="padding: 80px 0"
    >
      <template #extra>
        <n-button type="primary" @click="router.push('/jobs')">返回岗位列表</n-button>
      </template>
    </n-empty>

    <!-- 岗位详情 -->
    <template v-else>
      <!-- 岗位头部信息 -->
      <n-card class="detail-header-card" :bordered="false">
        <div class="detail-header">
          <div class="header-left">
            <h1 class="job-title">{{ job.title }}</h1>
            <div class="job-subtitle">
              <span class="company-name">{{ job.company }}</span>
              <n-tag
                :type="getCompanyTypeColor(job.company_type)"
                size="small"
                round
                :bordered="false"
              >
                {{ formatCompanyType(job.company_type) }}
              </n-tag>
              <n-tag
                :type="getJobTypeColor(job.job_type)"
                size="small"
                round
              >
                {{ formatJobType(job.job_type) }}
              </n-tag>
            </div>

            <div class="job-info-grid">
              <div class="info-item">
                <n-icon size="18" color="#2563eb"><CashOutline /></n-icon>
                <div>
                  <p class="info-label">薪资</p>
                  <p class="info-value">{{ formatSalary(job.salary_min, job.salary_max, job.salary_unit) }}</p>
                </div>
              </div>
              <div class="info-item">
                <n-icon size="18" color="#2563eb"><LocationOutline /></n-icon>
                <div>
                  <p class="info-label">地点</p>
                  <p class="info-value">{{ job.location || '未知' }}</p>
                </div>
              </div>
              <div class="info-item">
                <n-icon size="18" color="#2563eb"><SchoolOutline /></n-icon>
                <div>
                  <p class="info-label">学历要求</p>
                  <p class="info-value">{{ formatDegree(job.degree_required) }}</p>
                </div>
              </div>
              <div class="info-item">
                <n-icon size="18" color="#2563eb"><BriefcaseOutline /></n-icon>
                <div>
                  <p class="info-label">行业类别</p>
                  <p class="info-value">{{ job.job_category || '不限' }}</p>
                </div>
              </div>
              <div class="info-item">
                <n-icon size="18" color="#2563eb"><CalendarOutline /></n-icon>
                <div>
                  <p class="info-label">发布时间</p>
                  <p class="info-value">{{ formatDate(job.start_date) }}</p>
                </div>
              </div>
              <div class="info-item">
                <n-icon size="18" color="#2563eb"><TimeOutline /></n-icon>
                <div>
                  <p class="info-label">截止时间</p>
                  <p class="info-value">
                    {{ formatDate(job.end_date) }}
                    <n-tag :type="getDaysLeftType(job.end_date)" size="tiny" :bordered="false" style="margin-left: 4px">
                      {{ formatDaysLeft(job.end_date) }}
                    </n-tag>
                  </p>
                </div>
              </div>
            </div>

            <div class="job-tags" v-if="job.tags && job.tags.length">
              <n-tag
                v-for="tag in job.tags"
                :key="tag"
                type="info"
                size="small"
                round
                :bordered="false"
              >
                {{ tag }}
              </n-tag>
            </div>
          </div>

          <div class="header-actions">
            <n-button
              size="large"
              :type="job.is_favorited ? 'error' : 'default'"
              @click="handleFavorite"
            >
              <template #icon>
                <n-icon :component="job.is_favorited ? Heart : HeartOutline" />
              </template>
              {{ job.is_favorited ? '已收藏' : '收藏' }}
            </n-button>
            <n-button
              type="primary"
              size="large"
              @click="goToResume"
            >
              生成定制简历
            </n-button>
          </div>
        </div>
      </n-card>

      <!-- 来源提醒 -->
      <n-alert v-if="job.source_repo || job.source_url" type="info" class="source-alert" :bordered="false">
        <template #icon>
          <n-icon><LinkOutline /></n-icon>
        </template>
        本岗位信息来源于{{ job.source_repo ? ` GitHub 仓库 ${job.source_repo}` : '公开渠道' }}，
        <n-button text type="primary" @click="goToSource" v-if="job.source_url">
          点击查看原始链接
        </n-button>
      </n-alert>

      <!-- 岗位描述 -->
      <n-card title="岗位描述" :bordered="false" class="detail-section">
        <div class="job-description" v-html="job.description_html"></div>
      </n-card>

      <!-- 数据来源声明 -->
      <n-alert type="warning" :bordered="false" class="disclaimer-alert">
        <template #icon>
          <n-icon><AlertCircleOutline /></n-icon>
        </template>
        以上信息来源于公开渠道，仅供参考。具体岗位要求和薪资待遇以企业官方发布为准。
      </n-alert>
    </template>
  </div>
</template>

<style scoped>
.job-detail-page {
  max-width: 900px;
  margin: 0 auto;
}

.back-bar {
  margin-bottom: 16px;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.detail-header-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
}

.header-left {
  flex: 1;
}

.job-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px;
}

.job-subtitle {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.company-name {
  font-size: 16px;
  color: #4b5563;
  font-weight: 500;
}

.job-info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.info-label {
  font-size: 12px;
  color: #9ca3af;
  margin: 0 0 2px;
}

.info-value {
  font-size: 14px;
  color: #1f2937;
  font-weight: 500;
  margin: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.job-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.header-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-shrink: 0;
}

.source-alert {
  border-radius: 8px;
  margin-bottom: 16px;
}

.detail-section {
  border-radius: 12px;
  margin-bottom: 16px;
}

.job-description {
  line-height: 1.8;
  color: #374151;
  font-size: 14px;
}

.job-description :deep(h1),
.job-description :deep(h2),
.job-description :deep(h3) {
  font-weight: 600;
  margin: 16px 0 8px;
  color: #1f2937;
}

.job-description :deep(ul),
.job-description :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

.job-description :deep(li) {
  margin: 4px 0;
}

.job-description :deep(p) {
  margin: 8px 0;
}

.disclaimer-alert {
  border-radius: 8px;
}

@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
  }

  .job-info-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .header-actions {
    flex-direction: row;
    width: 100%;
  }

  .header-actions .n-button {
    flex: 1;
  }
}
</style>

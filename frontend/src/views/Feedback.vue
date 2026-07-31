<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NSelect,
  NRadioGroup,
  NRadio,
  NSpace,
  NIcon,
  NDivider,
  NEmpty,
  NTag,
  useMessage,
} from 'naive-ui'
import {
  ChatbubbleEllipsesOutline,
  BugOutline,
  BulbOutline,
  WarningOutline,
  HeartOutline,
  EllipsisHorizontalOutline,
  CheckmarkCircleOutline,
} from '@vicons/ionicons5'
import { submitFeedback, getFeedbackList } from '@/api/feedback'
import type { FeedbackCategory, Feedback } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

const loading = ref(false)
const submitted = ref(false)

const formRef = ref()
const formModel = reactive({
  category: 'suggestion' as FeedbackCategory,
  content: '',
})

const categoryOptions = [
  { label: '功能建议', value: 'suggestion' },
  { label: 'Bug 反馈', value: 'bug' },
  { label: '内容投诉', value: 'complaint' },
  { label: '表扬鼓励', value: 'praise' },
  { label: '其他', value: 'other' },
]

const rules = {
  category: {
    required: true,
    message: '请选择反馈类型',
    trigger: 'change',
  },
  content: {
    required: true,
    message: '请输入反馈内容',
    trigger: ['blur', 'input'],
  },
}

// 历史反馈
const feedbackHistory = ref<Feedback[]>([])

const categoryIcons: Record<string, any> = {
  suggestion: BulbOutline,
  bug: BugOutline,
  complaint: WarningOutline,
  praise: HeartOutline,
  other: EllipsisHorizontalOutline,
}

const statusLabels: Record<string, { label: string; type: 'default' | 'info' | 'success' | 'warning' }> = {
  pending: { label: '待处理', type: 'default' },
  processing: { label: '处理中', type: 'info' },
  resolved: { label: '已解决', type: 'success' },
  closed: { label: '已关闭', type: 'warning' },
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await submitFeedback({
      category: formModel.category,
      content: formModel.content,
    })
    message.success('反馈提交成功，感谢您的支持！')
    submitted.value = true
    formModel.content = ''
    // 刷新历史列表
    loadHistory()
  } catch (error: any) {
    message.error(error.message || '提交失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function loadHistory() {
  if (!authStore.isLoggedIn) return
  try {
    const res = await getFeedbackList({ page: 1, page_size: 10 })
    feedbackHistory.value = res.items
  } catch {
    // ignore
  }
}

function resetForm() {
  submitted.value = false
  formModel.category = 'suggestion'
  formModel.content = ''
}

loadHistory()
</script>

<template>
  <div class="feedback-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <n-icon size="24" color="#2563eb"><ChatbubbleEllipsesOutline /></n-icon>
        意见反馈
      </h1>
      <p class="page-desc">您的反馈是我们持续改进的动力</p>
    </div>

    <div class="feedback-layout">
      <!-- 反馈表单 -->
      <n-card :bordered="false" class="feedback-form-card">
        <!-- 提交成功 -->
        <div v-if="submitted" class="success-state">
          <n-icon size="48" color="#10b981"><CheckmarkCircleOutline /></n-icon>
          <h3 class="success-title">反馈提交成功</h3>
          <p class="success-desc">感谢您的反馈，我们会尽快处理！</p>
          <n-space>
            <n-button type="primary" @click="resetForm">继续反馈</n-button>
            <n-button @click="router.push('/')">返回首页</n-button>
          </n-space>
        </div>

        <!-- 反馈表单 -->
        <n-form
          v-else
          ref="formRef"
          :model="formModel"
          :rules="rules"
          label-placement="top"
          size="medium"
        >
          <n-form-item label="反馈类型" path="category">
            <n-radio-group v-model:value="formModel.category">
              <n-space>
                <n-radio value="suggestion">功能建议</n-radio>
                <n-radio value="bug">Bug 反馈</n-radio>
                <n-radio value="complaint">内容投诉</n-radio>
                <n-radio value="praise">表扬鼓励</n-radio>
                <n-radio value="other">其他</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>

          <n-form-item label="反馈内容" path="content">
            <n-input
              v-model:value="formModel.content"
              type="textarea"
              placeholder="请详细描述您的反馈内容，以便我们更好地处理..."
              :rows="6"
              :maxlength="1000"
              show-count
            />
          </n-form-item>

          <n-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSubmit"
          >
            提交反馈
          </n-button>
        </n-form>
      </n-card>

      <!-- 历史反馈 -->
      <div class="history-section" v-if="authStore.isLoggedIn">
        <n-card :bordered="false" class="history-card">
          <template #header>
            <div class="history-header">
              <n-icon size="18" color="#2563eb"><ChatbubbleEllipsesOutline /></n-icon>
              <span>我的反馈记录</span>
            </div>
          </template>

          <n-empty
            v-if="feedbackHistory.length === 0"
            description="暂无反馈记录"
            style="padding: 40px 0"
          />

          <div v-else class="history-list">
            <div
              v-for="item in feedbackHistory"
              :key="item.id"
              class="history-item"
            >
              <div class="history-item-header">
                <n-space align="center">
                  <n-icon :component="categoryIcons[item.category]" size="16" color="#6b7280" />
                  <span class="history-category">
                    {{ categoryOptions.find((c) => c.value === item.category)?.label }}
                  </span>
                  <n-tag
                    v-if="item.status"
                    :type="statusLabels[item.status]?.type"
                    size="tiny"
                    round
                    :bordered="false"
                  >
                    {{ statusLabels[item.status]?.label }}
                  </n-tag>
                </n-space>
                <span class="history-date">{{ item.created_at }}</span>
              </div>
              <p class="history-content">{{ item.content }}</p>
              <div v-if="item.admin_reply" class="admin-reply">
                <n-tag size="tiny" type="info" :bordered="false">官方回复</n-tag>
                <p class="reply-text">{{ item.admin_reply }}</p>
              </div>
            </div>
          </div>
        </n-card>
      </div>
    </div>

    <!-- 未登录提示 -->
    <n-card v-if="!authStore.isLoggedIn" :bordered="false" class="login-hint-card">
      <div class="login-hint">
        <p>登录后可查看您的反馈记录和处理状态</p>
        <n-button type="primary" size="small" @click="router.push('/login')">去登录</n-button>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
.feedback-page {
  max-width: 800px;
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

.feedback-form-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
}

.success-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 16px 0 8px;
}

.success-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 24px;
}

.history-card {
  border-radius: 12px;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-category {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.history-date {
  font-size: 12px;
  color: #9ca3af;
}

.history-content {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

.admin-reply {
  margin-top: 12px;
  padding: 10px 12px;
  background: #eff6ff;
  border-radius: 6px;
}

.reply-text {
  font-size: 13px;
  color: #1d4ed8;
  margin: 6px 0 0;
  line-height: 1.6;
}

.login-hint-card {
  border-radius: 12px;
}

.login-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.login-hint p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}
</style>

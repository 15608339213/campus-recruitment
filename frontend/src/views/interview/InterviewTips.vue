<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NCard,
  NButton,
  NTag,
  NSpace,
  NSelect,
  NEmpty,
  NSpin,
  NPagination,
  NIcon,
  NTabs,
  NTabPane,
  NCollapse,
  NCollapseItem,
  NRadioGroup,
  NRadio,
  useMessage,
} from 'naive-ui'
import {
  SchoolOutline,
  BookOutline,
  ChevronForwardOutline,
  CodeSlashOutline,
  FilterOutline,
  RefreshOutline,
  DocumentTextOutline,
  TrophyOutline,
  PersonOutline,
} from '@vicons/ionicons5'
import {
  getAllTips,
  getQuestionList,
  getCategories,
  type InterviewTip,
  type Question,
  type CategoryInfo,
} from '@/api/interview'

const message = useMessage()

// ===== 状态 =====
const activeTab = ref('tips')
const loading = ref(false)
const questionsLoading = ref(false)

// 技巧数据
const tips = ref<InterviewTip[]>([])
const selectedCategory = ref<string>('')

// 题库数据
const questions = ref<Question[]>([])
const questionTotal = ref(0)
const questionPage = ref(1)
const questionPageSize = ref(20)

// 筛选
const categories = ref<string[]>([])
const categoryCounts = ref<Record<string, number>>({})
const filterCategory = ref<string>('')
const filterType = ref<string>('')
const filterDifficulty = ref<string>('')
const filterCompany = ref<string>('')

// 公司选项（从来源自动提取）
const companyOptions = computed(() => {
  const companies = new Set<string>()
  questions.value.forEach(q => {
    if (q.source && q.source.includes('面试题')) {
      companies.add(q.source.replace('面试题',''))
    }
  })
  return [{ label: '全部', value: '' }, ...Array.from(companies).map(c => ({ label: c, value: c }))]
})

// 当前查看的技巧
const currentTip = computed(() => {
  if (!tips.value.length) return null
  if (!selectedCategory.value) return tips.value[0]
  return tips.value.find((t) => t.job_category === selectedCategory.value) || tips.value[0]
})

// 题型选项
const typeOptions = [
  { label: '全部', value: '' },
  { label: '笔试', value: '笔试' },
  { label: '面试', value: '面试' },
  { label: 'HR面', value: 'HR面' },
]

// 难度选项
const difficultyOptions = [
  { label: '全部', value: '' },
  { label: '简单', value: 'easy' },
  { label: '中等', value: 'medium' },
  { label: '困难', value: 'hard' },
]

// 难度标签颜色
const difficultyTagType: Record<string, 'default' | 'info' | 'warning' | 'error'> = {
  easy: 'default',
  medium: 'info',
  hard: 'warning',
}

const difficultyLabel: Record<string, string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

// ===== 数据加载 =====
async function loadTips() {
  loading.value = true
  try {
    const res = await getAllTips()
    tips.value = res.items
    if (tips.value.length > 0 && !selectedCategory.value) {
      selectedCategory.value = tips.value[0].job_category
    }
  } catch (error: any) {
    message.error(error.message || '加载面试技巧失败')
  } finally {
    loading.value = false
  }
}

async function loadQuestions() {
  questionsLoading.value = true
  try {
    const res = await getQuestionList({
      job_category: filterCategory.value || undefined,
      question_type: filterType.value || undefined,
      difficulty: filterDifficulty.value || undefined,
      company: filterCompany.value || undefined,
      page: questionPage.value,
      page_size: questionPageSize.value,
    })
    questions.value = res.items
    questionTotal.value = res.total
  } catch (error: any) {
    message.error(error.message || '加载题库失败')
  } finally {
    questionsLoading.value = false
  }
}

async function loadCategories() {
  try {
    const res = await getCategories()
    categories.value = res.categories
    categoryCounts.value = res.counts
  } catch {
    // ignore
  }
}

// 筛选变化时重新加载
function handleFilterChange() {
  questionPage.value = 1
  loadQuestions()
}

function handlePageChange(page: number) {
  questionPage.value = page
  loadQuestions()
}

function handleResetFilter() {
  filterCategory.value = ''
  filterType.value = ''
  filterDifficulty.value = ''
  filterCompany.value = ''
  questionPage.value = 1
  loadQuestions()
}

// 简易 Markdown 渲染（将 ## ### ** 等转为 HTML）
function renderMarkdown(md: string): string {
  if (!md) return ''
  let html = md
    // 标题
    .replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>')
    // 粗体
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // 列表项
    .replace(/^\d+\. (.+)$/gm, '<li class="md-li">$1</li>')
    .replace(/^- (.+)$/gm, '<li class="md-li">$1</li>')
    // 段落（连续非标签行）
    .replace(/^(?!<[hlu])(.+)$/gm, '<p class="md-p">$1</p>')
    // 换行
    .replace(/\n/g, '')
  return html
}

// 类别图标
const categoryIcons: Record<string, any> = {
  '技术': CodeSlashOutline,
  '产品': TrophyOutline,
  '运营': PersonOutline,
  '金融': SchoolOutline,
  '设计': BookOutline,
}

onMounted(() => {
  loadTips()
  loadCategories()
  loadQuestions()
})
</script>

<template>
  <div class="interview-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <n-icon size="24" color="#2563eb"><SchoolOutline /></n-icon>
        面试技巧与题库
      </h1>
      <p class="page-desc">按岗位类别查看面试技巧，练习笔试面试题目</p>
    </div>

    <n-tabs v-model:value="activeTab" type="line" animated size="large">
      <!-- ===== 面试技巧 Tab ===== -->
      <n-tab-pane name="tips" tab="面试技巧">
        <div class="tips-layout">
          <!-- 类别侧边栏 -->
          <div class="tips-sidebar">
            <n-card title="岗位类别" :bordered="false" size="small">
              <n-space vertical size="small">
                <div
                  v-for="tip in tips"
                  :key="tip.job_category"
                  class="category-item"
                  :class="{ active: selectedCategory === tip.job_category }"
                  @click="selectedCategory = tip.job_category"
                >
                  <n-icon
                    v-if="categoryIcons[tip.job_category]"
                    size="16"
                    :color="selectedCategory === tip.job_category ? '#2563eb' : '#9ca3af'"
                    :component="categoryIcons[tip.job_category]"
                  />
                  <span>{{ tip.job_category }}</span>
                  <n-icon size="14" color="#d1d5db">
                    <ChevronForwardOutline />
                  </n-icon>
                </div>
              </n-space>
            </n-card>
          </div>

          <!-- 技巧内容 -->
          <div class="tips-content">
            <n-spin :show="loading">
              <n-card v-if="currentTip" :bordered="false" class="tip-card">
                <template #header>
                  <div class="tip-header">
                    <n-icon size="20" color="#2563eb"><BookOutline /></n-icon>
                    <span>{{ currentTip.job_category }} 面试技巧</span>
                  </div>
                </template>
                <template #header-extra>
                  <n-tag size="tiny" type="info" :bordered="false" round>
                    更新于 {{ currentTip.updated_at?.slice(0, 10) }}
                  </n-tag>
                </template>
                <div class="markdown-body" v-html="renderMarkdown(currentTip.content_markdown)">
                </div>
              </n-card>
              <n-empty v-else description="暂无面试技巧数据" style="padding: 60px 0">
                <template #extra>
                  <n-button type="primary" @click="loadTips">重新加载</n-button>
                </template>
              </n-empty>
            </n-spin>
          </div>
        </div>
      </n-tab-pane>

      <!-- ===== 题库 Tab ===== -->
      <n-tab-pane name="questions" tab="笔试题库">
        <!-- 筛选栏 -->
        <n-card :bordered="false" class="filter-card">
          <div class="filter-bar">
            <div class="filter-group">
              <span class="filter-label">
                <n-icon size="14"><FilterOutline /></n-icon>
                岗位类别
              </span>
              <n-select
                v-model:value="filterCategory"
                :options="[
                  { label: '全部', value: '' },
                  ...categories.map((c) => ({ label: `${c} (${categoryCounts[c] || 0})`, value: c })),
                ]"
                placeholder="选择类别"
                clearable
                style="width: 200px"
                @update:value="handleFilterChange"
              />
            </div>

            <div class="filter-group">
              <span class="filter-label">题型</span>
              <n-radio-group v-model:value="filterType" @update:value="handleFilterChange">
                <n-space>
                  <n-radio v-for="opt in typeOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </n-radio>
                </n-space>
              </n-radio-group>
            </div>

            <div class="filter-group">
              <span class="filter-label">难度</span>
              <n-radio-group v-model:value="filterDifficulty" @update:value="handleFilterChange">
                <n-space>
                  <n-radio v-for="opt in difficultyOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </n-radio>
                </n-space>
              </n-radio-group>
            </div>

            <div class="filter-group">
              <span class="filter-label">公司</span>
              <n-select
                v-model:value="filterCompany"
                :options="companyOptions"
                placeholder="全部公司"
                clearable
                filterable
                style="width:200px"
                @update:value="handleFilterChange"
              />
            </div>

            <n-button size="small" @click="handleResetFilter">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              重置
            </n-button>
          </div>
        </n-card>

        <!-- 题目列表 -->
        <div class="questions-section">
          <n-spin :show="questionsLoading">
            <n-empty
              v-if="questions.length === 0"
              description="暂无符合条件的题目"
              style="padding: 60px 0"
            >
              <template #extra>
                <n-button type="primary" @click="handleResetFilter">清除筛选</n-button>
              </template>
            </n-empty>

            <n-collapse v-else accordion :arrow-placement="'right'">
              <n-collapse-item
                v-for="q in questions"
                :key="q.id"
                :name="q.id"
              >
                <template #header>
                  <div class="question-header">
                    <div class="question-meta">
                      <n-tag size="tiny" type="info" :bordered="false" round>
                        {{ q.job_category }}
                      </n-tag>
                      <n-tag v-if="q.question_type" size="tiny" :bordered="false" round>
                        {{ q.question_type }}
                      </n-tag>
                      <n-tag
                        v-if="q.difficulty"
                        size="tiny"
                        :type="difficultyTagType[q.difficulty] || 'default'"
                        :bordered="false"
                        round
                      >
                        {{ difficultyLabel[q.difficulty] || q.difficulty }}
                      </n-tag>
                    </div>
                    <span class="question-text">{{ q.question }}</span>
                  </div>
                </template>

                <div class="answer-section">
                  <div class="answer-label">
                    <n-icon size="14" color="#10b981"><DocumentTextOutline /></n-icon>
                    参考答案
                  </div>
                  <p class="answer-content" v-if="q.answer">{{ q.answer }}</p>
                  <p class="answer-empty" v-else>暂无参考答案</p>
                  <div class="question-source" v-if="q.source">
                    来源：{{ q.source }}
                  </div>
                </div>
              </n-collapse-item>
            </n-collapse>
          </n-spin>

          <!-- 分页 -->
          <div class="pagination-wrapper" v-if="questions.length > 0">
            <n-pagination
              :page="questionPage"
              :item-count="questionTotal"
              :page-size="questionPageSize"
              show-quick-jumper
              @update:page="handlePageChange"
            />
          </div>
        </div>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<style scoped>
.interview-page {
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
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

/* ===== 技巧布局 ===== */
.tips-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.tips-sidebar {
  width: 200px;
  flex-shrink: 0;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #4b5563;
}

.category-item:hover {
  background: #f3f4f6;
}

.category-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 500;
}

.category-item span {
  flex: 1;
}

.tips-content {
  flex: 1;
  min-width: 0;
}

.tip-card {
  border-radius: 12px;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

/* ===== Markdown 渲染 ===== */
.markdown-body {
  line-height: 1.8;
  font-size: 14px;
  color: #374151;
}

:deep(.md-h1) {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 16px 0 12px;
}

:deep(.md-h2) {
  font-size: 17px;
  font-weight: 600;
  color: #1d4ed8;
  margin: 20px 0 10px;
  padding-bottom: 6px;
  border-bottom: 2px solid #eff6ff;
}

:deep(.md-h3) {
  font-size: 15px;
  font-weight: 600;
  color: #34495e;
  margin: 14px 0 8px;
}

:deep(.md-p) {
  margin: 8px 0;
}

:deep(.md-li) {
  margin: 6px 0;
  padding-left: 8px;
  list-style: none;
  position: relative;
}

:deep(.md-li::before) {
  content: "•";
  color: #3b82f6;
  font-weight: bold;
  position: absolute;
  left: -4px;
}

:deep(strong) {
  color: #1f2937;
  font-weight: 600;
}

/* ===== 筛选栏 ===== */
.filter-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  white-space: nowrap;
}

/* ===== 题目列表 ===== */
.questions-section {
  min-height: 300px;
}

.question-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.question-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.question-text {
  font-size: 14px;
  color: #1f2937;
  font-weight: 500;
  line-height: 1.5;
}

.answer-section {
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 3px solid #10b981;
}

.answer-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #10b981;
  margin-bottom: 8px;
}

.answer-content {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
}

.answer-empty {
  font-size: 13px;
  color: #9ca3af;
  margin: 0;
}

.question-source {
  margin-top: 8px;
  font-size: 12px;
  color: #9ca3af;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .tips-layout {
    flex-direction: column;
  }

  .tips-sidebar {
    width: 100%;
  }

  .filter-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

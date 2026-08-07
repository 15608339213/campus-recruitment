<script setup lang="ts">
import { ref, reactive, h, onMounted } from 'vue'
import {
  NCard,
  NButton,
  NTag,
  NSpace,
  NSelect,
  NInput,
  NDataTable,
  NModal,
  NPagination,
  NSpin,
  NIcon,
  NPopconfirm,
  useMessage,
} from 'naive-ui'
import {
  AddOutline,
  CloudUploadOutline,
  CreateOutline,
  TrashOutline,
  SearchOutline,
  FilterOutline,
  HelpCircleOutline,
} from '@vicons/ionicons5'
import {
  getQuestionList,
  deleteQuestion,
  type Question,
} from '@/api/interview'
import QuestionForm from '@/components/QuestionForm.vue'
import QuestionBatchImport from '@/components/QuestionBatchImport.vue'

const message = useMessage()

// ===== 数据状态 =====
const loading = ref(false)
const questions = ref<Question[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

// ===== 筛选参数 =====
const filterParams = reactive({
  keyword: '',
  job_category: null as string | null,
  difficulty: null as string | null,
  company: null as string | null,
})

// ===== 弹窗状态 =====
const showFormModal = ref(false)
const showBatchModal = ref(false)
const editingQuestion = ref<Question | null>(null)

// ===== 选项配置 =====
const jobCategoryOptions = [
  { label: '全部类别', value: null },
  { label: '技术', value: '技术' },
  { label: '产品', value: '产品' },
  { label: '运营', value: '运营' },
  { label: '金融', value: '金融' },
  { label: '设计', value: '设计' },
  { label: '市场', value: '市场' },
  { label: '人事', value: '人事' },
  { label: '财务', value: '财务' },
  { label: '法务', value: '法务' },
]

const difficultyOptions = [
  { label: '全部难度', value: null },
  { label: 'Easy', value: 'easy' },
  { label: 'Medium', value: 'medium' },
  { label: 'Hard', value: 'hard' },
]

// 难度标签样式映射
function getDifficultyTagType(d: string | undefined): 'success' | 'warning' | 'error' | 'default' {
  switch (d) {
    case 'easy': return 'success'
    case 'medium': return 'warning'
    case 'hard': return 'error'
    default: return 'default'
  }
}

function getDifficultyLabel(d: string | undefined): string {
  switch (d) {
    case 'easy': return 'Easy'
    case 'medium': return 'Medium'
    case 'hard': return 'Hard'
    default: return d || '-'
  }
}

// ===== 表格列定义 =====
const columns = [
  {
    title: 'ID',
    key: 'id',
    width: 60,
    sorter: true,
  },
  {
    title: '岗位类别',
    key: 'job_category',
    width: 90,
    render(row: Question) {
      return h(NTag, { size: 'small', type: 'info', bordered: false }, () => row.job_category)
    },
  },
  {
    title: '题目内容',
    key: 'question',
    ellipsis: { tooltip: true },
    width: 280,
  },
  {
    title: '题型',
    key: 'question_type',
    width: 80,
    render(row: Question) {
      return row.question_type || '-'
    },
  },
  {
    title: '难度',
    key: 'difficulty',
    width: 90,
    render(row: Question) {
      return h(
        NTag,
        { size: 'small', type: getDifficultyTagType(row.difficulty), bordered: false, round: true },
        () => getDifficultyLabel(row.difficulty)
      )
    },
  },
  {
    title: '公司',
    key: 'company',
    width: 120,
    ellipsis: { tooltip: true },
    render(row: Question) {
      return row.company || '-'
    },
  },
  {
    title: '来源',
    key: 'source',
    width: 120,
    ellipsis: { tooltip: true },
    render(row: Question) {
      return row.source || '-'
    },
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 150,
    render(row: Question) {
      return row.updated_at ? new Date(row.updated_at).toLocaleString('zh-CN') : '-'
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    fixed: 'right' as const,
    render(row: Question) {
      return h(NSpace, { size: 'small' }, () => [
        h(
          NButton,
          {
            size: 'small',
            quaternary: true,
            onClick: () => handleEdit(row),
          },
          { icon: () => h(NIcon, null, () => h(CreateOutline)) }
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete(row),
          },
          {
            trigger: () =>
              h(
                NButton,
                { size: 'small', quaternary: true, type: 'error' },
                { icon: () => h(NIcon, null, () => h(TrashOutline)) }
              ),
            default: () => '确认删除该题目？',
          }
        ),
      ])
    },
  },
]

// ===== 初始化 =====
onMounted(() => {
  loadQuestions()
})

// ===== 加载题目列表 =====
async function loadQuestions() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (filterParams.job_category) params.job_category = filterParams.job_category
    if (filterParams.difficulty) params.difficulty = filterParams.difficulty
    if (filterParams.company) params.company = filterParams.company

    const res = await getQuestionList(params)
    questions.value = res.items
    total.value = res.total
  } catch (e: any) {
    message.error(e.message || '获取题目列表失败')
  } finally {
    loading.value = false
  }
}

// ===== 搜索 =====
function handleSearch() {
  page.value = 1
  loadQuestions()
}

// ===== 筛选变更 =====
function handleFilterChange() {
  page.value = 1
  loadQuestions()
}

// ===== 分页 =====
function handlePageChange(p: number) {
  page.value = p
  loadQuestions()
}

// ===== 添加题目 =====
function handleAdd() {
  editingQuestion.value = null
  showFormModal.value = true
}

// ===== 编辑题目 =====
function handleEdit(question: Question) {
  editingQuestion.value = question
  showFormModal.value = true
}

// ===== 删除题目 =====
async function handleDelete(question: Question) {
  try {
    await deleteQuestion(question.id)
    message.success('题目已删除')
    // 如果当前页删空了，回退一页
    if (questions.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await loadQuestions()
  } catch (e: any) {
    message.error(e.message || '删除失败')
  }
}

// ===== 表单保存回调 =====
function handleFormSaved() {
  showFormModal.value = false
  loadQuestions()
}

// ===== 批量导入回调 =====
function handleBatchImported() {
  showBatchModal.value = false
  loadQuestions()
}
</script>

<template>
  <div class="question-manager-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <n-icon size="24" color="#2563eb"><HelpCircleOutline /></n-icon>
          题库管理
        </h1>
        <p class="page-desc">管理面试/笔试题库，支持添加、编辑、删除和批量导入题目。</p>
      </div>
      <div class="header-actions">
        <n-space>
          <n-button type="primary" @click="handleAdd">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            添加题目
          </n-button>
          <n-button secondary @click="showBatchModal = true">
            <template #icon><n-icon><CloudUploadOutline /></n-icon></template>
            批量导入
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 筛选区域 -->
    <n-card :bordered="false" class="filter-card">
      <div class="filter-bar">
        <div class="filter-left">
          <n-icon size="18" color="#6b7280"><FilterOutline /></n-icon>
          <n-select
            v-model:value="filterParams.job_category"
            :options="jobCategoryOptions"
            placeholder="岗位类别"
            clearable
            style="width: 140px"
            @update:value="handleFilterChange"
          />
          <n-select
            v-model:value="filterParams.difficulty"
            :options="difficultyOptions"
            placeholder="难度"
            clearable
            style="width: 130px"
            @update:value="handleFilterChange"
          />
          <n-input
            v-model:value="filterParams.company"
            placeholder="公司筛选"
            clearable
            style="width: 160px"
            @keyup.enter="handleSearch"
            @clear="handleFilterChange"
          >
            <template #prefix>
              <n-icon><SearchOutline /></n-icon>
            </template>
          </n-input>
        </div>
        <div class="filter-right">
          <span class="total-count">共 {{ total }} 条题目</span>
        </div>
      </div>
    </n-card>

    <!-- 表格区域 -->
    <n-card :bordered="false" class="table-card">
      <n-spin :show="loading">
        <n-data-table
          :columns="columns"
          :data="questions"
          :single-line="false"
          :bordered="false"
          size="small"
          class="question-table"
        />
        <div v-if="!loading && questions.length === 0 && total === 0" class="empty-wrap">
          <n-space vertical align="center" :size="12">
            <n-icon size="48" color="#d1d5db"><HelpCircleOutline /></n-icon>
            <span style="color: #9ca3af; font-size: 14px">暂无题目数据</span>
            <n-button size="small" secondary @click="handleAdd">添加第一条题目</n-button>
          </n-space>
        </div>
      </n-spin>

      <div v-if="total > pageSize" class="pagination-wrap">
        <n-pagination
          :page="page"
          :page-size="pageSize"
          :item-count="total"
          :page-sizes="[10, 20, 50, 100]"
          show-size-picker
          @update:page="handlePageChange"
          @update:page-size="(s: number) => { pageSize = s; page = 1; loadQuestions() }"
        />
      </div>
    </n-card>

    <!-- 添加/编辑弹窗 -->
    <QuestionForm
      :show="showFormModal"
      :question="editingQuestion"
      @close="showFormModal = false"
      @saved="handleFormSaved"
    />

    <!-- 批量导入弹窗 -->
    <QuestionBatchImport
      :show="showBatchModal"
      @close="showBatchModal = false"
      @imported="handleBatchImported"
    />
  </div>
</template>

<style scoped>
.question-manager-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.header-left {
  flex: 1;
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

.header-actions {
  flex-shrink: 0;
}

.filter-card {
  border-radius: 10px;
  margin-bottom: 12px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-right {
  flex-shrink: 0;
}

.total-count {
  font-size: 13px;
  color: #6b7280;
}

.table-card {
  border-radius: 10px;
}

.question-table {
  min-height: 200px;
}

.empty-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

:deep(.n-data-table-td) {
  font-size: 13px;
}
</style>

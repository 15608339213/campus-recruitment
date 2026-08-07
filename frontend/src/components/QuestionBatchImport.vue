<script setup lang="ts">
import { ref } from 'vue'
import {
  NModal,
  NSpace,
  NButton,
  NTag,
  NAlert,
  NSpin,
  NDataTable,
  NUpload,
  NUploadDragger,
  NText,
  NIcon,
  NScrollbar,
  useMessage,
} from 'naive-ui'
import { CloudUploadOutline, DocumentTextOutline } from '@vicons/ionicons5'
import { batchImportQuestions, type QuestionCreate } from '@/api/interview'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'imported'): void
}>()

const message = useMessage()
const importing = ref(false)
const parsedQuestions = ref<QuestionCreate[]>([])
const parsedFileName = ref('')
const importResult = ref<{ success: number; failed: number; errors?: string[] } | null>(null)

// 有效的字段列表
const validFields = ['job_category', 'question', 'answer', 'question_type', 'difficulty', 'company', 'source']

// 有效的 job_category 值
const validCategories = ['技术', '产品', '运营', '金融', '设计', '市场', '人事', '财务', '法务']

// 有效的 question_type 值
const validTypes = ['笔试', '面试', 'HR面']

// 有效的 difficulty 值
const validDifficulties = ['easy', 'medium', 'hard']

// 验证单条题目
function validateQuestion(item: Record<string, unknown>, index: number): string | null {
  if (!item.job_category) return `第 ${index + 1} 条：缺少 job_category 字段`
  if (!validCategories.includes(item.job_category as string))
    return `第 ${index + 1} 条：job_category 值无效（${item.job_category}），有效值：${validCategories.join('、')}`
  if (!item.question) return `第 ${index + 1} 条：缺少 question 字段`
  if (typeof item.question !== 'string' || !item.question.trim())
    return `第 ${index + 1} 条：question 不能为空`
  if (item.question_type && !validTypes.includes(item.question_type as string))
    return `第 ${index + 1} 条：question_type 值无效（${item.question_type}），有效值：${validTypes.join('、')}`
  if (item.difficulty && !validDifficulties.includes(item.difficulty as string))
    return `第 ${index + 1} 条：difficulty 值无效（${item.difficulty}），有效值：${validDifficulties.join('、')}`
  return null
}

// 处理文件上传
function handleFileChange(options: { file: File; fileList: File[] }) {
  const file = options.file
  parsedFileName.value = file.name
  importResult.value = null

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = e.target?.result as string
      const data = JSON.parse(content)

      if (!Array.isArray(data)) {
        message.error('JSON 文件格式错误：需要提供题目数组')
        parsedQuestions.value = []
        return
      }

      if (data.length === 0) {
        message.warning('JSON 文件中没有题目数据')
        parsedQuestions.value = []
        return
      }

      // 验证每条数据
      const errors: string[] = []
      for (let i = 0; i < data.length; i++) {
        const err = validateQuestion(data[i], i)
        if (err) errors.push(err)
      }

      if (errors.length > 0) {
        message.error(`数据验证失败：共 ${errors.length} 条错误`)
        parsedQuestions.value = []
        return
      }

      // 标准化数据
      parsedQuestions.value = data.map((item: Record<string, unknown>) => ({
        job_category: String(item.job_category),
        question: String(item.question).trim(),
        answer: item.answer ? String(item.answer).trim() : undefined,
        question_type: item.question_type ? String(item.question_type) : undefined,
        difficulty: item.difficulty ? String(item.difficulty) : undefined,
        company: item.company ? String(item.company).trim() : undefined,
        source: item.source ? String(item.source).trim() : undefined,
      }))

      message.success(`成功解析 ${parsedQuestions.value.length} 条题目`)
    } catch (e: any) {
      message.error(`JSON 解析失败：${e.message}`)
      parsedQuestions.value = []
    }
  }
  reader.readAsText(file)
}

// 执行批量导入
async function handleImport() {
  if (parsedQuestions.value.length === 0) {
    message.warning('没有可导入的题目数据')
    return
  }

  importing.value = true
  importResult.value = null
  try {
    const result = await batchImportQuestions(parsedQuestions.value)
    importResult.value = {
      success: result.success_count,
      failed: result.failed_count,
      errors: result.errors,
    }

    if (result.failed_count === 0) {
      message.success(`全部导入成功！共 ${result.success_count} 条题目`)
      parsedQuestions.value = []
      emit('imported')
    } else {
      message.warning(
        `导入完成：${result.success_count} 条成功，${result.failed_count} 条失败`
      )
    }
  } catch (e: any) {
    message.error(e.message || '批量导入失败')
  } finally {
    importing.value = false
  }
}

function handleClose() {
  parsedQuestions.value = []
  importResult.value = null
  parsedFileName.value = ''
  emit('close')
}

// 预览表格列
const previewColumns = [
  { title: '#', key: 'index', width: 50 },
  { title: '类别', key: 'job_category', width: 80, render: (row: QuestionCreate) => row.job_category },
  { title: '题目', key: 'question', ellipsis: { tooltip: true }, width: 200 },
  { title: '题型', key: 'question_type', width: 80 },
  { title: '难度', key: 'difficulty', width: 80 },
  { title: '公司', key: 'company', width: 100, render: (row: QuestionCreate) => row.company || '-' },
]
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    title="批量导入题目"
    style="max-width: 740px"
    :bordered="false"
    @update:show="(v: boolean) => !v && handleClose()"
  >
    <div class="batch-import-content">
      <!-- 上传区域 -->
      <div class="upload-section">
        <n-upload
          :show-file-list="false"
          accept=".json"
          @change="(opts: { file: File; fileList: File[] }) => handleFileChange(opts)"
        >
          <n-upload-dragger>
            <div class="dragger-content">
              <n-icon size="48" color="#2563eb">
                <CloudUploadOutline />
              </n-icon>
              <n-text class="dragger-title">点击或拖拽上传 JSON 文件</n-text>
              <n-text depth="3" class="dragger-desc">
                支持 .json 格式，数组内每条记录包含 job_category、question 等字段
              </n-text>
            </div>
          </n-upload-dragger>
        </n-upload>
      </div>

      <!-- 格式说明 -->
      <n-alert type="info" :bordered="false" class="format-tip">
        <template #header>JSON 格式说明</template>
        <pre class="format-code">[
  {
    "job_category": "技术",      <span class="comment">// 必填：技术/产品/运营/金融/设计/市场/人事/财务/法务</span>
    "question": "题目内容",       <span class="comment">// 必填</span>
    "answer": "答案或解析",       <span class="comment">// 选填</span>
    "question_type": "面试",     <span class="comment">// 选填：笔试/面试/HR面</span>
    "difficulty": "medium",     <span class="comment">// 选填：easy/medium/hard</span>
    "company": "字节跳动",        <span class="comment">// 选填</span>
    "source": "牛客网面经"        <span class="comment">// 选填</span>
  }
]</pre>
      </n-alert>

      <!-- 解析结果预览 -->
      <div v-if="parsedQuestions.length > 0" class="preview-section">
        <div class="preview-header">
          <n-icon size="18" color="#2563eb">
            <DocumentTextOutline />
          </n-icon>
          <span class="preview-title">
            已解析 <strong>{{ parsedQuestions.length }}</strong> 条题目（{{ parsedFileName }}）
          </span>
        </div>
        <n-scrollbar style="max-height: 240px">
          <n-data-table
            :columns="previewColumns"
            :data="parsedQuestions"
            :single-line="false"
            size="small"
            :bordered="false"
          />
        </n-scrollbar>
      </div>

      <!-- 导入结果 -->
      <n-alert
        v-if="importResult"
        :type="importResult.failed === 0 ? 'success' : 'warning'"
        :bordered="false"
      >
        <template #header>
          {{ importResult.failed === 0 ? '导入完成' : '导入部分成功' }}
        </template>
        <div>
          成功 <strong>{{ importResult.success }}</strong> 条，
          失败 <strong>{{ importResult.failed }}</strong> 条
        </div>
        <div v-if="importResult.errors && importResult.errors.length > 0" class="error-list">
          <div v-for="(err, i) in importResult.errors" :key="i" class="error-item">{{ err }}</div>
        </div>
      </n-alert>
    </div>

    <template #footer>
      <n-space justify="end">
        <n-button @click="handleClose">关闭</n-button>
        <n-button
          type="primary"
          :loading="importing"
          :disabled="parsedQuestions.length === 0"
          @click="handleImport"
        >
          开始导入（{{ parsedQuestions.length }} 条）
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<style scoped>
.batch-import-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-section {
  width: 100%;
}

.dragger-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
}

.dragger-title {
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
}

.dragger-desc {
  font-size: 13px;
}

.format-tip {
  font-size: 13px;
}

.format-code {
  background: #f3f4f6;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.7;
  overflow-x: auto;
  margin: 8px 0 0;
  color: #1f2937;
}

.format-code .comment {
  color: #9ca3af;
}

.preview-section {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  color: #374151;
}

.preview-title strong {
  color: #2563eb;
}

.error-list {
  margin-top: 8px;
  font-size: 12px;
  color: #dc2626;
}

.error-item {
  margin-top: 2px;
}

:deep(.n-upload-dragger) {
  border-style: dashed;
}
</style>

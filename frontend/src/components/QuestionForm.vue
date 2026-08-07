<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import {
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NButton,
  NSpace,
  NSpin,
  useMessage,
} from 'naive-ui'
import {
  createQuestion,
  updateQuestion,
  type Question,
  type QuestionCreate,
} from '@/api/interview'

const props = defineProps<{
  show: boolean
  question: Question | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const message = useMessage()
const submitting = ref(false)

const formData = reactive<QuestionCreate>({
  job_category: '技术',
  question: '',
  answer: '',
  question_type: '面试',
  difficulty: 'medium',
  company: '',
  source: '',
})

const isEdit = ref(false)

// 岗位类别选项
const jobCategoryOptions = [
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

// 题目类型选项
const questionTypeOptions = [
  { label: '笔试', value: '笔试' },
  { label: '面试', value: '面试' },
  { label: 'HR面', value: 'HR面' },
]

// 难度选项
const difficultyOptions = [
  { label: 'Easy', value: 'easy' },
  { label: 'Medium', value: 'medium' },
  { label: 'Hard', value: 'hard' },
]

// 监听 show 和 question 变化，初始化表单
watch(
  () => [props.show, props.question],
  ([showVal, questionVal]) => {
    if (!showVal) return
    if (questionVal) {
      isEdit.value = true
      formData.job_category = questionVal.job_category || '技术'
      formData.question = questionVal.question || ''
      formData.answer = questionVal.answer || ''
      formData.question_type = questionVal.question_type || '面试'
      formData.difficulty = questionVal.difficulty || 'medium'
      formData.company = questionVal.company || ''
      formData.source = questionVal.source || ''
    } else {
      isEdit.value = false
      formData.job_category = '技术'
      formData.question = ''
      formData.answer = ''
      formData.question_type = '面试'
      formData.difficulty = 'medium'
      formData.company = ''
      formData.source = ''
    }
  },
  { immediate: true }
)

// 表单验证
function validateForm(): string | null {
  if (!formData.job_category) return '请选择岗位类别'
  if (!formData.question.trim()) return '请输入题目内容'
  if (!formData.question_type) return '请选择题型'
  if (!formData.difficulty) return '请选择难度'
  return null
}

// 提交表单
async function handleSubmit() {
  const error = validateForm()
  if (error) {
    message.warning(error)
    return
  }

  submitting.value = true
  try {
    const data: QuestionCreate = {
      job_category: formData.job_category,
      question: formData.question.trim(),
      answer: formData.answer.trim() || undefined,
      question_type: formData.question_type,
      difficulty: formData.difficulty,
      company: formData.company.trim() || undefined,
      source: formData.source.trim() || undefined,
    }

    if (isEdit.value && props.question) {
      await updateQuestion(props.question.id, data)
      message.success('题目已更新')
    } else {
      await createQuestion(data)
      message.success('题目已添加')
    }
    emit('saved')
  } catch (e: any) {
    message.error(e.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

function handleClose() {
  emit('close')
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    :title="isEdit ? '编辑题目' : '添加题目'"
    style="max-width: 640px"
    :bordered="false"
    @update:show="(v: boolean) => !v && handleClose()"
  >
    <n-spin :show="submitting">
      <n-form label-placement="top" size="medium">
        <n-form-item label="岗位类别" required>
          <n-select
            v-model:value="formData.job_category"
            :options="jobCategoryOptions"
            placeholder="选择岗位类别"
          />
        </n-form-item>

        <n-form-item label="题目内容" required>
          <n-input
            v-model:value="formData.question"
            type="textarea"
            placeholder="请输入题目内容"
            :autosize="{ minRows: 3, maxRows: 8 }"
          />
        </n-form-item>

        <n-form-item label="答案 / 解析">
          <n-input
            v-model:value="formData.answer"
            type="textarea"
            placeholder="请输入答案或解析（选填）"
            :autosize="{ minRows: 3, maxRows: 12 }"
          />
        </n-form-item>

        <n-form-item label="题型" required>
          <n-select
            v-model:value="formData.question_type"
            :options="questionTypeOptions"
            placeholder="选择题型"
          />
        </n-form-item>

        <n-form-item label="难度" required>
          <n-select
            v-model:value="formData.difficulty"
            :options="difficultyOptions"
            placeholder="选择难度"
          />
        </n-form-item>

        <n-form-item label="关联公司">
          <n-input v-model:value="formData.company" placeholder="如：字节跳动（选填）" />
        </n-form-item>

        <n-form-item label="来源">
          <n-input v-model:value="formData.source" placeholder="如：牛客网面经（选填）" />
        </n-form-item>
      </n-form>
    </n-spin>

    <template #footer>
      <n-space justify="end">
        <n-button @click="handleClose">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '添加题目' }}
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<style scoped>
:deep(.n-form-item-blank) {
  width: 100%;
}
</style>

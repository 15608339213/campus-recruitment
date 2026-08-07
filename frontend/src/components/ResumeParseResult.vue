<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NCard, NButton, NTag, NSpace, NIcon, NInput, NForm, NFormItem,
  NSelect, NModal, NSpin, NEmpty, useMessage,
} from 'naive-ui'
import {
  CheckmarkCircleOutline, CloseOutline, CreateOutline,
} from '@vicons/ionicons5'

const props = defineProps<{
  parsedData: {
    name: string
    phone: string
    email: string
    city: string
    school: string
    major: string
    degree: string
    graduation_year: string
    skills: string[]
    experience: Array<Record<string, any>>
    projects: Array<Record<string, any>>
    languages: string[]
    certificates: string[]
  } | null
  loading: boolean
}>()

const emit = defineEmits<{
  confirm: [data: Record<string, any>]
  retry: []
  cancel: []
}>()

const message = useMessage()

const fields = computed(() => {
  if (!props.parsedData) return []
  return [
    { key: 'name', label: '姓名', value: props.parsedData.name },
    { key: 'phone', label: '手机', value: props.parsedData.phone },
    { key: 'email', label: '邮箱', value: props.parsedData.email },
    { key: 'city', label: '城市', value: props.parsedData.city },
    { key: 'school', label: '学校', value: props.parsedData.school },
    { key: 'major', label: '专业', value: props.parsedData.major },
    { key: 'degree', label: '学历', value: props.parsedData.degree },
    { key: 'graduation_year', label: '毕业年份', value: props.parsedData.graduation_year },
  ]
})

function handleConfirm() {
  if (!props.parsedData) return
  emit('confirm', {
    school: props.parsedData.school,
    major: props.parsedData.major,
    degree: props.parsedData.degree,
    graduation_year: props.parsedData.graduation_year,
    phone: props.parsedData.phone,
    skills: (props.parsedData.skills || []).join(', '),
    experience_json: props.parsedData.experience || [],
    projects_json: props.parsedData.projects || [],
  })
}
</script>

<template>
  <div class="parse-result">
    <!-- 加载中 -->
    <div v-if="loading" class="parse-loading">
      <n-spin size="medium" />
      <p>AI 正在分析简历，请稍候...</p>
    </div>

    <!-- 解析结果 -->
    <template v-else-if="parsedData">
      <n-card :bordered="false" class="result-card">
        <template #header>
          <div class="result-header">
            <n-icon size="20" color="#10b981"><CheckmarkCircleOutline /></n-icon>
            <span>AI 识别结果 - 请确认信息</span>
          </div>
        </template>

        <!-- 基本信息 -->
        <div class="field-group">
          <h4 class="group-title">基本信息</h4>
          <div class="field-grid">
            <div v-for="f in fields" :key="f.key" class="field-item">
              <span class="field-label">{{ f.label }}</span>
              <span class="field-value" :class="{ 'field-empty': !f.value }">
                {{ f.value || '未识别' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 技能 -->
        <div class="field-group" v-if="parsedData.skills?.length">
          <h4 class="group-title">技能标签</h4>
          <div class="skills-row">
            <n-tag v-for="(skill, i) in parsedData.skills" :key="i" type="info" size="small" round :bordered="false">
              {{ skill }}
            </n-tag>
          </div>
        </div>

        <!-- 工作经历 -->
        <div class="field-group" v-if="parsedData.experience?.length">
          <h4 class="group-title">工作/实习经历</h4>
          <div v-for="(exp, i) in parsedData.experience" :key="i" class="exp-item">
            <div class="exp-header">
              <strong>{{ exp.company || '未知公司' }}</strong>
              <span class="exp-date">{{ exp.start_date }} - {{ exp.end_date }}</span>
            </div>
            <p class="exp-pos">{{ exp.position }}</p>
            <p class="exp-desc">{{ exp.description }}</p>
          </div>
        </div>

        <!-- 项目经历 -->
        <div class="field-group" v-if="parsedData.projects?.length">
          <h4 class="group-title">项目经历</h4>
          <div v-for="(proj, i) in parsedData.projects" :key="i" class="exp-item">
            <div class="exp-header">
              <strong>{{ proj.name || '未知项目' }}</strong>
              <span>{{ proj.role }}</span>
            </div>
            <p class="exp-desc">{{ proj.description }}</p>
            <n-tag v-if="proj.tech_stack" size="tiny" :bordered="false">{{ proj.tech_stack }}</n-tag>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="parse-actions">
          <n-button @click="emit('cancel')">取消</n-button>
          <n-button @click="emit('retry')" quaternary>
            <template #icon><n-icon><CreateOutline /></n-icon></template>
            重新解析
          </n-button>
          <n-button type="primary" @click="handleConfirm">
            <template #icon><n-icon><CheckmarkCircleOutline /></n-icon></template>
            确认并填充表单
          </n-button>
        </div>
      </n-card>
    </template>

    <!-- 无数据 -->
    <n-empty v-else description="请先上传简历文件" />
  </div>
</template>

<style scoped>
.parse-result {
  margin-top: 16px;
}
.parse-loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}
.result-card {
  border-radius: 12px;
}
.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.field-group {
  margin-bottom: 20px;
}
.group-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f3f4f6;
}
.field-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}
.field-item {
  display: flex;
  flex-direction: column;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 6px;
}
.field-label {
  font-size: 11px;
  color: #9ca3af;
}
.field-value {
  font-size: 13px;
  color: #374151;
}
.field-empty {
  color: #d1d5db;
  font-style: italic;
}
.skills-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.exp-item {
  padding: 8px 10px;
  background: #f9fafb;
  border-radius: 6px;
  margin-bottom: 8px;
}
.exp-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 2px;
}
.exp-date {
  color: #9ca3af;
  font-size: 12px;
}
.exp-pos {
  font-size: 12px;
  color: #6b7280;
  margin: 2px 0;
}
.exp-desc {
  font-size: 12px;
  color: #6b7280;
  margin: 2px 0;
  line-height: 1.5;
}
.parse-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}
</style>

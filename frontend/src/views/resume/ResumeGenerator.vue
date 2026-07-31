<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NCard,
  NButton,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NTag,
  NSpace,
  NIcon,
  NSteps,
  NStep,
  NSpin,
  NEmpty,
  NDivider,
  NDynamicTags,
  NDynamicInput,
  useMessage,
} from 'naive-ui'
import {
  DocumentTextOutline,
  DownloadOutline,
  SparklesOutline,
  AddCircleOutline,
  TrashOutline,
  RefreshOutline,
  PersonOutline,
} from '@vicons/ionicons5'
import type { ResumeContent, ProjectItem, Resume } from '@/types'
import { generateResume, downloadResumePdf, getResumeList } from '@/api/resume'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const currentStep = ref(1)
const generating = ref(false)
const generatedResume = ref<Resume | null>(null)
const resumeList = ref<Resume[]>([])

// 目标岗位
const targetJobId = ref<number | null>(null)
const targetJobTitle = ref('')

// 简历内容
const resumeContent = reactive<ResumeContent>({
  basic_info: {
    name: '',
    phone: '',
    email: '',
    location: '',
  },
  education: [
    {
      school: '',
      major: '',
      degree: '本科',
      graduation_year: '',
    },
  ],
  experience: [
    {
      company: '',
      position: '',
      start_date: '',
      end_date: '',
      description: '',
    },
  ],
  projects: [
    {
      name: '',
      role: '',
      description: '',
      url: '',
    },
  ],
  skills: [],
  self_evaluation: '',
})

// 个人经历文本（用于AI生成）
const personalExperience = ref('')

const degreeOptions = [
  { label: '大专', value: '大专' },
  { label: '本科', value: '本科' },
  { label: '硕士', value: '硕士' },
  { label: '博士', value: '博士' },
]

// 是否有简历生成结果
const hasResult = computed(() => !!generatedResume.value)

onMounted(async () => {
  // 从路由参数获取目标岗位
  if (route.query.job_id) {
    targetJobId.value = Number(route.query.job_id)
  }
  // 获取简历列表
  try {
    const res = await getResumeList({ page: 1, page_size: 5 })
    resumeList.value = res.items
  } catch {
    // ignore
  }
})

function nextStep() {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

async function handleGenerate() {
  if (!targetJobTitle.value && !targetJobId.value) {
    message.warning('请填写目标岗位')
    return
  }

  generating.value = true
  try {
    const res = await generateResume({
      target_job_id: targetJobId.value || undefined,
      target_job_title: targetJobTitle.value,
      personal_experience: personalExperience.value,
      skills: resumeContent.skills,
      projects: resumeContent.projects.filter((p) => p.name),
    })
    generatedResume.value = res
    currentStep.value = 3
    message.success('简历生成成功！')
  } catch (error: any) {
    message.error(error.message || '简历生成失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

async function handleDownload() {
  if (!generatedResume.value) return
  try {
    const res = await downloadResumePdf(generatedResume.value.id)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `简历_${generatedResume.value.target_job_title || '秋招'}.pdf`
    link.click()
    window.URL.revokeObjectURL(url)
    message.success('下载成功')
  } catch (error: any) {
    message.error('下载失败，请稍后重试')
  }
}

function handleRegenerate() {
  generatedResume.value = null
  currentStep.value = 2
}

function onCreateEducation() {
  return {
    school: '',
    major: '',
    degree: '本科',
    graduation_year: '',
  }
}

function onCreateExperience() {
  return {
    company: '',
    position: '',
    start_date: '',
    end_date: '',
    description: '',
  }
}

function onCreateProject() {
  return {
    name: '',
    role: '',
    description: '',
    url: '',
  }
}
</script>

<template>
  <div class="resume-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <n-icon size="24" color="#2563eb"><DocumentTextOutline /></n-icon>
        AI 简历生成
      </h1>
      <p class="page-desc">输入个人信息和经历，AI 帮你生成岗位定制简历</p>
    </div>

    <!-- 步骤指示器 -->
    <n-card :bordered="false" class="steps-card">
      <n-steps :current="currentStep" size="small">
        <n-step title="填写基本信息" description="个人资料和教育背景" />
        <n-step title="补充经历" description="工作经历、项目和技能" />
        <n-step title="生成简历" description="AI 定制生成并预览下载" />
      </n-steps>
    </n-card>

    <!-- 步骤1: 基本信息 -->
    <n-card v-if="currentStep === 1" title="基本信息" :bordered="false" class="content-card">
      <n-form label-placement="top" size="medium">
        <div class="form-grid">
          <n-form-item label="姓名">
            <n-input v-model:value="resumeContent.basic_info.name" placeholder="请输入姓名" />
          </n-form-item>
          <n-form-item label="手机号">
            <n-input v-model:value="resumeContent.basic_info.phone" placeholder="请输入手机号" />
          </n-form-item>
          <n-form-item label="邮箱">
            <n-input v-model:value="resumeContent.basic_info.email" placeholder="请输入邮箱" />
          </n-form-item>
          <n-form-item label="所在城市">
            <n-input v-model:value="resumeContent.basic_info.location" placeholder="请输入所在城市" />
          </n-form-item>
        </div>

        <n-divider>教育背景</n-divider>

        <n-dynamic-input
          v-model:value="resumeContent.education"
          :on-create="onCreateEducation"
          :min="1"
        >
          <template #default="{ value }">
            <div class="dynamic-form-grid">
              <n-input v-model:value="value.school" placeholder="学校名称" />
              <n-input v-model:value="value.major" placeholder="专业" />
              <n-select v-model:value="value.degree" :options="degreeOptions" placeholder="学历" />
              <n-input v-model:value="value.graduation_year" placeholder="毕业年份" />
            </div>
          </template>
        </n-dynamic-input>

        <div class="step-actions">
          <n-button type="primary" size="large" @click="nextStep">
            下一步
          </n-button>
        </div>
      </n-form>
    </n-card>

    <!-- 步骤2: 经历和技能 -->
    <n-card v-else-if="currentStep === 2" title="工作经历与技能" :bordered="false" class="content-card">
      <n-form label-placement="top" size="medium">
        <!-- 目标岗位 -->
        <n-form-item label="目标岗位">
          <n-input
            v-model:value="targetJobTitle"
            placeholder="请输入目标岗位名称（如：前端开发工程师）"
          />
        </n-form-item>

        <n-divider>工作/实习经历</n-divider>
        <n-dynamic-input
          v-model:value="resumeContent.experience"
          :on-create="onCreateExperience"
          :min="1"
        >
          <template #default="{ value }">
            <div class="experience-form">
              <div class="dynamic-form-grid">
                <n-input v-model:value="value.company" placeholder="公司名称" />
                <n-input v-model:value="value.position" placeholder="职位" />
                <n-input v-model:value="value.start_date" placeholder="开始时间 (2024-01)" />
                <n-input v-model:value="value.end_date" placeholder="结束时间 (2024-06)" />
              </div>
              <n-input
                v-model:value="value.description"
                type="textarea"
                placeholder="工作描述和成就（建议用要点形式）"
                :rows="3"
              />
            </div>
          </template>
        </n-dynamic-input>

        <n-divider>项目经历</n-divider>
        <n-dynamic-input
          v-model:value="resumeContent.projects"
          :on-create="onCreateProject"
          :min="1"
        >
          <template #default="{ value }">
            <div class="experience-form">
              <div class="dynamic-form-grid">
                <n-input v-model:value="value.name" placeholder="项目名称" />
                <n-input v-model:value="value.role" placeholder="担任角色" />
                <n-input v-model:value="value.url" placeholder="项目链接（选填）" />
              </div>
              <n-input
                v-model:value="value.description"
                type="textarea"
                placeholder="项目描述、技术栈和个人贡献"
                :rows="3"
              />
            </div>
          </template>
        </n-dynamic-input>

        <n-divider>技能标签</n-divider>
        <n-form-item label="掌握的技能（输入后回车添加）">
          <n-dynamic-tags v-model:value="resumeContent.skills" :max="20" />
        </n-form-item>

        <n-divider>个人评价（选填）</n-divider>
        <n-form-item label="个人经历概述（帮助AI更好地理解你）">
          <n-input
            v-model:value="personalExperience"
            type="textarea"
            placeholder="简要描述你的求职意向、核心优势和职业规划..."
            :rows="4"
          />
        </n-form-item>

        <div class="step-actions">
          <n-button size="large" @click="prevStep">上一步</n-button>
          <n-button
            type="primary"
            size="large"
            :loading="generating"
            @click="handleGenerate"
          >
            <template #icon>
              <n-icon><SparklesOutline /></n-icon>
            </template>
            AI 生成简历
          </n-button>
        </div>
      </n-form>
    </n-card>

    <!-- 步骤3: 生成结果 -->
    <div v-else-if="currentStep === 3" class="result-section">
      <!-- 生成中 -->
      <div v-if="generating" class="generating-wrapper">
        <n-spin size="large" />
        <p class="generating-text">AI 正在为你生成定制简历，请稍候...</p>
      </div>

      <!-- 生成结果 -->
      <template v-else-if="generatedResume">
        <n-card :bordered="false" class="resume-preview-card">
          <template #header>
            <div class="preview-header">
              <n-icon size="20" color="#2563eb"><DocumentTextOutline /></n-icon>
              <span>简历预览</span>
              <n-tag type="warning" size="small" round :bordered="false">AI 生成 · 请人工校对</n-tag>
            </div>
          </template>
          <template #header-extra>
            <n-space>
              <n-button @click="handleRegenerate">
                <template #icon>
                  <n-icon><RefreshOutline /></n-icon>
                </template>
                重新生成
              </n-button>
              <n-button type="primary" @click="handleDownload">
                <template #icon>
                  <n-icon><DownloadOutline /></n-icon>
                </template>
                下载 PDF
              </n-button>
            </n-space>
          </template>

          <div class="resume-preview">
            <!-- 基本信息 -->
            <div class="resume-section">
              <h2 class="resume-name">{{ generatedResume.customized_content.basic_info.name || '姓名' }}</h2>
              <div class="resume-contact">
                <span v-if="generatedResume.customized_content.basic_info.phone">
                  {{ generatedResume.customized_content.basic_info.phone }}
                </span>
                <span v-if="generatedResume.customized_content.basic_info.email">
                  | {{ generatedResume.customized_content.basic_info.email }}
                </span>
                <span v-if="generatedResume.customized_content.basic_info.location">
                  | {{ generatedResume.customized_content.basic_info.location }}
                </span>
              </div>
            </div>

            <!-- 教育背景 -->
            <div class="resume-section" v-if="generatedResume.customized_content.education?.length">
              <h3 class="resume-section-title">教育背景</h3>
              <div
                v-for="(edu, i) in generatedResume.customized_content.education"
                :key="i"
                class="resume-edu-item"
              >
                <div class="edu-header">
                  <span class="edu-school">{{ edu.school }}</span>
                  <span class="edu-year">{{ edu.graduation_year }}</span>
                </div>
                <p class="edu-detail">{{ edu.major }} · {{ edu.degree }}</p>
              </div>
            </div>

            <!-- 工作经历 -->
            <div class="resume-section" v-if="generatedResume.customized_content.experience?.length">
              <h3 class="resume-section-title">工作/实习经历</h3>
              <div
                v-for="(exp, i) in generatedResume.customized_content.experience"
                :key="i"
                class="resume-exp-item"
              >
                <div class="exp-header">
                  <span class="exp-company">{{ exp.company }}</span>
                  <span class="exp-date">{{ exp.start_date }} - {{ exp.end_date }}</span>
                </div>
                <p class="exp-position">{{ exp.position }}</p>
                <p class="exp-desc">{{ exp.description }}</p>
              </div>
            </div>

            <!-- 项目经历 -->
            <div class="resume-section" v-if="generatedResume.customized_content.projects?.length">
              <h3 class="resume-section-title">项目经历</h3>
              <div
                v-for="(proj, i) in generatedResume.customized_content.projects"
                :key="i"
                class="resume-proj-item"
              >
                <div class="proj-header">
                  <span class="proj-name">{{ proj.name }}</span>
                  <span class="proj-role">{{ proj.role }}</span>
                </div>
                <p class="proj-desc">{{ proj.description }}</p>
              </div>
            </div>

            <!-- 技能 -->
            <div class="resume-section" v-if="generatedResume.customized_content.skills?.length">
              <h3 class="resume-section-title">专业技能</h3>
              <div class="resume-skills">
                <n-tag
                  v-for="skill in generatedResume.customized_content.skills"
                  :key="skill"
                  type="info"
                  size="small"
                  round
                  :bordered="false"
                >
                  {{ skill }}
                </n-tag>
              </div>
            </div>

            <!-- 自我评价 -->
            <div class="resume-section" v-if="generatedResume.customized_content.self_evaluation">
              <h3 class="resume-section-title">自我评价</h3>
              <p class="resume-evaluation">{{ generatedResume.customized_content.self_evaluation }}</p>
            </div>
          </div>
        </n-card>
      </template>

      <div class="step-actions" v-if="!generating">
        <n-button size="large" @click="prevStep">返回修改</n-button>
      </div>
    </div>

    <!-- 历史简历 -->
    <n-card v-if="resumeList.length > 0 && currentStep === 1" title="历史简历" :bordered="false" class="history-card">
      <div class="history-list">
        <div
          v-for="item in resumeList"
          :key="item.id"
          class="history-item"
          @click="router.push(`/resume/generate`)"
        >
          <div class="history-info">
            <p class="history-title">{{ item.target_job_title || '未命名简历' }}</p>
            <p class="history-date">{{ item.created_at }}</p>
          </div>
          <n-button text type="primary" size="small">查看</n-button>
        </div>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
.resume-page {
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

.steps-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.content-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0 16px;
}

.dynamic-form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  width: 100%;
  margin-bottom: 8px;
}

.experience-form {
  width: 100%;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.generating-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.generating-text {
  margin-top: 16px;
  color: #6b7280;
  font-size: 14px;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.resume-preview-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.resume-preview {
  max-width: 700px;
  margin: 0 auto;
  padding: 16px 0;
}

.resume-section {
  margin-bottom: 24px;
}

.resume-name {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  text-align: center;
  margin: 0 0 8px;
}

.resume-contact {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.resume-contact span {
  margin: 0 4px;
}

.resume-section-title {
  font-size: 16px;
  font-weight: 600;
  color: #2563eb;
  border-bottom: 2px solid #eff6ff;
  padding-bottom: 6px;
  margin: 0 0 12px;
}

.resume-edu-item,
.resume-exp-item,
.resume-proj-item {
  margin-bottom: 12px;
}

.edu-header,
.exp-header,
.proj-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.edu-school,
.exp-company,
.proj-name {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}

.edu-year,
.exp-date,
.proj-role {
  font-size: 12px;
  color: #9ca3af;
}

.edu-detail,
.exp-position {
  font-size: 13px;
  color: #4b5563;
  margin: 2px 0;
}

.exp-desc,
.proj-desc {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  margin: 4px 0 0;
}

.resume-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.resume-evaluation {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.8;
  margin: 0;
}

.history-card {
  border-radius: 12px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.history-item:hover {
  background: #eff6ff;
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin: 0 0 4px;
}

.history-date {
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .dynamic-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>

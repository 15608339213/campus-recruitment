<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NTag,
  NSpace,
  NIcon,
  NAvatar,
  NDynamicTags,
  NDynamicInput,
  NDivider,
  NAlert,
  NTabs,
  NTabPane,
  useMessage,
} from 'naive-ui'
import {
  PersonCircleOutline,
  SchoolOutline,
  CodeSlashOutline,
  BriefcaseOutline,
  CheckmarkCircleOutline,
  MailOutline,
} from '@vicons/ionicons5'
import { sendEduVerifyCode, verifyEduEmail, updateProfile } from '@/api/auth'
import type { ExperienceItem, ProjectItem } from '@/types'

const authStore = useAuthStore()
const message = useMessage()

const activeTab = ref('info')
const saving = ref(false)

// 个人信息
const profileForm = reactive({
  nickname: authStore.user?.nickname || '',
  phone: '',
  bio: '',
  school: '',
  major: '',
  graduation_year: '',
})

// 教育邮箱验证
const eduEmail = ref('')
const verifyCode = ref('')
const verifySending = ref(false)
const verifying = ref(false)
const eduVerified = ref(false)

// 技能
const skills = ref<string[]>([])

// 经历
const experiences = ref<ExperienceItem[]>([
  { company: '', position: '', start_date: '', end_date: '', description: '' },
])

// 项目
const projects = ref<ProjectItem[]>([
  { name: '', role: '', description: '', url: '' },
])

onMounted(() => {
  // 模拟已有数据
  if (authStore.profile) {
    skills.value = authStore.profile.skills || []
    // 后端返回 experience_json / projects_json，映射到本地字段
    experiences.value = authStore.profile.experience_json || authStore.profile.experience || experiences.value
    projects.value = authStore.profile.projects_json || authStore.profile.projects || projects.value
    eduVerified.value = authStore.profile.edu_verified || false
    eduEmail.value = authStore.profile.edu_email || ''
  }
  if (authStore.user?.profile) {
    skills.value = authStore.user.profile.skills || skills.value
    experiences.value = authStore.user.profile.experience_json || experiences.value
    projects.value = authStore.user.profile.projects_json || projects.value
    eduVerified.value = authStore.user.profile.edu_verified || eduVerified.value
    eduEmail.value = authStore.user.profile.edu_email || eduEmail.value
    profileForm.phone = authStore.user.profile.phone || ''
    profileForm.bio = authStore.user.profile.bio || ''
    profileForm.school = authStore.user.profile.school || ''
    profileForm.major = authStore.user.profile.major || ''
    profileForm.graduation_year = authStore.user.profile.graduation_year?.toString() || ''
  }
})

async function handleSendVerifyCode() {
  if (!eduEmail.value) {
    message.warning('请先输入教育邮箱')
    return
  }
  const eduRegex = /^[^\s@]+@[^\s@]+\.edu\.cn$/
  if (!eduRegex.test(eduEmail.value)) {
    message.error('教育邮箱需以 .edu.cn 结尾')
    return
  }

  verifySending.value = true
  try {
    await sendEduVerifyCode({ edu_email: eduEmail.value })
    message.success('验证码已发送至您的教育邮箱')
  } catch (error: any) {
    message.error(error.message || '发送验证码失败')
  } finally {
    verifySending.value = false
  }
}

async function handleVerifyEdu() {
  if (!eduEmail.value || !verifyCode.value) {
    message.warning('请输入邮箱和验证码')
    return
  }

  verifying.value = true
  try {
    const res = await verifyEduEmail({ edu_email: eduEmail.value, code: verifyCode.value })
    if (res.verified) {
      eduVerified.value = true
      message.success('教育邮箱验证成功！')
    } else {
      message.error('验证码错误或已过期')
    }
  } catch (error: any) {
    message.error(error.message || '验证失败')
  } finally {
    verifying.value = false
  }
}

function onCreateExperience() {
  return { company: '', position: '', start_date: '', end_date: '', description: '' }
}

function onCreateProject() {
  return { name: '', role: '', description: '', url: '' }
}

async function handleSave() {
  saving.value = true
  try {
    await updateProfile({
      phone: profileForm.phone,
      bio: profileForm.bio,
      school: profileForm.school,
      major: profileForm.major,
      graduation_year: Number(profileForm.graduation_year) || undefined,
      skills: skills.value,
      experience_json: experiences.value.filter((e) => e.company),
      projects_json: projects.value.filter((p) => p.name),
    } as any)
    message.success('保存成功')
    // 刷新用户信息
    await authStore.fetchCurrentUser()
  } catch (error: any) {
    message.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <!-- 页面头部 -->
    <n-card :bordered="false" class="profile-header-card">
      <div class="profile-header">
        <n-avatar
          round
          :size="72"
          :src="authStore.user?.avatar_url"
          style="background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%)"
        >
          {{ authStore.nickname.charAt(0).toUpperCase() }}
        </n-avatar>
        <div class="header-info">
          <h2 class="profile-name">{{ authStore.nickname }}</h2>
          <p class="profile-email">{{ authStore.user?.email }}</p>
          <n-space>
            <n-tag type="info" size="small" round :bordered="false">
              {{ authStore.userRole === 'admin' ? '管理员' : authStore.isVerifiedStudent ? '认证学生' : '普通用户' }}
            </n-tag>
            <n-tag v-if="eduVerified" type="success" size="small" round :bordered="false">
              <template #icon>
                <n-icon><CheckmarkCircleOutline /></n-icon>
              </template>
              教育邮箱已验证
            </n-tag>
          </n-space>
        </div>
      </div>
    </n-card>

    <!-- 标签页 -->
    <n-card :bordered="false" class="profile-content-card">
      <n-tabs v-model:value="activeTab" type="line" animated>
        <!-- 个人信息 -->
        <n-tab-pane name="info" tab="个人信息">
          <n-form label-placement="top" size="medium" style="max-width: 600px; margin-top: 16px">
            <div class="form-grid">
              <n-form-item label="昵称">
                <n-input v-model:value="profileForm.nickname" placeholder="请输入昵称" />
              </n-form-item>
              <n-form-item label="手机号">
                <n-input v-model:value="profileForm.phone" placeholder="请输入手机号" />
              </n-form-item>
              <n-form-item label="学校">
                <n-input v-model:value="profileForm.school" placeholder="请输入学校名称" />
              </n-form-item>
              <n-form-item label="专业">
                <n-input v-model:value="profileForm.major" placeholder="请输入专业" />
              </n-form-item>
              <n-form-item label="毕业年份">
                <n-input v-model:value="profileForm.graduation_year" placeholder="如 2027" />
              </n-form-item>
            </div>
            <n-form-item label="个人简介">
              <n-input
                v-model:value="profileForm.bio"
                type="textarea"
                placeholder="简单介绍一下自己..."
                :rows="3"
              />
            </n-form-item>
            <n-button type="primary" :loading="saving" @click="handleSave">保存修改</n-button>
          </n-form>
        </n-tab-pane>

        <!-- 教育邮箱验证 -->
        <n-tab-pane name="edu" tab="教育邮箱">
          <div style="max-width: 600px; margin-top: 16px">
            <n-alert v-if="eduVerified" type="success" style="margin-bottom: 16px" :bordered="false">
              <template #icon>
                <n-icon><CheckmarkCircleOutline /></n-icon>
              </template>
              您的教育邮箱 {{ eduEmail }} 已验证通过，可享受认证学生专属功能。
            </n-alert>
            <n-alert v-else type="info" style="margin-bottom: 16px" :bordered="false">
              <template #icon>
                <n-icon><SchoolOutline /></n-icon>
              </template>
              验证教育邮箱（.edu.cn）可升级为认证学生，享受更多专属功能。
            </n-alert>

            <n-form label-placement="top" size="medium">
              <n-form-item label="教育邮箱">
                <n-input v-model:value="eduEmail" placeholder="请输入 .edu.cn 教育邮箱" :disabled="eduVerified">
                  <template #prefix>
                    <n-icon :component="MailOutline" />
                  </template>
                </n-input>
              </n-form-item>

              <template v-if="!eduVerified">
                <n-form-item label="验证码">
                  <n-space style="width: 100%">
                    <n-input v-model:value="verifyCode" placeholder="请输入验证码" style="flex: 1" />
                    <n-button :loading="verifySending" @click="handleSendVerifyCode">
                      发送验证码
                    </n-button>
                  </n-space>
                </n-form-item>

                <n-button type="primary" :loading="verifying" @click="handleVerifyEdu">
                  验证邮箱
                </n-button>
              </template>
            </n-form>
          </div>
        </n-tab-pane>

        <!-- 技能管理 -->
        <n-tab-pane name="skills" tab="技能管理">
          <div style="max-width: 600px; margin-top: 16px">
            <p class="section-desc">添加你掌握的技能，帮助 AI 生成更精准的简历</p>
            <n-form-item label="技能标签（输入后回车添加）">
              <n-dynamic-tags v-model:value="skills" :max="30" />
            </n-form-item>
            <n-button type="primary" :loading="saving" @click="handleSave">保存技能</n-button>
          </div>
        </n-tab-pane>

        <!-- 经历管理 -->
        <n-tab-pane name="experience" tab="经历管理">
          <div style="margin-top: 16px">
            <div class="section-header">
              <h3 class="section-title">
                <n-icon size="18" color="#2563eb"><BriefcaseOutline /></n-icon>
                工作/实习经历
              </h3>
            </div>
            <n-dynamic-input
              v-model:value="experiences"
              :on-create="onCreateExperience"
              :min="0"
            >
              <template #default="{ value }">
                <div class="dynamic-form">
                  <div class="form-grid-2">
                    <n-input v-model:value="value.company" placeholder="公司名称" />
                    <n-input v-model:value="value.position" placeholder="职位" />
                    <n-input v-model:value="value.start_date" placeholder="开始时间" />
                    <n-input v-model:value="value.end_date" placeholder="结束时间" />
                  </div>
                  <n-input
                    v-model:value="value.description"
                    type="textarea"
                    placeholder="工作描述和成就"
                    :rows="2"
                  />
                </div>
              </template>
            </n-dynamic-input>

            <n-divider />

            <div class="section-header">
              <h3 class="section-title">
                <n-icon size="18" color="#2563eb"><CodeSlashOutline /></n-icon>
                项目经历
              </h3>
            </div>
            <n-dynamic-input
              v-model:value="projects"
              :on-create="onCreateProject"
              :min="0"
            >
              <template #default="{ value }">
                <div class="dynamic-form">
                  <div class="form-grid-2">
                    <n-input v-model:value="value.name" placeholder="项目名称" />
                    <n-input v-model:value="value.role" placeholder="担任角色" />
                  </div>
                  <n-input v-model:value="value.url" placeholder="项目链接（选填）" />
                  <n-input
                    v-model:value="value.description"
                    type="textarea"
                    placeholder="项目描述和技术栈"
                    :rows="2"
                  />
                </div>
              </template>
            </n-dynamic-input>

            <div style="margin-top: 16px">
              <n-button type="primary" :loading="saving" @click="handleSave">保存经历</n-button>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 900px;
  margin: 0 auto;
}

.profile-header-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.profile-name {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px;
}

.profile-email {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 8px;
}

.profile-content-card {
  border-radius: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0 16px;
}

.section-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 16px;
}

.section-header {
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.dynamic-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

@media (max-width: 768px) {
  .form-grid,
  .form-grid-2 {
    grid-template-columns: 1fr;
  }
}
</style>

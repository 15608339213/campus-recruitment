<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NCard, NButton, NTag, NSpace, NSelect, NIcon, NSpin, useMessage } from 'naive-ui'
import { EyeOutline, DownloadOutline, HeartOutline, Heart } from '@vicons/ionicons5'
import { getTemplates, type ResumeTemplate } from '@/api/resume'

const router = useRouter()
const message = useMessage()
const templates = ref<ResumeTemplate[]>([])
const loading = ref(true)
const filterCategory = ref('')

const categories = [
  { label: '全部', value: '' },
  { label: '经典', value: '经典' },
  { label: '现代', value: '现代' },
  { label: '创意', value: '创意' },
  { label: '极简', value: '极简' },
  { label: '学术', value: '学术' },
  { label: '科技', value: '科技' },
]

const filteredTemplates = computed(() => {
  if (!filterCategory.value) return templates.value
  return templates.value.filter(t => t.category === filterCategory.value)
})

onMounted(async () => {
  try {
    const res = await getTemplates()
    templates.value = res.items
  } catch (e: any) {
    message.error('加载模板失败')
  } finally {
    loading.value = false
  }
})

function selectTemplate(tpl: ResumeTemplate) {
  router.push({ path: '/resume/generate', query: { template_id: tpl.id.toString() } })
}

function previewTemplate(tpl: ResumeTemplate) {
  const w = window.open('', '_blank')
  if (!w) return
  const html = `<style>${tpl.css_rules} body{margin:0;padding:20px}</style>${tpl.html_structure
    .replace(/\{\{name\}\}/g, '张三')
    .replace(/\{\{email\}\}/g, 'example@mail.com')
    .replace(/\{\{phone\}\}/g, '138****0000')
    .replace(/\{\{school\}\}/g, '清华大学')
    .replace(/\{\{major\}\}/g, '计算机科学')
    .replace(/\{\{\#education\}\}/g, '')
    .replace(/\{\{\/education\}\}/g, '')
  }`
  w.document.write(html)
}
</script>

<script lang="ts">
import { computed } from 'vue'
</script>

<template>
  <div class="template-gallery">
    <div class="page-header">
      <h1>简历模板库</h1>
      <p>选择心仪模板，填入信息即可生成精美简历</p>
    </div>

    <n-space class="filter-bar" align="center">
      <span class="filter-label">风格：</span>
      <n-select v-model:value="filterCategory" :options="categories" style="width:160px" />
    </n-space>

    <n-spin :show="loading">
      <div class="template-grid">
        <n-card
          v-for="tpl in filteredTemplates"
          :key="tpl.id"
          class="template-card"
          hoverable
        >
          <div class="card-preview" v-html="tpl.html_structure.slice(0, 200) + '...'"></div>
          <div class="card-body">
            <h3>{{ tpl.name }}</h3>
            <n-tag size="tiny" type="info" :bordered="false">{{ tpl.category }}</n-tag>
            <p class="card-desc">{{ tpl.description }}</p>
          </div>
          <n-space justify="end" class="card-actions">
            <n-button size="small" quaternary @click="previewTemplate(tpl)">
              <template #icon><n-icon><EyeOutline /></n-icon></template>
              预览
            </n-button>
            <n-button size="small" type="primary" ghost @click="selectTemplate(tpl)">
              <template #icon><n-icon><DownloadOutline /></n-icon></template>
              使用
            </n-button>
          </n-space>
        </n-card>
      </div>
    </n-spin>
  </div>
</template>

<style scoped>
.template-gallery { max-width: 1200px; margin: 0 auto; padding-bottom: 40px }
.page-header { margin-bottom: 24px }
.page-header h1 { font-size: 24px; color: #1f2937; margin: 0 0 4px }
.page-header p { font-size: 14px; color: #6b7280; margin: 0 }
.filter-bar { margin-bottom: 20px }
.filter-label { font-size: 14px; color: #4b5563 }
.template-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px }
.template-card { cursor: pointer; border-radius: 10px }
.card-preview { height: 120px; overflow: hidden; background: #f3f4f6; border-radius: 6px; padding: 8px; font-size: 8px; line-height: 1.2; color: #9ca3af; margin-bottom: 12px }
.card-body h3 { font-size: 15px; margin: 0 0 6px; color: #1f2937 }
.card-desc { font-size: 12px; color: #6b7280; margin: 6px 0 0 }
.card-actions { margin-top: 12px }
</style>

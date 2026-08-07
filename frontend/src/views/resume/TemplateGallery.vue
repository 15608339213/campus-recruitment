<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NButton,
  NTag,
  NSpace,
  NIcon,
  NSpin,
  NEmpty,
  NModal,
  NDivider,
  NGradientText,
  useMessage,
} from 'naive-ui'
import {
  GridOutline,
  AlbumsOutline,
  ColorPaletteOutline,
  FlashOutline,
  CloudDoneOutline,
  EyeOutline,
  SparklesOutline,
} from '@vicons/ionicons5'
import type { ResumeTemplate } from '@/types'
import { getTemplates } from '@/api/resume'

const router = useRouter()
const message = useMessage()

const templates = ref<ResumeTemplate[]>([])
const loading = ref(true)
const selectedCategory = ref('')
const previewTemplate = ref<ResumeTemplate | null>(null)
const showPreview = ref(false)

// 分类定义
const categories = [
  { label: '全部模板', value: '' },
  { label: '经典上下结构', value: '经典上下结构' },
  { label: '经典左右分栏', value: '经典左右分栏' },
  { label: '创意/时尚', value: '创意/时尚' },
  { label: '极简线条', value: '极简线条' },
  { label: '表格风格', value: '表格风格' },
  { label: '技术/程序员', value: '技术/程序员' },
]

// 分类图标映射
const categoryIconMap: Record<string, any> = {
  '经典上下结构': GridOutline,
  '经典左右分栏': AlbumsOutline,
  '创意/时尚': ColorPaletteOutline,
  '极简线条': FlashOutline,
  '表格风格': GridOutline,
  '技术/程序员': CloudDoneOutline,
}

// 分类颜色映射
const categoryColorMap: Record<string, string> = {
  '经典上下结构': '#3b82f6',
  '经典左右分栏': '#8b5cf6',
  '创意/时尚': '#ec4899',
  '极简线条': '#6b7280',
  '表格风格': '#10b981',
  '技术/程序员': '#f59e0b',
}

// 筛选后的模板
const filteredTemplates = computed(() => {
  if (!selectedCategory.value) return templates.value
  return templates.value.filter((t) => t.category === selectedCategory.value)
})

// 解析 JSON 字段
function parseTags(styleTags: string | null): string[] {
  if (!styleTags) return []
  try {
    return JSON.parse(styleTags)
  } catch {
    return []
  }
}

function getCategoryIcon(category: string) {
  return categoryIconMap[category] || GridOutline
}

function getCategoryColor(category: string): string {
  return categoryColorMap[category] || '#6b7280'
}

async function fetchTemplates() {
  loading.value = true
  try {
    const res = await getTemplates()
    templates.value = res.items
  } catch (error: any) {
    message.error('获取模板列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function openPreview(tpl: ResumeTemplate) {
  previewTemplate.value = tpl
  showPreview.value = true
}

function closePreview() {
  showPreview.value = false
  previewTemplate.value = null
}

function useTemplate(tpl: ResumeTemplate) {
  closePreview()
  router.push({ path: '/resume/generate', query: { template_id: tpl.id.toString() } })
}

function handleCategoryChange(value: string) {
  selectedCategory.value = value
}

onMounted(() => {
  fetchTemplates()
})
</script>

<template>
  <div class="template-gallery-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <n-icon size="24" color="#2563eb"><AlbumsOutline /></n-icon>
        简历模板库
      </h1>
      <p class="page-desc">选择一款模板，快速生成专业简历，共 {{ templates.length }} 套模板</p>
    </div>

    <div class="gallery-layout">
      <!-- 左侧筛选栏 -->
      <div class="filter-sidebar">
        <n-card title="模板分类" :bordered="false" size="small">
          <n-space vertical size="small">
            <div
              v-for="cat in categories"
              :key="cat.value"
              class="category-item"
              :class="{ active: selectedCategory === cat.value }"
              @click="handleCategoryChange(cat.value)"
            >
              <n-icon v-if="cat.value" size="16" :color="selectedCategory === cat.value ? '#fff' : getCategoryColor(cat.value)">
                <component :is="getCategoryIcon(cat.value)" />
              </n-icon>
              <span>{{ cat.label }}</span>
            </div>
          </n-space>
        </n-card>
      </div>

      <!-- 模板网格 -->
      <div class="gallery-main">
        <!-- 加载中 -->
        <div v-if="loading" class="loading-wrapper">
          <n-spin size="large" />
          <p style="color:#9ca3af;margin-top:12px">加载模板中...</p>
        </div>

        <!-- 空状态 -->
        <n-empty
          v-else-if="filteredTemplates.length === 0"
          description="暂无符合条件的模板"
          style="padding:80px 0"
        >
          <template #extra>
            <n-button type="primary" @click="selectedCategory = ''">显示全部模板</n-button>
          </template>
        </n-empty>

        <!-- 模板网格 -->
        <div v-else class="template-grid">
          <n-card
            v-for="tpl in filteredTemplates"
            :key="tpl.id"
            class="template-card"
            :bordered="false"
            hoverable
            size="small"
          >
            <div class="card-inner" @click="openPreview(tpl)">
              <!-- 预览区域 -->
              <div class="card-preview" :style="{ borderColor: getCategoryColor(tpl.category) }">
                <div class="preview-placeholder">
                  <n-icon size="32" :color="getCategoryColor(tpl.category)">
                    <component :is="getCategoryIcon(tpl.category)" />
                  </n-icon>
                  <span class="preview-label">{{ tpl.name }}</span>
                </div>
              </div>

              <!-- 模板信息 -->
              <div class="card-info">
                <h3 class="card-name">{{ tpl.name }}</h3>
                <p class="card-desc" v-if="tpl.description">{{ tpl.description }}</p>

                <div class="card-meta">
                  <n-tag
                    :color="{ color: getCategoryColor(tpl.category), textColor: '#fff' }"
                    size="tiny"
                    round
                    :bordered="false"
                  >
                    {{ tpl.category }}
                  </n-tag>
                  <n-tag
                    v-for="tag in parseTags(tpl.style_tags).slice(0, 2)"
                    :key="tag"
                    size="tiny"
                    type="info"
                    :bordered="false"
                    round
                  >
                    {{ tag }}
                  </n-tag>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="card-actions">
                <n-button size="small" quaternary @click.stop="openPreview(tpl)">
                  <template #icon><n-icon><EyeOutline /></n-icon></template>
                  预览
                </n-button>
                <n-button size="small" type="primary" ghost @click.stop="useTemplate(tpl)">
                  <template #icon><n-icon><SparklesOutline /></n-icon></template>
                  使用此模板
                </n-button>
              </div>
            </div>
          </n-card>
        </div>
      </div>
    </div>

    <!-- 预览模态框 -->
    <n-modal
      v-model:show="showPreview"
      preset="card"
      title="模板预览"
      style="max-width: 860px"
      :bordered="false"
      :mask-closable="true"
    >
      <template #header-extra>
        <n-tag v-if="previewTemplate" type="info" size="small" round :bordered="false">
          {{ previewTemplate.category }}
        </n-tag>
      </template>

      <template v-if="previewTemplate">
        <div class="preview-container">
          <!-- 模板基本信息 -->
          <div class="preview-meta">
            <h2>{{ previewTemplate.name }}</h2>
            <p v-if="previewTemplate.description" class="preview-desc">{{ previewTemplate.description }}</p>
            <n-space v-if="previewTemplate.style_tags" size="small">
              <n-tag
                v-for="tag in parseTags(previewTemplate.style_tags)"
                :key="tag"
                size="small"
                round
                :bordered="false"
                :color="{ color: getCategoryColor(previewTemplate.category), textColor: '#fff' }"
              >
                {{ tag }}
              </n-tag>
            </n-space>
          </div>

          <n-divider />

          <!-- HTML结构预览 -->
          <div class="preview-section">
            <h3 class="preview-section-title">HTML 结构</h3>
            <pre class="code-block"><code>{{ previewTemplate.html_structure.substring(0, 800) }}{{ previewTemplate.html_structure.length > 800 ? '...' : '' }}</code></pre>
          </div>

          <!-- CSS样式预览 -->
          <div class="preview-section">
            <h3 class="preview-section-title">CSS 样式</h3>
            <pre class="code-block"><code>{{ previewTemplate.css_rules.substring(0, 600) }}{{ previewTemplate.css_rules.length > 600 ? '...' : '' }}</code></pre>
          </div>

          <!-- 支持的板块 -->
          <div class="preview-section" v-if="previewTemplate.supported_sections">
            <h3 class="preview-section-title">支持板块</h3>
            <n-space size="small">
              <n-tag
                v-for="section in parseTags(previewTemplate.supported_sections)"
                :key="section"
                size="small"
                type="success"
                round
                :bordered="false"
              >
                {{ section }}
              </n-tag>
            </n-space>
          </div>
        </div>

        <n-divider />

        <div class="preview-actions">
          <n-button @click="closePreview">关闭</n-button>
          <n-button type="primary" @click="useTemplate(previewTemplate)">
            <template #icon><n-icon><SparklesOutline /></n-icon></template>
            使用此模板创建简历
          </n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.template-gallery-page {
  max-width: 1200px;
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

.gallery-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.filter-sidebar {
  width: 220px;
  flex-shrink: 0;
  position: sticky;
  top: 88px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #4b5563;
  transition: all 0.2s;
  user-select: none;
}

.category-item:hover {
  background: #f3f4f6;
}

.category-item.active {
  background: #2563eb;
  color: #fff;
  font-weight: 500;
}

.gallery-main {
  flex: 1;
  min-width: 0;
}

.loading-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.template-card {
  cursor: pointer;
  border-radius: 10px;
  overflow: hidden;
}

.template-card:hover .card-preview {
  transform: scale(1.02);
}

.card-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.card-preview {
  height: 120px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  transition: transform 0.2s;
  overflow: hidden;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.preview-label {
  font-size: 12px;
  color: #9ca3af;
}

.card-info {
  flex: 1;
}

.card-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-desc {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 10px;
}

.card-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #f3f4f6;
}

.preview-container {
  max-height: 70vh;
  overflow-y: auto;
}

.preview-meta h2 {
  font-size: 20px;
  color: #1f2937;
  margin: 0 0 6px;
}

.preview-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 12px;
}

.preview-section {
  margin-bottom: 18px;
}

.preview-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px;
}

.code-block {
  background: #1e293b;
  color: #e2e8f0;
  padding: 14px 16px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  max-height: 200px;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.code-block code {
  font-family: 'SF Mono', 'Consolas', monospace;
}

.preview-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 1024px) {
  .template-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .gallery-layout {
    flex-direction: column;
  }

  .filter-sidebar {
    width: 100%;
    position: static;
  }

  .template-grid {
    grid-template-columns: 1fr;
  }
}
</style>

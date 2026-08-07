<script setup lang="ts">
import { ref, computed } from 'vue'
import { NButton, NIcon, NProgress, NSpace, NTag, useMessage } from 'naive-ui'
import { CloudUploadOutline, DocumentOutline, Close, CheckmarkCircle } from '@vicons/ionicons5'

const props = defineProps<{
  accept?: string
  maxSize?: number
  maxFiles?: number
  endpoint?: string
}>()

const emit = defineEmits<{
  (e: 'uploaded', files: UploadedFile[]): void
  (e: 'text-extracted', text: string): void
}>()

const message = useMessage()

interface UploadedFile {
  name: string
  type: string
  size: number
  text?: string
  progress: number
  status: 'pending' | 'uploading' | 'done' | 'error'
  error?: string
}

const files = ref<UploadedFile[]>([])
const dragging = ref(false)

const acceptStr = computed(() => props.accept || '.pdf,.docx,.doc,.png,.jpg,.jpeg')
const maxSizeBytes = computed(() => (props.maxSize || 10) * 1024 * 1024)
const maxFilesCount = computed(() => props.maxFiles || 5)

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}

function validateFile(file: File): string | null {
  const exts = acceptStr.value.split(',').map(e => e.trim().replace('.', ''))
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!exts.includes(ext)) return `不支持 .${ext} 格式`
  if (file.size > maxSizeBytes.value) return `超过 ${props.maxSize || 10}MB 限制`
  if (files.value.length >= maxFilesCount.value) return `最多 ${maxFilesCount.value} 个文件`
  return null
}

async function handleFiles(fileList: FileList | File[]) {
  for (const file of Array.from(fileList)) {
    const err = validateFile(file)
    if (err) { message.warning(err); continue }

    const uploaded: UploadedFile = {
      name: file.name,
      type: file.type,
      size: file.size,
      progress: 0,
      status: 'uploading',
    }
    files.value.push(uploaded)

    // 模拟进度 + 文本提取
    const reader = new FileReader()
    reader.onprogress = (e) => {
      if (e.lengthComputable) uploaded.progress = Math.round((e.loaded / e.total) * 100)
    }
    reader.onload = () => {
      uploaded.progress = 100
      uploaded.status = 'done'
      uploaded.text = reader.result as string
      emit('text-extracted', reader.result as string)

      // 上传到后端
      uploadToServer(file, uploaded)
    }
    reader.onerror = () => {
      uploaded.status = 'error'
      uploaded.error = '读取失败'
    }

    if (file.type.includes('text') || file.type.includes('json') || file.type.includes('xml')) {
      reader.readAsText(file)
    } else {
      // 非文本文件：直接标记完成，上传到后端解析
      uploaded.progress = 100
      uploaded.status = 'done'
      uploadToServer(file, uploaded)
    }
  }
}

async function uploadToServer(file: File, uploaded: UploadedFile) {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const token = localStorage.getItem('access_token')
    const resp = await fetch('/api/v1/resume/upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token || ''}` },
      body: formData,
    })
    if (resp.ok) {
      const data = await resp.json()
      uploaded.text = data.text
      emit('text-extracted', data.text || '')
    }
  } catch (e) {
    console.error('Upload failed:', e)
  }
  emit('uploaded', files.value.filter(f => f.status === 'done'))
}

function removeFile(index: number) {
  files.value.splice(index, 1)
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
  dragging.value = true
}
function onDragLeave() { dragging.value = false }
function onDrop(e: DragEvent) {
  e.preventDefault()
  dragging.value = false
  if (e.dataTransfer?.files) handleFiles(e.dataTransfer.files)
}
function onFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files) handleFiles(target.files)
  target.value = ''
}
</script>

<template>
  <div class="file-uploader">
    <!-- 拖拽区域 -->
    <div
      class="drop-zone"
      :class="{ dragging }"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
      @click="($refs.fileInput as HTMLInputElement).click()"
    >
      <n-icon size="32" :color="dragging ? '#3b82f6' : '#94a3b8'">
        <CloudUploadOutline />
      </n-icon>
      <p class="drop-text">
        {{ dragging ? '释放文件即可上传' : '拖拽文件到此处，或点击选择' }}
      </p>
      <p class="drop-hint">支持 {{ acceptStr }} · 单文件 ≤{{ props.maxSize || 10 }}MB</p>
      <input
        ref="fileInput"
        type="file"
        :accept="acceptStr"
        multiple
        hidden
        @change="onFileInput"
      />
    </div>

    <!-- 文件列表 -->
    <div v-if="files.length" class="file-list">
      <div v-for="(f, i) in files" :key="i" class="file-item">
        <div class="file-info">
          <n-icon size="20" :color="f.status === 'error' ? '#ef4444' : '#3b82f6'">
            <DocumentOutline v-if="f.status !== 'done'" />
            <CheckmarkCircle v-else />
          </n-icon>
          <div class="file-detail">
            <span class="file-name">{{ f.name }}</span>
            <span class="file-size">{{ formatSize(f.size) }}</span>
            <n-tag v-if="f.status === 'error'" type="error" size="tiny" :bordered="false">
              {{ f.error }}
            </n-tag>
          </div>
        </div>
        <n-button text size="small" @click="removeFile(i)">
          <template #icon><n-icon><Close /></n-icon></template>
        </n-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-uploader { width: 100% }
.drop-zone {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafbfc;
}
.drop-zone:hover, .drop-zone.dragging {
  border-color: #3b82f6;
  background: #eff6ff;
}
.drop-text { font-size: 15px; color: #4b5563; margin: 10px 0 4px }
.drop-hint { font-size: 12px; color: #9ca3af; margin: 0 }
.file-list { margin-top: 12px; display: flex; flex-direction: column; gap: 8px }
.file-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: #f9fafb; border-radius: 8px;
}
.file-info { display: flex; align-items: center; gap: 10px }
.file-detail { display: flex; flex-direction: column }
.file-name { font-size: 14px; color: #1f2937 }
.file-size { font-size: 12px; color: #9ca3af }
</style>

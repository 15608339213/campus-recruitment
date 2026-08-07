<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NUpload,
  NUploadDragger,
  NButton,
  NIcon,
  NText,
  NP,
  NProgress,
  NSpace,
  NTag,
  useMessage,
} from 'naive-ui'
import {
  CloudUploadOutline,
  DocumentOutline,
  ImageOutline,
  TrashOutline,
  EyeOutline,
} from '@vicons/ionicons5'

const props = withDefaults(
  defineProps<{
    accept?: string
    maxSize?: number // bytes
    multiple?: boolean
    uploadUrl?: string
    tip?: string
    preview?: boolean
  }>(),
  {
    accept: '.pdf,.docx,.doc,.png,.jpg,.jpeg',
    maxSize: 10 * 1024 * 1024,
    multiple: false,
    uploadUrl: '/api/v1/resume/upload',
    tip: '支持 PDF、Word、图片文件',
    preview: false,
  }
)

const emit = defineEmits<{
  'upload-success': [data: { fileId: number; fileName: string; fileType: string; extractedText: string }]
  'upload-error': [error: string]
  'file-removed': []
}>()

const message = useMessage()

const fileList = ref<any[]>([])
const uploading = ref(false)
const uploadProgress = ref(0)
const lastUploaded = ref<{
  fileId: number
  fileName: string
  fileType: string
  extractedText: string
} | null>(null)

const fileTypeLabel = (name: string) => {
  const ext = name.split('.').pop()?.toLowerCase()
  const map: Record<string, string> = {
    pdf: 'PDF',
    docx: 'Word',
    doc: 'Word',
    png: '图片',
    jpg: '图片',
    jpeg: '图片',
    webp: '图片',
  }
  return map[ext || ''] || '未知'
}

const fileTypeIcon = (name: string) => {
  const ext = name.split('.').pop()?.toLowerCase()
  if (['png', 'jpg', 'jpeg', 'webp'].includes(ext || '')) {
    return ImageOutline
  }
  return DocumentOutline
}

const acceptFormats = computed(() => {
  return props.accept || '.pdf,.docx,.doc,.png,.jpg,.jpeg'
})

async function handleUpload(options: { file: any; onFinish: Function; onError: Function }) {
  uploading.value = true
  uploadProgress.value = 0

  const formData = new FormData()
  formData.append('file', options.file.file as File)

  const simulateProgress = setInterval(() => {
    if (uploadProgress.value < 90) {
      uploadProgress.value += 10
    }
  }, 200)

  try {
    const response = await fetch(props.uploadUrl, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    })

    clearInterval(simulateProgress)
    uploadProgress.value = 100

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || '上传失败')
    }

    const data = await response.json()
    lastUploaded.value = data
    emit('upload-success', data)
    options.onFinish()
    message.success('文件上传成功')
  } catch (error: any) {
    clearInterval(simulateProgress)
    uploadProgress.value = 0
    emit('upload-error', error.message)
    options.onError()
    message.error(error.message || '上传失败')
  } finally {
    uploading.value = false
    setTimeout(() => {
      uploadProgress.value = 0
    }, 1000)
  }
}

function handleRemove() {
  fileList.value = []
  lastUploaded.value = null
  emit('file-removed')
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div class="file-uploader">
    <n-upload
      v-model:file-list="fileList"
      :accept="acceptFormats"
      :max="multiple ? 10 : 1"
      :custom-request="handleUpload"
      @remove="handleRemove"
    >
      <n-upload-dragger>
        <div class="dragger-content">
          <n-icon size="48" color="#d1d5db">
            <CloudUploadOutline />
          </n-icon>
          <n-text class="dragger-title">点击或拖拽文件到此区域上传</n-text>
          <n-text class="dragger-tip">{{ tip || `支持 PDF、Word（≤${formatSize(maxSize)}）、图片（≤${formatSize(maxSize)}）文件` }}</n-text>
        </div>
      </n-upload-dragger>
    </n-upload>

    <!-- 上传进度 -->
    <div v-if="uploading" class="upload-progress">
      <n-progress
        type="line"
        :percentage="uploadProgress"
        :indicator-placement="'inside'"
        processing
      />
    </div>

    <!-- 上传成功信息 -->
    <div v-if="lastUploaded && !uploading" class="upload-result">
      <n-space align="center">
        <n-icon size="20" color="#10b981">
          <component :is="fileTypeIcon(lastUploaded.fileName)" />
        </n-icon>
        <span class="result-name">{{ lastUploaded.fileName }}</span>
        <n-tag size="small" type="success" round :bordered="false">
          上传成功
        </n-tag>
        <n-button text size="small" type="error" @click="handleRemove">
          <template #icon><n-icon><TrashOutline /></n-icon></template>
          删除
        </n-button>
      </n-space>
      <n-text v-if="lastUploaded.extractedText" depth="3" class="result-preview">
        已提取 {{ lastUploaded.extractedText.length }} 个字符的文本内容
      </n-text>
    </div>
  </div>
</template>

<style scoped>
.file-uploader {
  width: 100%;
}

.dragger-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
}

.dragger-title {
  margin-top: 12px;
  font-size: 15px;
  font-weight: 500;
  color: #374151;
}

.dragger-tip {
  margin-top: 4px;
  font-size: 13px;
  color: #9ca3af;
}

.upload-progress {
  margin-top: 16px;
}

.upload-result {
  margin-top: 16px;
  padding: 12px 16px;
  background: #f0fdf4;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
}

.result-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.result-preview {
  display: block;
  margin-top: 8px;
  font-size: 12px;
}
</style>

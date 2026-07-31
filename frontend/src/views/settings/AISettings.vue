<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import {
  NCard,
  NButton,
  NInput,
  NSelect,
  NTag,
  NSpace,
  NEmpty,
  NIcon,
  NModal,
  NForm,
  NFormItem,
  NSpin,
  NAlert,
  NRadio,
  NRadioGroup,
  useMessage,
} from 'naive-ui'
import {
  AddOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  TrashOutline,
  CreateOutline,
  SwapHorizontalOutline,
  ServerOutline,
} from '@vicons/ionicons5'
import {
  getBuiltinProviders,
  getMyProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  testConnection,
} from '@/api/aiProvider'
import type {
  BuiltinProvider,
  AIProviderConfig,
  CreateProviderData,
} from '@/api/aiProvider'

const message = useMessage()

// ===== 数据 =====
const loading = ref(false)
const testing = ref(false)
const builtinProviders = ref<BuiltinProvider[]>([])
const myProviders = ref<AIProviderConfig[]>([])

// ===== 添加/编辑弹窗 =====
const showModal = ref(false)
const editingId = ref<number | null>(null)
const testResult = ref<{ success: boolean; message: string } | null>(null)

const formData = reactive({
  provider_id: 'deepseek',
  display_name: '',
  api_key: '',
  base_url: '',
  model: '',
  is_active: true,
})

// 当前选中的内置提供商信息（用于自动填充）
const selectedBuiltin = computed(() => {
  return builtinProviders.value.find((p) => p.id === formData.provider_id)
})

// ===== 初始化 =====
onMounted(async () => {
  await Promise.all([loadBuiltin(), loadMyProviders()])
})

async function loadBuiltin() {
  try {
    builtinProviders.value = await getBuiltinProviders()
  } catch (e) {
    console.error('获取内置提供商列表失败', e)
  }
}

async function loadMyProviders() {
  loading.value = true
  try {
    const res = await getMyProviders()
    myProviders.value = res.items
  } catch (e) {
    console.error('获取我的提供商列表失败', e)
  } finally {
    loading.value = false
  }
}

// ===== 内置提供商选项 =====
const providerOptions = computed(() => {
  return builtinProviders.value.map((p) => ({
    label: p.name,
    value: p.id,
  }))
})

// ===== 模型选项 =====
const modelOptions = computed(() => {
  if (!selectedBuiltin.value) return []
  return selectedBuiltin.value.models.map((m) => ({
    label: m,
    value: m,
  }))
})

// ===== 选择提供商时自动填充 =====
function handleProviderChange(providerId: string) {
  const builtin = builtinProviders.value.find((p) => p.id === providerId)
  if (builtin) {
    formData.base_url = builtin.base_url
    formData.model = builtin.default_model
    if (!formData.display_name) {
      formData.display_name = builtin.name
    }
  }
}

// ===== 打开添加弹窗 =====
function openAddModal() {
  editingId.value = null
  formData.provider_id = 'deepseek'
  formData.display_name = ''
  formData.api_key = ''
  formData.base_url = 'https://api.deepseek.com'
  formData.model = 'deepseek-chat'
  formData.is_active = true
  testResult.value = null
  showModal.value = true
  // 自动填充
  handleProviderChange('deepseek')
}

// ===== 打开编辑弹窗 =====
function openEditModal(config: AIProviderConfig) {
  editingId.value = config.id
  formData.provider_id = config.provider_id
  formData.display_name = config.display_name
  formData.api_key = ''
  formData.base_url = config.base_url
  formData.model = config.model
  formData.is_active = config.is_active
  testResult.value = null
  showModal.value = true
}

// ===== 测试连接 =====
async function handleTest() {
  if (!formData.api_key || !formData.base_url || !formData.model) {
    message.warning('请填写完整的 API 配置信息')
    return
  }
  testing.value = true
  testResult.value = null
  try {
    const result = await testConnection({
      api_key: formData.api_key,
      base_url: formData.base_url,
      model: formData.model,
    })
    testResult.value = {
      success: result.success,
      message: result.message,
    }
    if (result.success) {
      message.success('连接测试成功！')
    } else {
      message.error(`测试失败：${result.message}`)
    }
  } catch (e: any) {
    testResult.value = {
      success: false,
      message: e.message || '测试请求失败',
    }
    message.error('测试请求失败')
  } finally {
    testing.value = false
  }
}

// ===== 保存配置 =====
async function handleSave() {
  if (!formData.display_name.trim()) {
    message.warning('请填写显示名称')
    return
  }
  if (!formData.api_key.trim()) {
    message.warning('请填写 API Key')
    return
  }
  if (!formData.base_url.trim()) {
    message.warning('请填写 API 地址')
    return
  }
  if (!formData.model.trim()) {
    message.warning('请选择或填写模型名称')
    return
  }

  loading.value = true
  try {
    const data: CreateProviderData = {
      provider_id: formData.provider_id,
      display_name: formData.display_name,
      api_key: formData.api_key,
      base_url: formData.base_url,
      model: formData.model,
      is_active: formData.is_active,
    }

    if (editingId.value) {
      // 编辑模式：如果不填 api_key 则不更新
      const updateData: Record<string, unknown> = {
        display_name: formData.display_name,
        base_url: formData.base_url,
        model: formData.model,
        is_active: formData.is_active,
      }
      if (formData.api_key) {
        updateData.api_key = formData.api_key
      }
      await updateProvider(editingId.value, updateData)
      message.success('配置已更新')
    } else {
      await createProvider(data)
      message.success('AI 提供商配置已添加')
    }
    showModal.value = false
    await loadMyProviders()
  } catch (e: any) {
    message.error(e.message || '保存失败')
  } finally {
    loading.value = false
  }
}

// ===== 删除配置 =====
async function handleDelete(config: AIProviderConfig) {
  try {
    await deleteProvider(config.id)
    message.success('配置已删除')
    await loadMyProviders()
  } catch (e: any) {
    message.error('删除失败')
  }
}

// ===== 设为激活 =====
async function handleSetActive(config: AIProviderConfig) {
  try {
    await updateProvider(config.id, { is_active: true })
    message.success(`已将「${config.display_name}」设为当前使用的 AI`)
    await loadMyProviders()
  } catch (e: any) {
    message.error('设置失败')
  }
}

// ===== 获取提供商中文名 =====
function getProviderName(providerId: string): string {
  const builtin = builtinProviders.value.find((p) => p.id === providerId)
  return builtin?.name || providerId
}
</script>

<template>
  <div class="ai-settings-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <n-icon size="24" color="#2563eb"><ServerOutline /></n-icon>
        AI 提供商设置
      </h1>
      <p class="page-desc">
        添加您自己的 AI API Key，选择喜欢的 AI 模型生成简历。支持 DeepSeek、OpenAI、通义千问、智谱 GLM、Kimi 等多种服务商。
      </p>
    </div>

    <!-- 当前激活的提供商 -->
    <n-card :bordered="false" class="active-card" v-if="myProviders.find((p) => p.is_active)">
      <div class="active-provider">
        <n-icon size="28" color="#10b981"><CheckmarkCircleOutline /></n-icon>
        <div class="active-info">
          <span class="active-label">当前使用</span>
          <span class="active-name">
            {{ myProviders.find((p) => p.is_active)?.display_name }}
            <n-tag size="tiny" type="success" round :bordered="false">
              {{ myProviders.find((p) => p.is_active)?.model }}
            </n-tag>
          </span>
        </div>
      </div>
    </n-card>

    <!-- 未配置提示 -->
    <n-card :bordered="false" class="empty-card" v-else>
      <n-empty description="尚未配置 AI 提供商，简历生成功能暂不可用">
        <template #extra>
          <n-button type="primary" @click="openAddModal">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            添加第一个 AI 配置
          </n-button>
        </template>
      </n-empty>
    </n-card>

    <!-- 我的配置列表 -->
    <div class="provider-list" v-if="myProviders.length > 0">
      <div class="list-header">
        <span class="list-title">我的 AI 配置 ({{ myProviders.length }})</span>
        <n-button type="primary" size="small" @click="openAddModal">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          添加配置
        </n-button>
      </div>

      <n-spin :show="loading">
        <div class="config-cards">
          <n-card
            v-for="config in myProviders"
            :key="config.id"
            :bordered="false"
            class="config-card"
            :class="{ 'config-active': config.is_active }"
            hoverable
          >
            <div class="config-content">
              <div class="config-info">
                <div class="config-header">
                  <span class="config-name">{{ config.display_name }}</span>
                  <n-tag v-if="config.is_active" size="tiny" type="success" round :bordered="false">
                    使用中
                  </n-tag>
                </div>
                <div class="config-meta">
                  <n-tag size="tiny" :bordered="false" type="info">
                    {{ getProviderName(config.provider_id) }}
                  </n-tag>
                  <span class="meta-item">模型: {{ config.model }}</span>
                  <span class="meta-item">Key: {{ config.api_key_masked }}</span>
                </div>
                <div class="config-test" v-if="config.last_tested">
                  <n-icon
                    size="14"
                    :color="config.last_test_ok ? '#10b981' : '#ef4444'"
                  >
                    <component :is="config.last_test_ok ? CheckmarkCircleOutline : CloseCircleOutline" />
                  </n-icon>
                  <span class="test-text">
                    {{ config.last_test_ok ? '连接正常' : '连接异常' }}
                  </span>
                </div>
              </div>
              <div class="config-actions">
                <n-button
                  v-if="!config.is_active"
                  size="small"
                  type="primary"
                  ghost
                  @click="handleSetActive(config)"
                >
                  <template #icon><n-icon><SwapHorizontalOutline /></n-icon></template>
                  设为当前
                </n-button>
                <n-button size="small" quaternary @click="openEditModal(config)">
                  <template #icon><n-icon><CreateOutline /></n-icon></template>
                  编辑
                </n-button>
                <n-button size="small" quaternary type="error" @click="handleDelete(config)">
                  <template #icon><n-icon><TrashOutline /></n-icon></template>
                </n-button>
              </div>
            </div>
          </n-card>
        </div>
      </n-spin>
    </div>

    <!-- 内置提供商说明 -->
    <n-card :bordered="false" class="builtin-card">
      <template #header>
        <div class="builtin-header">
          <n-icon size="18" color="#2563eb"><ServerOutline /></n-icon>
          <span>支持的 AI 服务商</span>
        </div>
      </template>
      <div class="builtin-grid">
        <div
          v-for="provider in builtinProviders"
          :key="provider.id"
          class="builtin-item"
        >
          <div class="builtin-name">{{ provider.name }}</div>
          <div class="builtin-desc">{{ provider.description }}</div>
          <div class="builtin-models">
            <n-tag
              v-for="model in provider.models"
              :key="model"
              size="tiny"
              :bordered="false"
              round
            >
              {{ model }}
            </n-tag>
          </div>
          <n-button
            text
            size="small"
            tag="a"
            :href="provider.website"
            target="_blank"
            v-if="provider.website"
          >
            获取 API Key →
          </n-button>
        </div>
      </div>
    </n-card>

    <!-- 添加/编辑弹窗 -->
    <n-modal
      v-model:show="showModal"
      preset="card"
      :title="editingId ? '编辑 AI 配置' : '添加 AI 配置'"
      style="max-width: 560px"
      :bordered="false"
    >
      <n-form label-placement="top" size="medium">
        <n-form-item label="AI 服务商">
          <n-select
            v-model:value="formData.provider_id"
            :options="providerOptions"
            placeholder="选择服务商"
            @update:value="handleProviderChange"
          />
        </n-form-item>

        <n-alert
          v-if="selectedBuiltin"
          :type="formData.provider_id === 'custom' ? 'warning' : 'info'"
          style="margin-bottom: 16px"
        >
          {{ selectedBuiltin.description }}
          <template v-if="selectedBuiltin.website">
            ，前往 <n-button text type="primary" tag="a" :href="selectedBuiltin.website" target="_blank">获取 API Key</n-button>
          </template>
        </n-alert>

        <n-form-item label="显示名称">
          <n-input v-model:value="formData.display_name" placeholder="如：我的 DeepSeek" />
        </n-form-item>

        <n-form-item label="API Key">
          <n-input
            v-model:value="formData.api_key"
            type="password"
            show-password-on="click"
            :placeholder="editingId ? '留空则不修改' : '请输入您的 API Key'"
          />
        </n-form-item>

        <n-form-item label="API 地址">
          <n-input v-model:value="formData.base_url" placeholder="https://api.deepseek.com" />
        </n-form-item>

        <n-form-item label="模型" v-if="modelOptions.length > 0">
          <n-select
            v-model:value="formData.model"
            :options="modelOptions"
            tag
            filterable
            placeholder="选择或输入模型名称"
          />
        </n-form-item>
        <n-form-item label="模型" v-else>
          <n-input v-model:value="formData.model" placeholder="输入模型名称" />
        </n-form-item>

        <n-form-item label="设为当前使用">
          <n-radio-group v-model:value="formData.is_active">
            <n-space>
              <n-radio :value="true">是，使用此配置生成简历</n-radio>
              <n-radio :value="false">否，仅保存</n-radio>
            </n-space>
          </n-radio-group>
        </n-form-item>

        <!-- 测试结果 -->
        <n-alert
          v-if="testResult"
          :type="testResult.success ? 'success' : 'error'"
          style="margin-bottom: 16px"
        >
          {{ testResult.message }}
        </n-alert>
      </n-form>

      <template #footer>
        <n-space justify="space-between">
          <n-button :loading="testing" @click="handleTest">
            <template #icon><n-icon><SwapHorizontalOutline /></n-icon></template>
            测试连接
          </n-button>
          <n-space>
            <n-button @click="showModal = false">取消</n-button>
            <n-button type="primary" :loading="loading" @click="handleSave">
              保存配置
            </n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.ai-settings-page {
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
  line-height: 1.6;
}

.active-card {
  border-radius: 12px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
}

.active-provider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.active-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.active-label {
  font-size: 12px;
  color: #6b7280;
}

.active-name {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.provider-list {
  margin-bottom: 24px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.list-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.config-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-card {
  border-radius: 10px;
  transition: all 0.2s;
}

.config-active {
  border: 2px solid #10b981;
}

.config-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-info {
  flex: 1;
}

.config-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.config-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.config-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
}

.meta-item {
  color: #6b7280;
}

.config-test {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}

.config-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.builtin-card {
  border-radius: 12px;
}

.builtin-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.builtin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.builtin-item {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.builtin-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.builtin-desc {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
  line-height: 1.5;
}

.builtin-models {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}
</style>

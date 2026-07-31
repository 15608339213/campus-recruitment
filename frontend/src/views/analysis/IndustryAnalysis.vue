<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import {
  NCard,
  NGrid,
  NGridItem,
  NStatistic,
  NButton,
  NSpace,
  NIcon,
  NSpin,
  NEmpty,
  NTag,
} from 'naive-ui'
import {
  TrendingUpOutline,
  CashOutline,
  CalendarOutline,
  BusinessOutline,
  BarChartOutline,
  PieChartOutline,
  MapOutline,
  TrophyOutline,
  RefreshOutline,
} from '@vicons/ionicons5'
import { getAnalysisStats } from '@/api/analysis'
import type { AnalysisStats } from '@/types'
import { formatNumber, formatSalary, formatAvgSalary } from '@/utils/format'

const loading = ref(true)
const stats = ref<AnalysisStats | null>(null)
const error = ref(false)

// 图表实例
const trendChart = ref<echarts.ECharts | null>(null)
const industryChart = ref<echarts.ECharts | null>(null)
const companyTypeChart = ref<echarts.ECharts | null>(null)
const regionChart = ref<echarts.ECharts | null>(null)
const salaryChart = ref<echarts.ECharts | null>(null)

// DOM 引用
const trendRef = ref<HTMLElement>()
const industryRef = ref<HTMLElement>()
const companyTypeRef = ref<HTMLElement>()
const regionRef = ref<HTMLElement>()
const salaryRef = ref<HTMLElement>()

// 时间范围
const currentRange = ref('30D')
const rangeOptions = [
  { label: '7天', value: '7D' },
  { label: '30天', value: '30D' },
  { label: '月初至今', value: 'MTD' },
  { label: '本季至今', value: 'QTD' },
  { label: '年初至今', value: 'YTD' },
  { label: '全部', value: 'ALL' },
]

// 蓝色系配色
const chartColors = ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#1d4ed8', '#1e40af', '#dbeafe', '#6366f1', '#818cf8']

async function fetchData() {
  loading.value = true
  error.value = false
  try {
    stats.value = await getAnalysisStats({ range: currentRange.value })
  } catch (err) {
    error.value = true
    console.error('获取分析数据失败:', err)
    return
  } finally {
    loading.value = false
  }
  // loading 已设为 false，DOM 会渲染图表容器，等待 DOM 更新后渲染图表
  await nextTick()
  renderCharts()
}

function renderTrendChart() {
  if (!trendRef.value || !stats.value) return
  trendChart.value = echarts.init(trendRef.value)
  trendChart.value.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e5e7eb',
      textStyle: { color: '#1f2937' },
    },
    grid: { top: 30, right: 20, bottom: 40, left: 50 },
    xAxis: {
      type: 'category',
      data: stats.value.trend_data.map((d) => d.date),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
      axisLabel: { color: '#6b7280', fontSize: 11 },
    },
    series: [
      {
        name: '每日岗位数',
        type: 'line',
        smooth: true,
        data: stats.value.trend_data.map((d) => d.jobs),
        itemStyle: { color: '#2563eb' },
        lineStyle: { width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(37, 99, 235, 0.25)' },
            { offset: 1, color: 'rgba(37, 99, 235, 0.02)' },
          ]),
        },
      },
    ],
  })
}

function renderIndustryChart() {
  if (!industryRef.value || !stats.value) return
  industryChart.value = echarts.init(industryRef.value)
  industryChart.value.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#6b7280', fontSize: 12 },
    },
    color: chartColors,
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
        },
        data: stats.value.industry_distribution.map((item) => ({
          name: item.name,
          value: item.value,
        })),
      },
    ],
  })
}

function renderCompanyTypeChart() {
  if (!companyTypeRef.value || !stats.value) return
  companyTypeChart.value = echarts.init(companyTypeRef.value)
  companyTypeChart.value.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      bottom: 10,
      textStyle: { color: '#6b7280', fontSize: 12 },
    },
    color: ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'],
    series: [
      {
        type: 'pie',
        radius: '60%',
        center: ['50%', '42%'],
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: { color: '#6b7280', fontSize: 12 },
        data: stats.value.company_type_distribution.map((item) => ({
          name: item.name,
          value: item.value,
        })),
      },
    ],
  })
}

function renderRegionChart() {
  if (!regionRef.value || !stats.value) return
  regionChart.value = echarts.init(regionRef.value)
  regionChart.value.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 20, right: 20, bottom: 40, left: 80 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
    },
    yAxis: {
      type: 'category',
      data: stats.value.region_distribution.map((d) => d.name).reverse(),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 12 },
    },
    series: [
      {
        type: 'bar',
        data: stats.value.region_distribution.map((d) => d.value).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#2563eb' },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
        barWidth: '60%',
      },
    ],
  })
}

function renderSalaryChart() {
  if (!salaryRef.value || !stats.value) return
  salaryChart.value = echarts.init(salaryRef.value)
  salaryChart.value.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        let html = params[0].name + '<br/>'
        params.forEach((p: any) => {
          html += `${p.marker} ${p.seriesName}: ${formatAvgSalary(p.value)}<br/>`
        })
        return html
      },
    },
    legend: {
      top: 5,
      textStyle: { color: '#6b7280', fontSize: 12 },
    },
    grid: { top: 50, right: 20, bottom: 40, left: 50 },
    xAxis: {
      type: 'category',
      data: stats.value.salary_by_industry.map((d) => d.industry),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#6b7280', fontSize: 11, rotate: 15 },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f3f4f6' } },
      axisLabel: { color: '#6b7280', fontSize: 11 },
    },
    series: [
      {
        name: '平均薪资',
        type: 'bar',
        data: stats.value.salary_by_industry.map((d) => d.avg_salary),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3b82f6' },
            { offset: 1, color: '#93c5fd' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        barWidth: '40%',
      },
    ],
  })
}

function renderCharts() {
  if (!stats.value) return
  // 销毁旧图表
  disposeCharts()
  // 渲染新图表
  renderTrendChart()
  renderIndustryChart()
  renderCompanyTypeChart()
  renderRegionChart()
  renderSalaryChart()
}

function disposeCharts() {
  trendChart.value?.dispose()
  industryChart.value?.dispose()
  companyTypeChart.value?.dispose()
  regionChart.value?.dispose()
  salaryChart.value?.dispose()
}

function handleResize() {
  trendChart.value?.resize()
  industryChart.value?.resize()
  companyTypeChart.value?.resize()
  regionChart.value?.resize()
  salaryChart.value?.resize()
}

function handleRangeChange(value: string) {
  currentRange.value = value
  fetchData()
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  disposeCharts()
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="analysis-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">
          <n-icon size="24" color="#2563eb"><BarChartOutline /></n-icon>
          行业分析
        </h1>
        <p class="page-desc">2027届秋季校园招聘市场动态监测</p>
      </div>
      <div class="header-right">
        <n-space>
          <n-button
            v-for="opt in rangeOptions"
            :key="opt.value"
            :type="currentRange === opt.value ? 'primary' : 'default'"
            size="small"
            @click="handleRangeChange(opt.value)"
          >
            {{ opt.label }}
          </n-button>
          <n-button quaternary size="small" @click="fetchData">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
          </n-button>
        </n-space>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-wrapper">
      <n-spin size="large" />
      <p class="loading-text">正在加载分析数据...</p>
    </div>

    <!-- 加载失败 -->
    <n-empty
      v-else-if="error"
      description="数据加载失败，请稍后重试"
      style="padding: 80px 0"
    >
      <template #extra>
        <n-button type="primary" @click="fetchData">重新加载</n-button>
      </template>
    </n-empty>

    <!-- 分析内容 -->
    <template v-else-if="stats">
      <!-- KPI 指标卡 -->
      <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
        <n-grid-item span="4 m:2 l:1">
          <n-card :bordered="false" class="kpi-card">
            <div class="kpi-content">
              <div class="kpi-icon" style="background: #eff6ff; color: #2563eb">
                <n-icon size="24"><TrendingUpOutline /></n-icon>
              </div>
              <div class="kpi-info">
                <p class="kpi-label">岗位总数</p>
                <p class="kpi-value">{{ formatNumber(stats.total_jobs) }}</p>
              </div>
            </div>
          </n-card>
        </n-grid-item>
        <n-grid-item span="4 m:2 l:1">
          <n-card :bordered="false" class="kpi-card">
            <div class="kpi-content">
              <div class="kpi-icon" style="background: #ecfdf5; color: #10b981">
                <n-icon size="24"><CashOutline /></n-icon>
              </div>
              <div class="kpi-info">
                <p class="kpi-label">平均月薪</p>
                <p class="kpi-value">{{ formatAvgSalary(stats.avg_salary) }}</p>
              </div>
            </div>
          </n-card>
        </n-grid-item>
        <n-grid-item span="4 m:2 l:1">
          <n-card :bordered="false" class="kpi-card">
            <div class="kpi-content">
              <div class="kpi-icon" style="background: #fef3c7; color: #f59e0b">
                <n-icon size="24"><CalendarOutline /></n-icon>
              </div>
              <div class="kpi-info">
                <p class="kpi-label">日均发布</p>
                <p class="kpi-value">{{ formatNumber(stats.daily_avg_jobs) }}</p>
              </div>
            </div>
          </n-card>
        </n-grid-item>
        <n-grid-item span="4 m:2 l:1">
          <n-card :bordered="false" class="kpi-card">
            <div class="kpi-content">
              <div class="kpi-icon" style="background: #f3e8ff; color: #8b5cf6">
                <n-icon size="24"><BusinessOutline /></n-icon>
              </div>
              <div class="kpi-info">
                <p class="kpi-label">活跃行业</p>
                <p class="kpi-value">{{ stats.active_industries }}</p>
              </div>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <!-- 图表区域 -->
      <n-grid cols="s:1 m:2 l:2" :x-gap="16" :y-gap="16" responsive="screen" item-responsive style="margin-top: 16px">
        <!-- 每日岗位发布趋势 -->
        <n-grid-item span="1">
          <n-card :bordered="false" class="chart-card">
            <template #header>
              <div class="chart-header">
                <n-icon size="18" color="#2563eb"><TrendingUpOutline /></n-icon>
                <span>每日岗位发布趋势</span>
              </div>
            </template>
            <div ref="trendRef" class="chart-container" style="height: 300px"></div>
          </n-card>
        </n-grid-item>

        <!-- 行业岗位分布 -->
        <n-grid-item span="1">
          <n-card :bordered="false" class="chart-card">
            <template #header>
              <div class="chart-header">
                <n-icon size="18" color="#2563eb"><PieChartOutline /></n-icon>
                <span>行业岗位分布</span>
              </div>
            </template>
            <div ref="industryRef" class="chart-container" style="height: 300px"></div>
          </n-card>
        </n-grid-item>

        <!-- 企业类型分布 -->
        <n-grid-item span="1">
          <n-card :bordered="false" class="chart-card">
            <template #header>
              <div class="chart-header">
                <n-icon size="18" color="#2563eb"><BusinessOutline /></n-icon>
                <span>企业类型分布</span>
              </div>
            </template>
            <div ref="companyTypeRef" class="chart-container" style="height: 300px"></div>
          </n-card>
        </n-grid-item>

        <!-- 地域岗位分布 -->
        <n-grid-item span="1">
          <n-card :bordered="false" class="chart-card">
            <template #header>
              <div class="chart-header">
                <n-icon size="18" color="#2563eb"><MapOutline /></n-icon>
                <span>地域岗位分布</span>
              </div>
            </template>
            <div ref="regionRef" class="chart-container" style="height: 300px"></div>
          </n-card>
        </n-grid-item>

        <!-- 行业薪资对比 -->
        <n-grid-item span="1">
          <n-card :bordered="false" class="chart-card">
            <template #header>
              <div class="chart-header">
                <n-icon size="18" color="#2563eb"><CashOutline /></n-icon>
                <span>行业薪资对比</span>
              </div>
            </template>
            <div ref="salaryRef" class="chart-container" style="height: 300px"></div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <!-- 头部企业排行榜 -->
      <n-card :bordered="false" class="chart-card" style="margin-top: 16px">
        <template #header>
          <div class="chart-header">
            <n-icon size="18" color="#2563eb"><TrophyOutline /></n-icon>
            <span>头部企业招聘排行榜</span>
          </div>
        </template>
        <div class="ranking-table">
          <div class="ranking-header">
            <span class="col-rank">排名</span>
            <span class="col-company">企业</span>
            <span class="col-industry">行业</span>
            <span class="col-type">类型</span>
            <span class="col-jobs">岗位数</span>
            <span class="col-salary">平均薪资</span>
          </div>
          <div
            v-for="(company, index) in stats.top_companies.slice(0, 15)"
            :key="company.company"
            class="ranking-row"
          >
            <span class="col-rank">
              <span class="rank-badge" :class="`rank-${index + 1 <= 3 ? index + 1 : 'normal'}`">
                {{ index + 1 }}
              </span>
            </span>
            <span class="col-company">{{ company.company }}</span>
            <span class="col-industry">{{ company.industry }}</span>
            <span class="col-type">
              <n-tag size="tiny" round :bordered="false" type="info">{{ company.company_type }}</n-tag>
            </span>
            <span class="col-jobs">{{ formatNumber(company.jobs) }}</span>
            <span class="col-salary">{{ formatAvgSalary(company.salary_avg) }}</span>
          </div>
        </div>
      </n-card>
    </template>
  </div>
</template>

<style scoped>
.analysis-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
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

.loading-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 0;
}

.loading-text {
  margin-top: 16px;
  color: #6b7280;
  font-size: 14px;
}

.kpi-card {
  border-radius: 12px;
}

.kpi-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kpi-label {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 4px;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.chart-card {
  border-radius: 12px;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.chart-container {
  width: 100%;
}

/* 排行榜表格 */
.ranking-table {
  width: 100%;
}

.ranking-header {
  display: grid;
  grid-template-columns: 60px 1fr 1fr 80px 100px 120px;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.ranking-row {
  display: grid;
  grid-template-columns: 60px 1fr 1fr 80px 100px 120px;
  padding: 12px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
  color: #374151;
  align-items: center;
  transition: background 0.2s;
}

.ranking-row:hover {
  background: #f9fafb;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}

.rank-1 {
  background: #fef3c7;
  color: #d97706;
}

.rank-2 {
  background: #f3f4f6;
  color: #6b7280;
}

.rank-3 {
  background: #fed7aa;
  color: #c2410c;
}

.rank-normal {
  background: #eff6ff;
  color: #2563eb;
}

.col-company {
  font-weight: 500;
  color: #1f2937;
}

.col-salary {
  color: #2563eb;
  font-weight: 500;
}

@media (max-width: 768px) {
  .ranking-header,
  .ranking-row {
    grid-template-columns: 40px 1fr 80px 90px;
  }

  .col-industry,
  .col-type {
    display: none;
  }
}
</style>

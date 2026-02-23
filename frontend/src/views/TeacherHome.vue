<template>
  <div class="teacher-home">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-text">
        <h2>欢迎回来，{{ userStore.user?.username }} 老师 👋</h2>
        <p>今天是 {{ currentDate }}，准备好开始今天的教学工作了吗？</p>
      </div>
    </div>

    <!-- 1. 顶部核心指标卡片 (Key Metrics) -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="6" v-for="(item, index) in metricsCards" :key="index">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: item.bg, color: item.color }">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ item.value }}</div>
              <div class="stat-label">{{ item.label }}</div>
              <div class="stat-sub" v-if="item.subLabel">{{ item.subLabel }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 2. 中部可视化图表区 (Visual Analytics) -->
    <el-row :gutter="20" class="charts-row">
      <!-- 左侧：章节掌握度 & 学习趋势 -->
      <el-col :span="16">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>📊 教学概览</span>
              <el-radio-group v-model="chartTab" size="small">
                <el-radio-button label="mastery">章节掌握度</el-radio-button>
                <el-radio-button label="trend">学情趋势</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container" ref="mainChartRef"></div>
        </el-card>
      </el-col>

      <!-- 右侧：能力雷达图 -->
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>🕸️ 全班能力模型</span>
            </div>
          </template>
          <div class="chart-container" ref="radarChartRef"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 3. 底部详细数据区 (Detailed Insights) -->
    <el-row :gutter="20" class="details-row">
      <!-- 全班高频错题知识点 -->
      <el-col :span="24">
        <el-card shadow="hover" class="detail-card">
          <template #header>
            <div class="card-header">
              <span>🔥 全班高频错题知识点</span>
              <el-tag type="danger" effect="plain" size="small">Top 10</el-tag>
            </div>
          </template>
          <el-table :data="dashboardData.details.weaknesses" style="width: 100%" size="default" :stripe="true">
            <el-table-column type="index" label="排名" width="80" align="center">
                <template #default="scope">
                    <span v-if="scope.$index < 3" style="font-size: 16px;">
                        {{ ['🥇', '🥈', '🥉'][scope.$index] }}
                    </span>
                    <span v-else>{{ scope.$index + 1 }}</span>
                </template>
            </el-table-column>
            <el-table-column prop="content" label="知识点内容" min-width="200" show-overflow-tooltip>
              <template #default="scope">
                <span class="weak-point-text" style="font-weight: 600;">{{ scope.row.content }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="source" label="所属章节/小节" min-width="250" show-overflow-tooltip>
                 <template #default="scope">
                    <el-tag size="small" type="info" effect="light">{{ scope.row.source }}</el-tag>
                 </template>
            </el-table-column>
            <el-table-column prop="error_count" label="错误次数" width="120" align="center" sortable>
                 <template #default="scope">
                    <span style="color: #f56c6c; font-weight: bold;">{{ scope.row.error_count }}</span>
                    <span style="color: #909399; font-size: 12px;"> / {{ scope.row.total_attempts }}</span>
                 </template>
            </el-table-column>
            <el-table-column prop="error_rate" label="错误率" width="120" align="center" sortable>
              <template #default="scope">
                <el-progress 
                    :percentage="scope.row.error_rate" 
                    :color="getErrorColor(scope.row.error_rate)"
                    :stroke-width="8"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 快捷入口悬浮球 (Optional) -->
    <div class="quick-fab" @click="$router.push('/chapters')">
        <el-tooltip content="章节/文档管理" placement="left">
            <el-button type="primary" circle size="large" :icon="Reading" class="fab-btn" />
        </el-tooltip>
    </div>

  </div>
</template>

<script setup lang="ts">
import { getDashboardStats } from '@/api/auth'
import { useUserStore } from '@/stores'
import {
    ChatDotRound,
    MagicStick,
    Reading,
    Trophy,
    User
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const currentDate = dayjs().format('YYYY年MM月DD日 dddd')

// Data State
const dashboardData = ref({
  metrics: {
    total_students: 0,
    active_students: 0,
    total_quizzes: 0,
    avg_accuracy: 0,
    ai_interactions: 0,
    ai_quiz_count: 0
  },
  charts: {
    chapter_mastery: [],
    learning_trend: [],
    radar: []
  },
  details: {
    weaknesses: [],
    risk_students: [],
    type_stats: [],
    activities: []
  }
})

// Metrics Cards Configuration
const metricsCards = computed(() => [
  {
    label: '学生总数',
    value: dashboardData.value.metrics.total_students,
    subLabel: '注册学生总数',
    icon: User,
    bg: '#e1f3d8',
    color: '#67c23a'
  },
  {
    label: '总刷题量',
    value: dashboardData.value.metrics.total_quizzes,
    subLabel: `平均正确率: ${dashboardData.value.metrics.avg_accuracy}%`,
    icon: Trophy,
    bg: '#faecd8',
    color: '#e6a23c'
  },
  {
    label: 'AI 辅导交互',
    value: dashboardData.value.metrics.ai_interactions,
    subLabel: '次对话',
    icon: ChatDotRound,
    bg: '#d9ecff',
    color: '#409eff'
  },
  {
    label: 'AI 出题数',
    value: dashboardData.value.metrics.ai_quiz_count,
    subLabel: '累计生成练习',
    icon: MagicStick,
    bg: '#fde2e2',
    color: '#f56c6c'
  }
])

// Chart Refs
const mainChartRef = ref<HTMLElement | null>(null)
const radarChartRef = ref<HTMLElement | null>(null)
let mainChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null

// Chart Tab State
const chartTab = ref('mastery')

const getErrorColor = (rate: number) => {
    if (rate > 80) return '#f56c6c'
    if (rate > 50) return '#e6a23c'
    return '#67c23a'
}

// Fetch Data
const fetchData = async () => {
  try {
    const res = await getDashboardStats()
    dashboardData.value = res
    initCharts()
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error)
    ElMessage.error('获取仪表盘数据失败')
  }
}

// Initialize Charts
const initCharts = () => {
  if (!dashboardData.value) return

  // 1. Main Chart (Mastery or Trend)
  initMainChart()

  // 2. Radar Chart
  if (radarChartRef.value) {
    if (radarChart) radarChart.dispose()
    radarChart = echarts.init(radarChartRef.value)
    
    const radarData = dashboardData.value.charts.radar
    const indicator = radarData.map((item: any) => ({ name: item.name, max: 100 }))
    const values = radarData.map((item: any) => item.value)

    radarChart.setOption({
      tooltip: {},
      radar: {
        indicator: indicator,
        radius: '65%',
        center: ['50%', '50%'],
      },
      series: [{
        name: '全班能力模型',
        type: 'radar',
        data: [{
          value: values,
          name: '平均得分率',
          areaStyle: {
            color: 'rgba(64, 158, 255, 0.2)'
          },
          lineStyle: {
            color: '#409eff'
          },
          itemStyle: {
            color: '#409eff'
          }
        }]
      }]
    })
  }
}

const initMainChart = () => {
  if (!mainChartRef.value) return
  if (mainChart) mainChart.dispose()
  mainChart = echarts.init(mainChartRef.value)

  if (chartTab.value === 'mastery') {
    // Bar Chart for Chapter Mastery
    const data = dashboardData.value.charts.chapter_mastery
    mainChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.map((item: any) => item.name),
        axisLabel: { interval: 0, rotate: 30 }
      },
      yAxis: {
        type: 'value',
        max: 100,
        name: '平均分'
      },
      series: [{
        data: data.map((item: any) => ({
            value: item.value,
            itemStyle: {
                color: (params: any) => {
                    if (params.value < 60) return '#f56c6c'
                    if (params.value < 80) return '#e6a23c'
                    return '#67c23a'
                }
            }
        })),
        type: 'bar',
        barWidth: '40%',
        showBackground: true,
        backgroundStyle: {
            color: 'rgba(180, 180, 180, 0.2)'
        },
        label: {
            show: true,
            position: 'top'
        }
      }]
    })
  } else {
    // Line Chart for Learning Trend
    const data = dashboardData.value.charts.learning_trend
    mainChart.setOption({
      tooltip: {
        trigger: 'axis',
        formatter: function (params: any) {
            let tooltip = `<div>${params[0].axisValue}</div>`;
            params.forEach((item: any) => {
                if (item.seriesName === '当日平均分') {
                    tooltip += `<div><span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${item.color};"></span>${item.seriesName}: ${item.value} (全章节综合)</div>`;
                } else {
                    tooltip += `<div><span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${item.color};"></span>${item.seriesName}: ${item.value}</div>`;
                }
            });
            return tooltip;
        }
      },
      legend: {
        data: ['当日平均分', '全班刷题量'],
        top: 0,
        left: 'center'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '5%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.map((item: any) => item.date)
      },
      yAxis: [
        {
          type: 'value',
          name: '平均分',
          max: 100
        },
        {
          type: 'value',
          name: '刷题量',
          position: 'right',
          minInterval: 1,
          min: 0,
          max: (value: any) => {
             return Math.max(value.max, 50);
          }
        }
      ],
      series: [
        {
          name: '当日平均分',
          type: 'line',
          data: data.map((item: any) => item.score),
          smooth: true,
          lineStyle: { color: '#409eff' },
          areaStyle: {
             color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
               { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
               { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
             ])
          }
        },
        {
          name: '全班刷题量',
          type: 'line',
          yAxisIndex: 1,
          data: data.map((item: any) => item.count),
          smooth: true,
          lineStyle: { color: '#67c23a' }
        }
      ]
    })
  }
}

// Watch for tab change
watch(chartTab, () => {
  nextTick(() => {
    initMainChart()
  })
})

// Resize handler
const handleResize = () => {
  mainChart?.resize()
  radarChart?.resize()
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  mainChart?.dispose()
  radarChart?.dispose()
})
</script>

<style scoped>
.teacher-home {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.welcome-section {
  margin-bottom: 24px;
}

.welcome-text h2 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.welcome-text p {
  color: #909399;
  margin: 0;
}

.metrics-row {
  margin-bottom: 24px;
}

.stat-card {
  height: 100%;
  transition: all 0.3s;
  border: none;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-top: 4px;
}

.stat-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.charts-row {
  margin-bottom: 24px;
}

.chart-card {
  height: 400px;
  display: flex;
  flex-direction: column;
}

.chart-container {
  height: 320px;
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.details-row .detail-card {
  height: 300px;
  overflow: hidden;
}

.weak-point-text {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-feed {
  height: 220px;
  overflow-y: auto;
}

.activity-item {
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-time {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.activity-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.quick-fab {
  position: fixed;
  bottom: 40px;
  right: 40px;
  z-index: 100;
}

.fab-btn {
  width: 60px;
  height: 60px;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}
</style>
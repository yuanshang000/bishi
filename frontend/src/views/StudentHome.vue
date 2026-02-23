<template>
  <div class="student-home">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-text">
        <h2>欢迎回来，{{ userStore.user?.username }} 👋</h2>
        <p>今天是 {{ currentDate }}，开始今天的学习吧！</p>
      </div>
    </div>

    <!-- 1. 核心指标卡片 -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #e1f3d8; color: #67c23a">
              <el-icon><EditPen /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.metrics.total_questions }}</div>
              <div class="stat-label">刷题总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #faecd8; color: #e6a23c">
              <el-icon><Aim /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.metrics.avg_accuracy }}%</div>
              <div class="stat-label">平均正确率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/wrong-questions')" style="cursor: pointer;">
          <div class="stat-content">
            <div class="stat-icon" style="background-color: #fde2e2; color: #f56c6c">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.metrics.pending_wrong }}</div>
              <div class="stat-label">待复习错题</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 2. 可视化图表区 -->
    <el-row :gutter="20" class="charts-row">
      <!-- 左侧：学习趋势 & 最近练习 -->
      <el-col :span="16">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>📈 学习趋势 {{ trendDateRange }}</span>
            </div>
          </template>
          <div class="chart-container" ref="trendChartRef"></div>
        </el-card>

        <el-card shadow="hover" class="list-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>🕒 最近练习记录</span>
              <el-button link type="primary" @click="$router.push('/quiz')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="dashboardData.details.recent_activities.slice(0, 4)" style="width: 100%; font-size: 16px;" :row-style="{ height: '50px' }" :show-header="true">
            <el-table-column prop="time" label="时间" width="160">
              <template #default="scope">
                {{ scope.row.time.slice(5) }}
              </template>
            </el-table-column>
            <el-table-column prop="content" label="内容" show-overflow-tooltip />
            <el-table-column prop="score" label="正确率" width="120" align="right">
              <template #default="scope">
                <span :style="{ color: getScoreColor(scope.row.score), fontWeight: 'bold' }">{{ scope.row.score }}%</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧：能力雷达 & 待强化点 -->
      <el-col :span="8">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>🕸️ 个人能力模型</span>
            </div>
          </template>
          <div class="chart-container" ref="radarChartRef"></div>
        </el-card>

        <el-card shadow="hover" class="list-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <span>💪 待强化知识点</span>
            </div>
          </template>
          <div class="weak-points-list">
            <div v-if="dashboardData.details.weaknesses.length === 0" class="empty-state">
              暂无薄弱点数据，继续加油！
            </div>
            <div v-else v-for="(wp, index) in dashboardData.details.weaknesses" :key="index" class="weak-point-item">
              <div class="wp-content">
                <div class="wp-title">{{ wp.content }}</div>
                <div class="wp-source">{{ wp.source }}</div>
              </div>
              <div class="wp-stat">
                <el-tag type="danger" size="small" effect="plain">错 {{ wp.error_count }} 次</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { getDashboardStats } from '@/api/auth'
import { useUserStore } from '@/stores'
import {
    Aim,
    EditPen,
    Warning
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const currentDate = dayjs().format('YYYY年MM月DD日 dddd')

// Data State
const dashboardData = ref({
  metrics: {
    learning_days: 0,
    total_questions: 0,
    avg_accuracy: 0,
    pending_wrong: 0
  },
  charts: {
    trend: [],
    radar: []
  },
  details: {
    weaknesses: [],
    recent_activities: []
  }
})

// Computed
const trendDateRange = computed(() => {
  const trend = dashboardData.value.charts.trend
  if (trend && trend.length > 0) {
    const start = trend[0].date
    const end = trend[trend.length - 1].date
    return `(${start} ~ ${end})`
  }
  return '(近7天)'
})

// Chart Refs
const trendChartRef = ref<HTMLElement | null>(null)
const radarChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null

const getScoreColor = (score: number) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

// Fetch Data
const fetchData = async () => {
  try {
    const res = await getDashboardStats()
    dashboardData.value = res
    nextTick(() => {
        initCharts()
    })
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error)
    ElMessage.error('获取仪表盘数据失败')
  }
}

// Initialize Charts
const initCharts = () => {
  if (!dashboardData.value) return

  // 1. Trend Chart
  if (trendChartRef.value) {
    if (trendChart) trendChart.dispose()
    trendChart = echarts.init(trendChartRef.value)
    
    const data = dashboardData.value.charts.trend
    trendChart.setOption({
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['正确率', '刷题量'],
        top: 0,
        textStyle: {
          fontSize: 14
        }
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
        data: data.map((item: any) => item.date),
        axisLabel: {
          fontSize: 14
        }
      },
      yAxis: [
        {
          type: 'value',
          name: '正确率',
          max: 100,
          nameTextStyle: {
            fontSize: 14,
            padding: [0, 0, 0, 10]
          },
          axisLabel: {
            fontSize: 14
          }
        },
        {
          type: 'value',
          name: '刷题量',
          position: 'right',
          minInterval: 1,
          nameTextStyle: {
            fontSize: 14,
            padding: [0, 0, 0, 10]
          },
          axisLabel: {
            fontSize: 14
          }
        }
      ],
      series: [
        {
          name: '正确率',
          type: 'line',
          data: data.map((item: any) => item.score),
          smooth: true,
          lineStyle: { color: '#409eff', width: 3 },
          symbolSize: 8,
          areaStyle: {
             color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
               { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
               { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
             ])
          }
        },
        {
          name: '刷题量',
          type: 'line',
          yAxisIndex: 1,
          data: data.map((item: any) => item.count),
          smooth: true,
          lineStyle: { color: '#67c23a', width: 3 },
          symbolSize: 8
        }
      ]
    })
  }

  // 2. Radar Chart
  if (radarChartRef.value) {
    if (radarChart) radarChart.dispose()
    radarChart = echarts.init(radarChartRef.value)
    
    const radarData = dashboardData.value.charts.radar
    const indicator = radarData.map((item: any) => ({ name: item.name, max: 100 }))
    const values = radarData.map((item: any) => item.value)

    // Ensure at least 3 indicators for radar chart to look good
    // If empty or less than 3, we might want to handle gracefully, but backend ensures 3 keys
    
    radarChart.setOption({
      tooltip: {},
      radar: {
        indicator: indicator,
        radius: '65%',
        center: ['50%', '50%'],
      },
      series: [{
        name: '能力模型',
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

// Resize handler
const handleResize = () => {
  trendChart?.resize()
  radarChart?.resize()
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  radarChart?.dispose()
})
</script>

<style scoped>
.student-home {
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

.chart-card, .list-card {
  margin-bottom: 0; 
}

.chart-container {
  height: 250px;
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.weak-points-list {
  max-height: 250px;
  overflow-y: auto;
}

.weak-point-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.weak-point-item:last-child {
  border-bottom: none;
}

.wp-content {
  flex: 1;
  overflow: hidden;
  margin-right: 10px;
}

.wp-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wp-source {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-state {
  text-align: center;
  color: #909399;
  padding: 20px 0;
  font-size: 13px;
}
</style>
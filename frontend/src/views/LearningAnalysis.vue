<template>
  <div class="learning-analysis-container">
    <!-- 加载弹窗 -->
    <el-dialog
      v-model="loading"
      :show-close="false"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      width="450px"
      align-center
      class="loading-dialog"
    >
      <div class="loading-content">
        <el-icon class="loading-icon" :size="60" color="#409EFF">
          <Loading />
        </el-icon>
        <h3>AI正在分析中...</h3>
        <p>正在分析你的学习数据，生成个性化学情报告</p>
        <el-progress :percentage="100" :indeterminate="true" :duration="3" />
      </div>
    </el-dialog>

    <el-card class="header-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="24" color="#409EFF"><TrendCharts /></el-icon>
            <span class="header-title">AI 学情分析</span>
          </div>
          <el-button
            type="primary"
            :loading="loading"
            @click="analyzeMyLearning"
            :icon="Refresh"
          >
            {{ loading ? '分析中...' : '重新分析' }}
          </el-button>
        </div>
      </template>

      <div v-if="!analyzed" class="empty-state">
        <el-empty description="正在加载你的学习数据...">
          <template #image>
            <el-icon :size="100" color="#909399"><DataAnalysis /></el-icon>
          </template>
        </el-empty>
      </div>

      <div v-else-if="analysisData">
        <!-- 分析报告 -->
        <el-alert
          v-if="analysisData.data.status === 'no_data'"
          title="暂无数据"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <p>{{ analysisData.report }}</p>
            <el-button type="primary" @click="$router.push('/quiz')" style="margin-top: 10px">
              去做练习
            </el-button>
          </template>
        </el-alert>

        <div v-else>
          <!-- 整体统计卡片 -->
          <el-row :gutter="20" class="stats-row">
            <el-col :xs="24" :sm="12" :md="6">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-content">
                  <el-icon :size="32" color="#409EFF"><Document /></el-icon>
                  <div class="stat-info">
                    <div class="stat-value">{{ analysisData.data.total_records }}</div>
                    <div class="stat-label">完成练习</div>
                  </div>
                </div>
              </el-card>
            </el-col>

            <el-col :xs="24" :sm="12" :md="6">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-content">
                  <el-icon :size="32" color="#67C23A"><Medal /></el-icon>
                  <div class="stat-info">
                    <div class="stat-value">{{ analysisData.data.average_score.toFixed(1) }}</div>
                    <div class="stat-label">平均分</div>
                  </div>
                </div>
              </el-card>
            </el-col>

            <el-col :xs="24" :sm="12" :md="6">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-content">
                  <el-icon :size="32" :color="getTrendColor(analysisData.data.trend)">
                    <component :is="getTrendIcon(analysisData.data.trend)" />
                  </el-icon>
                  <div class="stat-info">
                    <div class="stat-value">{{ analysisData.data.recent_average.toFixed(1) }}</div>
                    <div class="stat-label">最近表现</div>
                  </div>
                </div>
              </el-card>
            </el-col>

            <el-col :xs="24" :sm="12" :md="6">
              <el-card shadow="hover" class="stat-card">
                <div class="stat-content">
                  <el-icon :size="32" color="#E6A23C"><Warning /></el-icon>
                  <div class="stat-info">
                    <div class="stat-value">{{ analysisData.data.weak_points.length }}</div>
                    <div class="stat-label">薄弱知识点</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 图表分析区域 -->
          <el-row :gutter="20" class="charts-row" style="margin-top: 20px;">
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover" class="chart-card">
                <template #header>
                  <div class="card-header">
                    <span class="header-title">章节掌握度 (Chapter Mastery)</span>
                  </div>
                </template>
                <div ref="radarChartRef" class="chart-container"></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :lg="12">
              <el-card shadow="hover" class="chart-card">
                <template #header>
                  <div class="card-header">
                    <span class="header-title">薄弱点分布 (Weak Points Distribution)</span>
                  </div>
                </template>
                <div ref="barChartRef" class="chart-container"></div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 目标完成情况 -->
          <el-card 
            class="goal-progress-card" 
            :class="{ 'fullscreen-mode': isFullscreen }"
            shadow="hover" 
            style="margin-top: 20px;"
          >
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon :size="24" color="#409EFF"><Medal /></el-icon>
                  <span class="header-title">目标完成情况 (Goal Completion)</span>
                </div>
                <el-button @click="toggleFullscreen" :type="isFullscreen ? 'primary' : 'default'" plain size="small">
                  <el-icon style="margin-right: 5px"><FullScreen /></el-icon>
                  {{ isFullscreen ? '退出全屏' : '全屏查看' }}
                </el-button>
              </div>
            </template>
            
            <div class="goal-list">
              <el-collapse v-if="goalProgress.length > 0">
                <el-collapse-item v-for="chapter in goalProgress" :key="chapter.id" :name="chapter.id">
                  <template #title>
                    <div class="chapter-title">
                      <span class="chapter-number">第 {{ chapter.chapter_number }} 章</span>
                      <span class="chapter-name">{{ chapter.title }}</span>
                    </div>
                  </template>
                  
                  <div v-for="section in chapter.sections" :key="section.id" class="section-block">
                    <h4 class="section-title">{{ section.title }}</h4>
                    
                    <div class="subsection-list">
                      <div v-for="sub in section.subsections" :key="sub.id" class="subsection-item">
                        <div class="subsection-info">
                          <div class="subsection-header">
                            <span class="subsection-title">{{ sub.title }}</span>
                            <el-tag :type="sub.is_passed ? 'success' : 'warning'" effect="dark" size="large">
                              {{ sub.is_passed ? '已达标' : '未达标' }}
                            </el-tag>
                          </div>
                          <div class="subsection-content">{{ sub.content }}</div>
                          <div class="subsection-metrics">
                            <div class="metric">
                              <span class="label">平均得分:</span>
                              <span class="value" :style="{ color: getScoreColor(sub.average_score) }">{{ sub.average_score }}</span>
                            </div>
                            <div class="metric">
                              <span class="label">及格分:</span>
                              <span class="value">{{ sub.passing_score }}</span>
                            </div>
                            <div class="metric" v-if="sub.weight">
                              <span class="label">权重:</span>
                              <span class="value">{{ sub.weight }}</span>
                            </div>
                            <div class="metric">
                              <span class="label">练习次数:</span>
                              <span class="value">{{ sub.practice_count }}</span>
                            </div>
                          </div>
                        </div>
                        <div class="subsection-progress">
                          <el-progress 
                            type="dashboard" 
                            :percentage="Math.min(100, (sub.average_score / 100) * 100)" 
                            :color="getScoreColor(sub.average_score)"
                            :width="isFullscreen ? 120 : 80"
                            :stroke-width="isFullscreen ? 10 : 6"
                          >
                            <template #default="{ percentage }">
                              <span class="progress-score">{{ sub.average_score }}</span>
                              <span class="progress-label">分</span>
                            </template>
                          </el-progress>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
              <el-empty v-else description="暂无目标数据" />
            </div>
          </el-card>

          <!-- 趋势提示 -->
          <el-alert
            :title="analysisData.data.trend_text"
            :type="getTrendType(analysisData.data.trend)"
            :closable="false"
            show-icon
            style="margin: 20px 0"
          />

          <!-- 薄弱知识点详情 -->
          <el-card
            class="weak-points-card"
            shadow="hover"
          >
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon><Warning /></el-icon>
                  <span>薄弱知识点详情 (未达标小节)</span>
                </div>
                <el-button
                  type="primary"
                  @click="goToComprehensivePractice"
                  :icon="Edit"
                  :disabled="!analysisData.data.has_weak_points"
                >
                  去推荐训练
                </el-button>
              </div>
            </template>

            <div v-if="!analysisData.data.has_weak_points || analysisData.data.weak_points.length === 0" class="empty-weak-points">
                <el-empty description="太棒了！所有已练习小节平均分均≥60分" :image-size="100">
                    <template #image>
                        <el-icon :size="100" color="#67C23A"><Medal /></el-icon>
                    </template>
                </el-empty>
            </div>

            <el-table v-else :data="analysisData.data.weak_points" stripe style="width: 100%">
              <!-- 展开行：显示具体的薄弱知识点 -->
              <el-table-column type="expand">
                <template #default="{ row }">
                  <div style="padding: 10px 20px; background-color: #f8f9fa;">
                    <h4 style="margin-top: 0; margin-bottom: 10px; color: #606266;">
                      <el-icon><List /></el-icon> 具体薄弱点 (Top 5)
                    </h4>
                    <el-table :data="row.weak_details" border size="small">
                       <el-table-column prop="knowledge_point_id" label="内容" min-width="180">
                           <template #default="scope">
                               <span style="font-weight: bold;">{{ scope.row.knowledge_point_id }}</span>
                               <el-tag size="small" style="margin-left: 5px">{{ scope.row.type }}</el-tag>
                           </template>
                       </el-table-column>
                       <el-table-column prop="error_count" label="错误次数" width="100" align="center" />
                       <el-table-column prop="accuracy" label="正确率" width="100" align="center">
                           <template #default="scope">
                               <span :style="{ color: getScoreColor(scope.row.accuracy) }">{{ scope.row.accuracy }}%</span>
                           </template>
                       </el-table-column>
                       <el-table-column prop="total_attempts" label="练习总数" width="100" align="center" />
                    </el-table>
                    <div style="margin-top: 10px; color: #E6A23C;">
                        <strong>💡 强化建议：</strong> {{ row.suggestion }}
                    </div>
                  </div>
                </template>
              </el-table-column>

              <el-table-column prop="knowledge_point_id" label="未达标小节" min-width="200">
                  <template #default="{ row }">
                      <span style="font-weight: bold; font-size: 15px;">{{ row.knowledge_point_id }}</span>
                  </template>
              </el-table-column>
              
              <el-table-column label="小节平均分" width="120" align="center">
                <template #default="{ row }">
                  <span v-if="row.average_score !== null" :style="{ color: getScoreColor(row.average_score) }">
                    {{ row.average_score }} 分
                  </span>
                  <span v-else style="color: #909399">-</span>
                </template>
              </el-table-column>

              <el-table-column label="薄弱点总数" width="120" align="center">
                  <template #default="{ row }">
                      <el-tag type="danger">{{ row.weak_details ? row.weak_details.length : 0 }} 个</el-tag>
                  </template>
              </el-table-column>

              <el-table-column label="状态" width="120" align="center">
                <template #default="{ row }">
                  <el-tag :type="getSeverityType(row.severity)">
                    {{ row.severity_text || getSeverityText(row.severity) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 详细报告 -->
          <el-card class="report-card" shadow="hover" style="margin-top: 20px;">
            <template #header>
              <div class="card-header">
                <el-icon><Document /></el-icon>
                <span>详细分析报告</span>
              </div>
            </template>
            <div class="report-content">
              <pre>{{ analysisData.report }}</pre>
            </div>
          </el-card>

          <!-- 综合练习答题界面 -->
          <el-card v-if="currentQuiz" class="quiz-card" shadow="hover" style="margin-top: 20px">
            <template #header>
              <div class="card-header">
                <div class="header-left">
                  <el-icon><Edit /></el-icon>
                  <span>推荐训练 - 共{{ questions.length }}题</span>
                </div>
                <el-button size="small" @click="cancelQuiz">取消</el-button>
              </div>
            </template>

            <div v-for="(q, index) in questions" :key="index" class="question-item">
              <h4 class="question-title">
                <span class="question-number">{{ index + 1 }}.</span>
                <el-tag :type="getQuizTypeTagType(q.quiz_type)" size="small" style="margin-left: 10px">
                  {{ getQuizTypeLabel(q.quiz_type) }}
                </el-tag>
                <span style="margin-left: 10px">{{ q.question_text || q.question || q.topic }}</span>
              </h4>

              <!-- 听力理解题 -->
              <div v-if="q.quiz_type === 'listening'" class="listening-question">
                <div v-if="q.audio_text" class="audio-text-box">
                  <h5>听力材料：</h5>
                  <p>{{ q.audio_text }}</p>
                </div>
                <el-radio-group v-model="userAnswers[index]" class="answer-group">
                  <el-radio
                    v-for="(optText, optKey) in q.options"
                    :key="optKey"
                    :label="optKey"
                    class="answer-option"
                  >
                    <span class="option-key">{{ optKey }}.</span>
                    <span class="option-text">{{ optText }}</span>
                  </el-radio>
                </el-radio-group>
              </div>

              <!-- 阅读理解题 -->
              <div v-if="q.quiz_type === 'reading'" class="reading-question">
                <div class="passage-box">
                  <h5>阅读材料：</h5>
                  <p>{{ q.passage }}</p>
                </div>
                <el-radio-group v-model="userAnswers[index]" class="answer-group">
                  <el-radio
                    v-for="(optText, optKey) in q.options"
                    :key="optKey"
                    :label="optKey"
                    class="answer-option"
                  >
                    <span class="option-key">{{ optKey }}.</span>
                    <span class="option-text">{{ optText }}</span>
                  </el-radio>
                </el-radio-group>
              </div>

              <!-- 翻译题 -->
              <div v-if="q.quiz_type === 'translation'" class="translation-question">
                <div v-if="q.key_points && q.key_points.length > 0" class="key-points-box">
                  <h5>翻译要点：</h5>
                  <ul>
                    <li v-for="(point, i) in q.key_points" :key="i">{{ point }}</li>
                  </ul>
                </div>
                <el-input
                  v-model="userAnswers[index]"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入你的翻译..."
                />
              </div>

              <!-- 写作题 -->
              <div v-if="q.quiz_type === 'writing'" class="writing-question">
                <div class="writing-requirements">
                  <h5>写作要求：</h5>
                  <ul>
                    <li v-for="(req, i) in q.requirements" :key="i">{{ req }}</li>
                  </ul>
                  <p><strong>字数要求：</strong>{{ q.word_count }}</p>
                </div>
                <el-input
                  v-model="userAnswers[index]"
                  type="textarea"
                  :rows="10"
                  placeholder="请在此处写作..."
                />
              </div>
            </div>

            <div style="text-align: center; margin-top: 30px;">
              <el-button type="primary" size="large" @click="handleSubmitQuiz" :loading="submitting">
                提交答案
              </el-button>
              <el-button size="large" @click="cancelQuiz">
                取消
              </el-button>
            </div>
          </el-card>

          <!-- 结果对话框 -->
          <el-dialog v-model="showResult" title="练习结果" width="800px" :close-on-click-modal="false">
            <el-result
              :icon="result.accuracy >= 60 ? 'success' : 'warning'"
              :title="`得分: ${result.score?.toFixed(1) || 0}`"
            >
              <template #sub-title>
                <div class="result-stats">
                  <div class="stat-item">
                    <span class="stat-label">正确率</span>
                    <span class="stat-value">{{ result.accuracy?.toFixed(1) || 0 }}%</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">正确题数</span>
                    <span class="stat-value">{{ result.correct_count }} / {{ result.total_count }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">错题数</span>
                    <span class="stat-value error">{{ result.wrong_count || 0 }}</span>
                  </div>
                </div>
              </template>
            </el-result>

            <template #footer>
              <el-button type="primary" @click="() => { showResult = false; currentQuiz = null }">关闭</el-button>
            </template>
          </el-dialog>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { getGoalProgress, getMyLearningAnalysis, submitQuiz } from '@/api'
import type { AIAnalysisResult } from '@/types'
import {
    Bottom,
    DataAnalysis,
    Document,
    Edit,
    FullScreen,
    List,
    Loading,
    Medal,
    Minus,
    Refresh,
    Top,
    TrendCharts,
    Warning
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { ElMessage, ElNotification } from 'element-plus'
import { nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const loading = ref(false)
const analyzed = ref(false)
const analysisData = ref<AIAnalysisResult | null>(null)
const goalProgress = ref<any[]>([])
const isFullscreen = ref(false)
const radarChartRef = ref<HTMLElement | null>(null)
const barChartRef = ref<HTMLElement | null>(null)
let radarChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null

// 切换全屏模式
const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  // 等待DOM更新后重绘图表
  setTimeout(() => {
    radarChart?.resize()
    barChart?.resize()
  }, 300)
}

// 初始化图表
const initCharts = () => {
  if (!radarChartRef.value || !barChartRef.value) return
  
  // 1. 章节掌握度雷达图
  radarChart = echarts.init(radarChartRef.value)
  const chapterNames = goalProgress.value.map(c => `第${c.chapter_number}章`)
  const chapterScores = goalProgress.value.map(c => {
    // 计算该章节所有小节的平均分
    let totalScore = 0
    let count = 0
    c.sections?.forEach((s: any) => {
      s.subsections?.forEach((sub: any) => {
        totalScore += sub.current_score || 0
        count++
      })
    })
    return count > 0 ? (totalScore / count).toFixed(1) : 0
  })

  radarChart.setOption({
    tooltip: {
        confine: true, // 限制在图表容器内
        appendToBody: true // 将 tooltip 插入到 body 元素，避免被父容器遮挡
    },
    radar: {
      indicator: chapterNames.map(name => ({ name, max: 100 })),
      radius: '65%'
    },
    series: [{
      name: '章节掌握度',
      type: 'radar',
      data: [
        {
          value: chapterScores,
          name: '平均得分',
          areaStyle: {
            color: 'rgba(64, 158, 255, 0.2)'
          },
          lineStyle: {
            color: '#409EFF'
          },
          itemStyle: {
            color: '#409EFF'
          }
        }
      ]
    }]
  })

  // 2. 薄弱点分布 (基于小节掌握程度)
  barChart = echarts.init(barChartRef.value)
  const subsectionMastery = analysisData.value?.data.subsection_mastery || []
  
  // 显示全部数据（移除 slice(0, 20)），让滚动条来控制显示数量
  const displayData = subsectionMastery
  
  const yAxisData = displayData.map((item: any) => {
      // 构建富文本标签
      return {
          value: item.title, // 只显示标题，不带序号
          textStyle: {
              rich: {
                  chapter: {
                      color: '#909399',
                      fontSize: 10,
                      align: 'right',
                      padding: [0, 4, 0, 0]
                  },
                  title: {
                      color: '#606266',
                      fontSize: 12
                  }
              }
          },
          // 这里的 value 是给 echarts 内部用的，formatter 里可以拿到
          chapter_info: `第${item.chapter_number}章` 
      }
  })
  
  const seriesData = displayData.map((item: any) => ({
    value: item.has_data ? item.average_score : 0,
    itemStyle: {
       // 根据分数设置颜色：<60红色，60-80黄色，>=80绿色
       color: !item.has_data ? '#DCDFE6' : (item.average_score < 60 ? '#F56C6C' : (item.average_score < 80 ? '#E6A23C' : '#67C23A'))
    },
    // 将完整信息存入 data 中，供 tooltip 使用
    customInfo: {
        full_title: `第${item.chapter_number}章 - ${item.title}`,
        has_data: item.has_data,
        practice_count: item.practice_count,
        average_score: item.average_score
    }
  }))

  // 计算每行的高度和总高度
  const barHeight = 40; // 每行高度
  const totalHeight = displayData.length * barHeight;
  
  // 如果容器有style属性，设置高度；或者我们可以在dataZoom里控制视口大小
  // 这里我们通过dataZoom控制每次显示的数量，比如每次显示10个
  const viewCount = 10;
  const startPercent = 0;
  const endPercent = Math.min(100, (viewCount / displayData.length) * 100);

  barChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      confine: true, // 限制在图表容器内
      appendToBody: true, // 将 tooltip 插入到 body 元素，避免被父容器遮挡
      formatter: (params: any) => {
        const data = params[0].data
        const info = data.customInfo
        if (!info.has_data) return `${info.full_title}<br/>状态: 还没有做题数据`
        return `${info.full_title}<br/>平均分: ${info.average_score} 分<br/>练习次数: ${info.practice_count} 次`
      }
    },
    grid: {
      left: '3%',
      right: '12%',
      bottom: '3%',
      containLabel: true
    },
    dataZoom: [
      {
        type: 'slider',
        yAxisIndex: 0,
        start: 0,
        end: endPercent, // 默认显示前10个
        zoomLock: true, // 锁定缩放，只能滚动
        showDetail: false,
        handleSize: '0%', // 隐藏手柄，看起来像纯滚动条
        width: 20,
        right: 10,
        brushSelect: false
      },
      {
        type: 'inside',
        yAxisIndex: 0,
        start: 0,
        end: endPercent,
        zoomOnMouseWheel: false, // 禁止鼠标滚轮缩放
        moveOnMouseWheel: true, // 允许鼠标滚轮移动
        moveOnMouseMove: true
      }
    ],
    xAxis: {
      type: 'value',
      name: '平均得分',
      max: 100,
      interval: 10, // 设置刻度间隔为10，虽然主要关注60/80/90/100，但均匀间隔更好看
      // 或者使用 splitLine 自定义关键刻度线颜色
      splitLine: {
          lineStyle: {
              color: (params: any) => {
                  if (params.value === 60) return '#F56C6C'; // 红色警戒线
                  if (params.value === 80) return '#E6A23C'; // 黄色良好线
                  if (params.value === 90) return '#67C23A'; // 绿色优秀线
                  return '#E4E7ED'; // 默认颜色
              },
              width: (params: any) => {
                  return [60, 80, 90].includes(params.value) ? 2 : 1; // 关键线加粗
              },
              type: (params: any) => {
                  return [60, 80, 90].includes(params.value) ? 'dashed' : 'solid'; // 关键线虚线
              }
          }
      },
      axisLabel: {
           formatter: (value: number) => {
               // 只显示关键刻度
               if ([0, 60, 80, 90, 100].includes(value)) {
                   return value.toString();
               }
               return '';
           }
       }
    },
    yAxis: {
      type: 'category',
      data: yAxisData.map((d: any) => d.value), // echarts category axis expects strings
      inverse: true,
      axisLabel: {
        interval: 0,
        width: 150, // Increase width for labels
        overflow: 'truncate',
        formatter: (value: string, index: number) => {
            const item = displayData[index];
            // 显示格式：[第X章] 标题
            return `{chapter|第${item.chapter_number}章} {title|${value}}`;
        },
        rich: {
            chapter: {
                color: '#909399',
                fontSize: 10,
                backgroundColor: '#f4f4f5',
                padding: [2, 4],
                borderRadius: 2
            },
            title: {
                color: '#606266',
                fontSize: 12,
                padding: [0, 0, 0, 5]
            }
        }
      }
    },
    series: [
      {
        name: '平均得分',
        type: 'bar',
        data: seriesData,
        barWidth: 20, // 固定柱子宽度
        label: {
            show: true,
            position: 'right',
            formatter: (params: any) => {
                const item = displayData[params.dataIndex]
                return item.has_data ? `${item.average_score}` : '无数据'
            },
            color: '#606266'
        }
      }
    ]
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    radarChart?.resize()
    barChart?.resize()
  })
}


// 综合练习相关
const generatingQuiz = ref(false)
const submitting = ref(false)
const currentQuiz = ref<any>(null)
const questions = ref<any[]>([])
const userAnswers = ref<any[]>([])
const showResult = ref(false)
const result = ref<any>({})

// 页面加载时自动分析
onMounted(() => {
  analyzeMyLearning()
})

// 分析学习情况
const analyzeMyLearning = async () => {
  loading.value = true
  try {
    const [res, progressRes] = await Promise.all([
      getMyLearningAnalysis(),
      getGoalProgress()
    ])
    
    // res 的结构是 { success, report, data }
    analysisData.value = res  // 存储整个响应
    
    if (progressRes.success) {
      goalProgress.value = progressRes.data
    }
    
    analyzed.value = true
    
    nextTick(() => {
      initCharts()
    })

    if (res.data?.status === 'success') {
      ElNotification({
        title: '✅ 分析完成',
        message: `已完成学情分析！共分析了 ${res.data.total_records} 条学习记录`,
        type: 'success',
        duration: 3000
      })
    } else if (res.data?.status === 'no_data') {
      ElNotification({
        title: 'ℹ️ 暂无数据',
        message: '还没有学习记录哦，快去做练习吧！',
        type: 'info',
        duration: 3000
      })
    } else {
      ElMessage.info(res.report || '分析完成')
    }
  } catch (error: any) {
    ElNotification({
      title: '❌ 分析失败',
      message: error.response?.data?.detail || '分析失败，请稍后重试',
      type: 'error',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

// 跳转到综合训练
const goToComprehensivePractice = () => {
  if (!analysisData.value?.data?.weak_points || analysisData.value.data.weak_points.length === 0) {
    ElMessage.warning('没有薄弱知识点数据')
    return
  }

  // 跳转到练习中心，并自动选择综合练习模式
  router.push({
    path: '/quiz',
    query: {
      mode: 'comprehensive'
    }
  })

  ElNotification({
    title: '💡 提示',
    message: '已跳转到推荐训练，请选择题型开始练习',
    type: 'info',
    duration: 2500
  })
}

// 提交答题
const handleSubmitQuiz = async () => {
  // 检查是否所有题目都已作答
  const hasEmpty = userAnswers.value.some((ans) => {
    return !ans || (typeof ans === 'string' && ans.trim() === '')
  })

  if (hasEmpty) {
    ElMessage.warning('请完成所有题目后再提交')
    return
  }

  submitting.value = true
  ElMessage.info({
    message: '正在提交答案，请稍候...',
    duration: 0,
    showClose: false
  })

  try {
    // 调用后端API提交答案
    const res: any = await submitQuiz({
      quiz_id: currentQuiz.value.id,
      user_answers: userAnswers.value
    })

    ElMessage.closeAll()

    result.value = res
    showResult.value = true

    ElNotification({
      title: res.accuracy >= 60 ? '🎉 完成练习' : '💪 继续加油',
      message: `得分: ${res.score.toFixed(1)}分 | 正确率: ${res.accuracy.toFixed(1)}%`,
      type: res.accuracy >= 60 ? 'success' : 'warning',
      duration: 3000
    })

    // 重新分析学习情况，更新薄弱点数据
    await analyzeMyLearning()
  } catch (error: any) {
    ElMessage.closeAll()
    console.error('Submit quiz error:', error)
    ElNotification({
      title: '❌ 提交失败',
      message: error.response?.data?.detail || error.message || '提交失败，请稍后重试',
      type: 'error',
      duration: 3000
    })
  } finally {
    submitting.value = false
  }
}

// 取消答题
const cancelQuiz = () => {
  currentQuiz.value = null
  questions.value = []
  userAnswers.value = []
}

// 获取题型标签类型
const getQuizTypeTagType = (type: string) => {
  const types: any = {
    listening: 'primary',
    reading: 'success',
    translation: 'warning',
    writing: 'danger'
  }
  return types[type] || ''
}

// 获取题型标签文本
const getQuizTypeLabel = (type: string) => {
  const labels: any = {
    listening: '听力理解',
    reading: '阅读理解',
    translation: '翻译练习',
    writing: '写作练习'
  }
  return labels[type] || type
}

// 获取趋势图标
const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'improving':
      return Top
    case 'declining':
      return Bottom
    default:
      return Minus
  }
}

// 获取趋势颜色
const getTrendColor = (trend: string) => {
  switch (trend) {
    case 'improving':
      return '#67C23A'
    case 'declining':
      return '#F56C6C'
    default:
      return '#909399'
  }
}

// 获取趋势类型
const getTrendType = (trend: string): 'success' | 'warning' | 'info' => {
  switch (trend) {
    case 'improving':
      return 'success'
    case 'declining':
      return 'warning'
    default:
      return 'info'
  }
}

// 获取严重程度类型
const getSeverityType = (severity: string): 'danger' | 'warning' | 'success' => {
  switch (severity) {
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    default:
      return 'success'
  }
}

// 获取严重程度文本
const getSeverityText = (severity: string): string => {
  switch (severity) {
    case 'high':
      return '严重'
    case 'medium':
      return '中等'
    default:
      return '轻微'
  }
}

// 获取分数颜色
const getScoreColor = (score: number): string => {
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
}
</script>

<style scoped>
.learning-analysis-container {
  padding: 20px;
  position: relative;
  /* 整体字体调大 */
  font-size: 16px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.header-title {
  font-size: 20px; /* 大字体 */
  font-weight: bold;
}

.stat-value {
  font-size: 28px; /* 大字体 */
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 16px; /* 大字体 */
  color: #606266;
  margin-top: 5px;
}

.chapter-number {
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
  margin-right: 10px;
}

.chapter-name {
  font-size: 18px;
  font-weight: bold;
}

.section-title {
  font-size: 18px;
  margin: 15px 0;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}

.subsection-title {
  font-size: 18px;
  font-weight: 600;
}

.subsection-content {
  font-size: 16px;
  color: #606266;
  margin: 10px 0;
}

.metric .label {
  font-size: 15px;
  color: #909399;
}

.metric .value {
  font-size: 16px;
  font-weight: 600;
  margin-left: 5px;
}

/* 全屏模式下的样式增强 */
.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  margin: 0 !important;
  border-radius: 0;
  overflow-y: auto;
  padding: 20px;
}

.fullscreen-mode .chapter-name,
.fullscreen-mode .section-title,
.fullscreen-mode .subsection-title {
  font-size: 22px; /* 全屏模式下更大 */
}

.fullscreen-mode .subsection-content {
  font-size: 18px;
}

/* 高对比度颜色 */
.pass {
  color: #67C23A;
  font-weight: bold;
}

.fail {
  color: #F56C6C;
  font-weight: bold;
}

/* 加载弹窗样式 */
:deep(.loading-dialog) {
  border-radius: 12px;
}

:deep(.loading-dialog .el-dialog__header) {
  display: none;
}

:deep(.loading-dialog .el-dialog__body) {
  padding: 0;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 60px;
}

.loading-icon {
  margin-bottom: 20px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-content h3 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.loading-content p {
  margin: 0 0 20px 0;
  color: #909399;
  font-size: 14px;
}

.loading-content .el-progress {
  width: 100%;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  height: 100%;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.report-card {
  margin-bottom: 20px;
}

.report-content {
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.report-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}

.weak-points-card {
  margin-bottom: 20px;
}

/* 答题界面样式 */
.quiz-card {
  margin-top: 20px;
}

.question-item {
  margin-bottom: 40px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.question-title {
  margin-bottom: 15px;
  font-size: 16px;
  color: #303133;
  display: flex;
  align-items: center;
}

.question-number {
  display: inline-block;
  min-width: 30px;
  font-weight: bold;
  color: #409EFF;
}

.answer-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.answer-option {
  margin-bottom: 0;
  padding: 12px 15px;
  background: white;
  border: 1.5px solid #DCDFE6;
  border-radius: 4px;
  transition: all 0.3s;
}

.answer-option:hover {
  border-color: #409EFF;
  background: #f0f9ff;
}

.option-key {
  display: inline-block;
  min-width: 28px;
  font-weight: 600;
  color: #409EFF;
  font-size: 15px;
}

.option-text {
  margin-left: 8px;
  line-height: 1.6;
  color: #303133;
}

.audio-text-box,
.passage-box {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 15px;
}

.audio-text-box h5,
.passage-box h5 {
  margin: 0 0 10px 0;
  color: #409EFF;
  font-weight: bold;
}

.audio-text-box p,
.passage-box p {
  line-height: 1.8;
  color: #606266;
  margin: 0;
}

.key-points-box {
  padding: 12px;
  background: #fff3e0;
  border-radius: 4px;
  border-left: 3px solid #E6A23C;
  margin-bottom: 15px;
}

.key-points-box h5 {
  margin: 0 0 8px 0;
  color: #E6A23C;
  font-weight: bold;
}

.key-points-box ul {
  margin: 0;
  padding-left: 20px;
}

.key-points-box li {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 5px;
}

.writing-requirements {
  padding: 15px;
  background: #f0f9ff;
  border-radius: 4px;
  border-left: 3px solid #409EFF;
  margin-bottom: 15px;
}

.writing-requirements h5 {
  margin: 0 0 10px 0;
  color: #409EFF;
  font-weight: bold;
}

.writing-requirements ul {
  margin: 10px 0;
  padding-left: 20px;
}

.writing-requirements li {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 5px;
}

.writing-requirements p {
  margin: 8px 0;
  color: #606266;
}

.result-stats {
  display: flex;
  justify-content: space-around;
  margin: 20px 0;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  color: #909399;
  font-size: 14px;
  margin-bottom: 5px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-value.error {
  color: #F56C6C;
}

@media (max-width: 768px) {
  .stat-card {
    margin-bottom: 10px;
  }

  .stats-row {
    margin-bottom: 10px;
  }
}

/* 目标完成情况列表样式 */
.goal-list {
  margin-top: 10px;
}

.chapter-title {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 16px;
  font-weight: 600;
}

.chapter-number {
  color: #409EFF;
  font-weight: bold;
}

.section-block {
  margin-bottom: 20px;
  padding-left: 20px;
}

.section-title {
  font-size: 15px;
  color: #303133;
  margin: 15px 0 10px;
  border-left: 4px solid #409EFF;
  padding-left: 10px;
}

.subsection-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.subsection-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background-color: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  transition: all 0.3s;
}

.subsection-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.subsection-info {
  flex: 1;
  padding-right: 20px;
}

.subsection-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 8px;
}

.subsection-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.subsection-content {
  font-size: 14px;
  color: #909399;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.subsection-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  background-color: #f8f9fa;
  padding: 10px 15px;
  border-radius: 6px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric .label {
  font-size: 13px;
  color: #909399;
}

.metric .value {
  font-size: 15px;
  font-weight: bold;
  color: #606266;
}

.metric .value.pass {
  color: #67C23A;
}

.metric .value.fail {
  color: #F56C6C;
}

.subsection-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-left: 20px;
  border-left: 1px solid #ebeef5;
}

.progress-score {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.progress-label {
  font-size: 12px;
  color: #909399;
}

/* 全屏模式样式 */
.fullscreen-mode {
  position: fixed !important;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 2000;
  margin: 0 !important;
  border-radius: 0 !important;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.fullscreen-mode :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
}

/* 全屏模式下的大字体增强 */
.fullscreen-mode .chapter-title {
  font-size: 24px;
  padding: 15px 0;
}

.fullscreen-mode .section-title {
  font-size: 20px;
  margin: 25px 0 15px;
  border-left-width: 6px;
}

.fullscreen-mode .subsection-item {
  padding: 25px;
  margin-bottom: 20px;
}

.fullscreen-mode .subsection-title {
  font-size: 22px;
}

.fullscreen-mode .subsection-content {
  font-size: 16px;
  -webkit-line-clamp: 3;
  margin-bottom: 20px;
}

.fullscreen-mode .subsection-metrics {
  padding: 20px;
  gap: 40px;
}

.fullscreen-mode .metric .label {
  font-size: 16px;
}

.fullscreen-mode .metric .value {
  font-size: 24px;
}

.fullscreen-mode .progress-score {
  font-size: 28px;
}
</style>

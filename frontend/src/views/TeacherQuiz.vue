<template>
  <div class="teacher-quiz-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">练习中心 (教师端)</span>
        </div>
      </template>
      
      <!-- 筛选区域 -->
      <div class="filter-section">
        <span class="filter-label">选择章节范围：</span>
        <el-cascader
          v-model="selectedScope"
          :options="chapterOptions"
          :props="{ checkStrictly: true, value: 'id', label: 'title', children: 'children' }"
          placeholder="请选择章节/节/小节"
          style="width: 100%"
          @change="handleScopeChange"
          clearable
        />
      </div>

      <el-divider />

      <el-row :gutter="20">
        <!-- 左侧：成绩分布 -->
        <el-col :span="12">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="chart-header">
                <span>📊 成绩分布与人数统计</span>
                <el-tag type="info">总人数: {{ gradeStats.total_students }}</el-tag>
              </div>
            </template>
            <div ref="pieChartRef" style="width: 100%; height: 400px;"></div>
            <div class="chart-footer">
              <span>平均分: <strong>{{ gradeStats.avg_score }}</strong></span>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：知识点薄弱项 -->
        <el-col :span="12">
          <el-card shadow="hover" class="kp-card">
            <template #header>
              <div class="chart-header">
                <span>📉 知识点薄弱项 (Top 4)</span>
                <span class="sub-text">按正确率由低到高排序</span>
              </div>
            </template>
            <div v-if="kpStats.length > 0" class="kp-list">
              <div v-for="(item, index) in kpStats" :key="index" class="kp-item">
                <div class="kp-info">
                  <span class="kp-content">{{ item.content }}</span>
                  <span class="kp-accuracy">{{ item.accuracy }}% 正确率</span>
                </div>
                <el-progress 
                  :percentage="item.accuracy" 
                  :color="getProgressColor(item.accuracy)"
                  :stroke-width="18"
                  text-inside
                />
                <div class="kp-meta">
                  <small>共练习 {{ item.total_attempts }} 次</small>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无薄弱知识点数据" />
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { getTeacherGradeStats, getTeacherKpStats } from '@/api/quiz'
import { useChapterStore } from '@/stores'
import * as echarts from 'echarts'
import { onMounted, ref } from 'vue'

const chapterStore = useChapterStore()
const selectedScope = ref<number[]>([]) // [chapter_id, section_id, subsection_id]
const chapterOptions = ref<any[]>([])

const gradeStats = ref({
  total_students: 0,
  avg_score: 0,
  distribution: []
})

const kpStats = ref<any[]>([])
const pieChartRef = ref<HTMLElement | null>(null)
let pieChart: echarts.ECharts | null = null

// Load chapters
onMounted(async () => {
  await chapterStore.fetchChapters()
  // Transform chapters to cascader options
  // Note: Element Plus Cascader expects specific structure. 
  // If 'children' is empty array, it might still show expand icon. We should handle empty children.
  chapterOptions.value = chapterStore.chapters.map(chapter => ({
    id: chapter.id,
    title: chapter.title,
    children: chapter.sections && chapter.sections.length > 0 ? chapter.sections.map(section => ({
      id: section.id,
      title: section.title,
      children: section.subsections && section.subsections.length > 0 ? section.subsections.map(sub => ({
        id: sub.id,
        title: sub.title
      })) : undefined
    })) : undefined
  }))
  
  // Initial fetch (default to first chapter if available)
  if (chapterOptions.value.length > 0) {
      selectedScope.value = [chapterOptions.value[0].id]
      fetchData()
  }
})

const handleScopeChange = () => {
  fetchData()
}

const fetchData = async () => {
  // Cascader value is an array of IDs from root to leaf
  // e.g. [chapter_id] or [chapter_id, section_id] or [chapter_id, section_id, subsection_id]
  const ids = selectedScope.value || []
  let chapterId, sectionId, subsectionId
  
  if (ids.length > 0) chapterId = ids[0]
  if (ids.length > 1) sectionId = ids[1]
  if (ids.length > 2) subsectionId = ids[2]
  
  const params = {
    chapter_id: chapterId,
    section_id: sectionId,
    subsection_id: subsectionId
  }

  try {
    const gradeRes: any = await getTeacherGradeStats(params)
    gradeStats.value = gradeRes
    renderPieChart()
    
    const kpRes: any = await getTeacherKpStats(params)
    kpStats.value = kpRes
  } catch (e) {
    console.error(e)
  }
}

const renderPieChart = () => {
  if (!pieChartRef.value) return
  
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value)
  }
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      top: '5%',
      left: 'center'
    },
    series: [
      {
        name: '成绩分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: gradeStats.value.distribution
      }
    ]
  }
  
  pieChart.setOption(option)
}

const getProgressColor = (accuracy: number) => {
  if (accuracy < 60) return '#F56C6C'
  if (accuracy < 80) return '#E6A23C'
  return '#67C23A'
}

// Handle window resize
window.addEventListener('resize', () => {
  pieChart?.resize()
})
</script>

<style scoped>
.teacher-quiz-container {
  padding: 20px;
}
.filter-section {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}
.filter-label {
  font-size: 16px;
  margin-right: 10px;
  font-weight: bold;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chart-footer {
  margin-top: 10px;
  text-align: center;
  font-size: 16px;
}
.kp-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.kp-item {
  margin-bottom: 10px;
}
.kp-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-weight: 500;
}
.kp-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  text-align: right;
}
.sub-text {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}
</style>
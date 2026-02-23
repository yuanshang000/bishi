<template>
  <div class="home">
    <!-- 教师端首页 -->
    <TeacherHome v-if="userStore.isTeacher" />

    <!-- 学生端首页 (原有内容) -->
    <template v-else>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card>
            <template #header>
              <el-icon><Reading /></el-icon> 章节统计
            </template>
            <div class="stat-number">{{ chapterCount }}</div>
            <div class="stat-label">总章节数</div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card>
            <template #header>
              <el-icon><Document /></el-icon> 文档统计
            </template>
            <div class="stat-number">{{ documentCount }}</div>
            <div class="stat-label">总文档数</div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card>
            <template #header>
              <el-icon><Edit /></el-icon> 练习统计
            </template>
            <div class="stat-number">{{ quizStats.total_count }}</div>
            <div class="stat-label">已完成 {{ quizStats.completed_count }} 次</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>最近练习记录</span>
            </template>
            <el-table :data="recentQuizzes" height="300">
              <el-table-column prop="quiz_type" label="类型" width="100">
                <template #default="{ row }">
                  {{ getQuizTypeLabel(row.quiz_type) }}
                </template>
              </el-table-column>
              <el-table-column prop="score" label="分数" width="80" />
              <el-table-column prop="accuracy" label="正确率" width="100">
                <template #default="{ row }">
                  {{ row.accuracy.toFixed(1) }}%
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间">
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card>
            <template #header>
              <span>快速操作</span>
            </template>
            <el-space direction="vertical" style="width: 100%" :size="16">
              <el-button type="primary" :icon="Edit" @click="$router.push('/quiz')" block>
                开始练习
              </el-button>
              <el-button v-if="!userStore.isTeacher" type="success" :icon="ChatDotRound" @click="$router.push('/chat')" block>
                智能问答
              </el-button>
              <!-- 教师端的按钮虽然这里有v-if，但整个template是else分支，所以这里其实只会显示给学生 -->
              <!-- 保留原始逻辑以防万一 -->
              <el-button
                v-if="userStore.isTeacher"
                type="warning"
                :icon="Document"
                @click="$router.push('/documents')"
                block
              >
                上传文档
              </el-button>
            </el-space>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { getDocuments, getQuizHistory, getQuizStats } from '@/api'
import { useChapterStore, useUserStore } from '@/stores'
import dayjs from 'dayjs'
import { onMounted, ref } from 'vue'
import TeacherHome from './TeacherHome.vue'

const userStore = useUserStore()
const chapterStore = useChapterStore()

const chapterCount = ref(0)
const documentCount = ref(0)
const quizStats = ref({ total_count: 0, completed_count: 0, avg_score: 0, avg_accuracy: 0 })
const recentQuizzes = ref<any[]>([])

onMounted(async () => {
  await chapterStore.fetchChapters()
  chapterCount.value = chapterStore.chapters.length

  try {
    const docs: any = await getDocuments()
    documentCount.value = docs.length
  } catch (e) {
    console.error(e)
  }

  try {
    const stats: any = await getQuizStats()
    quizStats.value = stats
  } catch (e) {
    console.error(e)
  }

  try {
    const quizzes: any = await getQuizHistory({ limit: 5 })
    recentQuizzes.value = quizzes
  } catch (e) {
    console.error(e)
  }
})

const getQuizTypeLabel = (type: string) => {
  const labels: any = {
    choice: '选择题',
    blank: '填空题',
    translation: '翻译题'
  }
  return labels[type] || type
}

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}
</script>

<style scoped>
.home {
  padding: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  text-align: center;
  margin: 20px 0;
}

.stat-label {
  text-align: center;
  color: #909399;
  font-size: 14px;
}
</style>

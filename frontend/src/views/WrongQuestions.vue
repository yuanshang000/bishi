<template>
  <div class="wrong-questions-container">
    <el-container style="height: calc(100vh - 100px);">
      <!-- 左侧目录树 -->
      <el-aside width="300px" class="tree-aside">
        <div class="tree-header">
          <span>📚 错题目录</span>
          <el-button link type="primary" @click="fetchTreeData">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <el-scrollbar>
          <el-tree
            ref="treeRef"
            :data="treeData"
            :props="defaultProps"
            node-key="id"
            highlight-current
            :expand-on-click-node="false"
            default-expand-all
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <div class="custom-tree-node">
                <span class="node-label" :title="node.label">{{ node.label }}</span>
                <el-tag v-if="data.count > 0" size="small" type="danger" effect="plain" round>
                  {{ data.count }}
                </el-tag>
              </div>
            </template>
          </el-tree>
        </el-scrollbar>
      </el-aside>

      <!-- 右侧主要内容 -->
      <el-main class="main-content">
        <!-- 顶部统计 -->
        <el-row :gutter="20" class="stats-row">
          <el-col :span="6">
            <el-card shadow="hover" class="stats-card">
              <el-statistic title="当前选中错题" :value="currentStats.total">
                <template #prefix>
                  <el-icon color="#F56C6C"><DocumentDelete /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stats-card">
              <el-statistic title="未掌握" :value="currentStats.unmastered">
                <template #prefix>
                  <el-icon color="#E6A23C"><Warning /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stats-card">
              <el-statistic title="已掌握" :value="currentStats.mastered">
                <template #prefix>
                  <el-icon color="#67C23A"><SuccessFilled /></el-icon>
                </template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stats-card">
               <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                  <el-button type="primary" @click="showReviewDialog = true" :disabled="currentStats.unmastered === 0">
                    <el-icon style="margin-right: 5px"><EditPen /></el-icon>
                    错题重练
                  </el-button>
               </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 错题列表 -->
        <el-card shadow="never" class="list-card">
          <template #header>
            <div class="card-header">
              <span>{{ currentTitle }}</span>
              <div style="display: flex; align-items: center;">
                 <!-- 练习模式选择 (仅在非小节节点显示) -->
                 <el-radio-group 
                    v-model="practiceMode" 
                    size="small" 
                    @change="fetchWrongQuestions" 
                    style="margin-right: 20px;"
                    v-if="currentNode?.type === 'section' || currentNode?.type === 'chapter'"
                 >
                    <el-radio-button label="chapter">章节训练</el-radio-button>
                    <el-radio-button label="random">综合训练</el-radio-button>
                 </el-radio-group>

                 <el-radio-group v-model="filterStatus" size="small" @change="fetchWrongQuestions">
                    <el-radio-button label="all">全部</el-radio-button>
                    <el-radio-button label="unmastered">未掌握</el-radio-button>
                    <el-radio-button label="mastered">已掌握</el-radio-button>
                 </el-radio-group>
              </div>
            </div>
          </template>

          <el-table :data="wrongQuestions" v-loading="loading" style="width: 100%" stripe @row-click="handleViewDetail">
            <el-table-column label="题型" width="100">
              <template #default="{ row }">
                <el-tag :type="getQuestionTypeTagType(row.question_type)" size="small">
                  {{ getQuestionTypeLabel(row.question_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="题目内容" min-width="300">
              <template #default="{ row }">
                <div class="question-preview">{{ getQuestionText(row.question_data) }}</div>
              </template>
            </el-table-column>
            <el-table-column label="得分" width="100">
               <template #default="{ row }">
                 <span :style="{ color: getScoreColor(row.score), fontWeight: 'bold' }">
                   {{ (row.score * 100).toFixed(0) }}分
                 </span>
               </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_mastered ? 'success' : 'warning'" size="small">
                  {{ row.is_mastered ? '已掌握' : '未掌握' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click.stop="handleViewDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="错题详情" width="800px" destroy-on-close>
      <div v-if="currentDetail" class="detail-container">
        
        <!-- 元数据信息 (知识点 & AI Prompt) -->
        <el-alert type="info" :closable="false" class="meta-alert">
           <template #title>
              <div class="meta-title" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                  <span>📖 出题背景</span>
                  <el-tag :type="getQuestionTypeTagType(currentDetail.question_type)" size="small">
                    {{ getQuestionTypeLabel(currentDetail.question_type) }}
                  </el-tag>
              </div>
           </template>
           <template #default>
              <div class="meta-content">
                  <div class="meta-item">
                      <span class="label">🎯 知识点：</span>
                      <span class="value">{{ getMetaWord(currentDetail) }}</span>
                  </div>
                  <div class="meta-item" v-if="getMetaPrompt(currentDetail)">
                      <span class="label">🤖 AI提示词：</span>
                      <el-popover placement="top" width="400" trigger="hover">
                          <template #reference>
                              <el-tag size="small" style="cursor: pointer;">查看提示词</el-tag>
                          </template>
                          <div class="prompt-popover">{{ getMetaPrompt(currentDetail) }}</div>
                      </el-popover>
                  </div>
              </div>
           </template>
        </el-alert>

        <!-- 题目区域 -->
        <div class="question-detail-box">
           
           <!-- 阅读材料 -->
           <div v-if="currentDetail.question_data.passage" class="passage-box">
              <div class="label">阅读材料：</div>
              <div class="text">{{ currentDetail.question_data.passage }}</div>
           </div>

           <!-- 题目文本 -->
           <div class="question-text">
              <span class="label">题目：</span>
              {{ getQuestionText(currentDetail.question_data) }}
           </div>

           <!-- 选项 -->
           <div v-if="currentDetail.question_data.options" class="options-list">
              <div v-for="(opt, key) in currentDetail.question_data.options" :key="key" 
                   :class="['option-item', { 
                       'correct': key === currentDetail.correct_answer,
                       'wrong': key === currentDetail.user_answer && key !== currentDetail.correct_answer,
                       'selected': key === currentDetail.user_answer
                   }]">
                  <span class="key">{{ key }}.</span>
                  <span class="text">{{ opt }}</span>
                  <el-icon v-if="key === currentDetail.correct_answer" class="icon"><Check /></el-icon>
                  <el-icon v-if="key === currentDetail.user_answer && key !== currentDetail.correct_answer" class="icon"><Close /></el-icon>
              </div>
           </div>
        </div>

        <!-- 答案对比 -->
        <el-row :gutter="20" style="margin-top: 20px;">
           <el-col :span="12">
              <div class="answer-box user-box">
                 <div class="box-title">你的答案</div>
                 <div class="box-content">{{ formatAnswer(currentDetail.user_answer) }}</div>
              </div>
           </el-col>
           <el-col :span="12">
              <div class="answer-box correct-box">
                 <div class="box-title">正确答案</div>
                 <div class="box-content">{{ formatAnswer(currentDetail.correct_answer) }}</div>
              </div>
           </el-col>
        </el-row>

        <!-- 解析 -->
        <div class="explanation-box" v-if="currentDetail.question_data.explanation">
           <div class="box-title">📝 解析</div>
           <div class="box-content">{{ currentDetail.question_data.explanation }}</div>
        </div>

        <!-- 底部操作 -->
        <div class="dialog-footer">
            <div class="status-actions">
                <span>掌握状态：</span>
                <el-switch
                    v-model="currentDetail.is_mastered"
                    active-text="已掌握"
                    inactive-text="未掌握"
                    @change="handleMasteryChange(currentDetail)"
                />
            </div>
            <el-button type="success" size="large" @click="handleDrawInferences">
               <el-icon style="margin-right: 5px"><MagicStick /></el-icon>
               举一反三 (生成相似题)
            </el-button>
        </div>

      </div>
    </el-dialog>

    <!-- 举一反三练习弹窗 -->
    <el-dialog v-model="showSimilarPracticeDialog" title="举一反三 - 强化训练" width="700px" :close-on-click-modal="false">
       <div v-if="similarQuestion" class="similar-practice-container">
          <el-alert title="AI根据原题知识点为您生成了新的变式题目，请作答。" type="success" :closable="false" style="margin-bottom: 15px;" />
          
          <div class="question-card">
              <div class="q-type">
                  <el-tag>{{ getQuestionTypeLabel(similarQuestion.quiz_type) }}</el-tag>
              </div>
              <div class="q-text">{{ similarQuestion.question_text }}</div>
              
              <!-- Options -->
              <div v-if="similarQuestion.options && Object.keys(similarQuestion.options).length > 0" class="q-options">
                  <el-radio-group v-model="similarAnswer" class="vertical-options">
                      <el-radio v-for="(opt, key) in similarQuestion.options" :key="key" :label="key" border class="option-radio">
                          {{ key }}. {{ opt }}
                      </el-radio>
                  </el-radio-group>
              </div>
              <!-- Input -->
              <div v-else class="q-input">
                  <el-input v-model="similarAnswer" type="textarea" :rows="3" placeholder="请输入答案" />
              </div>
          </div>

          <div class="action-area" style="text-align: center; margin-top: 20px;">
             <el-button type="primary" size="large" @click="submitSimilarPractice" :loading="submittingSimilar" v-if="!similarResult">提交答案</el-button>
             <el-button @click="showSimilarPracticeDialog = false" v-if="!similarResult">取消</el-button>
             
             <div v-if="similarResult" class="result-feedback">
                <el-result :icon="similarResult.is_correct ? 'success' : 'error'" :title="similarResult.is_correct ? '回答正确！' : '回答错误'">
                   <template #sub-title>
                      <div v-if="!similarResult.is_correct">
                         正确答案：{{ similarResult.correct_answer }}
                      </div>
                   </template>
                   <template #extra>
                      <el-button type="primary" @click="showSimilarPracticeDialog = false">完成</el-button>
                   </template>
                </el-result>
             </div>
          </div>
       </div>
    </el-dialog>
    
    <!-- 错题重练设置对话框 (复用原有逻辑) -->
    <el-dialog v-model="showReviewDialog" title="错题重练设置" width="400px">
      <el-form :model="reviewForm" label-width="100px">
        <el-form-item label="选择范围">
           <span>当前选中目录</span>
        </el-form-item>
        <el-form-item label="题目数量">
          <el-input-number v-model="reviewForm.question_count" :min="1" :max="20" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateReviewQuiz" :loading="creatingReview">
          开始练习
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import {
  getWrongQuestionsTree,
  getWrongQuestions,
  getWrongQuestionDetail,
  updateMasteryStatus,
  generateSimilarQuestion,
  createReviewQuiz
} from '@/api'
import { ElMessage, ElNotification } from 'element-plus'
import {
  DocumentDelete,
  Warning,
  SuccessFilled,
  Refresh,
  Check,
  Close,
  MagicStick,
  EditPen
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 状态定义
const treeData = ref<any[]>([])
const loading = ref(false)
const wrongQuestions = ref<any[]>([])
const currentStats = reactive({
  total: 0,
  unmastered: 0,
  mastered: 0
})

const currentNode = ref<any>(null) // 当前选中的树节点
const filterStatus = ref('all') // all, unmastered, mastered
const practiceMode = ref('chapter') // chapter, random (comprehensive)

const showDetailDialog = ref(false)
const currentDetail = ref<any>(null)

// 举一反三相关
const showSimilarPracticeDialog = ref(false)
const similarQuestion = ref<any>(null)
const similarAnswer = ref('')
const submittingSimilar = ref(false)
const similarResult = ref<any>(null)

// 错题重练相关
const showReviewDialog = ref(false)
const creatingReview = ref(false)
const reviewForm = reactive({
  question_count: 5
})

const defaultProps = {
  children: 'children',
  label: 'label'
}

const currentTitle = computed(() => {
  if (!currentNode.value) return '全部错题'
  return currentNode.value.label
})

// 初始化
onMounted(() => {
  fetchTreeData()
  fetchWrongQuestions()
})

// 获取树数据
const fetchTreeData = async () => {
  try {
    const res = await getWrongQuestionsTree()
    treeData.value = res || []
  } catch (error) {
    console.error('Failed to fetch tree data', error)
  }
}

// 节点点击
const handleNodeClick = (data: any, node: any) => {
  currentNode.value = data
  
  // 如果是小节，强制设为章节训练
  if (data.type === 'subsection') {
      practiceMode.value = 'chapter'
  }
  
  fetchWrongQuestions()
}

// 获取错题列表
const fetchWrongQuestions = async () => {
  loading.value = true
  try {
    const params: any = { limit: 100 } // 暂时拉取100条
    
    if (currentNode.value) {
      if (currentNode.value.type === 'chapter') {
        params.chapter_id = currentNode.value.id
      } else if (currentNode.value.type === 'subsection') {
        params.subsection_id = currentNode.value.id
      } else if (currentNode.value.type === 'section') {
         // Use the new backend section_id filter
         params.section_id = currentNode.value.id
      }
    }
    
    // Add practice mode filter
    if (currentNode.value?.type !== 'subsection') {
        params.practice_mode = practiceMode.value
    } else {
        params.practice_mode = 'chapter'
    }

    if (filterStatus.value === 'unmastered') params.is_mastered = false
    if (filterStatus.value === 'mastered') params.is_mastered = true

    const res = await getWrongQuestions(params)
    wrongQuestions.value = res || []
    
    // Update local stats based on fetched data (approximation)
    // Or we should call a stats API. For now let's calc from list for "Current View Stats"
    currentStats.total = wrongQuestions.value.length
    currentStats.unmastered = wrongQuestions.value.filter((q: any) => !q.is_mastered).length
    currentStats.mastered = wrongQuestions.value.filter((q: any) => q.is_mastered).length

  } catch (error) {
    console.error(error)
    ElMessage.error('获取错题列表失败')
  } finally {
    loading.value = false
  }
}

// 查看详情
const handleViewDetail = async (row: any) => {
  try {
    const res = await getWrongQuestionDetail(row.id)
    currentDetail.value = res
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

// 切换掌握状态
const handleMasteryChange = async (item: any) => {
  try {
    await updateMasteryStatus(item.id, { is_mastered: item.is_mastered })
    ElMessage.success(item.is_mastered ? '已标记为掌握' : '已标记为未掌握')
    // Update list item
    const idx = wrongQuestions.value.findIndex(q => q.id === item.id)
    if (idx !== -1) wrongQuestions.value[idx].is_mastered = item.is_mastered
    // Update stats
    if (item.is_mastered) {
        currentStats.unmastered--
        currentStats.mastered++
    } else {
        currentStats.unmastered++
        currentStats.mastered--
    }
  } catch (error) {
    item.is_mastered = !item.is_mastered // revert
    ElMessage.error('更新状态失败')
  }
}

// 举一反三
const handleDrawInferences = async () => {
  if (!currentDetail.value) return
  
  // Show loading
  const loadingInstance = ElMessage.info({
      message: '正在生成相似题目，请稍候...',
      duration: 0
  })
  
  try {
     const res = await generateSimilarQuestion(currentDetail.value.id)
     similarQuestion.value = res
     similarAnswer.value = ''
     similarResult.value = null
     showSimilarPracticeDialog.value = true
     loadingInstance.close()
  } catch (error: any) {
     loadingInstance.close()
     ElMessage.error(error.message || '生成失败')
  }
}

// 提交举一反三
const submitSimilarPractice = () => {
    if (!similarAnswer.value) {
        ElMessage.warning('请先作答')
        return
    }
    submittingSimilar.value = true
    
    // Local check
    // Assuming simple check for now since backend doesn't have a "check similar" endpoint yet
    // But we have the correct answer in similarQuestion
    const correct = similarQuestion.value.correct_answer
    const user = similarAnswer.value
    
    // Normalize comparison
    const isCorrect = String(user).trim().toUpperCase() === String(correct).trim().toUpperCase()
    
    similarResult.value = {
        is_correct: isCorrect,
        correct_answer: correct
    }
    
    submittingSimilar.value = false
}

// 错题重练 (Bulk Review)
const handleCreateReviewQuiz = async () => {
    creatingReview.value = true
    try {
        const params: any = {
            question_count: reviewForm.question_count
        }
        if (currentNode.value && currentNode.value.type === 'chapter') {
            params.chapter_id = currentNode.value.id
        }
        
        const res = await createReviewQuiz(params)
        
        showReviewDialog.value = false
        // Navigate to Quiz page with quiz data
        // We can use router params or state
        router.push({
            name: 'Quiz',
            state: { quizData: res } // Pass generated quiz to Quiz view
        })
        
    } catch (error: any) {
        ElMessage.error(error.message || '创建练习失败')
    } finally {
        creatingReview.value = false
    }
}


// Helpers
const getQuestionTypeLabel = (type: string) => {
  const map: any = { choice: '选择题', blank: '填空题', translation: '翻译', reading: '阅读', writing: '写作' }
  return map[type] || type
}

const getQuestionTypeTagType = (type: string) => {
  const map: any = { choice: 'primary', blank: 'success', translation: 'warning', writing: 'danger' }
  return map[type] || 'info'
}

const getScoreColor = (score: number) => {
  if (score >= 0.8) return '#67C23A'
  if (score >= 0.6) return '#E6A23C'
  return '#F56C6C'
}

const getQuestionText = (data: any) => {
  if (!data) return ''
  if (data.question) return data.question
  if (data.question_text) return data.question_text
  return ''
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

const formatAnswer = (ans: any) => {
  if (typeof ans === 'object') return JSON.stringify(ans)
  return ans
}

const getMetaWord = (detail: any) => {
  if (detail?.question_data?.meta?.word) return detail.question_data.meta.word
  return '未知'
}

const getMetaPrompt = (detail: any) => {
  if (detail?.question_data?.meta?.prompt) return detail.question_data.meta.prompt
  return ''
}

</script>

<style scoped>
.wrong-questions-container {
  height: 100%;
}

.tree-aside {
  background: #fff;
  border-right: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;
}

.tree-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 18px;
  color: #303133;
}

.custom-tree-node {
  font-size: 16px;
  padding: 4px 0;
}

.main-content {
  background: #f5f7fa;
  padding: 25px;
}

.stats-row {
  margin-bottom: 25px;
}

.stats-card {
  height: 130px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* Increase statistic font sizes */
.stats-card :deep(.el-statistic__head) {
  font-size: 16px;
  margin-bottom: 10px;
}

.stats-card :deep(.el-statistic__content) {
  font-size: 28px;
  font-weight: bold;
}

.list-card {
  min-height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
}

/* Table font size adjustment */
:deep(.el-table) {
  font-size: 18px;
}

:deep(.el-table .cell) {
  line-height: 1.6;
  padding: 12px 0;
}

.question-preview {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 17px;
}

/* Detail Styles */
.detail-container {
  padding: 15px;
}

.meta-alert {
  margin-bottom: 25px;
}

.meta-content {
    margin-top: 15px;
}
.meta-item {
    margin-bottom: 8px;
    display: flex;
    align-items: flex-start;
    font-size: 15px;
}
.meta-item .label {
    font-weight: bold;
    color: #606266;
    min-width: 90px;
}
.prompt-popover {
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    font-size: 14px;
}

.question-detail-box {
    background: #f9f9f9;
    padding: 25px;
    border-radius: 8px;
    position: relative;
    margin-bottom: 25px;
}


.passage-box {
    background: #fff;
    padding: 15px;
    border: 1px dashed #ccc;
    margin-bottom: 20px;
    border-radius: 4px;
}
.passage-box .label {
    font-weight: bold;
    margin-bottom: 8px;
    font-size: 16px;
}
.passage-box .text {
    font-size: 16px;
    line-height: 1.8;
}

.question-text {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 20px;
    line-height: 1.6;
}

.options-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.option-item {
    padding: 15px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    display: flex;
    align-items: center;
    background: #fff;
    font-size: 16px;
}
.option-item.correct {
    border-color: #67C23A;
    background: #f0f9eb;
    color: #67C23A;
}
.option-item.wrong {
    border-color: #F56C6C;
    background: #fef0f0;
    color: #F56C6C;
}
.option-item.selected {
    border-color: #409EFF;
}
.option-item .key {
    font-weight: bold;
    margin-right: 12px;
    font-size: 18px;
}
.option-item .text {
    flex: 1;
}
.option-item .icon {
    font-size: 20px;
    font-weight: bold;
}

.answer-box {
    padding: 20px;
    border-radius: 8px;
    text-align: center;
}
.user-box {
    background: #fef0f0;
    color: #F56C6C;
}
.correct-box {
    background: #f0f9eb;
    color: #67C23A;
}
.box-title {
    font-size: 16px;
    margin-bottom: 8px;
    opacity: 0.9;
    font-weight: bold;
}
.box-content {
    font-size: 20px;
    font-weight: bold;
}

.explanation-box {
    margin-top: 25px;
    padding: 20px;
    background: #ecf5ff;
    border-radius: 8px;
    border-left: 5px solid #409EFF;
}
.explanation-box .box-title {
    color: #409EFF;
    font-size: 18px;
    margin-bottom: 12px;
}
.explanation-box .box-content {
    font-size: 16px;
    font-weight: normal;
    line-height: 1.8;
    color: #303133;
}

.dialog-footer {
    margin-top: 35px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 25px;
    border-top: 1px solid #eee;
}
.status-actions {
    display: flex;
    align-items: center;
    gap: 15px;
    font-size: 16px;
}

/* Similar Practice */
.similar-practice-container {
    padding: 15px;
}
.question-card {
    background: #fff;
    border: 1px solid #ebeef5;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 4px 16px 0 rgba(0,0,0,0.08);
}
.q-type {
    margin-bottom: 15px;
}
.q-text {
    font-size: 18px;
    margin-bottom: 25px;
    font-weight: 500;
    line-height: 1.6;
}
.vertical-options {
    display: flex;
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
}
.option-radio {
    margin: 0 !important;
    width: 100%;
    padding: 12px 20px;
    height: auto;
}
.option-radio :deep(.el-radio__label) {
    font-size: 16px;
    white-space: normal;
    line-height: 1.5;
}
.result-feedback {
    margin-top: 25px;
}
</style>

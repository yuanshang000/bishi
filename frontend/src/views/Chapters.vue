<template>
  <div class="chapters-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span class="header-title">章节管理 / Course Chapters</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleImportClick">📤 导入课程文档 (Markdown/Word/PDF/TXT)</el-button>
            <input 
              type="file" 
              ref="fileInput" 
              style="display: none" 
              accept=".md,.docx,.pdf,.txt" 
              @change="handleFileChange"
            />
          </div>
          <!-- <el-button type="primary" size="large" @click="handleCreate">新建章节</el-button> -->
        </div>
      </template>

      <el-table 
        :data="chapterStore.chapters" 
        v-loading="chapterStore.loading" 
        style="width: 100%; font-size: 18px;"
        row-key="id"
        border
      >
        <!-- 章节展开显示小节 -->
        <el-table-column type="expand">
          <template #default="{ row: chapter }">
            <div class="section-container">
              <h3 class="section-header">包含小节 (Sections)</h3>
              <el-table 
                :data="chapter.sections" 
                style="width: 100%; font-size: 18px;"
                :show-header="false"
                row-key="id"
                border
              >
                <!-- 小节展开显示小目标 -->
                <el-table-column type="expand">
                  <template #default="{ row: section }">
                    <div class="subsection-container">
                      <h4 class="subsection-header">学习小目标 (SubSections / Goals)</h4>
                      <el-table 
                        :data="section.subsections" 
                        style="width: 100%; font-size: 18px;" 
                        border
                      >
                        <el-table-column label="小目标标题" min-width="200">
                          <template #default="{ row }">
                            <el-tooltip
                              v-if="row.description"
                              effect="dark"
                              :content="row.description"
                              placement="top"
                            >
                              <span>{{ row.title }}</span>
                            </el-tooltip>
                            <span v-else>{{ row.title }}</span>
                          </template>
                        </el-table-column>
                        <el-table-column label="学习内容" min-width="500">
                          <template #default="{ row }">
                            <el-popover
                              placement="top"
                              :width="500"
                              trigger="hover"
                            >
                              <template #reference>
                                <div class="content-cell">{{ row.content }}</div>
                              </template>
                              <div class="content-popover">
                                <h4>完整内容预览</h4>
                                <div class="content-scroll">{{ row.content }}</div>
                                <div class="popover-footer">
                                  <el-button type="primary" size="small" @click="handlePreviewVector(row)">
                                    查看向量化详情
                                  </el-button>
                                </div>
                              </div>
                            </el-popover>
                          </template>
                        </el-table-column>
                        <el-table-column label="知识点类型" width="150">
                          <template #default="{ row }">
                             {{ getKnowledgeTypes(row.content) }}
                          </template>
                        </el-table-column>
                        <el-table-column label="考核指标" min-width="380">
                          <template #default="{ row: sub }">
                            <div class="assessment-tags">
                              <el-tag size="large" type="success" style="font-size: 16px;">权重: {{ sub.weight }}%</el-tag>
                              <el-tag size="large" type="warning" style="font-size: 16px;">及格分: {{ sub.passing_score }}</el-tag>
                              <el-tag size="large" type="info" style="font-size: 16px;">最少题数: {{ sub.min_questions || 10 }}</el-tag>
                            </div>
                          </template>
                        </el-table-column>
                      </el-table>
                    </div>
                  </template>
                </el-table-column>

                <el-table-column prop="title" label="小节标题">
                  <template #default="{ row: section }">
                    <span style="font-weight: bold;">{{ section.title }}</span>
                  </template>
                </el-table-column>
              </el-table>
              <div v-if="!chapter.sections || chapter.sections.length === 0" class="empty-tip">
                暂无小节数据
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="chapter_number" label="章号" width="100" align="center">
          <template #default="{ row }">
            <span style="font-weight: bold; font-size: 18px;">第 {{ row.chapter_number }} 章</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="章节标题" width="300">
          <template #default="{ row }">
            <span style="font-weight: bold; font-size: 18px;">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="章节目标" min-width="400" show-overflow-tooltip />
        
        <!-- 操作栏 -->
        <el-table-column label="操作" width="350" align="center">
          <template #default="{ row }">
            <el-button style="font-size: 16px;" type="success" plain @click="handleExport(row)">导出</el-button>
            <el-button style="font-size: 16px;" type="primary" plain @click="handleReplaceClick(row)">替换</el-button>
            <el-popconfirm title="确定要删除该章节及其所有内容吗？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button style="font-size: 16px;" type="danger" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Dialog 保持不变，用于编辑章节基本信息 -->
    <el-dialog v-model="showDialog" :title="editId ? '编辑章节' : '新建章节'" width="600px">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="章节编号">
          <el-input-number v-model="form.chapter_number" :min="1" :disabled="!editId" />
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入章节标题" />
        </el-form-item>
        <el-form-item label="章节目标">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>

    <!-- 预览向量化内容 Dialog -->
    <el-dialog v-model="showPreviewDialog" title="向量化内容预览" width="800px">
      <div v-if="previewData" class="preview-dialog-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="小目标标题">{{ previewData.title }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag type="success">已向量化 (Ready for RAG)</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="原始内容">
            <div class="preview-text">{{ previewData.content }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { exportChapter, uploadStructure } from '@/api/chapters'
import { useChapterStore } from '@/stores'
import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

const chapterStore = useChapterStore()
const showDialog = ref(false)
const showPreviewDialog = ref(false)
const previewData = ref<any>(null)
const editId = ref(0)
const replaceChapterId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref()
const fileInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  chapter_number: 1,
  title: '',
  description: ''
})

const formRules = {
  title: [
    { required: true, message: '请输入章节标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度应在1到200个字符之间', trigger: 'blur' }
  ]
}

onMounted(() => {
  chapterStore.fetchChapters()
})

const handleExport = async (row: any) => {
  try {
    ElMessage.info('正在生成 Markdown 文档...')
    const response: any = await exportChapter(row.id, 'md')
    
    // Create blob link and download
    const blob = new Blob([response])
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    // Use title or id for filename
    const safeTitle = row.title ? row.title.replace(/[\\/:*?"<>|]/g, '_') : `chapter_${row.id}`
    link.download = `${safeTitle}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(link.href)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Export chapter error:', error)
    ElMessage.error('导出失败')
  }
}

const handleImportClick = () => {
  replaceChapterId.value = null
  fileInput.value?.click()
}

const handleReplaceClick = (row: any) => {
  replaceChapterId.value = row.id
  fileInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return

  // 立即给出反馈
  ElMessage.info('已选择文件，准备导入...')

  const file = input.files[0]
  const formData = new FormData()
  formData.append('file', file)
  if (replaceChapterId.value) {
    formData.append('chapter_id', replaceChapterId.value.toString())
  }

  const confirmMsg = replaceChapterId.value 
    ? `即将替换章节内容，系统将删除原章节内容并解析新文档，是否继续？`
    : `即将导入文件 "${file.name}"，系统将自动进行AI结构化解析和向量化处理，这可能需要几分钟时间，是否继续？`
    
  const confirmTitle = replaceChapterId.value ? '确认替换' : '确认导入'
  const loadingText = replaceChapterId.value ? '正在替换章节内容（AI分析中）...' : '正在上传并解析文档（AI分析中）...'

  try {
    await ElMessageBox.confirm(
      confirmMsg,
      confirmTitle,
      {
        confirmButtonText: replaceChapterId.value ? '确认替换' : '开始导入',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    const loading = ElLoading.service({
      lock: true,
      text: loadingText,
      background: 'rgba(0, 0, 0, 0.7)',
    })
    
    try {
      await uploadStructure(formData)
      loading.close()
      ElMessage.success(replaceChapterId.value ? '章节内容替换成功！' : '课程结构导入成功！')
      // 刷新列表
      await chapterStore.fetchChapters()
    } catch (error: any) {
      loading.close()
      console.error('Import structure error:', error)
      ElMessage.error(error.response?.data?.detail || '导入失败，请检查文件格式或网络连接')
    } finally {
      // 确保loading关闭
      loading.close()
      // 清空input以允许重复上传同一文件
      input.value = ''
      replaceChapterId.value = null
    }
  } catch (error) {
    // Catch cancel or other errors
    if (error !== 'cancel') {
       console.error(error)
       ElMessage.error('操作异常: ' + String(error))
    }
    input.value = ''
    replaceChapterId.value = null
  }
}

const getKnowledgeTypes = (content: string) => {
  if (!content) return '无'
  const types = new Set<string>()
  
  // Extract types from [知识点:xxx] markers
  const regex = /\[知识点:([^\]]+)\]/g
  let match
  while ((match = regex.exec(content)) !== null) {
    if (match[1]) {
      types.add(match[1].trim())
    }
  }
  
  if (types.size === 0) return '无'
  return Array.from(types).join('、')
}

const handlePreviewVector = (row: any) => {
  previewData.value = {
    title: row.title,
    content: row.content,
    is_vectorized: true 
  }
  showPreviewDialog.value = true
}

const handleCreate = () => {
  editId.value = 0
  form.chapter_number = chapterStore.chapters.length + 1
  form.title = ''
  form.description = ''
  showDialog.value = true
}

const handleEdit = (row: any) => {
  editId.value = row.id
  form.chapter_number = row.chapter_number
  form.title = row.title
  form.description = row.description
  showDialog.value = true
}

const handleDelete = async (id: number) => {
  const success = await chapterStore.deleteChapter(id)
  if (success) {
    ElMessage.success('删除成功')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitting.value = true
      let result
      
      if (editId.value) {
        result = await chapterStore.updateChapter(editId.value, form)
      } else {
        result = await chapterStore.createChapter(form)
      }
      
      submitting.value = false
      if (result) {
        showDialog.value = false
      }
    }
  })
}
</script>

<style scoped>
.chapters-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.box-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 24px;
  font-weight: bold;
}

.header-tip {
  color: #909399;
  font-size: 14px;
  margin-left: 20px;
}

.section-container {
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.section-header {
  margin-top: 0;
  margin-bottom: 15px;
  color: #409EFF;
  font-size: 18px;
}

.subsection-container {
  padding: 15px;
  background-color: #fff;
  border-radius: 4px;
  border: 1px dashed #dcdfe6;
}

.subsection-header {
  margin-top: 0;
  margin-bottom: 10px;
  color: #67C23A;
  font-size: 16px;
}

.content-cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  color: #606266;
}

.content-popover {
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

.content-scroll {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 15px;
  white-space: pre-wrap;
  line-height: 1.6;
}

.popover-footer {
  text-align: right;
  padding-top: 10px;
  border-top: 1px solid #eee;
}

.preview-dialog-content {
  padding: 10px;
}

.preview-text {
  white-space: pre-wrap;
  max-height: 500px;
  overflow-y: auto;
  line-height: 1.6;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}

.generated-questions {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 10px;
}

.question-item {
  margin-bottom: 20px;
}

.q-header {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.q-index {
  margin-right: 5px;
  color: #409EFF;
}

.q-options {
  margin-left: 20px;
  margin-bottom: 10px;
}

.option-item {
  margin-bottom: 5px;
}

.opt-key {
  font-weight: bold;
}

.q-answer, .q-explanation {
  margin-left: 20px;
  margin-top: 5px;
  font-size: 14px;
}

.assessment-tags {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: nowrap;
}
</style>

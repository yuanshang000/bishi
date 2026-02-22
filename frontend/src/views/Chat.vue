<template>
  <div class="chat-container">
    <el-container class="chat-layout">
      <!-- 左侧会话列表 (仅在聊天模式下显示) -->
      <el-aside v-if="mode === 'chat'" width="280px" class="session-sidebar">
        <div class="sidebar-header">
          <h3>会话记录</h3>
          <el-button type="primary" size="small" @click="handleNewSession">
            <el-icon><Plus /></el-icon>
            新会话
          </el-button>
        </div>

        <div class="session-list">
          <div
            v-for="session in sessions"
            :key="session.session_id"
            :class="['session-item', { active: session.session_id === sessionId }]"
            @click="handleLoadSession(session)"
          >
            <div class="session-preview">
              {{ session.preview || '新对话' }}
            </div>
            <div class="session-meta">
              <span class="session-time">{{ formatTime(session.last_message_at) }}</span>
              <span class="session-count">{{ session.message_count }} 条消息</span>
            </div>
            <el-button
              type="danger"
              size="small"
              text
              class="delete-btn"
              @click.stop="handleDeleteSession(session.session_id)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>

          <el-empty v-if="sessions.length === 0" description="暂无会话记录" :image-size="80" />
        </div>
      </el-aside>

      <!-- 右侧聊天区域 -->
      <el-main class="chat-main">
        <el-card class="chat-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <span>智能问答</span>
                <el-radio-group v-model="mode" size="small">
                  <el-radio-button label="chat">聊天模式</el-radio-button>
                  <el-radio-button label="quiz">出题模式</el-radio-button>
                </el-radio-group>
              </div>
              <el-tag v-if="mode === 'chat' && currentSessionMessageCount > 0" type="info">
                当前会话：{{ currentSessionMessageCount }} 条消息
              </el-tag>
            </div>
          </template>

          <div v-if="mode === 'chat'" class="chat-messages" ref="messagesRef">
            <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
              <div class="message-content">
                <div class="message-header">
                  <el-avatar :size="32">{{ msg.role === 'user' ? 'U' : 'AI' }}</el-avatar>
                  <span class="message-role">{{ msg.role === 'user' ? '我' : 'AI助手' }}</span>
                </div>
                <!-- 如果消息包含图片，先显示图片 -->
                <div v-if="msg.image" class="message-image">
                  <img :src="msg.image" alt="图片" class="message-img" />
                </div>
                <div class="message-text" v-html="formatMessage(msg.content)"></div>
              </div>
            </div>
            <div v-if="loading" class="message assistant">
              <div class="message-content">
                <div class="message-header">
                  <el-avatar :size="32">AI</el-avatar>
                  <span class="message-role">AI助手</span>
                </div>
                <div class="message-text">
                  <el-icon class="is-loading"><Loading /></el-icon> 正在思考...
                </div>
              </div>
            </div>
          </div>

          <!-- 出题模式主区域 -->
          <div v-else class="quiz-main-container">
            <div class="quiz-hero">
              <h2>智能出题助手</h2>
              <p class="quiz-subtitle">输入您的要求，AI将为您生成个性化练习题</p>
              
              <div class="quiz-form">
                <el-input
                  v-model="quizPrompt"
                  placeholder="请输入出题提示词（例如：帮我出一套关于商务英语邮件写作的题目，包含选择题和填空题，难度中等）"
                  :rows="6"
                  type="textarea"
                  class="quiz-prompt-input-large"
                />
                
                <div class="quiz-actions-large">
                  <el-button type="primary" size="large" @click="handleGenerateQuiz" :loading="loading" :disabled="!quizPrompt.trim()">
                    <el-icon class="el-icon--left"><Loading v-if="loading" /><Picture v-else /></el-icon>
                    生成题目
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="mode === 'chat'" class="chat-input">
            <!-- 图片预览区域 -->
            <div v-if="selectedImage" class="image-preview-container">
              <div class="image-preview-box">
                <img :src="selectedImage" alt="预览图片" class="preview-image" />
                <el-button
                  type="danger"
                  size="small"
                  circle
                  class="remove-image-btn"
                  @click="removeImage"
                >
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </div>

            <!-- Chapter Selector Popover -->
            <div v-if="showChapterSelector" class="chapter-selector-popover">
              <div class="chapter-selector-header">
                <span>请选择章节上下文</span>
                <el-button size="small" circle @click="showChapterSelector = false"><el-icon><Close /></el-icon></el-button>
              </div>
              
              <div class="chapter-list-container" v-if="chapterStore.chapters && chapterStore.chapters.length > 0">
                 <el-tree
                    :data="chapterTreeData"
                    :props="defaultProps"
                    @node-click="handleNodeClick"
                    class="chapter-tree"
                    highlight-current
                    :expand-on-click-node="false"
                    default-expand-all
                 >
                    <template #default="{ node, data }">
                        <span class="custom-tree-node">
                           <span>{{ node.label }}</span>
                           <span v-if="data.type" class="node-type-tag">{{ data.type_label }}</span>
                        </span>
                    </template>
                 </el-tree>
              </div>
              <div v-else class="no-chapter-data">
                暂无章节数据
              </div>
            </div>

            <div class="input-row">
              <el-upload
                :show-file-list="false"
                :before-upload="handleImageUpload"
                accept="image/*"
                class="image-upload-btn"
              >
                <el-button type="default" :icon="Picture" circle title="上传图片" />
              </el-upload>

              <el-input
                v-model="inputMessage"
                placeholder="请输入您的问题...（支持 Ctrl+V 粘贴图片，输入 # 选择章节）"
                :rows="3"
                type="textarea"
                @keyup.ctrl.enter="handleSend"
                @paste="handlePaste"
                class="message-input"
              />

              <el-button type="primary" @click="handleSend" :loading="loading" :disabled="!inputMessage.trim()">
                发送 (Ctrl+Enter)
              </el-button>
            </div>
          </div>
        </el-card>
      </el-main>
    </el-container>

    <!-- Quiz Modal -->
    <el-dialog
      v-model="showQuizModal"
      title="智能生成题目"
      width="700px"
      :close-on-click-modal="false"
      destroy-on-close
      @close="resetQuiz"
    >
      <div v-if="quizData" class="quiz-modal-content">
        <div v-for="(q, index) in quizData.questions" :key="index" class="quiz-item">
          <div class="quiz-question-header">
            <span class="question-index">题目 {{ index + 1 }}</span>
            <el-tag size="small">{{ q.quiz_type }}</el-tag>
          </div>
          <div class="quiz-question-text">{{ q.question }}</div>
          
          <!-- Choice -->
          <div v-if="q.quiz_type === 'choice' || q.quiz_type === 'mixed' && q.options" class="quiz-options">
            <el-radio-group v-model="userAnswers[index]" :disabled="isSubmitted">
              <el-radio v-for="(val, key) in q.options" :key="key" :label="key" class="quiz-option-item">
                <span class="option-key">{{ key }}.</span> {{ val }}
              </el-radio>
            </el-radio-group>
          </div>
          
          <!-- Blank / Translation / Writing -->
          <div v-else class="quiz-text-input">
            <el-input 
              v-model="userAnswers[index]" 
              type="textarea" 
              :rows="2" 
              placeholder="请输入答案" 
              :disabled="isSubmitted"
            />
          </div>

          <!-- Result -->
          <div v-if="isSubmitted" class="quiz-result-box">
            <div class="result-header">
              <span class="label">参考答案：</span>
              <span class="value">{{ q.correct_answer }}</span>
            </div>
            <div class="result-explanation">
              <span class="label">解析：</span>
              <span class="value">{{ q.explanation }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showQuizModal = false">关闭</el-button>
          <el-button type="primary" @click="submitQuiz" v-if="!isSubmitted">
            提交答案
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { deleteChatSession, getChatHistory, getChatSessions, sendChatMessage } from '@/api'
import { useChapterStore } from '@/stores'
import { Close, Delete, Loading, Picture, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

const chapterStore = useChapterStore()
const messages = ref<any[]>([])
const inputMessage = ref('')
const loading = ref(false)
const mode = ref('chat') // 'chat' or 'quiz'
const quizPrompt = ref('')
const quizData = ref<any>(null)
const userAnswers = ref<any>({})
const isSubmitted = ref(false)
const showQuizModal = ref(false)
const showChapterSelector = ref(false)

const selectedContext = ref<{type: string, id: number, label: string} | null>(null)

const chapterTreeData = computed(() => {
  if (!chapterStore.chapters || !Array.isArray(chapterStore.chapters)) {
      return []
  }
  return chapterStore.chapters.map((c: any) => ({
    label: c.title,
    value: c.title,
    id: c.id,
    type: 'chapter',
    type_label: '章',
    children: c.sections?.map((s: any) => ({
      label: s.title,
      value: s.title,
      id: s.id,
      type: 'section',
      type_label: '节',
      children: s.subsections?.map((sub: any) => ({
         label: sub.title,
         value: sub.title,
         id: sub.id,
         type: 'subsection',
         type_label: '小节'
      }))
    }))
  }))
})

const defaultProps = {
  children: 'children',
  label: 'label',
}

watch(inputMessage, async (newVal) => {
  if (newVal.endsWith('#') || newVal.endsWith('＃')) {
    // Ensure chapters are loaded
    if (!chapterStore.chapters || chapterStore.chapters.length === 0) {
        // Force reload without await to ensure UI updates
        chapterStore.fetchChapters()
    }
    showChapterSelector.value = true
  } else if (!newVal.includes('#') && !newVal.includes('＃')) {
    // Optional: close if # is removed? maybe not strictly necessary
    showChapterSelector.value = false
  }
  
  // 如果删除了引用标记，清空上下文
  if (selectedContext.value && !newVal.includes(`【参考：${selectedContext.value.label}】`)) {
      selectedContext.value = null
  }
})

const handleNodeClick = (data: any) => {
  // Replace the trailing # with the selected text formatted as a tag/context
  inputMessage.value = inputMessage.value.replace(/([#＃])$/, `【参考：${data.value}】 `)
  showChapterSelector.value = false
  
  // 保存上下文信息
  selectedContext.value = {
      type: data.type,
      id: data.id,
      label: data.value
  }
}

const resetQuiz = () => {
  quizData.value = null
  userAnswers.value = {}
  isSubmitted.value = false
}

const submitQuiz = () => {
  isSubmitted.value = true
  ElMessage.success('答案已提交，请查看解析')
}
const sessionId = ref('')
const messagesRef = ref<HTMLElement>()
const sessions = ref<any[]>([])
const selectedImage = ref<string>('')  // 存储选中的图片base64

const currentSessionMessageCount = computed(() => messages.value.length)

onMounted(async () => {
  await chapterStore.fetchChapters()
  await fetchSessions()

  // 如果有历史会话，加载最近的一个，否则创建新会话
  if (sessions.value.length > 0) {
    await handleLoadSession(sessions.value[0])
  } else {
    handleNewSession()
  }
})

const fetchSessions = async () => {
  try {
    const res: any = await getChatSessions()
    sessions.value = res || []
  } catch (error) {
    console.error('Failed to fetch sessions:', error)
  }
}

const handleNewSession = () => {
  sessionId.value = Date.now().toString()
  messages.value = []
  inputMessage.value = ''

  ElMessage.success('已创建新会话')
}

const handleLoadSession = async (session: any) => {
  try {
    sessionId.value = session.session_id

    const history: any = await getChatHistory(session.session_id)

    // 转换历史记录为消息格式
    messages.value = []
    history.forEach((record: any) => {
      messages.value.push({
        id: `user-${record.id}`,
        role: 'user',
        content: record.user_message
      })
      messages.value.push({
        id: `assistant-${record.id}`,
        role: 'assistant',
        content: record.assistant_message
      })
    })

    scrollToBottom()
  } catch (error: any) {
    ElMessage.error(error.message || '加载会话失败')
  }
}

const handleDeleteSession = async (sessionIdToDelete: string) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个会话吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteChatSession(sessionIdToDelete)

    // 从列表中移除
    sessions.value = sessions.value.filter(s => s.session_id !== sessionIdToDelete)

    // 如果删除的是当前会话，创建新会话
    if (sessionIdToDelete === sessionId.value) {
      if (sessions.value.length > 0) {
        await handleLoadSession(sessions.value[0])
      } else {
        handleNewSession()
      }
    }

    ElMessage.success('会话已删除')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleGenerateQuiz = () => {
  if (!quizPrompt.value.trim()) return
  inputMessage.value = quizPrompt.value
  handleSend()
}

const handleSend = async () => {
  if (!inputMessage.value.trim()) return

  const userMessage = inputMessage.value
  const imageData = selectedImage.value  // 获取图片数据

  // 添加用户消息到显示列表（包含图片）
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMessage,
    image: imageData  // 保存图片用于显示
  })

  inputMessage.value = ''
  selectedImage.value = ''  // 清空已选择的图片
  loading.value = true

  try {
    // 构建请求数据
    const requestData: any = {
      message: userMessage,
      session_id: sessionId.value,
      use_rag: true,
      mode: mode.value
    }
    
    // 如果有选中的上下文，添加到请求中
    if (selectedContext.value && userMessage.includes(`【参考：${selectedContext.value.label}】`)) {
        requestData.context_type = selectedContext.value.type
        requestData.context_id = selectedContext.value.id
    }

    // 如果有图片，添加到请求中（只发送base64部分，不包含data:image前缀）
    if (imageData) {
      // 提取base64数据部分
      const base64Data = imageData.split(',')[1] || imageData
      requestData.image = base64Data
    }

    const res: any = await sendChatMessage(requestData)

    if (mode.value === 'quiz') {
      try {
        let quizJson = null
        // Try direct parse
        try {
          const parsed = JSON.parse(res.assistant_message)
          if (parsed.generate_interactive_quiz_response) {
            quizJson = parsed.generate_interactive_quiz_response
          }
        } catch (e) {}
        
        // Try regex if direct parse failed
        if (!quizJson) {
          const match = res.assistant_message.match(/\{[\s\S]*"generate_interactive_quiz_response"[\s\S]*\}/)
          if (match) {
             const parsed = JSON.parse(match[0])
             quizJson = parsed.generate_interactive_quiz_response
          }
        }
        
        if (quizJson) {
           quizData.value = quizJson
           showQuizModal.value = true
           ElMessage.success('题目生成成功！')
        }
      } catch (e) {
        console.error("Quiz parsing error", e)
      }
    }

    messages.value.push({
      id: res.id,
      role: 'assistant',
      content: res.assistant_message
    })

    scrollToBottom()

    // 刷新会话列表
    await fetchSessions()
  } catch (e) {
    console.error(e)
    ElMessage.error('发送失败')
  } finally {
    loading.value = false
  }
}

const formatMessage = (content: string) => {
  // 简单的Markdown格式转换
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

const formatTime = (time: string) => {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  // 1分钟内
  if (diff < 60000) return '刚刚'
  // 1小时内
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  // 今天
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  // 昨天
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  // 更早
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const handleImageUpload = (file: File) => {
  // 验证文件类型
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }

  // 验证文件大小（限制5MB）
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB！')
    return false
  }

  // 读取文件并转换为base64
  const reader = new FileReader()
  reader.onload = (e) => {
    selectedImage.value = e.target?.result as string
    ElMessage.success('图片已选择')
  }
  reader.readAsDataURL(file)

  // 返回false阻止自动上传
  return false
}

const removeImage = () => {
  selectedImage.value = ''
  ElMessage.info('已移除图片')
}

const handlePaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items
  if (!items) return

  // 遍历剪贴板项目，查找图片
  for (let i = 0; i < items.length; i++) {
    const item = items[i]

    // 检查是否是图片类型
    if (item.type.startsWith('image/')) {
      event.preventDefault()  // 阻止默认粘贴行为

      const file = item.getAsFile()
      if (!file) continue

      // 验证文件大小（限制5MB）
      const isLt5M = file.size / 1024 / 1024 < 5
      if (!isLt5M) {
        ElMessage.error('图片大小不能超过 5MB！')
        return
      }

      // 读取文件并转换为base64
      const reader = new FileReader()
      reader.onload = (e) => {
        selectedImage.value = e.target?.result as string
        ElMessage.success('图片已粘贴')
      }
      reader.readAsDataURL(file)

      break  // 只处理第一张图片
    }
  }
}
</script>

<style scoped>
.chat-container {
  height: calc(100vh - 100px);
  padding: 20px;
}

.chat-layout {
  height: 100%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

/* 左侧会话列表样式 */
.session-sidebar {
  border-right: 1px solid #EBEEF5;
  display: flex;
  flex-direction: column;
  background: #FAFAFA;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #EBEEF5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.session-item {
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid transparent;
  position: relative;
}

.session-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.session-item.active {
  background: #ECF5FF;
  border-color: #409EFF;
}

.session-preview {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 30px;
}

.session-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.session-time {
  margin-right: 10px;
}

.delete-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

/* 右侧聊天区域样式 */
.chat-main {
  padding: 0;
  display: flex;
  flex-direction: column;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  border: none;
  box-shadow: none;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

.message {
  margin-bottom: 20px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message-image {
  margin-bottom: 10px;
  border-radius: 8px;
  overflow: hidden;
  max-width: 100%;
}

.message-img {
  max-width: 100%;
  max-height: 300px;
  width: auto;
  height: auto;
  display: block;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.2s;
}

.message-img:hover {
  transform: scale(1.02);
}

.message.user .message-image {
  background: rgba(255, 255, 255, 0.1);
  padding: 5px;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.message-role {
  margin-left: 8px;
  font-weight: 500;
  font-size: 14px;
}

.message-text {
  line-height: 1.8;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message-text :deep(strong) {
  font-weight: 600;
  color: #409EFF;
}

.message-text :deep(em) {
  font-style: italic;
  color: #67C23A;
}

.chat-input {
  padding: 20px;
  background: white;
  border-top: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
}

.image-preview-container {
  width: 100%;
  margin-bottom: 10px;
}

.image-preview-box {
  position: relative;
  display: inline-block;
  max-width: 200px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7fa;
}

.preview-image {
  width: 100%;
  height: auto;
  display: block;
}

.remove-image-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  background: rgba(255, 255, 255, 0.9);
}

.input-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.image-upload-btn {
  flex-shrink: 0;
}

.message-input {
  flex: 1;
}

.chat-input :deep(.el-textarea) {
  flex: 1;
}

.chapter-selector-popover {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin: 0;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 8px 8px 8px 0;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.1);
  z-index: 2000;
  height: 250px;
  display: flex;
  flex-direction: column;
  width: 400px; /* 固定宽度，不要铺满 */
}

.chapter-selector-header {
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: #606266;
  background: #f5f7fa;
  border-radius: 8px 8px 0 0;
}

.chapter-list-container {
  overflow-y: auto;
  flex: 1;
  padding: 10px;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}

.node-type-tag {
  font-size: 12px;
  color: #909399;
  background-color: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.quiz-main-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
  padding: 40px;
}

.quiz-hero {
  text-align: center;
  max-width: 800px;
  width: 100%;
}

.quiz-hero h2 {
  font-size: 32px;
  color: #303133;
  margin-bottom: 10px;
}

.quiz-subtitle {
  font-size: 16px;
  color: #909399;
  margin-bottom: 40px;
}

.quiz-form {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.quiz-prompt-input-large :deep(.el-textarea__inner) {
  font-size: 16px;
  padding: 15px;
  border-radius: 8px;
}

.quiz-actions-large {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.quiz-actions-large .el-button {
  padding: 12px 40px;
  font-size: 16px;
}

.quiz-modal-content {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 10px;
}

.quiz-item {
  margin-bottom: 25px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.quiz-question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.question-index {
  font-weight: bold;
  font-size: 16px;
  color: #303133;
}

.quiz-question-text {
  font-size: 15px;
  margin-bottom: 15px;
  line-height: 1.6;
}

.quiz-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quiz-option-item {
  margin-left: 0 !important;
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 4px;
}

.quiz-option-item:hover {
  background: #f0f2f5;
}

.option-key {
  font-weight: bold;
  margin-right: 5px;
}

.quiz-text-input {
  margin-top: 10px;
}

.quiz-result-box {
  margin-top: 15px;
  padding: 15px;
  background: #f0f9eb;
  border-radius: 4px;
  border-left: 4px solid #67c23a;
}

.result-header, .result-explanation {
  margin-bottom: 8px;
}

.result-explanation {
  margin-bottom: 0;
}

.label {
  font-weight: bold;
  color: #606266;
}

.value {
  color: #303133;
}
</style>

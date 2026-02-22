<template>
  <div class="chat-container">
    <el-container class="chat-layout">
      <!-- 左侧会话列表 -->
      <el-aside width="280px" class="session-sidebar">
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
              <span>智能问答</span>
              <el-tag v-if="currentSessionMessageCount > 0" type="info">
                当前会话：{{ currentSessionMessageCount }} 条消息
              </el-tag>
            </div>
          </template>

          <div class="chat-messages" ref="messagesRef">
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

          <div class="chat-input">
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
                placeholder="请输入您的问题...（支持 Ctrl+V 粘贴图片）"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { useChapterStore } from '@/stores'
import { sendChatMessage, getChatHistory, getChatSessions, deleteChatSession } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Loading, Picture, Close } from '@element-plus/icons-vue'

const chapterStore = useChapterStore()
const messages = ref<any[]>([])
const inputMessage = ref('')
const loading = ref(false)
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
      use_rag: true
    }

    // 如果有图片，添加到请求中（只发送base64部分，不包含data:image前缀）
    if (imageData) {
      // 提取base64数据部分
      const base64Data = imageData.split(',')[1] || imageData
      requestData.image = base64Data
    }

    const res: any = await sendChatMessage(requestData)

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
</style>

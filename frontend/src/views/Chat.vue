<template>
  <div class="chat-container">
    <el-container class="chat-layout">
      <!-- 左侧边栏 -->
      <el-aside width="280px" class="session-sidebar">
        <div class="sidebar-tabs">
           <div 
             :class="['sidebar-tab', { active: activeTab === 'session' }]" 
             @click="activeTab = 'session'; mode = 'chat'"
           >
             会话
           </div>
           <div 
             :class="['sidebar-tab', { active: activeTab === 'history' }]" 
             @click="activeTab = 'history'; mode = 'quiz'"
           >
             出题历史
           </div>
        </div>

        <!-- 会话列表 -->
        <div v-if="activeTab === 'session'" class="sidebar-content-wrapper">
            <div class="sidebar-action">
              <el-button type="primary" size="small" @click="handleNewSession" style="width: 100%">
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
        </div>

        <!-- 出题历史列表 -->
        <div v-else class="sidebar-content-wrapper">
             <div class="sidebar-action">
                 <el-button type="default" size="small" @click="fetchQuizHistoryList" :loading="historyLoading" style="width: 100%">
                    刷新列表
                 </el-button>
             </div>
             <div class="session-list">
                <div v-for="item in quizHistoryList" :key="item.id" class="history-item" @click="handleLoadQuizHistory(item)">
                    <div class="history-prompt">{{ getQuizPrompt(item) }}</div>
                    <div class="history-meta">
                        <span>{{ formatTime(item.created_at) }}</span>
                        <el-tag size="small" :type="isQuizCompleted(item) ? 'success' : 'info'" effect="plain">
                           {{ isQuizCompleted(item) ? '已完成' : '未完成' }}
                        </el-tag>
                    </div>
                </div>
                <el-empty v-if="quizHistoryList.length === 0" description="暂无出题记录" :image-size="80" />
             </div>
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
                
                <!-- 题目生成卡片 -->
                <div v-if="msg.isQuiz" class="quiz-response-card">
                  <div class="quiz-card-content">
                    <div class="quiz-icon-wrapper">
                      <el-icon :size="24" color="#409EFF"><List /></el-icon>
                    </div>
                    <div class="quiz-info">
                      <div class="quiz-title">{{ msg.quizSummary?.topic || '智能生成练习' }}</div>
                      <div class="quiz-desc">包含 {{ msg.quizSummary?.count || 0 }} 道题目</div>
                    </div>
                  </div>
                  <div class="quiz-card-actions">
                    <el-button 
                      v-if="msg.isCompleted" 
                      type="success" 
                      size="small" 
                      @click="openQuizFromMessage(msg)"
                    >
                      查看记录
                    </el-button>
                    <el-button 
                      v-else 
                      type="primary" 
                      size="small" 
                      @click="openQuizFromMessage(msg)"
                    >
                      继续练习
                    </el-button>
                  </div>
                </div>
                
                <!-- 普通文本消息 -->
                <div v-else class="message-text" v-html="formatMessage(msg.content)"></div>
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
                <!-- Chapter Selector Popover for Quiz Mode -->
                <div v-if="showChapterSelector" class="chapter-selector-popover quiz-popover">
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

                <el-input
                  v-model="quizPrompt"
                  placeholder="请输入出题提示词（支持输入 # 选择章节、节或小节，AI将基于所选内容出题）"
                  :rows="6"
                  type="textarea"
                  class="quiz-prompt-input-large"
                />
                
                <div class="quiz-actions-large">
                  <el-button type="primary" size="large" @click="handleGenerateQuiz" :loading="loading" :disabled="!quizPrompt.trim()">
                    <el-icon class="el-icon--left" v-if="!loading"><Picture /></el-icon>
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
        <!-- Add quiz topic header -->
        <div v-if="quizData.topic" class="quiz-topic-header">
            <strong>出题要求：</strong> {{ quizData.topic }}
        </div>
        
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
import { deleteChatSession, getChatHistory, getChatQuizHistory, getChatSessions, sendChatMessage, submitQuizResult } from '@/api'

import { useChapterStore } from '@/stores'
import { Close, Delete, Loading, Picture, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, nextTick, onMounted, ref, watch } from 'vue'

const chapterStore = useChapterStore()
const messages = ref<any[]>([])
const inputMessage = ref('')
const loading = ref(false)
const mode = ref('chat') // 'chat' or 'quiz'
const activeTab = ref('session') // 'session' or 'history'
const quizHistoryList = ref<any[]>([])
const currentQuizId = ref<number | null>(null)

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

const quizContext = ref<{type: string, id: number, label: string} | null>(null)

// 解析题目内容的工具函数
const parseQuizContent = (content: string) => {
  try {
    if (!content) return { isQuiz: false }
    
    // 1. Try parsing strictly as JSON first (fastest)
    try {
      const parsed = JSON.parse(content)
      // 支持多种格式：generate_interactive_quiz_response, quiz, questions
      const quizData = parsed.generate_interactive_quiz_response || parsed.quiz || { questions: parsed.questions }
      if (quizData && Array.isArray(quizData.questions) && quizData.questions.length > 0) {
           return { isQuiz: true, count: quizData.questions.length, topic: quizData.topic || '智能生成练习', data: quizData }
      }
    } catch(e) {}

    // 2. Cleanup markdown wrappers
    let jsonStr = content
    if (content.includes('```')) {
      const jsonBlock = content.match(/```(?:json)?\s*([\s\S]*?)\s*```/i)
      if (jsonBlock) {
          jsonStr = jsonBlock[1]
      }
    }
    
    // 3. Try parsing cleaned string
    try {
      const parsed = JSON.parse(jsonStr)
      const quizData = parsed.generate_interactive_quiz_response || parsed.quiz || { questions: parsed.questions }
      if (quizData && Array.isArray(quizData.questions) && quizData.questions.length > 0) {
           return { isQuiz: true, count: quizData.questions.length, topic: quizData.topic || '智能生成练习', data: quizData }
      }
    } catch(e) {}

    // 4. Fallback: Find largest JSON-like block
    const firstOpen = jsonStr.indexOf('{')
    const lastClose = jsonStr.lastIndexOf('}')
    if (firstOpen !== -1 && lastClose > firstOpen) {
        const candidate = jsonStr.substring(firstOpen, lastClose + 1)
        try {
          const parsed = JSON.parse(candidate)
          const quizData = parsed.generate_interactive_quiz_response || parsed.quiz || { questions: parsed.questions }
          if (quizData && Array.isArray(quizData.questions) && quizData.questions.length > 0) {
            return { isQuiz: true, count: quizData.questions.length, topic: quizData.topic || '智能生成练习', data: quizData }
          }
        } catch(e) {}
    }

  } catch (e) {
    return { isQuiz: false }
  }
  return { isQuiz: false }
}

// 从消息打开题目
const openQuizFromMessage = (msg: any) => {
  if (msg.quizSummary && msg.quizSummary.data) {
    quizData.value = msg.quizSummary.data
    
    // 设置当前题目ID，确保可以提交更新
    currentQuizId.value = msg.realId || null
    
    // 根据消息状态设置
    if (msg.isCompleted && msg.userAnswers) {
        userAnswers.value = msg.userAnswers
        isSubmitted.value = true
    } else {
        userAnswers.value = {}
        isSubmitted.value = false
    }
    
    showQuizModal.value = true
  }
}

watch(mode, (newMode) => {
  if (newMode === 'chat') {
    nextTick(() => {
      scrollToBottom()
      // 额外延迟滚动，确保在DOM完全就绪后滚动到底部
      setTimeout(() => {
        scrollToBottom()
      }, 100)
    })
  }
})

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

watch(quizPrompt, async (newVal) => {
  if (mode.value === 'quiz') {
    if (newVal.endsWith('#') || newVal.endsWith('＃')) {
      if (!chapterStore.chapters || chapterStore.chapters.length === 0) {
          chapterStore.fetchChapters()
      }
      showChapterSelector.value = true
    } else if (!newVal.includes('#') && !newVal.includes('＃')) {
      showChapterSelector.value = false
    }
    
    if (quizContext.value && !newVal.includes(`【参考：${quizContext.value.label}】`)) {
        quizContext.value = null
    }
  }
})

const handleNodeClick = (data: any) => {
  // Replace the trailing # with the selected text formatted as a tag/context
  const tag = `【参考：${data.value}】 `
  if (mode.value === 'chat') {
      inputMessage.value = inputMessage.value.replace(/([#＃])$/, tag)
      // 保存上下文信息
      selectedContext.value = {
          type: data.type,
          id: data.id,
          label: data.value
      }
  } else {
      quizPrompt.value = quizPrompt.value.replace(/([#＃])$/, tag)
      // 保存上下文信息
      quizContext.value = {
          type: data.type,
          id: data.id,
          label: data.value
      }
  }
  showChapterSelector.value = false
}

const resetQuiz = () => {
  quizData.value = null
  userAnswers.value = {}
  isSubmitted.value = false
}

const historyLoading = ref(false)

const fetchQuizHistoryList = async () => {
    historyLoading.value = true
    try {
        const res: any = await getChatQuizHistory({ limit: 50 })
        quizHistoryList.value = res || []
    } catch (e) {
        console.error(e)
        ElMessage.error('获取出题历史失败')
    } finally {
        historyLoading.value = false
    }
}

const getQuizPrompt = (item: any) => {
    // 兼容新旧数据结构
    if (item.topic) {
        return item.topic.length > 30 ? item.topic.substring(0, 30) + '...' : item.topic
    }
    
    let prompt = item.user_message || ''
    // Clean up system instructions
    if (prompt.includes('用户的出题提示词:')) {
        const parts = prompt.split('用户的出题提示词:')
        if (parts.length > 1) {
            prompt = parts[1].trim()
        }
    }
    return prompt.length > 30 ? prompt.substring(0, 30) + '...' : prompt
}

const isQuizCompleted = (item: any) => {
    // 兼容新旧数据结构
    if (item.is_completed !== undefined) {
        return item.is_completed
    }
    if (item.user_answers) {
        return true
    }
    return !!(item.chat_metadata && item.chat_metadata.user_answers)
}

const handleLoadQuizHistory = (item: any) => {
    // 准备主题/提示词
    // 清理一下 "用户的出题提示词:" 前缀，如果有的话
    let topic = item.topic || item.user_message || ''
    if (topic.includes('用户的出题提示词:')) {
        const parts = topic.split('用户的出题提示词:')
        if (parts.length > 1) {
            topic = parts[1].trim()
        }
    }

    // 如果是新版数据结构，直接使用
    // 关键修复：增加长度判断，因为后端返回未完成的记录时 questions 可能是空数组
    if (item.questions && item.questions.length > 0) {
        currentQuizId.value = item.chat_history_id || item.id // 优先使用 chat_history_id 以兼容提交接口
        quizData.value = {
            questions: item.questions,
            quiz_type: item.quiz_type,
            topic: topic // 确保 topic 被传入
        }
        
        // 关键修复：
        // 1. 如果有 user_answers，则加载用户的答案
        // 2. 只有当 item.is_completed 为 true 时，才设为“已提交”状态
        // 3. 如果只是有答案但未完成（理论上不应发生，但为了保险），也允许继续编辑
        if (item.user_answers) {
            userAnswers.value = item.user_answers
        } else {
            userAnswers.value = {}
        }
        
        isSubmitted.value = !!item.is_completed
        
        showQuizModal.value = true
        return
    }

    // 旧版解析逻辑 (或者处理未完成的 ChatHistory 记录)
    // 这里的 item.id 是 chat_history_id
    currentQuizId.value = item.chat_history_id || item.id
    
    // Parse quiz data
    let quizJson = null
    try {
        // Try direct parse first
        try {
          // Remove potential markdown wrappers
          let cleanMsg = item.assistant_message.replace(/```json\s*/g, '').replace(/```\s*/g, '')
          const parsed = JSON.parse(cleanMsg)
          if (parsed.generate_interactive_quiz_response) {
            quizJson = parsed.generate_interactive_quiz_response
          } else {
            quizJson = parsed
          }
        } catch (e) {}
        
        if (!quizJson) {
           const match = item.assistant_message.match(/\{[\s\S]*"generate_interactive_quiz_response"[\s\S]*\}/)
           if (match) {
               const parsed = JSON.parse(match[0])
               quizJson = parsed.generate_interactive_quiz_response
           } else {
               // Try looser regex
               const match2 = item.assistant_message.match(/\{[\s\S]*"questions"[\s\S]*\}/)
               if (match2) {
                   const parsed = JSON.parse(match2[0])
                   quizJson = parsed.generate_interactive_quiz_response || parsed
               }
           }
        }
    } catch (e) {
        console.error("Failed to parse quiz history", e)
    }
    
    if (quizJson) {
        quizData.value = quizJson
        // 确保旧版数据也有 topic
        if (!quizData.value.topic) {
            quizData.value.topic = topic
        }
        
        // Set user answers if available
        if (item.chat_metadata && item.chat_metadata.user_answers) {
            userAnswers.value = item.chat_metadata.user_answers
            isSubmitted.value = true
        } else {
            userAnswers.value = {}
            isSubmitted.value = false
        }
        
        showQuizModal.value = true
    } else {
        ElMessage.error('无法解析该题目的数据')
    }
}

watch(activeTab, (val) => {
    if (val === 'history') {
        fetchQuizHistoryList()
    }
})

const submitQuiz = async () => {
  // 1. Calculate Score
  let correctCount = 0
  let totalCount = 0
  const results: boolean[] = []
  
  if (quizData.value && quizData.value.questions) {
      quizData.value.questions.forEach((q: any, index: number) => {
          totalCount++
          const userAns = userAnswers.value[index]
          const correctAns = q.correct_answer
          
          // Normalize for comparison
          let isCorrect = false
          if (userAns && correctAns) {
             // For choice questions (A, B, C, D)
             if (q.quiz_type === 'choice' || q.type === 'choice') {
                 isCorrect = userAns.toString().trim().toUpperCase() === correctAns.toString().trim().toUpperCase()
             } else {
                 // For others, simple string match
                 isCorrect = userAns.toString().trim().toLowerCase() === correctAns.toString().trim().toLowerCase()
             }
          }
          
          if (isCorrect) correctCount++
          results.push(isCorrect)
      })
  }
  
  const score = totalCount > 0 ? Math.round((correctCount / totalCount) * 100) : 0
  
  // 2. Submit to backend
  if (currentQuizId.value) {
      try {
          await submitQuizResult(currentQuizId.value, {
              user_answers: userAnswers.value,
              score: score,
              is_correct: results
          })
          ElMessage.success(`提交成功！得分: ${score}`)
          
          // 更新本地消息状态
          const msg = messages.value.find(m => m.realId === currentQuizId.value)
          if (msg) {
              msg.isCompleted = true
              msg.userAnswers = userAnswers.value
          }
          
          // Refresh history if in history tab
          if (activeTab.value === 'history') {
              fetchQuizHistoryList()
          }
      } catch (e) {
          console.error(e)
          ElMessage.warning('提交失败，但答案已在本地显示解析')
      }
  } else {
      ElMessage.success('答案已提交，请查看解析')
  }
  
  isSubmitted.value = true
}
const sessionId = ref('')
const messagesRef = ref<HTMLElement>()
const sessions = ref<any[]>([])
const selectedImage = ref<string>('')  // 存储选中的图片base64

const currentSessionMessageCount = computed(() => messages.value.length)

// onMounted should be imported from 'vue' - it is already imported in the file

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
  selectedImage.value = ''

  ElMessage.success('已创建新会话')
}

const handleLoadSession = async (session: any) => {
  try {
    sessionId.value = session.session_id

    const history: any = await getChatHistory(session.session_id)

    // 转换历史记录为消息格式
    messages.value = []
    if (history) {
      history.forEach((record: any) => {
        messages.value.push({
          id: `user-${record.id}`,
          role: 'user',
          content: record.user_message
        })
        
        // 预处理 AI 消息，检查是否为题目
        const quizInfo = parseQuizContent(record.assistant_message)
        
        messages.value.push({
          id: `assistant-${record.id}`,
          realId: record.id,
          role: 'assistant',
          content: record.assistant_message,
          isQuiz: quizInfo.isQuiz,
          quizSummary: quizInfo.isQuiz ? quizInfo : null,
          isCompleted: !!(record.chat_metadata && record.chat_metadata.user_answers),
          userAnswers: record.chat_metadata?.user_answers
        })
      })
    }
    
    // 如果是切换会话，清空输入框和图片
    inputMessage.value = ''
    selectedImage.value = ''

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

const handleGenerateQuiz = async () => {
  if (!quizPrompt.value.trim()) return
  
  loading.value = true
  
  try {
    const requestData: any = {
      message: quizPrompt.value,
      session_id: sessionId.value, // 可以使用当前会话ID，或者生成临时的
      use_rag: true,
      mode: 'quiz'
    }
    
    // 如果有选中的上下文，添加到请求中
    if (quizContext.value && quizPrompt.value.includes(`【参考：${quizContext.value.label}】`)) {
        requestData.context_type = quizContext.value.type
        requestData.context_id = quizContext.value.id
    }
    
    const res: any = await sendChatMessage(requestData)
    
    // 保存当前 Quiz ID
    if (res && res.id) {
        currentQuizId.value = res.id
    }
    
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
       
       // 手动将题目消息添加到聊天记录中，以便切换回聊天模式时可以看到
       // 1. 添加用户消息
       messages.value.push({
         id: `user-${res.id}`, 
         role: 'user',
         content: quizPrompt.value
       })
       
       // 2. 添加助手消息（题目卡片）
       const quizInfo = parseQuizContent(res.assistant_message)
       messages.value.push({
          id: `assistant-${res.id}`,
          realId: res.id,
          role: 'assistant',
          content: res.assistant_message,
          isQuiz: true,
          quizSummary: quizInfo.isQuiz ? quizInfo : null,
          isCompleted: false,
          userAnswers: null
       })
       
       // 滚动到底部
       scrollToBottom()
       
       // 刷新出题历史
       if (activeTab.value === 'history') {
           fetchQuizHistoryList()
       }
       loading.value = false
       return
    } else {
       ElMessage.warning('未能生成有效题目格式，请重试')
       console.log("Raw response:", res.assistant_message)
    }
    
  } catch (e) {
    console.error(e)
    ElMessage.error('生成题目失败')
  } finally {
    loading.value = false
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
      use_rag: true,
      mode: mode.value
    }
    
    // 如果有选中的上下文，添加到请求中
    // 检查输入框内容是否包含选中的标签
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
          // Check if response is wrapped in XML tag <quiz> or similar, or just plain JSON
          // Clean up potential markdown code blocks ```json ... ```
          let cleanMsg = res.assistant_message.replace(/```json\s*/g, '').replace(/```\s*/g, '')
          const parsed = JSON.parse(cleanMsg)
          if (parsed.generate_interactive_quiz_response) {
            quizJson = parsed.generate_interactive_quiz_response
          } else {
             // Maybe it's the root object directly?
             quizJson = parsed
          }
        } catch (e) {}
        
        // Try regex if direct parse failed
        if (!quizJson) {
          const match = res.assistant_message.match(/\{[\s\S]*"generate_interactive_quiz_response"[\s\S]*\}/)
          if (match) {
             const parsed = JSON.parse(match[0])
             quizJson = parsed.generate_interactive_quiz_response
          } else {
             // Try looser regex for just the object if the key is missing wrapper
             const match2 = res.assistant_message.match(/\{[\s\S]*"questions"[\s\S]*\}/)
             if (match2) {
                const parsed = JSON.parse(match2[0])
                quizJson = parsed.generate_interactive_quiz_response || parsed
             }
          }
        }
        
        if (quizJson) {
       quizData.value = quizJson
       // Force update session list if needed, but DO NOT add message to current view
       showQuizModal.value = true
       ElMessage.success('题目生成成功！')
       loading.value = false
       return 
    } else {
       // 如果解析失败，可能是LLM返回了普通文本回复，此时按普通消息处理
       console.log("Quiz parse failed, fallback to message display", res.assistant_message)
    }
      } catch (e) {
        console.error("Quiz parsing error", e)
      }
    }

    messages.value.push({
      id: res.id,
      realId: res.id,
      role: 'assistant',
      content: res.assistant_message,
      isQuiz: parseQuizContent(res.assistant_message).isQuiz,
      quizSummary: parseQuizContent(res.assistant_message).isQuiz ? parseQuizContent(res.assistant_message) : null,
      isCompleted: false,
      userAnswers: null
    })

    scrollToBottom()

    // 刷新会话列表
    await fetchSessions()
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e.message || '发送失败')
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
  position: relative;
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

/* Sidebar Tabs */
.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid #EBEEF5;
  background: white;
}

.sidebar-tab {
  flex: 1;
  text-align: center;
  padding: 12px;
  font-size: 14px;
  cursor: pointer;
  color: #606266;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
}

.sidebar-tab:hover {
  color: #409EFF;
}

.sidebar-tab.active {
  color: #409EFF;
  border-bottom-color: #409EFF;
  background: #ECF5FF;
}

.sidebar-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-action {
  padding: 10px 20px;
  background: white;
  border-bottom: 1px solid #EBEEF5;
}

/* History List */
.history-item {
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.history-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.history-prompt {
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.quiz-response-card {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 15px;
  margin-top: 5px;
  max-width: 300px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.quiz-card-content {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.quiz-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #ecf5ff;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 12px;
}

.quiz-info {
  flex: 1;
  overflow: hidden;
}

.quiz-title {
  font-size: 15px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quiz-desc {
  font-size: 13px;
  color: #909399;
}

.quiz-card-actions {
  display: flex;
  justify-content: flex-end;
}
</style>

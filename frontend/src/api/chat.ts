import type { ChatHistory, ChatRequest, ChatSession } from '@/types'
import request from '@/utils/request'

// 发送聊天消息
export const sendChatMessage = (data: ChatRequest) => {
  return request.post<ChatHistory>('/chat/', data)
}

// 获取聊天历史
export const getChatHistory = (sessionId: string, params?: { limit?: number }) => {
  return request.get<ChatHistory[]>(`/chat/history/${sessionId}`, { params })
}

// 获取会话列表
export const getChatSessions = () => {
  return request.get<ChatSession[]>('/chat/sessions')
}

// 删除会话
export const deleteChatSession = (sessionId: string) => {
  return request.delete(`/chat/session/${sessionId}`)
}

// 获取出题历史
export const getChatQuizHistory = (params?: { limit?: number }) => {
  return request.get<any[]>('/chat/quiz/history', { params })
}

// 提交测验结果
export const submitQuizResult = (messageId: number, data: any) => {
  return request.post(`/chat/quiz/submit/${messageId}`, data)
}


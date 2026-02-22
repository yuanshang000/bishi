import request from '@/utils/request'
import type { ChatRequest, ChatHistory, ChatSession } from '@/types'

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

import request from '@/utils/request'
import type {
  WrongQuestion,
  WeakKnowledgePoint,
  WrongQuestionStats,
  ReviewQuizResponse
} from '@/types'

// 获取错题列表
export const getWrongQuestions = (params?: {
  chapter_id?: number
  subsection_id?: number
  is_mastered?: boolean
  limit?: number
}) => {
  return request.get<WrongQuestion[]>('/wrong-questions/list', { params })
}

// 获取错题目录树
export const getWrongQuestionsTree = () => {
  return request.get<any[]>('/wrong-questions/tree')
}

// 举一反三：生成相似题目
export const generateSimilarQuestion = (wrongQuestionId: number) => {
  return request.post<any>(`/wrong-questions/${wrongQuestionId}/generate-similar`)
}

// 获取薄弱知识点统计
export const getWeakKnowledgePoints = (params?: {
  chapter_id?: number
  top_k?: number
}) => {
  return request.get<WeakKnowledgePoint[]>('/wrong-questions/weak-points', { params })
}

// 创建错题重练练习
export const createReviewQuiz = (params?: {
  chapter_id?: number
  question_count?: number
}) => {
  return request.post<ReviewQuizResponse>('/wrong-questions/review-quiz', null, { params })
}

// 提交错题重练答案
export const submitReviewQuiz = (data: {
  wrong_question_ids: number[]
  user_answers: any[]
}) => {
  return request.post('/wrong-questions/review-quiz/submit', data)
}

// 更新错题掌握状态
export const updateMasteryStatus = (
  wrongQuestionId: number,
  data: { is_mastered: boolean; retry_score?: number }
) => {
  return request.patch(`/wrong-questions/${wrongQuestionId}/mastery`, data)
}

// 获取错题统计
export const getWrongQuestionStats = () => {
  return request.get<WrongQuestionStats>('/wrong-questions/stats')
}

// 获取错题详情
export const getWrongQuestionDetail = (wrongQuestionId: number) => {
  return request.get(`/wrong-questions/${wrongQuestionId}/detail`)
}

// 按章节统计错题
export const getWrongQuestionStatsByChapter = () => {
  return request.get('/wrong-questions/stats/by-chapter')
}

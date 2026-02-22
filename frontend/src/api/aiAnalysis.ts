import request from '@/utils/request'
import type {
  AIAnalysisResult,
  WeakKnowledgePoint,
  LearningRecord,
  TargetedQuizRequest
} from '@/types'

/**
 * AI 学情分析 API
 */

// 获取我的学习分析
export const getMyLearningAnalysis = () => {
  return request.get<AIAnalysisResult>('/ai/analysis/my-learning')
}

// 获取我的薄弱知识点
export const getMyWeakPoints = (topK = 5) => {
  return request.get<{
    success: boolean
    weak_points: WeakKnowledgePoint[]
    total: number
  }>('/ai/analysis/weak-points', {
    params: { top_k: topK }
  })
}

// 获取我的学习记录
export const getMyLearningRecords = (limit = 20) => {
  return request.get<{
    success: boolean
    records: LearningRecord[]
    total: number
  }>('/ai/analysis/learning-records', {
    params: { limit }
  })
}

// 获取目标完成情况进度
export const getGoalProgress = () => {
  return request.get<{
    success: boolean
    data: any[]
  }>('/ai/analysis/goal-progress')
}

// 创建针对性练习（AI推荐）
export const createAITargetedQuiz = (data: TargetedQuizRequest) => {
  return request.post('/ai/quiz/create-targeted', data)
}

// 创建综合练习（基于薄弱点的混合题型）
export const createComprehensiveQuiz = (data: {
  weak_points: any[]
  question_count?: number
}) => {
  return request.post('/ai/quiz/create-comprehensive', data)
}

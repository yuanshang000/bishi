import type {
  KnowledgePointsResponse,
  Quiz,
  QuizCreateForm,
  QuizCreateTargetedForm,
  QuizResult,
  QuizSubmitForm
} from '@/types';
import request from '@/utils/request';

// 创建练习
export const createQuiz = (data: QuizCreateForm) => {
  return request.post<Quiz>('/quiz/create', data)
}

// 创建针对性练习（指定知识点）
export const createTargetedQuiz = (data: QuizCreateTargetedForm) => {
  return request.post<Quiz>('/quiz/create-targeted', data)
}

// 创建个性化练习（基于薄弱知识点）
export const createPersonalizedQuiz = (data: QuizCreateForm) => {
  return request.post<Quiz>('/quiz/create-personalized', data)
}

// 提交练习答案
export const submitQuiz = (data: QuizSubmitForm) => {
  return request.post<QuizResult>('/quiz/submit', data)
}

// 获取练习历史
export const getQuizHistory = (params?: { practice_mode?: string; chapter_id?: number; subsection_id?: number; limit?: number }) => {
  return request.get<Quiz[]>('/quiz/history', { params })
}

// 获取练习统计
export const getQuizStats = (chapterId?: number | null, practiceMode?: string) => {
  return request.get('/quiz/stats', { 
    params: { 
      chapter_id: chapterId,
      practice_mode: practiceMode
    } 
  })
}

// 获取练习详情
export const getQuiz = (quizId: number) => {
  return request.get<Quiz>(`/quiz/${quizId}`)
}

// 获取章节知识点列表
export const getKnowledgePoints = (chapterId: number) => {
  return request.get<KnowledgePointsResponse>(`/quiz/knowledge-points/${chapterId}`)
}

// 生成单词章节训练
export const generateWordTraining = (data: { subsection_id: number; count: number; practice_mode?: string }) => {
  return request.post<Quiz>('/quiz/word_training/generate', data)
}

// 获取小节练习统计
export const getSubsectionStats = (subsectionId: number) => {
  return request.get<any>(`/quiz/stats/subsection/${subsectionId}`)
}

// 生成综合训练（按节出题）
export const createSectionComprehensiveQuiz = (data: {
  section_id: number;
  difficulty: string;
  count: number;
}) => {
  return request.post<Quiz>('/quiz/comprehensive/generate', data)
}

// 教师端：获取成绩分布统计
export const getTeacherGradeStats = (params: { chapter_id?: number; section_id?: number; subsection_id?: number }) => {
  return request.get('/quiz/stats/teacher/grades', { params })
}

// 教师端：获取知识点薄弱项统计
export const getTeacherKpStats = (params: { chapter_id?: number; section_id?: number; subsection_id?: number; limit?: number }) => {
  return request.get('/quiz/stats/teacher/knowledge_points', { params })
}

// 获取节练习统计
export const getSectionStats = (sectionId: number) => {
  return request.get<any>(`/quiz/stats/section/${sectionId}`)
}

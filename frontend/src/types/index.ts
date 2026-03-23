// 用户相关类型
export interface User {
  id: number
  username: string
  email?: string
  full_name?: string
  role: 'teacher' | 'student'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  username: string
  password: string
  email?: string
  full_name?: string
  role: 'teacher' | 'student'
}

export interface TokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
}

// 章节相关类型
export interface SubSection {
  id: number
  section_id: number
  title: string
  content?: string
  requirements?: string
  weight: number
  passing_score: number
  min_questions: number
  created_at: string
  updated_at: string
}

export interface Section {
  id: number
  chapter_id: number
  title: string
  sequence: number
  created_at: string
  updated_at: string
  subsections?: SubSection[]
}

export interface Chapter {
  id: number
  chapter_number: number
  title: string
  description?: string
  learning_objectives?: string
  key_points?: string
  word_count: number
  difficulty_level: string
  created_at: string
  updated_at: string
  sections?: Section[]
}

export interface ChapterForm {
  chapter_number: number
  title: string
  description?: string
  learning_objectives?: string[]
  key_points?: string[]
  word_count?: number
  difficulty_level?: string
}

// 文档相关类型
export interface Document {
  id: number
  chapter_id: number
  title: string
  doc_type: 'textbook' | 'teaching_plan' | 'exercise' | 'reference'
  file_path?: string
  file_name?: string
  file_size: number
  is_vectorized: boolean
  vector_count: number
  created_at: string
  updated_at: string
}

export interface DocumentForm {
  chapter_id: number
  title: string
  doc_type: string
  content?: string
}

// 练习相关类型
export interface Quiz {
  id: number
  user_id: number
  chapter_id?: number  // 改为可选，随机和综合练习不需要章节
  subsection_id?: number
  practice_mode: 'chapter' | 'subsection' | 'random' | 'comprehensive'  // 添加练习方式
  quiz_type: string
  question_count: number
  questions?: any[]
  score: number
  accuracy: number
  time_spent: number
  is_completed: boolean
  knowledge_point_ids?: string[]
  started_at?: string
  completed_at?: string
  created_at: string
}

export interface QuizCreateForm {
  practice_mode: 'chapter' | 'subsection' | 'random' | 'comprehensive'  // 添加练习方式
  chapter_id?: number  // 改为可选
  subsection_id?: number
  quiz_type: 'choice' | 'blank' | 'translation' | 'matching' | 'ordering' | 'short_answer' | 'writing' | 'reading'
  question_count: number
  difficulty: 'easy' | 'intermediate' | 'hard'
  knowledge_point_ids?: string[]
}

export interface QuizCreateTargetedForm extends QuizCreateForm {
  knowledge_point_ids?: string[]
}

export interface QuizSubmitForm {
  quiz_id: number
  user_answers: any[]
  time_spent?: number // 新增：用时（秒）
}

export interface QuizResult {
  quiz_id: number
  score: number
  accuracy: number
  correct_count: number
  total_count: number
  time_spent: number
  wrong_count: number
  results: Array<{
    question_index: number
    user_answer: any
    correct_answer: any
    is_correct: boolean
    score?: number
    feedback?: string
    explanation: string
  }>
}

// 知识点相关类型
export interface KnowledgePoint {
  id: string
  name: string
  category: string
  description?: string
  examples?: string[]
}

export interface KnowledgePointsResponse {
  chapter_id: number
  knowledge_points: KnowledgePoint[]
}

// 错题相关类型
export interface WrongQuestion {
  id: number
  user_id: number
  quiz_record_id: number
  chapter_id: number
  question_type: string
  question_data: any
  user_answer: any
  correct_answer: any
  score: number
  knowledge_point_ids?: string[]
  is_mastered: boolean
  retry_count: number
  last_retry_score?: number
  last_retry_at?: string
  created_at: string
}

export interface WeakKnowledgePoint {
  knowledge_point_id: string
  error_count: number
  avg_score: number
}

export interface WrongQuestionStats {
  total_count: number
  unmastered_count: number
  mastered_count: number
  mastery_rate: number
}

export interface ReviewQuizResponse {
  questions: any[]
  wrong_question_ids: number[]
}

// 聊天相关类型
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatHistory {
  id: number
  user_id: number
  chapter_id?: number
  session_id: string
  user_message: string
  assistant_message: string
  message_role: string
  doc_count: number
  created_at: string
}

export interface ChatRequest {
  message: string
  chapter_id?: number
  session_id?: string
  use_rag?: boolean
}

export interface ChatSession {
  session_id: string
  chapter_id?: number
  last_message_at: string
  message_count: number
  preview: string
}

// API响应类型
export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

// AI 分析相关类型
export interface AIAnalysisResult {
  success: boolean
  report: string
  data: {
    status: string
    total_records: number
    average_score: number
    recent_average: number
    trend: 'improving' | 'declining' | 'stable' | 'insufficient_data'
    trend_text: string
    weak_points: WeakKnowledgePointDetail[]
    has_weak_points: boolean
    subsection_mastery?: Array<{
        id: number
        title: string
        full_title: string
        average_score: number
        practice_count: number
        has_data: boolean
    }>
  }
}

export interface WeakKnowledgePointDetail {
  knowledge_point_id: string
  error_count: number
  severity: 'high' | 'medium' | 'low'
  related_chapters: number[]
}

export interface LearningRecord {
  quiz_id: number
  chapter_id: number
  chapter_title: string
  quiz_type: string
  question_count: number
  score: number
  accuracy: number
  time_spent: number
  knowledge_points: string[]
  completed_at: string
}

export interface TargetedQuizRequest {
  chapter_id?: number
  quiz_type: string
  question_count?: number
}

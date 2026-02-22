import type { Chapter, ChapterForm } from '@/types';
import request from '@/utils/request';

// 获取章节列表
export const getChapters = (params?: { skip?: number; limit?: number }) => {
  return request.get<Chapter[]>('/chapters/', { params })
}

// 获取章节详情
export const getChapter = (chapterId: number) => {
  return request.get<Chapter>(`/chapters/${chapterId}`)
}

// 创建章节
export const createChapter = (data: ChapterForm) => {
  return request.post<Chapter>('/chapters/', data)
}

// 更新章节
export const updateChapter = (chapterId: number, data: Partial<ChapterForm>) => {
  return request.put<Chapter>(`/chapters/${chapterId}`, data)
}

// 删除章节
export const deleteChapter = (chapterId: number) => {
  return request.delete(`/chapters/${chapterId}`)
}

// 上传课程结构
export const uploadStructure = (data: FormData) => {
  return request.post('/chapters/structure/upload', data, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 导出章节
export const exportChapter = (chapterId: number, format: string = 'md') => {
  return request.get(`/chapters/${chapterId}/export`, {
    params: { format },
    responseType: 'blob'
  })
}

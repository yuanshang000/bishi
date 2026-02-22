import type { Document, DocumentForm } from '@/types'
import request from '@/utils/request'

// 获取文档列表
export const getDocuments = (params?: {
  chapter_id?: number
  doc_type?: string
  skip?: number
  limit?: number
}) => {
  return request.get<Document[]>('/documents/', { params })
}

// 获取文档详情
export const getDocument = (documentId: number) => {
  return request.get<Document>(`/documents/${documentId}`)
}

// 创建文档
export const createDocument = (data: DocumentForm) => {
  return request.post<Document>('/documents/', data)
}

// 上传文档文件
export const uploadDocument = (formData: FormData) => {
  return request.post<Document>('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 上传课程结构文档
export const uploadStructure = (formData: FormData) => {
  return request.post('/documents/upload_structure', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 下载课程结构模板
export const downloadTemplate = () => {
  return request.get('/documents/template/download', {
    responseType: 'blob'
  }).then((blob: any) => {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '课程结构导入模板.md'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  })
}

// 向量化文档
export const vectorizeDocument = (documentId: number) => {
  return request.post(`/documents/${documentId}/vectorize`)
}

// 删除文档
export const deleteDocument = (documentId: number) => {
  return request.delete(`/documents/${documentId}`)
}

// 下载文档
export const downloadDocument = (documentId: number, fileName: string) => {
  return request.get(`/documents/download/${documentId}`, {
    responseType: 'blob'
  }).then((blob: any) => {
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  })
}

// 获取向量库信息（调试用）
export const getVectorsInfo = () => {
  return request.get('/documents/debug/vectors-info')
}

// 获取文档向量化内容预览
export const getVectorizedContentPreview = (documentId: number) => {
  return request.get(`/documents/${documentId}/vectorized-content-preview`)
}

// 重建向量索引
export const rebuildIndex = (chapterId?: number) => {
  return request.post('/documents/rebuild-index', null, {
    params: chapterId ? { chapter_id: chapterId } : {}
  })
}

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Chapter } from '@/types'
import * as chapterApi from '@/api/chapters'
import { ElMessage } from 'element-plus'

export const useChapterStore = defineStore('chapter', () => {
  const chapters = ref<Chapter[]>([])
  const currentChapter = ref<Chapter | null>(null)
  const loading = ref(false)

  const fetchChapters = async () => {
    loading.value = true
    try {
      const res: any = await chapterApi.getChapters()
      chapters.value = res
    } catch (error) {
      console.error('Fetch chapters error:', error)
      ElMessage.error('获取章节列表失败')
    } finally {
      loading.value = false
    }
  }

  const fetchChapter = async (id: number) => {
    loading.value = true
    try {
      const res: any = await chapterApi.getChapter(id)
      currentChapter.value = res
      return res
    } catch (error) {
      console.error('Fetch chapter error:', error)
      ElMessage.error('获取章节详情失败')
    } finally {
      loading.value = false
    }
  }

  const createChapter = async (data: any) => {
    try {
      const res: any = await chapterApi.createChapter(data)
      ElMessage.success('章节创建成功')
      await fetchChapters()
      return res
    } catch (error) {
      console.error('Create chapter error:', error)
      return null
    }
  }

  const updateChapter = async (id: number, data: any) => {
    try {
      const res: any = await chapterApi.updateChapter(id, data)
      ElMessage.success('章节更新成功')
      await fetchChapters()
      return res
    } catch (error) {
      console.error('Update chapter error:', error)
      return null
    }
  }

  const deleteChapter = async (id: number) => {
    try {
      await chapterApi.deleteChapter(id)
      ElMessage.success('章节删除成功')
      await fetchChapters()
      return true
    } catch (error) {
      console.error('Delete chapter error:', error)
      return false
    }
  }

  return {
    chapters,
    currentChapter,
    loading,
    fetchChapters,
    fetchChapter,
    createChapter,
    updateChapter,
    deleteChapter
  }
})

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginForm, RegisterForm } from '@/types'
import * as authApi from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string>('')

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')

  // Actions
  const login = async (loginForm: LoginForm) => {
    try {
      const res: any = await authApi.login(loginForm)
      token.value = res.access_token
      localStorage.setItem('access_token', res.access_token)
      if (res.refresh_token) {
        localStorage.setItem('refresh_token', res.refresh_token)
      }
      await fetchUserInfo()
      ElMessage.success('登录成功')
      return true
    } catch (error) {
      console.error('Login error:', error)
      return false
    }
  }

  const register = async (registerForm: RegisterForm) => {
    try {
      const res: any = await authApi.register(registerForm)
      user.value = res
      ElMessage.success('注册成功')
      return true
    } catch (error) {
      console.error('Register error:', error)
      return false
    }
  }

  const fetchUserInfo = async () => {
    try {
      const res: any = await authApi.getCurrentUser()
      user.value = res
      localStorage.setItem('user', JSON.stringify(res))
    } catch (error) {
      console.error('Fetch user info error:', error)
      logout()
    }
  }

  const logout = () => {
    user.value = null
    token.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    ElMessage.success('已退出登录')
  }

  const initFromStorage = () => {
    const storedToken = localStorage.getItem('access_token')
    const storedUser = localStorage.getItem('user')

    if (storedToken) {
      token.value = storedToken
    }
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch (e) {
        console.error('Parse user error:', e)
      }
    }

    if (token.value && !user.value) {
      fetchUserInfo()
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    isTeacher,
    isStudent,
    login,
    register,
    logout,
    fetchUserInfo,
    initFromStorage
  }
})

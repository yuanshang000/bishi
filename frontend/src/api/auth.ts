import request from '@/utils/request'
import type { LoginForm, RegisterForm, TokenResponse, User } from '@/types'

// 用户注册
export const register = (data: RegisterForm) => {
  return request.post<TokenResponse>('/auth/register', data)
}

// 用户登录
export const login = (data: LoginForm) => {
  return request.post<TokenResponse>('/auth/login', data)
}

// 刷新令牌
export const refreshToken = (refreshToken: string) => {
  return request.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
}

// 获取当前用户信息
export const getCurrentUser = () => {
  return request.get<User>('/auth/me')
}

// 根据ID获取用户信息
export const getUserById = (userId: number) => {
  return request.get<User>(`/auth/users/${userId}`)
}

// 获取教师仪表盘统计数据
export const getDashboardStats = () => {
  return request.get<any>('/auth/dashboard/stats')
}

import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/layout/MainLayout.vue'),
      redirect: '/home',
      meta: { requiresAuth: true },
      children: [
        {
          path: '/home',
          name: 'Home',
          component: () => import('@/views/Home.vue'),
          meta: { title: '首页' }
        },
        {
          path: '/chapters',
          name: 'Chapters',
          component: () => import('@/views/Chapters.vue'),
          meta: { title: '章节管理', roles: ['teacher'] }
        },
        {
          path: '/quiz',
          name: 'Quiz',
          component: () => import('@/views/Quiz.vue'),
          meta: { title: '练习中心' }
        },
        {
          path: '/quiz/:id',
          name: 'QuizDetail',
          component: () => import('@/views/QuizDetail.vue'),
          meta: { title: '练习详情' }
        },
        {
          path: '/wrong-questions',
          name: 'WrongQuestions',
          component: () => import('@/views/WrongQuestions.vue'),
          meta: { title: '错题库', roles: ['student'] }
        },
        {
          path: '/chat',
          name: 'Chat',
          component: () => import('@/views/Chat.vue'),
          meta: { title: '智能问答', roles: ['student'] }
        },
        {
          path: '/learning-analysis',
          name: 'LearningAnalysis',
          component: () => import('@/views/LearningAnalysis.vue'),
          meta: { title: 'AI学情分析', roles: ['student'] }
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/')
  } else {
    // 权限检查
    const requiredRoles = to.meta.roles as string[] | undefined
    if (requiredRoles && userStore.user) {
      if (!requiredRoles.includes(userStore.user.role)) {
        ElMessage.warning('无权访问该页面')
        next('/home')
        return
      }
    }
    next()
  }
})

export default router

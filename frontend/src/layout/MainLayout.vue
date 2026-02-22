<template>
  <el-container class="main-layout">
    <el-aside width="240px">
      <div class="logo">
        <h3>英语助手</h3>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        class="el-menu-vertical"
      >
        <el-menu-item index="/home">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>

        <el-menu-item index="/chapters" v-if="userStore.isTeacher">
          <el-icon><Reading /></el-icon>
          <span>章节管理</span>
        </el-menu-item>

        <el-menu-item index="/quiz">
          <el-icon><Edit /></el-icon>
          <span>练习中心</span>
        </el-menu-item>

        <el-menu-item index="/wrong-questions">
          <el-icon><Warning /></el-icon>
          <span>错题库</span>
        </el-menu-item>

        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </el-menu-item>

        <el-menu-item index="/learning-analysis">
          <el-icon><TrendCharts /></el-icon>
          <span>AI学情分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header>
        <div class="header-content">
          <span class="page-title">{{ $route.meta.title || '大学英语智慧助手' }}</span>
          <div class="user-info">
            <el-dropdown>
              <span class="el-dropdown-link">
                <el-avatar :size="32">{{ userStore.user?.username?.[0] }}</el-avatar>
                <span style="margin-left: 8px">{{ userStore.user?.username }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled>
                    {{ userStore.user?.role === 'teacher' ? '教师' : '学生' }}
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores'
import {
    ArrowDown,
    ChatDotRound,
    Edit,
    HomeFilled,
    Reading,
    SwitchButton,
    TrendCharts,
    Warning
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

const router = useRouter()
const userStore = useUserStore()

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logout()
    router.push('/login')
  }).catch(() => {})
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b3a4b;
}

.logo h3 {
  color: #fff;
  margin: 0;
  font-size: 36px;
  font-weight: 800;
  letter-spacing: 4px;
  width: 100%;
  text-align: center;
}

.el-menu-vertical {
  border-right: none;
  background-color: #304156;
}

.el-menu-vertical :deep(.el-menu-item) {
  color: #bfcbd9;
  font-size: 18px;
  height: 65px;
  line-height: 65px;
}

.el-menu-vertical :deep(.el-menu-item:hover),
.el-menu-vertical :deep(.el-menu-item.is-active) {
  background-color: #263445 !important;
  color: #409eff;
}

.el-header {
  background-color: #fff;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
}

.el-dropdown-link {
  cursor: pointer;
  display: flex;
  align-items: center;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>

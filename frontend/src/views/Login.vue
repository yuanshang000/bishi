<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>{{ isLogin ? '登录' : '注册' }} - 大学英语智慧助手</h2>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-form-item v-if="!isLogin" label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>

        <el-form-item v-if="!isLogin" label="姓名" prop="full_name">
          <el-input v-model="form.full_name" placeholder="请输入姓名（可选）" />
        </el-form-item>

        <el-form-item v-if="!isLogin" label="角色" prop="role">
          <el-radio-group v-model="form.role">
            <el-radio label="student">学生</el-radio>
            <el-radio label="teacher">教师</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
            style="width: 100%"
          >
            {{ isLogin ? '登录' : '注册' }}
          </el-button>
        </el-form-item>

        <el-form-item>
          <el-link type="primary" @click="toggleMode">
            {{ isLogin ? '没有账号？立即注册' : '已有账号？立即登录' }}
          </el-link>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores'
import type { FormInstance } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const isLogin = ref(true)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  password: '',
  email: '',
  full_name: '',
  role: 'student' as 'student' | 'teacher'
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在6-50个字符', trigger: 'blur' }
  ]
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (isLogin.value) {
          const success = await userStore.login({
            username: form.username,
            password: form.password
          })
          if (success) {
            router.push('/')
          }
        } else {
          const success = await userStore.register({
            username: form.username,
            password: form.password,
            email: form.email || undefined,
            full_name: form.full_name || undefined,
            role: form.role
          })
          if (success) {
            isLogin.value = true
            formRef.value?.resetFields()
          }
        }
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 450px;
}

.login-card :deep(.el-card__header) {
  text-align: center;
  background: #f5f7fa;
}

h2 {
  margin: 0;
  color: #303133;
}
</style>

<template>
  <div class="home">
    <!-- 教师端首页 -->
    <TeacherHome v-if="userStore.isTeacher" />

    <!-- 学生端首页 -->
    <StudentHome v-else />
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores';
import StudentHome from './StudentHome.vue';
import TeacherHome from './TeacherHome.vue';

const userStore = useUserStore()
</script>

<style scoped>
.home {
  padding: 0;
}
</style>

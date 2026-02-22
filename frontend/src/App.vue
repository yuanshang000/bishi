<template>
  <router-view />
</template>

<script setup lang="ts">
</script>

<style>
:root {
  --el-font-size-base: 16px;
  --el-font-size-small: 14px;
  --el-font-size-large: 18px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
}
</style>

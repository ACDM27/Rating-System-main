<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { useSystemStore } from './stores/system'

const authStore = useAuthStore()
const systemStore = useSystemStore()

onMounted(() => {
  // 恢复登录状态
  authStore.restoreSession()
  
  // 如果已登录，获取系统状态
  if (authStore.isLoggedIn) {
    systemStore.fetchState()
    systemStore.connectWebSocket()
  }
})
</script>

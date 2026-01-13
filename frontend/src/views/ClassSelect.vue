<template>
  <div class="class-select-container">
    <div class="class-select-card">
      <h1 class="title">选择比赛场次</h1>
      <p class="subtitle">欢迎，{{ authStore.user?.display_name }}</p>
      
      <div v-if="classes.length === 0" class="empty-state">
        <el-empty description="暂无可选场次">
          <p>请联系系统管理员</p>
        </el-empty>
      </div>
      
      <div v-else class="class-list">
        <div 
          v-for="cls in classes" 
          :key="cls.id" 
          class="class-item"
          @click="handleSelectClass(cls)"
        >
          <div class="class-icon">
            <el-icon :size="32"><School /></el-icon>
          </div>
          <div class="class-info">
            <h3>{{ cls.name }}</h3>
            <p>点击进入</p>
          </div>
          <el-icon class="arrow"><ArrowRight /></el-icon>
        </div>
      </div>
      
      <div class="actions">
        <el-button @click="handleLogout">退出登录</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { School, ArrowRight } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useSystemStore } from '../stores/system'

const router = useRouter()
const authStore = useAuthStore()
const systemStore = useSystemStore()

const classes = computed(() => authStore.availableClasses)

onMounted(() => {
  // 如果没有可选班级且是管理员，直接跳转到班级管理页面
  if (classes.value.length === 0 && authStore.user?.role === 'admin') {
    router.push('/admin/classes')
  }
})

async function handleSelectClass(cls) {
  try {
    await authStore.selectClass(cls.id)
    
    // 获取系统状态并连接 WebSocket
    await systemStore.fetchState()
    systemStore.connectWebSocket()
    
    ElMessage.success(`已进入场次：${cls.name}`)
    
    // 根据角色跳转
    const routes = {
      admin: '/admin/debate',
      judge: '/judge',
      audience: '/audience'
    }
    router.push(routes[authStore.user.role] || '/login')
  } catch (error) {
    ElMessage.error(error.detail || '选择班级失败')
  }
}

function handleLogout() {
  authStore.logout()
  systemStore.disconnect()
  router.push('/login')
}
</script>

<style scoped>
.class-select-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.class-select-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.title {
  text-align: center;
  margin: 0 0 8px 0;
  font-size: 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  text-align: center;
  margin: 0 0 32px 0;
  color: #666;
}

.class-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.class-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.class-item:hover {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  transform: translateX(4px);
}

.class-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
  margin-right: 16px;
}

.class-info {
  flex: 1;
}

.class-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #303133;
}

.class-info p {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.arrow {
  color: #c0c4cc;
  font-size: 20px;
}

.class-item:hover .arrow {
  color: #667eea;
}

.empty-state {
  padding: 40px 0;
}

.actions {
  margin-top: 32px;
  text-align: center;
}
</style>

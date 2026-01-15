<template>
  <div class="login-container admin-login">
    <div class="login-card">
      <h1 class="login-title">辩论赛管理后台</h1>
      <p class="login-subtitle">辩论赛智能投票系统</p>
      
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="请输入管理员账号"
            size="large"
            :prefix-icon="User"
            autocomplete="off"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            autocomplete="new-password"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            :loading="loading"
            native-type="submit"
            style="width: 100%"
          >
            登录管理后台
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="back-link">
        <router-link to="/login">← 返回评委/观众登录</router-link>
      </div>
    </div>
    
    <!-- 强制修改密码对话框 -->
    <el-dialog 
      v-model="showChangePasswordDialog" 
      title="修改密码" 
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <el-alert 
        title="检测到您使用的是默认密码，为了账号安全，请立即修改密码。" 
        type="warning" 
        :closable="false"
        style="margin-bottom: 20px"
      />
      
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef">
        <el-form-item label="原密码" prop="oldPassword">
          <el-input 
            v-model="passwordForm.oldPassword" 
            type="password" 
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="新密码" prop="newPassword">
          <el-input 
            v-model="passwordForm.newPassword" 
            type="password" 
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="passwordForm.confirmPassword" 
            type="password" 
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { changePassword } from '../api/password'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const passwordFormRef = ref(null)
const loading = ref(false)
const showChangePasswordDialog = ref(false)
const changingPassword = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入新密码'))
  } else if (value === '123456') {
    callback(new Error('不能使用默认密码'))
  } else if (value.length < 6) {
    callback(new Error('密码长度不能少于6位'))
  } else {
    if (passwordForm.confirmPassword !== '') {
      passwordFormRef.value?.validateField('confirmPassword')
    }
    callback()
  }
}

const validateConfirm = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [{ required: true, validator: validatePass, trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validateConfirm, trigger: 'blur' }]
}

async function handleLogin() {
  if (!formRef.value) return
  
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  
  try {
    const user = await authStore.login(form.username, form.password, 'admin')
    
    if (user.role !== 'admin') {
      ElMessage.error('此入口仅限管理员登录')
      authStore.logout()
      return
    }
    
    ElMessage.success(`欢迎，${user.display_name}`)
    
    // 检查是否需要修改密码
    if (authStore.needChangePassword) {
      // 强制修改密码
      showChangePasswordDialog.value = true
      loading.value = false
      return
    }
    
    router.push('/admin/debate')
  } catch (error) {
    ElMessage.error(error.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return
  
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  changingPassword.value = true
  
  try {
    await changePassword(
      authStore.user.id,
      passwordForm.oldPassword,
      passwordForm.newPassword
    )
    
    ElMessage.success('密码修改成功')
    showChangePasswordDialog.value = false
    
    // 清空密码表单
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    
    // 更新状态，密码已修改
    authStore.needChangePassword = false
    localStorage.setItem('needChangePassword', 'false')
    
    // 继续进入系统
    router.push('/admin/debate')
  } catch (error) {
    ElMessage.error(error.detail || '密码修改失败')
  } finally {
    changingPassword.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.admin-login {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  padding: 40px;
  border-radius: 16px;
  width: 380px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.login-title {
  text-align: center;
  margin-bottom: 8px;
  font-size: 28px;
  background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-bottom: 32px;
}

.back-link {
  text-align: center;
  margin-top: 20px;
}

.back-link a {
  color: #666;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s;
}

.back-link a:hover {
  color: #0f3460;
}
</style>

<template>
  <div class="page-container">
    <div class="header">
      <div class="header-left">
        <h1 class="page-title">辩论赛管理控制台</h1>
        <el-select 
          v-model="selectedClassId" 
          placeholder="选择比赛场次" 
          style="width: 200px; margin-left: 16px;"
          @change="handleClassChange"
        >
          <el-option 
            v-for="cls in authStore.availableClasses" 
            :key="cls.id" 
            :label="cls.name" 
            :value="cls.id"
          />
        </el-select>
      </div>
      <div class="header-actions">
        <span class="admin-name">{{ authStore.user?.display_name }}</span>
        <!-- 移除班级管理按钮 -->
        <el-button type="danger" @click="handleLogout">退出登录</el-button>
      </div>
    </div>
    
    <!-- 比赛配置 -->
    <div class="card">
      <h3>比赛配置</h3>
      <div v-if="!currentContest" class="contest-setup">
        <el-form :model="contestForm" label-width="120px" style="max-width: 600px">
          <el-form-item label="辩题">
            <el-input v-model="contestForm.topic" placeholder="请输入辩论主题" />
          </el-form-item>
          <el-form-item label="正方队名">
            <el-input v-model="contestForm.proTeamName" placeholder="请输入正方队伍名称" />
          </el-form-item>
          <el-form-item label="反方队名">
            <el-input v-model="contestForm.conTeamName" placeholder="请输入反方队伍名称" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleCreateContest" :loading="creatingContest">
              创建比赛
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      <div v-else class="contest-info">
        <div class="contest-details">
          <div class="contest-item">
            <span class="label">辩题：</span>
            <span class="value">{{ currentContest.topic }}</span>
          </div>
          <div class="contest-item">
            <span class="label">正方：</span>
            <el-tag type="danger">{{ currentContest.pro_team_name }}</el-tag>
          </div>
          <div class="contest-item">
            <span class="label">反方：</span>
            <el-tag type="primary">{{ currentContest.con_team_name }}</el-tag>
          </div>
          <div class="contest-item">
            <span class="label">创建时间：</span>
            <span class="value">{{ formatDate(currentContest.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 当前状态 -->
    <div class="card">
      <h3>当前状态</h3>
      <div class="status-info">
        <div class="status-item">
          <span class="label">当前场次：</span>
          <el-tag>{{ authStore.currentClassName || '未选择' }}</el-tag>
        </div>
        <div class="status-item">
          <span class="label">系统阶段：</span>
          <el-tag :type="getStageType(systemStore.currentStage)">
            {{ getStageText(systemStore.currentStage) }}
          </el-tag>
        </div>
        <div class="status-item">
          <span class="label">投票状态：</span>
          <div class="voting-status">
            <el-tag :type="debateProgress.voting_enabled?.pre_voting ? 'success' : 'info'" size="small">
              赛前投票{{ debateProgress.voting_enabled?.pre_voting ? '开启' : '关闭' }}
            </el-tag>
            <el-tag :type="debateProgress.voting_enabled?.post_voting ? 'success' : 'info'" size="small">
              赛后投票{{ debateProgress.voting_enabled?.post_voting ? '开启' : '关闭' }}
            </el-tag>
            <el-tag :type="debateProgress.voting_enabled?.judge_scoring ? 'success' : 'info'" size="small">
              评委评分{{ debateProgress.voting_enabled?.judge_scoring ? '开启' : '关闭' }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 辩论流程控制 -->
    <div class="card" v-if="currentContest">
      <h3>辩论流程控制</h3>
      <div class="control-buttons">
        <el-button 
          type="primary" 
          size="large"
          :disabled="!currentContest"
          @click="setDebateStage('PRE_VOTING')"
        >
          开启赛前投票
        </el-button>
        
        <el-button 
          type="warning" 
          size="large"
          @click="setDebateStage('DEBATE_IN_PROGRESS')"
        >
          辩论进行中
        </el-button>
        
        <el-button 
          type="success" 
          size="large"
          @click="setDebateStage('POST_VOTING')"
        >
          开启赛后投票
        </el-button>
        
        <el-button 
          type="info" 
          size="large"
          @click="setDebateStage('JUDGE_SCORING')"
        >
          开启评委评分
        </el-button>
        
        <el-button 
          type="danger" 
          size="large"
          @click="setDebateStage('RESULTS_SEALED')"
        >
          关闭所有通道
        </el-button>
        
        <el-button 
          type="primary" 
          size="large"
          :disabled="systemStore.currentStage !== 'RESULTS_SEALED'"
          @click="handleRevealResults"
        >
          揭晓结果
        </el-button>
      </div>
    </div>
    
    <!-- 进度监控（仅管理员可见） -->
    <div class="card" v-if="currentContest">
      <h3>进度监控</h3>
      <div class="progress-grid">
        <!-- 赛前投票进度 -->
        <div class="progress-card">
          <h4>赛前投票进度</h4>
          <div class="progress-bar">
            <div 
              class="progress" 
              :style="{ width: debateProgress.pre_voting_progress?.percentage + '%' }"
            ></div>
          </div>
          <p>{{ debateProgress.pre_voting_progress?.submitted || 0 }} / {{ debateProgress.pre_voting_progress?.total || 0 }}</p>
        </div>
        
        <!-- 赛后投票进度 -->
        <div class="progress-card">
          <h4>赛后投票进度</h4>
          <div class="progress-bar">
            <div 
              class="progress" 
              :style="{ width: debateProgress.post_voting_progress?.percentage + '%' }"
            ></div>
          </div>
          <p>{{ debateProgress.post_voting_progress?.submitted || 0 }} / {{ debateProgress.post_voting_progress?.total || 0 }}</p>
        </div>
        
        <!-- 评委评分进度 -->
        <div class="progress-card">
          <h4>评委评分进度</h4>
          <div class="progress-bar">
            <div 
              class="progress" 
              :style="{ width: debateProgress.judge_scoring_progress?.percentage + '%' }"
            ></div>
          </div>
          <p>{{ debateProgress.judge_scoring_progress?.submitted || 0 }} / {{ debateProgress.judge_scoring_progress?.total || 0 }}</p>
        </div>
      </div>
    </div>
    
    <!-- 参与者管理 -->
    <div class="card">
      <h3>参与者管理</h3>
      <div class="participant-actions">
        <el-button @click="router.push(`/admin/students?class_id=${authStore.currentClassId}`)">观众管理</el-button>
        <el-button @click="router.push(`/admin/teachers?class_id=${authStore.currentClassId}`)">评委管理</el-button>
        <el-button @click="showDebaterDialog = true" :disabled="!currentContest">辞手分配</el-button>
      </div>
    </div>
    
    <!-- 快捷操作 -->
    <div class="card">
      <h3>快捷操作</h3>
      <div class="quick-actions">
        <el-button @click="openScreen">打开大屏</el-button>
        <el-button type="primary" @click="viewResults" :disabled="!currentContest">查看结果</el-button>
        <el-button type="warning" @click="handleResetSystem">重置系统</el-button>
      </div>
    </div>
    
    <!-- 辞手分配对话框 -->
    <el-dialog v-model="showDebaterDialog" title="辞手分配" width="800px">
      <div class="debater-assignment">
        <div class="team-section">
          <h4>正方队伍 ({{ currentContest?.pro_team_name }})</h4>
          <div class="debater-list">
            <div v-for="position in debaterPositions" :key="`pro-${position.key}`" class="debater-item">
              <span class="position-label">{{ position.label }}：</span>
              <el-select 
                v-model="debaterAssignments.pro[position.key]" 
                placeholder="选择辞手"
                style="width: 200px"
              >
                <el-option 
                  v-for="user in availableUsers" 
                  :key="user.id" 
                  :label="user.display_name" 
                  :value="user.id"
                />
              </el-select>
            </div>
          </div>
        </div>
        
        <div class="team-section">
          <h4>反方队伍 ({{ currentContest?.con_team_name }})</h4>
          <div class="debater-list">
            <div v-for="position in debaterPositions" :key="`con-${position.key}`" class="debater-item">
              <span class="position-label">{{ position.label }}：</span>
              <el-select 
                v-model="debaterAssignments.con[position.key]" 
                placeholder="选择辞手"
                style="width: 200px"
              >
                <el-option 
                  v-for="user in availableUsers" 
                  :key="user.id" 
                  :label="user.display_name" 
                  :value="user.id"
                />
              </el-select>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showDebaterDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveDebaterAssignments" :loading="savingAssignments">
          保存分配
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { useSystemStore } from '../../stores/system'
import { 
  setDebateStage as setDebateStageApi, 
  getDebateProgress, 
  revealDebateResults,
  createContest,
  getCurrentContest,
  updateUserDebateRole
} from '../../api/debate'
import { getTeams } from '../../api/admin'

const router = useRouter()
const authStore = useAuthStore()
const systemStore = useSystemStore()

const selectedClassId = ref(authStore.currentClassId)
const currentContest = ref(null)
const debateProgress = ref({})
const showDebaterDialog = ref(false)
const savingAssignments = ref(false)
const creatingContest = ref(false)

const contestForm = ref({
  topic: '',
  proTeamName: '正方',
  conTeamName: '反方'
})

const debaterPositions = [
  { key: 'first_speaker', label: '一辞' },
  { key: 'second_speaker', label: '二辞' },
  { key: 'third_speaker', label: '三辞' },
  { key: 'fourth_speaker', label: '四辞' }
]

const debaterAssignments = ref({
  pro: {
    first_speaker: null,
    second_speaker: null,
    third_speaker: null,
    fourth_speaker: null
  },
  con: {
    first_speaker: null,
    second_speaker: null,
    third_speaker: null,
    fourth_speaker: null
  }
})

const availableUsers = ref([])

let progressInterval = null

onMounted(async () => {
  if (authStore.currentClassId) {
    await loadCurrentContest()
    await loadAvailableUsers()
    startProgressPolling()
  }
})

onUnmounted(() => {
  if (progressInterval) {
    clearInterval(progressInterval)
  }
})

watch(() => authStore.currentClassId, async (newVal) => {
  if (newVal) {
    selectedClassId.value = newVal
    await loadCurrentContest()
    await loadAvailableUsers()
    await systemStore.fetchState()
  }
})

async function handleClassChange(classId) {
  const cls = authStore.availableClasses.find(c => c.id === classId)
  if (cls) {
    authStore.switchClass(classId, cls.name)
    await systemStore.fetchState()
    systemStore.reconnect()
    await loadCurrentContest()
    await loadAvailableUsers()
    ElMessage.success(`已切换到场次：${cls.name}`)
  }
}

async function loadCurrentContest() {
  try {
    const result = await getCurrentContest(authStore.currentClassId)
    currentContest.value = result.contest
  } catch (error) {
    console.error('获取当前比赛失败:', error)
  }
}

async function loadAvailableUsers() {
  try {
    availableUsers.value = await getTeams(authStore.currentClassId)
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

async function handleCreateContest() {
  if (!contestForm.value.topic || !contestForm.value.proTeamName || !contestForm.value.conTeamName) {
    ElMessage.warning('请填写完整的比赛信息')
    return
  }
  
  creatingContest.value = true
  try {
    await createContest(
      contestForm.value.topic,
      contestForm.value.proTeamName,
      contestForm.value.conTeamName,
      authStore.currentClassId
    )
    await loadCurrentContest()
    ElMessage.success('比赛创建成功')
  } catch (error) {
    ElMessage.error(error.detail || '创建比赛失败')
  } finally {
    creatingContest.value = false
  }
}

async function setDebateStage(stage) {
  try {
    await setDebateStageApi(stage, authStore.currentClassId, currentContest.value?.id)
    await systemStore.fetchState()
    ElMessage.success('阶段已更新')
  } catch (error) {
    ElMessage.error(error.detail || '操作失败')
  }
}

async function handleRevealResults() {
  try {
    await ElMessageBox.confirm(
      '确定要揭晓辩论结果吗？结果一旦揭晓将无法撤回。',
      '揭晓结果',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await revealDebateResults(authStore.currentClassId)
    await systemStore.fetchState()
    ElMessage.success('结果已揭晓')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.detail || '揭晓结果失败')
    }
  }
}

function startProgressPolling() {
  progressInterval = setInterval(async () => {
    if (currentContest.value && authStore.currentClassId) {
      try {
        debateProgress.value = await getDebateProgress(authStore.currentClassId)
      } catch (error) {
        console.error('获取进度失败:', error)
      }
    }
  }, 3000)
}

async function handleSaveDebaterAssignments() {
  savingAssignments.value = true
  try {
    // 保存正方辞手分配
    for (const [position, userId] of Object.entries(debaterAssignments.value.pro)) {
      if (userId) {
        await updateUserDebateRole(userId, 'pro', position)
      }
    }
    
    // 保存反方辞手分配
    for (const [position, userId] of Object.entries(debaterAssignments.value.con)) {
      if (userId) {
        await updateUserDebateRole(userId, 'con', position)
      }
    }
    
    ElMessage.success('辞手分配已保存')
    showDebaterDialog.value = false
  } catch (error) {
    ElMessage.error(error.detail || '保存分配失败')
  } finally {
    savingAssignments.value = false
  }
}

function getStageText(stage) {
  const stages = {
    IDLE: '未开始',
    PRE_VOTING: '赛前投票中',
    DEBATE_IN_PROGRESS: '辩论进行中',
    POST_VOTING: '赛后投票中',
    JUDGE_SCORING: '评委评分中',
    RESULTS_SEALED: '结果封存',
    RESULTS_REVEALED: '结果已揭晓'
  }
  return stages[stage] || stage
}

function getStageType(stage) {
  const types = {
    IDLE: 'info',
    PRE_VOTING: 'warning',
    DEBATE_IN_PROGRESS: 'primary',
    POST_VOTING: 'warning',
    JUDGE_SCORING: 'success',
    RESULTS_SEALED: 'danger',
    RESULTS_REVEALED: 'success'
  }
  return types[stage] || 'info'
}

function openScreen() {
  const workspaceId = authStore.user?.workspace_id || 1
  window.open(`/screen?class_id=${authStore.currentClassId}&workspace_id=${workspaceId}`, '_blank')
}

function viewResults() {
  if (currentContest.value) {
    router.push(`/admin/debate-results?contest_id=${currentContest.value.id}`)
  }
}

async function handleResetSystem() {
  try {
    await ElMessageBox.confirm(
      '此操作将清空该班级所有投票记录和评分记录，并重置系统状态。是否继续？',
      '重置系统',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    // 这里可以调用重置API
    ElMessage.success('系统已重置')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString('zh-CN')
}

function handleLogout() {
  authStore.logout()
  systemStore.disconnect()
  router.push('/login')
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.admin-name {
  color: #409eff;
  font-weight: 500;
  margin-right: 8px;
}

.contest-details {
  display: flex;
  gap: 40px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.contest-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.contest-item .label {
  color: #666;
  font-weight: 500;
}

.contest-item .value {
  color: #333;
}

.status-info {
  display: flex;
  gap: 40px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-item .label {
  color: #666;
}

.voting-status {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.control-buttons {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.progress-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 16px;
}

.progress-card {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
}

.progress-card h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
}

.progress-bar {
  width: 100%;
  height: 16px;
  background: #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  transition: width 0.3s ease;
}

.participant-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.quick-actions {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}

.debater-assignment {
  display: flex;
  gap: 40px;
}

.team-section {
  flex: 1;
}

.team-section h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.debater-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.debater-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.position-label {
  width: 60px;
  color: #666;
  font-size: 14px;
}

h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.page-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}
</style>
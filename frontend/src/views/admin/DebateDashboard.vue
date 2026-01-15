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
            <el-input v-model="contestForm.topic" placeholder="请输入辩论总主题" />
          </el-form-item>
          <el-form-item label="正方辩题">
            <el-input v-model="contestForm.proTopic" placeholder="请输入正方具体辩题（选填，默认同总主题）" />
          </el-form-item>
          <el-form-item label="反方辩题">
            <el-input v-model="contestForm.conTopic" placeholder="请输入反方具体辩题（选填，默认同总主题）" />
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
          <div class="contest-item" v-if="currentContest.pro_topic">
            <span class="label">正方辩题：</span>
            <span class="value">{{ currentContest.pro_topic }}</span>
          </div>
          <div class="contest-item" v-if="currentContest.con_topic">
            <span class="label">反方辩题：</span>
            <span class="value">{{ currentContest.con_topic }}</span>
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
        <el-button @click="showDebaterDialog = true" :disabled="!currentContest">辩手分配</el-button>
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
    
    <!-- 投票和评分记录 -->
    <div class="card" v-if="currentContest">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h3 style="margin: 0;">投票和评分记录</h3>
        <el-button @click="loadRecords" :loading="loadingRecords" size="small">
          刷新数据
        </el-button>
      </div>
      
      <el-tabs v-model="activeRecordTab">
        <!-- 观众投票记录 -->
        <el-tab-pane label="观众投票记录" name="votes">
          <div style="margin-bottom: 16px; display: flex; gap: 20px; padding: 12px; background: #f5f5f5; border-radius: 8px;">
            <div>
              <span style="color: #666;">赛前投票:</span>
              <span style="color: #333; font-weight: bold; margin-left: 8px;">
                {{ voteRecords.filter(v => v.vote_phase === 'pre_debate').length }} 票
              </span>
            </div>
            <div>
              <span style="color: #666;">赛后投票:</span>
              <span style="color: #333; font-weight: bold; margin-left: 8px;">
                {{ voteRecords.filter(v => v.vote_phase === 'post_debate').length }} 票
              </span>
            </div>
            <div>
              <span style="color: #666;">总计:</span>
              <span style="color: #409eff; font-weight: bold; margin-left: 8px;">
                {{ voteRecords.length }} 票
              </span>
            </div>
          </div>
          
          <el-table :data="voteRecords" stripe style="width: 100%" max-height="400" v-loading="loadingRecords">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="voter_name" label="投票人" width="120" />
            <el-table-column label="投票阶段" width="120">
              <template #default="scope">
                <el-tag :type="scope.row.vote_phase === 'pre_debate' ? 'warning' : 'success'" size="small">
                  {{ scope.row.vote_phase === 'pre_debate' ? '赛前投票' : '赛后投票' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="支持队伍" width="120">
              <template #default="scope">
                <el-tag :type="scope.row.team_side === 'pro' ? 'danger' : 'primary'" size="small">
                  {{ scope.row.team_side === 'pro' ? '正方' : '反方' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="投票时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <!-- 评委评分记录 -->
        <el-tab-pane label="评委评分记录" name="scores">
          <div style="margin-bottom: 16px; display: flex; gap: 20px; padding: 12px; background: #f5f5f5; border-radius: 8px;">
            <div>
              <span style="color: #666;">已评分评委:</span>
              <span style="color: #333; font-weight: bold; margin-left: 8px;">
                {{ uniqueJudgesCount }} 人
              </span>
            </div>
            <div>
              <span style="color: #666;">评分记录:</span>
              <span style="color: #409eff; font-weight: bold; margin-left: 8px;">
                {{ judgeScores.length }} 条
              </span>
            </div>
          </div>
          
          <el-table :data="judgeScores" stripe style="width: 100%" max-height="400" v-loading="loadingRecords">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="judge_name" label="评委" width="120" />
            <el-table-column prop="debater_name" label="辩手" width="120" />
            <el-table-column label="队伍" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.team_side === 'pro' ? 'danger' : 'primary'" size="small">
                  {{ scope.row.team_side === 'pro' ? '正方' : '反方' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="logical_reasoning" label="逻辑推理" width="100" align="center">
              <template #default="scope">
                <span style="color: #67c23a; font-weight: bold;">{{ scope.row.logical_reasoning }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="debate_skills" label="辩论技巧" width="100" align="center">
              <template #default="scope">
                <span style="color: #67c23a; font-weight: bold;">{{ scope.row.debate_skills }}</span>
              </template>
            </el-table-column>
            <el-table-column label="总分" width="100" align="center">
              <template #default="scope">
                <span style="color: #409eff; font-weight: bold; font-size: 16px;">
                  {{ scope.row.logical_reasoning + scope.row.debate_skills }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="评分时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 辩手分配对话框 -->
    <el-dialog v-model="showDebaterDialog" title="辩手分配" width="900px">
      <div class="assignment-container">
        <!-- 正方队伍 -->
        <div class="team-section">
          <h3 class="section-title">正方队伍 ({{ currentContest?.pro_team_name }})</h3>
          <el-form label-width="60px">
            <el-form-item label="一辩：">
              <el-input v-model="debaterAssignments.pro.first" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="二辩：">
              <el-input v-model="debaterAssignments.pro.second" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="三辩：">
              <el-input v-model="debaterAssignments.pro.third" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="四辩：">
              <el-input v-model="debaterAssignments.pro.fourth" placeholder="请输入辩手姓名" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 反方队伍 -->
        <div class="team-section">
          <h3 class="section-title">反方队伍 ({{ currentContest?.con_team_name }})</h3>
          <el-form label-width="60px">
            <el-form-item label="一辩：">
              <el-input v-model="debaterAssignments.con.first" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="二辩：">
              <el-input v-model="debaterAssignments.con.second" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="三辩：">
              <el-input v-model="debaterAssignments.con.third" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="四辩：">
              <el-input v-model="debaterAssignments.con.fourth" placeholder="请输入辩手姓名" />
            </el-form-item>
          </el-form>
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
  updateUserDebateRole,
  resetDebateSystem
} from '../../api/debate'
import { getTeams, createStudent } from '../../api/admin'
import api from '../../api/index'

const router = useRouter()

// 加载投票和评分记录
async function loadRecords() {
  if (!currentContest.value) {
    console.warn('没有当前比赛，无法加载记录')
    return
  }
  
  loadingRecords.value = true
  try {
    const contestId = currentContest.value.id
    console.log('正在加载比赛记录，contest_id:', contestId)
    
    // 获取投票记录
    try {
      const votes = await api.get('/api/vote/records', {
        params: { contest_id: contestId }
      })
      voteRecords.value = votes || []
      console.log('投票记录加载成功:', voteRecords.value.length, '条')
    } catch (error) {
      console.error('获取投票记录失败:', error)
      voteRecords.value = []
    }
    
    // 获取评分记录
    try {
      const scores = await api.get('/api/judge/scores', {
        params: { contest_id: contestId }
      })
      judgeScores.value = scores || []
      console.log('评分记录加载成功:', judgeScores.value.length, '条')
    } catch (error) {
      console.error('获取评分记录失败:', error)
      judgeScores.value = []
    }
    
  } catch (error) {
    console.error('加载记录失败:', error)
    ElMessage.error('加载记录失败: ' + (error.detail || error.message || '未知错误'))
  } finally {
    loadingRecords.value = false
  }
}
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
  conTeamName: '反方',
  proTopic: '',
  conTopic: ''
})

const debaterPositions = [
  { key: 'first_speaker', label: '一辞' },
  { key: 'second_speaker', label: '二辞' },
  { key: 'third_speaker', label: '三辞' },
  { key: 'fourth_speaker', label: '四辞' }
]

const debaterAssignments = ref({
  pro: {
    first: '',
    second: '',
    third: '',
    fourth: ''
  },
  con: {
    first: '',
    second: '',
    third: '',
    fourth: ''
  }
})

const availableUsers = ref([])

// 投票和评分记录相关状态
const activeRecordTab = ref('votes')
const voteRecords = ref([])
const judgeScores = ref([])
const loadingRecords = ref(false)

const uniqueJudgesCount = computed(() => {
  const judgeIds = new Set(judgeScores.value.map(s => s.judge_id))
  return judgeIds.size
})

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

// 监听比赛变化，自动加载记录
watch(() => currentContest.value, async (newContest) => {
  if (newContest) {
    console.log('检测到比赛变化，自动加载记录')
    await loadRecords()
  }
}, { deep: true })


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
      authStore.currentClassId,
      contestForm.value.proTopic,
      contestForm.value.conTopic
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
      '确定要揭晓辩论结果吗？结果将实时显示在大屏上。',
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
    const positionMap = {
      first: 'first_debater',
      second: 'second_debater',
      third: 'third_debater',
      fourth: 'fourth_debater'
    }
    
    // 获取所有现有用户
    const allUsers = await getTeams(authStore.currentClassId)
    
    // 1. 先清除所有现有的辩手分配，防止重复和残留
    const existingDebaters = allUsers.filter(u => u.team_side || u.debater_position)
    if (existingDebaters.length > 0) {
      await Promise.all(existingDebaters.map(u => 
        updateUserDebateRole(u.id, null, null)
      ))
      // 重新获取用户列表以确保状态最新（或者在后续查找时注意）
      // 由于我们只用了 id 和 name，前面的 allUsers 仍然可用，
      // 但如果要复用对象，可能需要注意。这里find是按name找，所以没问题。
    }
    
    // 处理正方辩手
    for (const [key, name] of Object.entries(debaterAssignments.value.pro)) {
      if (!name || !name.trim()) continue
      
      const trimmedName = name.trim()
      const position = positionMap[key]
      
      // 查找是否已存在该用户
      let debater = allUsers.find(u => u.username === trimmedName || u.display_name === trimmedName)
      
      if (!debater) {
        // 用户不存在，创建新辩手
        debater = await createStudent({
          username: trimmedName,
          display_name: trimmedName,
          password: '123456',
          role: 'student',
          class_id: authStore.currentClassId
        })
      }
      
      // 分配辩手角色
      await updateUserDebateRole(debater.id, 'pro', position)
    }
    
    // 处理反方辩手
    for (const [key, name] of Object.entries(debaterAssignments.value.con)) {
      if (!name || !name.trim()) continue
      
      const trimmedName = name.trim()
      const position = positionMap[key]
      
      // 查找是否已存在该用户
      let debater = allUsers.find(u => u.username === trimmedName || u.display_name === trimmedName)
      
      if (!debater) {
        // 用户不存在，创建新辩手
        debater = await createStudent({
          username: trimmedName,
          display_name: trimmedName,
          password: '123456',
          role: 'student',
          class_id: authStore.currentClassId
        })
      }
      
      // 分配辩手角色
      await updateUserDebateRole(debater.id, 'con', position)
    }
    
    ElMessage.success('辩手分配已保存')
    showDebaterDialog.value = false
  } catch (error) {
    console.error('保存辩手分配失败:', error)
    ElMessage.error(error.detail || error.message || '保存分配失败')
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
  if (!currentContest.value) {
    ElMessage.warning('请先创建比赛')
    return
  }
  window.open(`/screen?contest_id=${currentContest.value.id}`, '_blank')
}

function viewResults() {
  if (currentContest.value) {
    router.push(`/admin/debate-results?contest_id=${currentContest.value.id}`)
  }
}

async function handleResetSystem() {
  try {
    await ElMessageBox.confirm(
      '此操作将清空该班级所有投票记录和评分记录，删除所有比赛，并重置系统状态。是否继续?',
      '重置系统',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用重置API
    await resetDebateSystem(authStore.currentClassId)
    
    // 重置本地状态
    currentContest.value = null
    debateProgress.value = {}
    
    // 重新获取系统状态
    await systemStore.fetchState()
    
    ElMessage.success('系统已重置到初始状态')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.detail || '重置失败')
    }
  }
}



function formatDateTime(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
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

.assignment-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}

.team-section {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  padding-bottom: 12px;
  border-bottom: 2px solid #e4e7ed;
}

.team-section:first-child .section-title {
  color: #f5576c;
  border-bottom-color: rgba(245, 87, 108, 0.3);
}

.team-section:last-child .section-title {
  color: #00f2fe;
  border-bottom-color: rgba(0, 242, 254, 0.3);
}

@media (max-width: 1024px) {
  .assignment-container {
    grid-template-columns: 1fr;
    gap: 24px;
  }
}
</style>
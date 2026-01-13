<template>
  <div class="mobile-container">
    <!-- 头部信息 -->
    <div class="header">
      <div class="contest-info">
        <h2 class="contest-title">{{ contestInfo?.topic || '辩论赛投票' }}</h2>
        <div class="voting-phase">
          <el-tag :type="getPhaseType(currentPhase)" size="large">
            {{ getPhaseText(currentPhase) }}
          </el-tag>
        </div>
      </div>
      <div class="audience-info">
        <span class="audience-name">观众：{{ authStore.user?.display_name }}</span>
        <el-button size="small" type="danger" @click="handleLogout">退出</el-button>
      </div>
    </div>

    <!-- 状态提示 -->
    <div class="status-bar" v-if="!votingEnabled">
      <el-alert 
        :title="getStatusMessage()" 
        :type="getStatusType()"
        :closable="false"
        show-icon
      />
    </div>

    <!-- 投票区域 -->
    <div class="voting-container" v-if="votingEnabled && contestInfo">
      <div class="voting-instruction">
        <p>{{ getVotingInstruction() }}</p>
      </div>

      <!-- 分屏投票布局 -->
      <div class="teams-voting">
        <!-- 正方投票区 -->
        <div class="team-vote-section pro-section">
          <div class="team-header">
            <h3 class="team-name">{{ contestInfo.pro_team_name }}</h3>
            <div class="team-label">正方</div>
          </div>
          
          <div class="vote-button-container">
            <button 
              class="vote-button pro-button"
              :disabled="!canVote || isVoting"
              @click="submitVote('pro')"
            >
              <div class="button-content">
                <div class="vote-icon">👍</div>
                <div class="vote-text">投票支持</div>
              </div>
            </button>
          </div>
          
          <div class="vote-status" v-if="hasVoted('pro')">
            <el-icon class="check-icon"><Check /></el-icon>
            <span>已投票</span>
          </div>
        </div>

        <!-- 分割线 -->
        <div class="divider">
          <span class="vs-text">VS</span>
        </div>

        <!-- 反方投票区 -->
        <div class="team-vote-section con-section">
          <div class="team-header">
            <h3 class="team-name">{{ contestInfo.con_team_name }}</h3>
            <div class="team-label">反方</div>
          </div>
          
          <div class="vote-button-container">
            <button 
              class="vote-button con-button"
              :disabled="!canVote || isVoting"
              @click="submitVote('con')"
            >
              <div class="button-content">
                <div class="vote-icon">👍</div>
                <div class="vote-text">投票支持</div>
              </div>
            </button>
          </div>
          
          <div class="vote-status" v-if="hasVoted('con')">
            <el-icon class="check-icon"><Check /></el-icon>
            <span>已投票</span>
          </div>
        </div>
      </div>

      <!-- 投票历史 -->
      <div class="voting-history" v-if="myVotes.length > 0">
        <h4>我的投票记录</h4>
        <div class="vote-records">
          <div 
            v-for="vote in myVotes" 
            :key="`${vote.vote_phase}-${vote.team_side}`"
            class="vote-record"
          >
            <span class="phase">{{ getPhaseText(vote.vote_phase) }}</span>
            <span class="team" :class="vote.team_side">
              {{ vote.team_side === 'pro' ? contestInfo.pro_team_name : contestInfo.con_team_name }}
            </span>
            <span class="time">{{ formatTime(vote.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载遮罩 -->
    <div v-if="isVoting" class="loading-overlay">
      <div class="loading-content">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>正在提交投票...</p>
      </div>
    </div>

    <!-- 投票成功提示 -->
    <el-dialog v-model="showSuccessDialog" title="投票成功" width="300px" center>
      <div class="success-content">
        <el-icon class="success-icon"><SuccessFilled /></el-icon>
        <p>您的投票已成功提交！</p>
        <p class="success-hint">请关注大屏幕查看最终结果</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="showSuccessDialog = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Loading, SuccessFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { useSystemStore } from '../../stores/system'
import { getCurrentContest } from '../../api/debate'
import { submitVote as submitVoteApi, getMyVotes } from '../../api/vote'

const router = useRouter()
const authStore = useAuthStore()
const systemStore = useSystemStore()

const contestInfo = ref(null)
const myVotes = ref([])
const isVoting = ref(false)
const showSuccessDialog = ref(false)

// 计算当前投票阶段
const currentPhase = computed(() => {
  const stage = systemStore.currentStage
  if (stage === 'PRE_VOTING') return 'pre_debate'
  if (stage === 'POST_VOTING') return 'post_debate'
  return null
})

// 计算是否可以投票
const votingEnabled = computed(() => {
  return currentPhase.value && 
         systemStore.debateProgress && 
         (systemStore.debateProgress.voting_enabled?.pre_voting || 
          systemStore.debateProgress.voting_enabled?.post_voting)
})

// 计算是否可以投票（未投过票）
const canVote = computed(() => {
  if (!currentPhase.value) return false
  return !myVotes.value.some(vote => vote.vote_phase === currentPhase.value)
})

onMounted(async () => {
  await loadContestInfo()
  await loadMyVotes()
  await systemStore.fetchState()
  await systemStore.fetchDebateProgress()
})

// 监听系统状态变化
watch(() => systemStore.currentStage, async (newStage) => {
  if (newStage === 'RESULTS_REVEALED') {
    ElMessage.success('比赛结果已揭晓！请查看大屏幕')
  }
  // 当阶段变化时重新加载投票记录
  await loadMyVotes()
})

async function loadContestInfo() {
  try {
    const result = await getCurrentContest(authStore.currentClassId)
    contestInfo.value = result.contest
  } catch (error) {
    console.error('获取比赛信息失败:', error)
  }
}

async function loadMyVotes() {
  try {
    if (contestInfo.value) {
      myVotes.value = await getMyVotes(contestInfo.value.id)
    }
  } catch (error) {
    console.error('获取投票记录失败:', error)
  }
}

async function submitVote(teamSide) {
  if (!canVote.value || !currentPhase.value) {
    ElMessage.warning('当前无法投票')
    return
  }

  isVoting.value = true
  
  try {
    await submitVoteApi({
      contest_id: contestInfo.value.id,
      team_side: teamSide,
      vote_phase: currentPhase.value
    })
    
    // 重新加载投票记录
    await loadMyVotes()
    
    // 显示成功对话框
    showSuccessDialog.value = true
    
  } catch (error) {
    ElMessage.error(error.detail || '投票失败，请重试')
  } finally {
    isVoting.value = false
  }
}

function hasVoted(teamSide) {
  if (!currentPhase.value) return false
  return myVotes.value.some(vote => 
    vote.vote_phase === currentPhase.value && vote.team_side === teamSide
  )
}

function getPhaseText(phase) {
  const phases = {
    pre_debate: '赛前投票',
    post_debate: '赛后投票'
  }
  return phases[phase] || phase
}

function getPhaseType(phase) {
  const types = {
    pre_debate: 'warning',
    post_debate: 'success'
  }
  return types[phase] || 'info'
}

function getStatusMessage() {
  const stage = systemStore.currentStage
  
  if (stage === 'IDLE') {
    return '比赛尚未开始，请等待管理员开启投票'
  } else if (stage === 'DEBATE_IN_PROGRESS') {
    return '辩论正在进行中，请认真观看'
  } else if (stage === 'JUDGE_SCORING') {
    return '评委正在评分中，请耐心等待'
  } else if (stage === 'RESULTS_SEALED') {
    return '投票已结束，正在统计结果...'
  } else if (stage === 'RESULTS_REVEALED') {
    return '比赛结果已揭晓！'
  }
  
  return '投票通道未开启，请等待管理员操作'
}

function getStatusType() {
  const stage = systemStore.currentStage
  
  if (stage === 'RESULTS_REVEALED') return 'success'
  if (stage === 'DEBATE_IN_PROGRESS') return 'info'
  return 'warning'
}

function getVotingInstruction() {
  if (currentPhase.value === 'pre_debate') {
    return '请根据您的第一印象，选择您认为更有可能获胜的队伍'
  } else if (currentPhase.value === 'post_debate') {
    return '辩论结束后，请选择您认为表现更好的队伍'
  }
  return '请选择您支持的队伍'
}

function formatTime(timeString) {
  return new Date(timeString).toLocaleTimeString('zh-CN')
}

function handleLogout() {
  authStore.logout()
  systemStore.disconnect()
  router.push('/login')
}
</script>

<style scoped>
.mobile-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.contest-info {
  margin-bottom: 12px;
  text-align: center;
}

.contest-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #333;
}

.voting-phase {
  display: flex;
  justify-content: center;
}

.audience-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.audience-name {
  font-size: 14px;
  color: #666;
}

.status-bar {
  padding: 16px;
}

.voting-container {
  padding: 20px 16px;
}

.voting-instruction {
  text-align: center;
  margin-bottom: 24px;
}

.voting-instruction p {
  color: white;
  font-size: 16px;
  margin: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.teams-voting {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.team-vote-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  position: relative;
}

.pro-section {
  border-left: 4px solid #f56565;
}

.con-section {
  border-left: 4px solid #4299e1;
}

.team-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.team-name {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.team-label {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.pro-section .team-label {
  background: #f56565;
}

.con-section .team-label {
  background: #4299e1;
}

.vote-button-container {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.vote-button {
  width: 100%;
  height: 80px;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: bold;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.pro-button {
  background: linear-gradient(135deg, #f56565, #e53e3e);
}

.pro-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #e53e3e, #c53030);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
}

.con-button {
  background: linear-gradient(135deg, #4299e1, #3182ce);
}

.con-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #3182ce, #2c5282);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
}

.vote-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.button-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.vote-icon {
  font-size: 24px;
}

.vote-text {
  font-size: 16px;
}

.vote-status {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: #48bb78;
  font-weight: 500;
}

.check-icon {
  font-size: 20px;
}

.divider {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 8px 0;
}

.vs-text {
  background: rgba(255, 255, 255, 0.9);
  color: #666;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.voting-history {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 16px;
  backdrop-filter: blur(10px);
}

.voting-history h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 16px;
}

.vote-records {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vote-record {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f7fafc;
  border-radius: 8px;
}

.vote-record .phase {
  font-size: 12px;
  color: #666;
}

.vote-record .team {
  font-weight: 500;
}

.vote-record .team.pro {
  color: #f56565;
}

.vote-record .team.con {
  color: #4299e1;
}

.vote-record .time {
  font-size: 12px;
  color: #999;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.loading-content {
  background: white;
  padding: 32px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.loading-icon {
  font-size: 32px;
  color: #409eff;
  margin-bottom: 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.success-content {
  text-align: center;
  padding: 16px 0;
}

.success-icon {
  font-size: 48px;
  color: #67c23a;
  margin-bottom: 16px;
}

.success-content p {
  margin: 8px 0;
  color: #333;
}

.success-hint {
  font-size: 14px;
  color: #666;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .teams-voting {
    gap: 12px;
  }
  
  .team-vote-section {
    padding: 16px;
  }
  
  .vote-button {
    height: 70px;
    font-size: 16px;
  }
  
  .vote-icon {
    font-size: 20px;
  }
  
  .vote-text {
    font-size: 14px;
  }
}

/* 大屏幕适配 */
@media (min-width: 768px) {
  .teams-voting {
    flex-direction: row;
    gap: 20px;
  }
  
  .team-vote-section {
    flex: 1;
  }
  
  .divider {
    flex-direction: column;
    justify-content: center;
    width: 60px;
    margin: 0;
  }
  
  .vs-text {
    writing-mode: vertical-rl;
    text-orientation: mixed;
  }
}
</style>
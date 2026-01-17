<template>
  <div class="mobile-container pro-theme">
    <!-- 顶部导航栏 -->
    <header class="app-header glass-effect">
      <div class="header-left">
        <h1 class="app-title">辩论赛投票</h1>
      </div>
      
      <div class="header-center">
        <div class="status-pill" :class="systemStore.currentStage?.toLowerCase() || 'default'">
          <span class="status-dot"></span>
          <span class="status-text">{{ visualState }}</span>
        </div>
      </div>

      <div class="header-right">
        <div class="user-profile" @click="handleLogout" title="退出登录">
          <span class="username">{{ authStore.user?.display_name }}</span>
          <el-icon class="logout-icon"><SwitchButton /></el-icon>
        </div>
      </div>
    </header>

    <!-- 主体内容区域 -->
    <main class="app-content">
      <transition name="fade-slide" mode="out-in">
        
        <!-- A. 赛前投票完成 - 等待页 -->
        <div class="content-card waiting-card" v-if="showPreVotingWaitingPage" key="pre-waiting">
          <div class="success-animation">
            <div class="success-circle">
              <el-icon class="success-tick"><SuccessFilled /></el-icon>
            </div>
          </div>
          
          <h2 class="card-title">赛前站队成功</h2>
          
          <div class="choice-display">
            <span class="choice-label">当前支持</span>
            <div :class="['choice-badge', getMyPreVoteTeam() === 'pro' ? 'badge-pro' : 'badge-con']">
              {{ getMyPreVoteTeam() === 'pro' ? contestInfo?.pro_team_name : contestInfo?.con_team_name }}
              <span class="side-tag">{{ getMyPreVoteTeam() === 'pro' ? '正方' : '反方' }}</span>
            </div>
          </div>
          
          <div class="waiting-message">
            <p>比赛即将开始，请专心观看辩论</p>
            <small>赛后将开启第二轮投票</small>
          </div>
          
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>

        <!-- B. 赛后投票完成 - 最终锁定页 -->
        <div class="content-card waiting-card final-card" v-else-if="showPostVotingWaitingPage" key="post-waiting">
          <div class="success-animation">
            <div class="success-circle final">
              <el-icon class="success-tick"><SuccessFilled /></el-icon>
            </div>
          </div>
          
          <h2 class="card-title">最终投票已提交</h2>
          
          <div class="choice-display">
            <span class="choice-label">最终选择</span>
            <div :class="['choice-badge', getMyPostVoteTeam() === 'pro' ? 'badge-pro' : 'badge-con']">
              {{ getMyPostVoteTeam() === 'pro' ? contestInfo?.pro_team_name : contestInfo?.con_team_name }}
              <span class="side-tag">{{ getMyPostVoteTeam() === 'pro' ? '正方' : '反方' }}</span>
            </div>
          </div>
          
          <div class="waiting-message highlight">
            <p>投票通道已关闭</p>
            <small>请关注大屏揭晓结果</small>
          </div>
           <div class="hourglass-animation">⏳</div>
        </div>

        <!-- C. 状态页面 (未开始/进行中/评分中/封存/揭晓/无比赛信息) -->
        <div class="content-card status-card" v-else-if="!votingEnabled || !contestInfo" key="status-page">
           <!-- No Contest Info -->
           <div v-if="!contestInfo" class="status-content">
             <div class="status-icon-lg">⚠️</div>
             <h2>暂无比赛信息</h2>
             <p>请联系管理员配置比赛</p>
           </div>

           <!-- IDLE -->
           <div v-else-if="systemStore.currentStage === 'IDLE'" class="status-content">
             <div class="status-icon-lg">👋</div>
             <h2>欢迎来到辩论赛</h2>
             <p>比赛即将开始，请等待管理员开启投票</p>
             <div class="loading-dots"><span></span><span></span><span></span></div>
           </div>

           <!-- DEBATE / OTHERS -->
           <div v-else-if="votingEnabled === false && systemStore.currentStage !== 'RESULTS_REVEALED'" class="status-content">
              <div class="status-icon-lg">
                {{ getStatusIcon() }}
              </div>
              <h2>{{ visualState }}</h2>
              <p>
                {{ getStatusMessage() }}
              </p>
              <div v-if="systemStore.currentStage === 'RESULTS_SEALED'" class="hourglass-animation">⏳</div>
           </div>

           <!-- REVEALED - Pro Max Results Display -->
           <div v-else-if="systemStore.currentStage === 'RESULTS_REVEALED'" class="results-reveal">
              <div v-if="debateResults" class="results-container">
                <!-- Winner Announcement -->
                <div class="winner-banner" :class="`winner-${debateResults.winner}`">
                  <div class="confetti-container">
                    <div v-for="i in 50" :key="i" class="confetti" :style="getConfettiStyle(i)"></div>
                  </div>
                  <div class="winner-content">
                    <div class="trophy-icon">🏆</div>
                    <h1 class="winner-title" v-if="debateResults.winner === 'pro'">
                      {{ debateResults.pro_team_name }} 获胜！
                    </h1>
                    <h1 class="winner-title" v-else-if="debateResults.winner === 'con'">
                      {{ debateResults.con_team_name }} 获胜！
                    </h1>
                    <h1 class="winner-title tie" v-else>
                      实力相当！平局
                    </h1>
                  </div>
                </div>

                <!-- Debate Topic -->
                <div class="debate-topic-result">
                  <p>{{ debateResults.topic }}</p>
                </div>

                <!-- Vote Results Grid -->
                <div class="vote-results-grid">
                  <!-- Pro Team Card -->
                  <div class="team-result-card pro-card" :class="{ 'winner-card': debateResults.winner === 'pro' }">
                    <div class="team-header-result">
                      <span class="side-badge pro">正方</span>
                      <h3>{{ debateResults.pro_team_name }}</h3>
                      <div v-if="debateResults.winner === 'pro'" class="winner-crown">👑</div>
                    </div>
                    
                    <div class="vote-stats">
                      <div class="stat-row">
                        <span class="stat-label">赛前投票</span>
                        <span class="stat-value fade-in">{{ debateResults.pro_pre_votes }}</span>
                      </div>
                      <div class="stat-row">
                        <span class="stat-label">赛后投票</span>
                        <span class="stat-value final-vote fade-in-delay">{{ debateResults.pro_post_votes }}</span>
                      </div>
                      <div class="stat-divider"></div>
                      <div class="swing-indicator">
                        <span class="swing-label">跑票值</span>
                        <span class="swing-value" :class="getSwingClass(debateResults.pro_swing_vote)">
                          {{ debateResults.pro_swing_vote > 0 ? '+' : '' }}{{ debateResults.pro_swing_vote }}
                        </span>
                      </div>
                    </div>

                    <!-- Progress Bar -->
                    <div class="vote-bar-container">
                      <div class="vote-bar pro-bar" :style="{ width: getProPercentage() + '%' }">
                        <span class="bar-label">{{ getProPercentage() }}%</span>
                      </div>
                    </div>
                  </div>

                  <!-- VS Divider -->
                  <div class="vs-divider-result">
                    <div class="vs-circle">VS</div>
                  </div>

                  <!-- Con Team Card -->
                  <div class="team-result-card con-card" :class="{ 'winner-card': debateResults.winner === 'con' }">
                    <div class="team-header-result">
                      <span class="side-badge con">反方</span>
                      <h3>{{ debateResults.con_team_name }}</h3>
                      <div v-if="debateResults.winner === 'con'" class="winner-crown">👑</div>
                    </div>
                    
                    <div class="vote-stats">
                      <div class="stat-row">
                        <span class="stat-label">赛前投票</span>
                        <span class="stat-value fade-in">{{ debateResults.con_pre_votes }}</span>
                      </div>
                      <div class="stat-row">
                        <span class="stat-label">赛后投票</span>
                        <span class="stat-value final-vote fade-in-delay">{{ debateResults.con_post_votes }}</span>
                      </div>
                      <div class="stat-divider"></div>
                      <div class="swing-indicator">
                        <span class="swing-label">跑票值</span>
                        <span class="swing-value" :class="getSwingClass(debateResults.con_swing_vote)">
                          {{ debateResults.con_swing_vote > 0 ? '+' : '' }}{{ debateResults.con_swing_vote }}
                        </span>
                      </div>
                    </div>

                    <!-- Progress Bar -->
                    <div class="vote-bar-container">
                      <div class="vote-bar con-bar" :style="{ width: getConPercentage() + '%' }">
                        <span class="bar-label">{{ getConPercentage() }}%</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Thank You Message -->
                <div class="thank-you-message">
                  <p>感谢您的参与！</p>
                </div>
              </div>

              <!-- Loading State -->
              <div v-else class="results-loading">
                <el-icon class="spinning"><Loading /></el-icon>
                <p>正在加载结果...</p>
              </div>
           </div>

           <!-- Default Fallback -->
           <div v-else class="status-content">
             <div class="status-icon-lg">ℹ️</div>
             <h2>{{ visualState }}</h2>
             <p>请等待管理员操作</p>
           </div>
        </div>

        <!-- D. 投票区域 -->
        <div class="voting-wrapper" v-else-if="votingEnabled && contestInfo" key="voting-area">
          <div class="contest-topic-card glass-effect">
            <h3>{{ contestInfo.topic }}</h3>
            <div class="round-tag">{{ currentPhase === 'pre_debate' ? '第一轮：赛前站队' : '第二轮：赛后最终投票' }}</div>
          </div>

          <div class="teams-container">
            <!-- 正方 -->
            <div class="team-card pro-team" :class="{ 'voted': hasVoted('pro'), 'disabled': isVoting || !canVote }">
              <h3 class="team-name">{{ contestInfo.pro_team_name }}</h3>
              <p class="team-topic-detail" v-if="contestInfo.pro_topic">{{ contestInfo.pro_topic }}</p>
              <button class="vote-btn btn-pro" @click="submitVote('pro')" :disabled="!canVote || isVoting">
                <span class="btn-icon">👍</span>
                <span>支持正方</span>
              </button>
              <div class="vote-confirmation" v-if="hasVoted('pro')">
                <el-icon><Check /></el-icon> 已投
              </div>
            </div>

            <div class="vs-divider">VS</div>

            <!-- 反方 -->
            <div class="team-card con-team" :class="{ 'voted': hasVoted('con'), 'disabled': isVoting || !canVote }">
              <h3 class="team-name">{{ contestInfo.con_team_name }}</h3>
              <p class="team-topic-detail" v-if="contestInfo.con_topic">{{ contestInfo.con_topic }}</p>
              <button class="vote-btn btn-con" @click="submitVote('con')" :disabled="!canVote || isVoting">
                <span class="btn-icon">👍</span>
                <span>支持反方</span>
              </button>
              <div class="vote-confirmation" v-if="hasVoted('con')">
                <el-icon><Check /></el-icon> 已投
              </div>
            </div>
          </div>
        </div>

      </transition>
    </main>

    <!-- 底部调试开关 -->
    <div class="debug-trigger" @click="showDebug = !showDebug"></div>
    <div class="debug-panel glass-effect" v-if="showDebug">
       <p>State: {{ systemStore.currentStage }} | Phase: {{ currentPhase }}</p>
       <p>Voting: {{ votingEnabled }} | CanVote: {{ canVote }}</p>
       <p>Msg: {{ getDiagnosisMessage() }}</p>
    </div>
    
    <!-- 全局加载遮罩 -->
    <div v-if="isVoting" class="loading-mask glass-effect">
      <el-icon class="spinning"><Loading /></el-icon>
      <p>正在提交...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Loading, SuccessFilled, Trophy, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { useSystemStore } from '../../stores/system'
import { getCurrentContest } from '../../api/debate'
import { submitVote as submitVoteApi, getMyVotes, getPublicResults } from '../../api/vote'

const router = useRouter()
const authStore = useAuthStore()
const systemStore = useSystemStore()

const contestInfo = ref(null)
const myVotes = ref({})
const debateResults = ref(null)
const isVoting = ref(false)
const showDebug = ref(false) // 控制调试信息显示

// 计算当前投票阶段
const currentPhase = computed(() => {
  const stage = systemStore.currentStage
  if (stage === 'PRE_VOTING') return 'pre_debate'
  if (stage === 'POST_VOTING') return 'post_debate'
  return null
})

// UI显示的状态文本
const visualState = computed(() => {
  const stage = systemStore.currentStage
  if (stage === 'IDLE') return '未开始'
  if (stage === 'PRE_VOTING') return '赛前投票'
  if (stage === 'POST_VOTING') return '赛后投票'
  if (stage === 'RESULTS_REVEALED') return '已结束'
  if (['DEBATE_IN_PROGRESS', 'JUDGE_SCORING', 'RESULTS_SEALED', 'QNA_SNATCH', 'QNA_INPUT', 'SCORING_TEACHER', 'SCORING_STUDENT'].includes(stage)) {
    return '比赛进行中'
  }
  return '未开始' // 默认
})

// 计算是否显示赛前投票等待页
const showPreVotingWaitingPage = computed(() => {
  const hasPreVote = myVotes.value.pre_debate_voted
  const hasPostVote = myVotes.value.post_debate_voted
  
  // 只有在非投票阶段（如辩论中）才显示等待页
  // 如果是赛后投票阶段，应该显示投票卡片
  const isNotVotingStage = !currentPhase.value
  
  return hasPreVote && !hasPostVote && isNotVotingStage
})

// 计算是否显示赛后投票等待页
const showPostVotingWaitingPage = computed(() => {
  const hasPostVote = myVotes.value.post_debate_voted
  const isNotPostVoting = currentPhase.value !== 'post_debate'
  const isNotResultsRevealed = systemStore.currentStage !== 'RESULTS_REVEALED'
  
  return hasPostVote && isNotPostVoting && isNotResultsRevealed
})

// 计算是否可以投票
const votingEnabled = computed(() => {
  if (!currentPhase.value || !systemStore.debateProgress) {
    return false
  }
  
  // 根据当前阶段检查对应的投票开启状态
  if (currentPhase.value === 'pre_debate') {
    return systemStore.debateProgress.voting_enabled?.pre_voting === true
  } else if (currentPhase.value === 'post_debate') {
    return systemStore.debateProgress.voting_enabled?.post_voting === true
  }
  
  return false
})

// 计算是否可以投票（未投过票）
const canVote = computed(() => {
  if (!currentPhase.value) return false
  if (currentPhase.value === 'pre_debate') return !myVotes.value.pre_debate_voted
  if (currentPhase.value === 'post_debate') return !myVotes.value.post_debate_voted
  return false
})

onMounted(async () => {
  await loadContestInfo()
  await loadMyVotes()
  await systemStore.fetchState()
  await systemStore.fetchDebateProgress()
  
  // 如果已经揭晓结果，加载结果数据
  if (systemStore.currentStage === 'RESULTS_REVEALED') {
    await loadResults()
  }
  
  // 连接 WebSocket
  systemStore.connectWebSocket()
})

// 监听系统状态变化
watch(() => systemStore.currentStage, async (newStage, oldStage) => {
  console.log('系统状态变化:', oldStage, '->', newStage)
  if (newStage === 'RESULTS_REVEALED') {
    ElMessage.success('比赛结果已揭晓！')
    await loadResults()
  }
  // 当阶段变化时重新加载投票记录和辩论进度
  await loadMyVotes()
  await systemStore.fetchDebateProgress()
})

async function loadContestInfo() {
  try {
    const res = await getCurrentContest(authStore.currentClassId)
    // 后端返回格式可能是 { contest: {...} } 或直接 {...}
    contestInfo.value = res.contest || res
  } catch (error) {
    console.error('获取比赛信息失败', error)
  }
}

async function loadMyVotes() {
  if (!contestInfo.value?.id) return
  try {
    const votes = await getMyVotes(contestInfo.value.id)
    myVotes.value = votes
  } catch (error) {
    console.error('获取投票记录失败', error)
  }
}

async function submitVote(teamSide) {
  if (isVoting.value) return
  
  try {
    isVoting.value = true
    const stage = systemStore.currentStage
    let phase = ''
    
    if (stage === 'PRE_VOTING') phase = 'pre_debate'
    else if (stage === 'POST_VOTING') phase = 'post_debate'
    else {
      ElMessage.warning('当前不在投票阶段')
      return
    }

    await submitVoteApi({
      contest_id: contestInfo.value.id,
      team_side: teamSide,
      vote_phase: phase
    })
    
    ElMessage.success('投票成功')
    await loadMyVotes()
    
  } catch (error) {
    console.error('投票失败', error)
    ElMessage.error(error.detail || '投票失败，请重试')
  } finally {
    isVoting.value = false
  }
}

function getStatusIcon() {
  const stage = systemStore.currentStage
  if (stage?.includes('DEBATE') || stage?.includes('QNA')) return '🎤'
  if (stage === 'PRE_VOTING' || stage === 'POST_VOTING') return '⏳'
  if (stage === 'JUDGE_SCORING') return '📝'
  return 'ℹ️'
}

function getStatusMessage() {
  const stage = systemStore.currentStage
  if (stage === 'PRE_VOTING') return '等待投票开启...'
  if (stage === 'POST_VOTING') return '等待投票通道开启...'
  if (stage === 'JUDGE_SCORING') return '评委正在打分，请耐心等待'
  if (stage?.includes('DEBATE')) return '精彩辩论进行中，请认真观看'
  return '请等待管理员操作'
}

function hasVoted(teamSide) {
  if (currentPhase.value === 'pre_debate') {
    return myVotes.value.pre_debate_voted && myVotes.value.pre_debate_team === teamSide
  }
  if (currentPhase.value === 'post_debate') {
    return myVotes.value.post_debate_voted && myVotes.value.post_debate_team === teamSide
  }
  return false
}

function getMyPreVoteTeam() {
  return myVotes.value.pre_debate_team || null
}

function getMyPostVoteTeam() {
  return myVotes.value.post_debate_team || null
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



function getStatusType() {
  return 'info'
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString()
}

// 加载辩论结果
async function loadResults() {
  if (!contestInfo.value?.id) return
  try {
    const results = await getPublicResults(contestInfo.value.id)
    debateResults.value = results
  } catch (error) {
    console.error('获取结果失败', error)
  }
}

// 计算正方得票百分比
function getProPercentage() {
  if (!debateResults.value) return 0
  const total = debateResults.value.pro_post_votes + debateResults.value.con_post_votes
  if (total === 0) return 50
  return Math.round((debateResults.value.pro_post_votes / total) * 100)
}

// 计算反方得票百分比
function getConPercentage() {
  if (!debateResults.value) return 0
  const total = debateResults.value.pro_post_votes + debateResults.value.con_post_votes
  if (total === 0) return 50
  return Math.round((debateResults.value.con_post_votes / total) * 100)
}

// 获取跑票值样式类
function getSwingClass(swingValue) {
  if (swingValue > 0) return 'swing-positive'
  if (swingValue < 0) return 'swing-negative'
  return 'swing-neutral'
}

// 生成彩纸样式
function getConfettiStyle(index) {
  const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#ffa07a', '#98d8c8', '#f7dc6f']
  const randomColor = colors[index % colors.length]
  const randomLeft = Math.random() * 100
  const randomDelay = Math.random() * 3
  const randomDuration = 3 + Math.random() * 2
  
  return {
    left: `${randomLeft}%`,
    backgroundColor: randomColor,
    animationDelay: `${randomDelay}s`,
    animationDuration: `${randomDuration}s`
  }
}

function getDiagnosisMessage() {
  if (!authStore.currentClassId) return "未选择班级"
  if (!systemStore.currentStage) return "系统状态未连接"
  if (!contestInfo.value) return "无比赛信息"
  if (!systemStore.debateProgress) return "辩论进度未加载"
  return "一切正常"
}

// 投票说明文本
function getVotingInstruction() {
  if (currentPhase.value === 'pre_debate') return '请根据你的初始立场进行投票'
  if (currentPhase.value === 'post_debate') return '经过辩论，请投出你最终支持的一方'
  return ''
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
/* Global Reset & Pro Theme */
.mobile-container.pro-theme {
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
  min-height: 100vh;
  padding: 0;
  display: flex;
  flex-direction: column;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  color: #1f2937;
  overflow-x: hidden;
}

/* Glass Effect */
.glass-effect {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

/* Header */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  letter-spacing: -0.5px;
}

/* Status Pill */
.status-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  background: #f1f5f9;
  color: #64748b;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 6px currentColor;
}

/* Status Colors (matching systemStore.currentStage) */
.status-pill.idle { color: #8b5cf6; background: #f3e8ff; }
.status-pill.pre_voting { color: #f59e0b; background: #fef3c7; }
.status-pill.post_voting { color: #0ea5e9; background: #e0f2fe; }
.status-pill.results_revealed { color: #ec4899; background: #fce7f3; }
.status-pill.debate_in_progress, .status-pill.judge_scoring { color: #10b981; background: #d1fae5; }
.status-pill.default { color: #64748b; background: #f1f5f9; }

/* User Profile */
.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255,255,255,0.6);
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.8);
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.03);
}
.user-profile:active { transform: scale(0.96); }
.username { font-size: 13px; font-weight: 600; color: #334155; }
.logout-icon { color: #ef4444; font-size: 16px; }

/* Main Content */
.app-content {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  position: relative;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

.content-card {
  flex: 1;
  background: #ffffff;
  border-radius: 24px;
  padding: 32px 24px;
  box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  border: 1px solid rgba(255,255,255,0.8);
}

.card-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 20px 0;
}

/* Badge Styles */
.choice-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-radius: 16px;
  font-size: 20px;
  font-weight: 700;
  margin: 16px 0 24px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.12);
  transform: translateY(0);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.choice-badge:hover { transform: translateY(-2px); }

.badge-pro { background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); color: white; }
.badge-con { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; }
.side-tag { font-size: 12px; background: rgba(255,255,255,0.25); padding: 4px 8px; border-radius: 6px; font-weight: 600; }

/* Status Content */
.status-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.status-icon-lg {
  font-size: 64px;
  margin-bottom: 8px;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
}
.status-content h2 { font-size: 24px; color: #334155; margin: 0; }
.status-content p { color: #64748b; margin: 0; line-height: 1.6; }

/* Voting Wrapper */
.voting-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.contest-topic-card {
  margin-bottom: 24px;
  padding: 24px;
  border-radius: 20px;
  text-align: center;
  background: white;
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
}
.contest-topic-card h3 { margin: 0 0 12px 0; font-size: 20px; color: #0f172a; line-height: 1.4; }
.round-tag { 
  display: inline-block; 
  background: #f1f5f9; 
  color: #475569; 
  font-size: 12px; 
  font-weight: 600;
  padding: 6px 16px; 
  border-radius: 99px; 
}

.teams-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.team-card {
  flex: 1;
  background: white;
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.team-card:hover { transform: translateY(-2px); box-shadow: 0 12px 24px -8px rgba(0,0,0,0.1); }

/* Pro Team Style */
.team-card.pro-team .team-header { border-left: 4px solid #ef4444; padding-left: 12px; }
.team-card.con-team .team-header { border-left: 4px solid #3b82f6; padding-left: 12px; }

.team-header { flex: 1; display: flex; flex-direction: column; align-items: flex-start; }
.side-label { font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; }
.pro-team .side-label { color: #ef4444; }
.con-team .side-label { color: #3b82f6; }

.team-name { margin: 0; font-size: 18px; color: #1e293b; }

.vote-button-container { flex-shrink: 0; margin-left: 16px; }

.vote-btn {
  padding: 12px 20px;
  border-radius: 14px;
  border: none;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: transform 0.2s;
  color: white;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}
.vote-btn:active { transform: scale(0.95); }
.vote-btn:disabled { opacity: 0.5; cursor: not-allowed; filter: grayscale(1); box-shadow: none; }

.btn-pro { background: linear-gradient(135deg, #ef4444, #b91c1c); }
.btn-con { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }

.vote-confirmation {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  background: #ecfccb;
  color: #4d7c0f;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* ===== Voting Area Styles ===== */
.voting-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: fadeInUp 0.5s ease-out;
}

.contest-topic-card {
  text-align: center;
  padding: 24px;
  background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(255,255,255,0.85));
  backdrop-filter: blur(10px);
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.8);
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
}

.contest-topic-card h3 {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 12px 0;
}

.round-tag {
  display: inline-block;
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.teams-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.team-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(255,255,255,0.85));
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 20px 24px;
  border: 2px solid transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  gap: 20px;
}

.team-card.pro-team {
  border-color: rgba(245, 87, 108, 0.3);
}

.team-card.con-team {
  border-color: rgba(79, 172, 254, 0.3);
}

.team-card.voted {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
  border-color: #10b981;
}

.team-card.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.team-name {
  flex: 1;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.pro-team .team-name {
  color: #f5576c;
}

.con-team .team-name {
  color: #00f2fe;
}

.vote-btn {
  flex-shrink: 0;
  min-width: 180px;
  padding: 14px 28px;
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 700;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.btn-pro {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.btn-pro:hover:not(:disabled) {
  background: linear-gradient(135deg, #f5576c, #f093fb);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(245, 87, 108, 0.4);
}

.btn-con {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.btn-con:hover:not(:disabled) {
  background: linear-gradient(135deg, #00f2fe, #4facfe);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(79, 172, 254, 0.4);
}

.vote-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.vote-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-icon {
  font-size: 20px;
}

.vote-confirmation {
  flex-shrink: 0;
  padding: 10px 16px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #10b981;
  font-weight: 600;
  font-size: 14px;
}

.vs-divider {
  text-align: center;
  font-size: 18px;
  font-weight: 800;
  color: #cbd5e1;
  padding: 12px 0;
  position: relative;
}

.teams-voting {
  position: relative;
}

/* Loading Overlay */
.loading-mask {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(255,255,255,0.8);
}
.spinning { animation: spin 1s linear infinite; font-size: 40px; color: #3b82f6; margin-bottom: 16px; }

/* Utils */
@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulseDot { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1.2); opacity: 0; } }

.loading-dots { display: flex; gap: 6px; margin-top: 16px; }
.loading-dots span { width: 8px; height: 8px; background: #cbd5e1; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* Debug Panel */
.debug-panel {
  position: fixed;
  bottom: 0px;
  left: 0;
  right: 0;
  padding: 12px;
  font-size: 10px;
  z-index: 200;
  background: white; border-top: 1px solid #1e293b;
}
.debug-trigger {
  position: fixed;
  bottom: 0; right: 0; width: 40px; height: 40px; z-index: 300;
}

/* Responsive for Voting Cards */
@media (max-width: 600px) {
  .team-card {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .team-name {
    text-align: center;
    padding-bottom: 12px;
    border-bottom: 2px solid rgba(0,0,0,0.05);
  }
  
  .vote-btn {
    width: 100%;
    min-width: 0;
  }
  
  .vote-confirmation {
    width: 100%;
  }
}


/* ===== Pro Max Results Display Styles ===== */
.results-reveal {
  width: 100%;
  min-height: calc(100vh - 80px);
  padding: 20px;
  overflow-y: auto;
}

.results-container {
  max-width: 900px;
  margin: 0 auto;
  animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Winner Banner */
.winner-banner {
  position: relative;
  margin-bottom: 20px;
  padding: 30px 24px;
  border-radius: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.35);
}

.winner-banner.winner-pro {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 12px 40px rgba(245, 87, 108, 0.35);
}

.winner-banner.winner-con {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  box-shadow: 0 12px 40px rgba(79, 172, 254, 0.35);
}

.winner-banner.winner-tie {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  box-shadow: 0 12px 40px rgba(250, 112, 154, 0.35);
}

/* Confetti Animation */
.confetti-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.confetti {
  position: absolute;
  width: 10px;
  height: 10px;
  top: -10px;
  border-radius: 2px;
  animation: confettiFall linear infinite;
}

@keyframes confettiFall {
  to {
    transform: translateY(calc(100vh + 20px)) rotate(360deg);
    opacity: 0;
  }
}

.winner-content {
  position: relative;
  z-index: 1;
}

.trophy-icon {
  font-size: 56px;
  margin-bottom: 12px;
  animation: trophyBounce 2s ease-in-out infinite;
}

@keyframes trophyBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.winner-title {
  font-size: 28px;
  font-weight: 800;
  margin: 0;
  text-shadow: 0 3px 15px rgba(0,0,0,0.2);
  animation: titlePulse 1.5s ease-in-out infinite;
}

@keyframes titlePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}

/* Debate Topic Result */
.debate-topic-result {
  text-align: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));
  backdrop-filter: blur(10px);
  border-radius: 14px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.06);
}

.debate-topic-result p {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

/* Vote Results Grid */
.vote-results-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 20px;
  margin-bottom: 30px;
  align-items: stretch;
}

@media (max-width: 768px) {
  .winner-banner {
    padding: 24px 20px;
    margin-bottom: 16px;
  }
  
  .trophy-icon {
    font-size: 48px;
    margin-bottom: 10px;
  }
  
  .winner-title {
    font-size: 24px;
  }
  
  .debate-topic-result {
    margin-bottom: 20px;
    padding: 14px 16px;
  }
  
  .debate-topic-result p {
    font-size: 15px;
  }
  
  .vote-results-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .vs-divider-result {
    order: 2;
  }
}

/* Team Result Cards */
.team-result-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(255,255,255,0.85));
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  border: 2px solid transparent;
}

.team-result-card.winner-card {
  border-color: #fbbf24;
  box-shadow: 0 10px 40px rgba(251, 191, 36, 0.4), 0 0 0 4px rgba(251, 191, 36, 0.1);
}

.team-result-card.winner-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 48px rgba(251, 191, 36, 0.45), 0 0 0 4px rgba(251, 191, 36, 0.15);
}

.team-header-result {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  position: relative;
}

.side-badge {
  padding: 6px 14px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.side-badge.pro {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: white;
}

.side-badge.con {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
  color: white;
}

.team-header-result h3 {
  flex: 1;
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.winner-crown {
  font-size: 28px;
  animation: crownRotate 2s ease-in-out infinite;
}

@keyframes crownRotate {
  0%, 100% { transform: rotate(-10deg); }
  50% { transform: rotate(10deg); }
}

/* Vote Stats */
.vote-stats {
  margin-bottom: 20px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.stat-label {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
}

.stat-value.final-vote {
  color: #3b82f6;
}

.fade-in {
  animation: fadeInScale 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-in-delay {
  animation: fadeInScale 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.3s both;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.stat-divider {
  height: 2px;
  background: linear-gradient(90deg, transparent, #cbd5e1, transparent);
  margin: 16px 0;
}

/* Swing Indicator */
.swing-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(0,0,0,0.02);
  border-radius: 12px;
  margin-top: 8px;
}

.swing-label {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.swing-value {
  font-size: 24px;
  font-weight: 800;
  padding: 4px 12px;
  border-radius: 8px;
}

.swing-positive {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.swing-negative {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.swing-neutral {
  color: #6b7280;
  background: rgba(107, 114, 128, 0.1);
}

/* Progress Bars */
.vote-bar-container {
  position: relative;
  width: 100%;
  height: 36px;
  background: rgba(0,0,0,0.05);
  border-radius: 18px;
  overflow: hidden;
}

.vote-bar {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 12px;
  border-radius: 18px;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1) 0.5s;
  position: relative;
  overflow: hidden;
}

.vote-bar::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  100% {
    left: 100%;
  }
}

.pro-bar {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.con-bar {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.bar-label {
  font-size: 16px;
  font-weight: 700;
  color: white;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
  position: relative;
  z-index: 1;
}

/* VS Divider Result */
.vs-divider-result {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
}

.vs-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  animation: vsRotate 3s ease-in-out infinite;
}

@keyframes vsRotate {
  0%, 100% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.1); }
}

/* Thank You Message */
.thank-you-message {
  text-align: center;
  padding: 30px;
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08);
}

.thank-you-message p {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

/* Results Loading */
.results-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 20px;
}

.results-loading p {
  font-size: 18px;
  color: #64748b;
  font-weight: 500;
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

</style>

<style scoped>
.team-topic-detail {
  font-size: 14px;
  color: rgba(0,0,0,0.6);
  margin: 4px 0 12px;
  line-height: 1.3;
  font-weight: 500;
}
</style>

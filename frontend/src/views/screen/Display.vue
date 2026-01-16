<template>
  <div class="screen-container">
    <!-- 错误提示：缺少比赛ID -->
    <div v-if="!contestIdFromUrl" class="error-state">
      <h2>❌ 缺少比赛ID</h2>
      <p>请从管理端点击"打开大屏"按钮</p>
      <p class="example">或访问: /screen?contest_id=1</p>
    </div>
    
    <!-- 加载状态 -->
    <div v-else-if="loading" class="loading-state">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <p>加载比赛数据中...</p>
    </div>
    
    <!-- 比赛不存在 -->
    <div v-else-if="!contestInfo" class="error-state">
      <h2>❌ 比赛不存在</h2>
      <p>比赛ID: {{ contestIdFromUrl }}</p>
    </div>
    
    <template v-else>
      <!-- 头部信息 -->
      
      <!-- 辩论赛模式 -->
      <template v-if="isDebateMode">
        <!-- 辩论赛状态面板 -->
        <div class="debate-status-panel">
          <div class="contest-info" v-if="contestInfo">
            <h2 class="contest-topic">{{ contestInfo.topic }}</h2>
            <div class="teams-display">
              <div class="team pro-team">
                <span class="team-label">正方</span>
                <span class="team-name">{{ contestInfo.pro_team_name }}</span>
                <div class="team-topic" v-if="contestInfo.pro_topic">{{ contestInfo.pro_topic }}</div>
              </div>
              <div class="vs-divider">VS</div>
              <div class="team con-team">
                <span class="team-label">反方</span>
                <span class="team-name">{{ contestInfo.con_team_name }}</span>
                <div class="team-topic" v-if="contestInfo.con_topic">{{ contestInfo.con_topic }}</div>
              </div>
            </div>
          </div>
          

        </div>

        <!-- 主内容区域 - 辩论赛 -->
        <div class="main-content">
          <!-- 投票引导阶段 -->
          <div v-if="stage === 'PRE_VOTING' || stage === 'POST_VOTING'" class="voting-state">
            <div class="qr-section">
              <div class="qr-container">
                <img src="/assest/login.png" alt="扫码参与投票" class="qr-image" />
                <p class="qr-text">扫码参与投票</p>
              </div>
            </div>
            
            <div class="voting-progress">
              <h3>{{ stage === 'PRE_VOTING' ? '赛前投票进行中' : '赛后投票进行中' }}</h3>
              
              <!-- 投票总数 -->
              <div class="vote-count">
                <span class="count-number">{{ currentVotingProgress.submitted || 0 }}</span>
                <span class="count-label">/ {{ currentVotingProgress.total || 0 }} 人已投票</span>
              </div>
              
              <!-- 进度条 -->
              <div class="progress-bar-container">
                <div class="progress-bar-bg">
                  <div 
                    class="progress-bar-fill" 
                    :style="{ width: currentVotingProgress.percentage + '%' }"
                  ></div>
                </div>
                <div class="progress-percentage">{{ currentVotingProgress.percentage || 0 }}%</div>
              </div>
              
              <div class="progress-note">
                <p>投票分布将在结果揭晓时公布</p>
              </div>
            </div>
          </div>

          <!-- 辩论进行中 -->
          <div v-else-if="stage === 'DEBATE_IN_PROGRESS'" class="debate-progress-state">
            <div class="big-text">辩论正在进行中</div>
            <div class="sub-text">请认真观看，准备投票</div>
          </div>

          <!-- 评委评分中 -->
          <div v-else-if="stage === 'JUDGE_SCORING'" class="scoring-state">
            <div class="big-text">评委评分中</div>
            <div class="sub-text">请等待评委完成评分</div>
            
            <!-- 评分进度详情 -->
            <div class="scoring-progress" v-if="debateProgress.judge_scoring_progress">
              <div class="progress-circle">
                <span class="progress-number">{{ debateProgress.judge_scoring_progress.submitted }}</span>
                <span class="progress-total">/ {{ debateProgress.judge_scoring_progress.total }}</span>
              </div>
              <p>评委已提交评分</p>
              
              <!-- 进度条 -->
              <div class="progress-bar-container" style="margin-top: 20px;">
                <div class="progress-bar-bg">
                  <div 
                    class="progress-bar-fill scoring" 
                    :style="{ width: debateProgress.judge_scoring_progress.percentage + '%' }"
                  ></div>
                </div>
                <div class="progress-percentage">{{ debateProgress.judge_scoring_progress.percentage || 0 }}%</div>
              </div>
            </div>
          </div>

          <!-- 结果封存 -->
          <div v-else-if="stage === 'RESULTS_SEALED'" class="sealed-state">
            <div class="big-text">投票通道已关闭</div>
            <div class="sub-text">数据封存计算中...</div>
            <div class="loading-animation">
              <el-icon class="loading-icon"><Loading /></el-icon>
            </div>
          </div>

          <!-- 结果揭晓 -->
          <!-- 结果揭晓 (UI UX Pro Max) -->
          <div v-else-if="stage === 'RESULTS_REVEALED'" class="results-state-max">
            <div class="results-header">
               <div class="winner-label">🏆 获胜队伍 🏆</div>
               <div class="winner-name-max" :class="contestResults?.winning_team">
                  {{ contestResults?.winning_team === 'pro' ? contestInfo?.pro_team_name : 
                     contestResults?.winning_team === 'con' ? contestInfo?.con_team_name : '平局' }}
               </div>
            </div>

            <div v-if="contestResults" class="results-content-max">
              <!-- 左侧：观众投票评分 -->
              <div class="result-card glass-panel vote-panel">
                <h3 class="panel-title">👥 观众投票评分</h3>
                <div class="vote-swing-container">
                  <div class="team-vote-row pro">
                     <div class="team-name-large">{{ contestInfo?.pro_team_name }}</div>
                     
                     <div class="vote-stats-grid">
                        <div class="stat-box">
                            <div class="stat-label">赛前</div>
                            <div class="stat-val">{{ contestResults.vote_analysis[0].pre_debate_votes }}</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">赛后</div>
                            <div class="stat-val">{{ contestResults.vote_analysis[0].post_debate_votes }}</div>
                        </div>
                        <div class="stat-box highlight">
                            <div class="stat-label">跑票</div>
                            <div class="stat-val" :class="{positive: contestResults.pro_team_swing > 0, negative: contestResults.pro_team_swing < 0}">
                                {{ contestResults.pro_team_swing > 0 ? '+' : '' }}{{ contestResults.pro_team_swing }}
                            </div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">增长率</div>
                            <div class="stat-val">{{ formatRate(contestResults.vote_analysis[0].growth_rate) }}</div>
                        </div>
                     </div>
                  </div>
                  <div class="vs-divider-mini">VS</div>
                  <div class="team-vote-row con">
                     <div class="team-name-large">{{ contestInfo?.con_team_name }}</div>
                     
                     <div class="vote-stats-grid">
                        <div class="stat-box">
                            <div class="stat-label">赛前</div>
                            <div class="stat-val">{{ contestResults.vote_analysis[1].pre_debate_votes }}</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">赛后</div>
                            <div class="stat-val">{{ contestResults.vote_analysis[1].post_debate_votes }}</div>
                        </div>
                        <div class="stat-box highlight">
                            <div class="stat-label">跑票</div>
                            <div class="stat-val" :class="{positive: contestResults.con_team_swing > 0, negative: contestResults.con_team_swing < 0}">
                                {{ contestResults.con_team_swing > 0 ? '+' : '' }}{{ contestResults.con_team_swing }}
                            </div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">增长率</div>
                            <div class="stat-val">{{ formatRate(contestResults.vote_analysis[1].growth_rate) }}</div>
                        </div>
                     </div>
                  </div>
                </div>
              </div>

              <!-- 右侧：优秀辩手排行榜 (Top 4) -->
              <div class="result-card glass-panel rank-panel">
                <h3 class="panel-title">🌟 优秀辩手排行榜</h3>
                <div class="rank-list-max">
                  <div 
                    v-for="(debater, index) in contestResults.debater_rankings.slice(0, 4)" 
                    :key="debater.debater_id"
                    class="rank-row"
                    :class="'rank-' + (index + 1)"
                    :style="{'--delay': index * 0.15 + 's'}"
                  >
                    <div class="rank-num">{{ index + 1 }}</div>
                    <div class="debater-avatar-placeholder">
                       {{ debater.debater_name.charAt(0) }}
                    </div>
                    <div class="debater-info">
                       <span class="d-name">{{ debater.debater_name }}</span>
                       <div class="d-team-info">
                           <span class="d-team-badge" :class="debater.team_side">
                              {{ debater.team_side === 'pro' ? '正方' : '反方' }}
                           </span>
                           <span class="d-team-name-text">
                              {{ debater.team_side === 'pro' ? contestInfo?.pro_team_name : contestInfo?.con_team_name }}
                           </span>
                       </div>
                    </div>
                    <div class="final-score">{{ debater.final_score }} <span class="unit">分</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 等待开始 -->
          <div v-else class="idle-state">
            <h2>等待辩论赛开始...</h2>
          </div>
        </div>
      </template>

      <!-- 传统答辩模式 -->
      <template v-else>
        <!-- 当前状态 -->
        <div class="status-panel">
          <div class="stage-display">
            <span class="stage-label">当前阶段</span>
            <span class="stage-value" :class="stageClass">{{ stageText }}</span>
          </div>
          
          <div v-if="currentTeam" class="team-display">
            <span class="team-label">答辩团队</span>
            <span class="team-value">{{ currentTeam.name }}</span>
          </div>
          
          <div v-if="currentTeam?.topic" class="topic-display">
            <span class="topic-label">课题主题</span>
            <span class="topic-value">{{ currentTeam.topic }}</span>
          </div>
          
          <!-- 正计时（答辩展示阶段显示） -->
          <div v-if="stage === 'PRESENTATION' && elapsedTime !== null" class="elapsed-display">
            <span class="elapsed-label">已用时间</span>
            <span class="elapsed-value">{{ formatElapsedTime(elapsedTime) }}</span>
          </div>
          
          <div v-if="stage === 'QNA_SNATCH'" class="snatch-display">
            <span class="snatch-label">剩余提问名额</span>
            <span class="snatch-value">{{ snatchRemaining }} / 3</span>
          </div>
          
          <!-- 倒计时 -->
          <div v-if="stage === 'QNA_SNATCH'" class="countdown-display">
            <span class="countdown-label">倒计时</span>
            <span class="countdown-value" v-if="countdown > 0" :class="{ urgent: countdown <= 10 }">{{ countdown }}s</span>
            <span class="countdown-value urgent" v-else>结束</span>
          </div>
        </div>
        
        <!-- 主内容区域 - 传统答辩 -->
        <div class="main-content">
          <div v-if="stage === 'IDLE'" class="idle-state">
            <h2>等待答辩开始...</h2>
          </div>
          
          <div v-else-if="stage === 'PRESENTATION'" class="presentation-state">
            <div class="big-text">{{ currentTeam?.name }}</div>
            <div class="sub-text">正在进行答辩展示</div>
          </div>
          
          <div v-else-if="stage === 'SCORING_TEACHER'" class="scoring-state">
            <div class="big-text">{{ teacherScoringCompleted ? '评分完成' : '评委评分中' }}</div>
            <div v-if="!teacherScoringCompleted" class="sub-text">请各位评委完成评分</div>
            <div v-if="teacherScoringCompleted && teacherAvgScore !== null" class="teacher-score-display">
              <span class="score-label">评委评分</span>
              <span class="score-value">{{ teacherAvgScore }}</span>
              <span class="score-suffix">分（平均分）</span>
            </div>
          </div>
          
          <div v-else-if="stage === 'SCORING_STUDENT'" class="scoring-state">
            <div class="big-text">{{ studentScoringCompleted ? '评分完成' : '学生互评中' }}</div>
            <div v-if="!studentScoringCompleted" class="sub-text">请各团队完成互评</div>
            <div v-if="studentScoringCompleted && studentAvgScore !== null" class="teacher-score-display">
              <span class="score-label">学生评分</span>
              <span class="score-value">{{ studentAvgScore }}</span>
              <span class="score-suffix">分（平均分）</span>
            </div>
          </div>
          
          <!-- 提问环节 - 只显示问题墙 -->
          <div v-else-if="stage === 'QNA_SNATCH'" class="snatch-state">
            <div class="question-wall">
              <el-card 
                v-for="(slot, index) in 3" 
                :key="index"
                class="question-card"
                :class="{ active: questions[index] }"
                shadow="hover"
              >
                <template v-if="questions[index]" #header>
                  <div class="card-header">
                    <el-icon class="header-icon"><ChatDotRound /></el-icon>
                    <span>{{ questions[index].asker_team_name }}</span>
                  </div>
                </template>
                <template v-if="questions[index]">
                  <div class="question-text">{{ questions[index].content || '正在输入问题...' }}</div>
                </template>
                <template v-else>
                  <div class="empty-slot">
                    <el-icon class="waiting-icon"><Clock /></el-icon>
                    <span>等待提问</span>
                  </div>
                </template>
              </el-card>
            </div>
          </div>
          
          <div v-else-if="stage === 'FINISHED'" class="finished-state">
            <div class="big-text">{{ currentTeam?.name }}</div>
            <div class="sub-text">答辩已结束</div>
            <div class="scores-container">
              <div v-if="teacherAvgScore !== null" class="teacher-score-display">
                <span class="score-label">评委评分</span>
                <span class="score-value">{{ teacherAvgScore }}</span>
                <span class="score-suffix">分（平均分）</span>
              </div>
              <div v-if="studentAvgScore !== null" class="teacher-score-display">
                <span class="score-label">学生评分</span>
                <span class="score-value">{{ studentAvgScore }}</span>
                <span class="score-suffix">分（平均分）</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Expand, Loading, ChatDotRound, Clock } from '@element-plus/icons-vue'
import { getSystemState } from '../../api/admin'
import { getContestById, getDebateResults } from '../../api/debate'

const route = useRoute()
const router = useRouter()

// 从URL获取比赛ID
const contestIdFromUrl = ref(null)
const loading = ref(true)
const stage = ref('IDLE')
const currentTeam = ref(null)
const snatchRemaining = ref(3)
const snatchStartTime = ref(null)
const countdown = ref(30)
const questions = ref([])
const teacherAvgScore = ref(null)
const studentAvgScore = ref(null)
const teacherScoringCompleted = ref(false)
const studentScoringCompleted = ref(false)
const updateTime = ref(null)
const elapsedTime = ref(null)

// 辩论赛相关状态
const contestInfo = ref(null)
const contestResults = ref(null)
const debateProgress = ref({})
const totalVotes = ref(0)
const isDebateMode = computed(() => !!contestInfo.value)

let elapsedTimer = null
let ws = null

// 辩论赛阶段文本和样式
const debateStageText = computed(() => {
  const texts = {
    IDLE: '等待开始',
    PRE_VOTING: '赛前投票中',
    DEBATE_IN_PROGRESS: '辩论进行中',
    POST_VOTING: '赛后投票中',
    JUDGE_SCORING: '评委评分中',
    RESULTS_SEALED: '结果封存',
    RESULTS_REVEALED: '结果已揭晓'
  }
  return texts[stage.value] || stage.value
})

const debateStageClass = computed(() => {
  return `debate-stage-${stage.value?.toLowerCase()}`
})

// 当前投票进度（根据当前阶段）
const currentVotingProgress = computed(() => {
  if (!debateProgress.value) return { submitted: 0, total: 0, percentage: 0 }
  
  if (stage.value === 'PRE_VOTING') {
    return debateProgress.value.pre_voting_progress || { submitted: 0, total: 0, percentage: 0 }
  } else if (stage.value === 'POST_VOTING') {
    return debateProgress.value.post_voting_progress || { submitted: 0, total: 0, percentage: 0 }
  }
  
  return { submitted: 0, total: 0, percentage: 0 }
})

// 传统答辩阶段文本和样式
const stageText = computed(() => {
  const texts = {
    IDLE: '等待开始',
    PRESENTATION: '答辩展示',
    SCORING_TEACHER: '评委评分',
    SCORING_STUDENT: '学生互评',
    QNA_SNATCH: '提问环节',
    QNA_INPUT: '提问输入',
    FINISHED: '本轮结束'
  }
  return texts[stage.value] || stage.value
})

const stageClass = computed(() => {
  return `stage-${stage.value?.toLowerCase()}`
})

onMounted(async () => {
  // 从 URL 参数获取 contest_id
  const contestId = route.query.contest_id
  if (contestId) {
    contestIdFromUrl.value = parseInt(contestId)
    await loadContestData()
  } else {
    loading.value = false
  }
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  stopElapsedTimer()
})

// 加载比赛数据
async function loadContestData() {
  try {
    loading.value = true
    // 根据 contest_id 获取比赛信息
    contestInfo.value = await getContestById(contestIdFromUrl.value)
    console.log('比赛信息已加载:', contestInfo.value)
    
    if (contestInfo.value) {
      // 获取系统状态（使用比赛的 class_id）
      await fetchState()
      console.log('系统状态:', stage.value)
      
      // 如果结果已揭晓，获取比赛结果
      if (stage.value === 'RESULTS_REVEALED') {
        console.log('正在加载比赛结果...')
        await loadContestResults()
        console.log('比赛结果已加载:', contestResults.value)
      }
      
      // 连接WebSocket
      connectWebSocket()
    }
  } catch (error) {
    console.error('加载比赛数据失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadContestResults() {
  if (!contestInfo.value) return
  
  try {
    contestResults.value = await getDebateResults(contestInfo.value.id)
    console.log('获取到比赛结果:', contestResults.value)
  } catch (error) {
    console.error('获取比赛结果失败:', error)
  }
}

async function fetchState() {
  if (!contestInfo.value) return
  
  try {
    const state = await getSystemState(contestInfo.value.class_id)
    stage.value = state.current_stage
    currentTeam.value = state.current_team_id ? {
      id: state.current_team_id,
      name: state.current_team_name,
      topic: state.current_team_topic
    } : null
    snatchRemaining.value = state.snatch_slots_remaining
    snatchStartTime.value = state.snatch_start_time
    
    // 设置倒计时（如果 API 返回了当前值）
    if (state.countdown !== null && state.countdown !== undefined) {
      countdown.value = state.countdown
    } else if (stage.value === 'QNA_SNATCH' && state.snatch_start_time) {
      // 如果在提问阶段且有开始时间，计算剩余倒计时
      const elapsed = Math.floor((Date.now() - state.snatch_start_time) / 1000)
      countdown.value = Math.max(0, 30 - elapsed)
    } else {
      countdown.value = 0
    }
    
    // 获取评委平均分
    teacherAvgScore.value = state.teacher_avg_score ?? null
    
    // 获取学生平均分
    studentAvgScore.value = state.student_avg_score ?? null
    
    // 获取评分完成状态
    teacherScoringCompleted.value = state.teacher_scoring_completed ?? false
    studentScoringCompleted.value = state.student_scoring_completed ?? false
    
    // 获取更新时间并启动正计时
    updateTime.value = state.update_time ?? null
    if (stage.value === 'PRESENTATION' && updateTime.value) {
      startElapsedTimer()
    } else {
      stopElapsedTimer()
    }
    
    if (stage.value === 'QNA_SNATCH') {
      await fetchQuestions()
    }
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

async function fetchQuestions() {
  if (!currentTeam.value || !contestInfo.value) return
  try {
    const allQuestions = await getQuestions(contestInfo.value.class_id)
    // 过滤出当前团队的问题
    questions.value = allQuestions.filter(q => q.target_team_id === currentTeam.value.id)
  } catch (error) {
    console.error('获取问题失败:', error)
  }
}

// Removed stopCountdown function

// 启动正计时
function startElapsedTimer() {
  stopElapsedTimer() // 先清除已有的定时器
  if (!updateTime.value) return
  
  // 立即计算一次
  elapsedTime.value = Math.floor((Date.now() - updateTime.value) / 1000)
  
  // 每秒更新
  elapsedTimer = setInterval(() => {
    elapsedTime.value = Math.floor((Date.now() - updateTime.value) / 1000)
  }, 1000)
}

// 停止正计时
function stopElapsedTimer() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
  elapsedTime.value = null
}

// 格式化增长率
function formatRate(rate) {
  if (rate === Infinity || rate > 9999) return '∞'
  return (rate || 0).toFixed(1) + '%'
}

// 格式化已用时间（秒 -> 分:秒）
function formatElapsedTime(seconds) {
  if (seconds === null || seconds < 0) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function connectWebSocket() {
  if (!contestInfo.value) return
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws?class_id=${contestInfo.value.class_id}`
  ws = new WebSocket(wsUrl)
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    handleMessage(message)
  }
  
  ws.onclose = () => {
    console.log('WebSocket 断开，5秒后重连...')
    setTimeout(() => {
      if (contestInfo.value) {
        connectWebSocket()
      }
    }, 5000)
  }
}

async function openCountdownPopup() {
  // 检查是否支持 Document Picture-in-Picture API
  if ('documentPictureInPicture' in window) {
    try {
      const pipWindow = await window.documentPictureInPicture.requestWindow({
        width: 300,
        height: 200
      })
      
      // 复制样式到 PiP 窗口
      const style = pipWindow.document.createElement('style')
      style.textContent = `
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          color: white;
          text-align: center;
        }
        .container { padding: 20px; }
        .stage { 
          font-size: 14px; 
          padding: 6px 16px; 
          border-radius: 20px; 
          background: rgba(255,255,255,0.1);
          margin-bottom: 15px;
          display: inline-block;
        }
        .stage.qna { background: rgba(245,108,108,0.3); color: #f56c6c; }
        .stage.presentation { background: rgba(64,158,255,0.3); color: #409eff; }
        .countdown { 
          font-size: 100px; 
          font-weight: bold; 
          color: #67c23a;
          line-height: 1;
          text-shadow: 0 0 30px rgba(103,194,58,0.5);
        }
        .countdown.urgent { 
          color: #f56c6c; 
          text-shadow: 0 0 30px rgba(245,108,108,0.5);
          animation: pulse 1s infinite;
        }
        .elapsed {
          font-size: 60px;
          font-weight: bold;
          color: #409eff;
          text-shadow: 0 0 30px rgba(64,158,255,0.5);
        }
        .unit { font-size: 18px; color: rgba(255,255,255,0.6); margin-top: 5px; }
        .team { font-size: 14px; color: rgba(255,255,255,0.5); margin-top: 10px; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
      `
      pipWindow.document.head.appendChild(style)
      
      // 创建内容容器
      const container = pipWindow.document.createElement('div')
      container.className = 'container'
      pipWindow.document.body.appendChild(container)
      
      // 更新函数
      const updatePipContent = () => {
        let stageClass = ''
        let stageText = ''
        const texts = {
          IDLE: '等待开始',
          PRESENTATION: '答辩展示',
          SCORING_TEACHER: '评委评分',
          SCORING_STUDENT: '学生互评',
          QNA_SNATCH: '提问环节',
          FINISHED: '本轮结束'
        }
        stageText = texts[stage.value] || stage.value
        
        if (stage.value === 'QNA_SNATCH') {
          stageClass = 'qna'
          const urgentClass = countdown.value <= 10 ? 'urgent' : ''
          container.innerHTML = `
            <div class="countdown ${urgentClass}">${countdown.value}</div>
            <div class="unit">秒</div>
          `
        } else if (stage.value === 'PRESENTATION' && elapsedTime.value !== null) {
          stageClass = 'presentation'
          container.innerHTML = `
            <div class="elapsed">${formatElapsedTime(elapsedTime.value)}</div>
            <div class="unit">已用时间</div>
          `
        } else {
          container.innerHTML = `
            <div class="stage">${stageText}</div>
          `
        }
      }
      
      // 初始渲染
      updatePipContent()
      
      // 定时更新
      const pipInterval = setInterval(updatePipContent, 500)
      
      // 窗口关闭时清理
      pipWindow.addEventListener('pagehide', () => {
        clearInterval(pipInterval)
      })
      
      return
    } catch (error) {
      console.error('Document PiP 不可用:', error)
    }
  } else {
    console.warn('浏览器不支持 Document Picture-in-Picture API')
  }
}

function handleMessage(message) {
  // 统一转换 type 为小写以兼容后端可能的大写类型
  const msgType = message.type ? message.type.toLowerCase() : ''
  
  switch (msgType) {
    case 'state_update':
      // 兼容 stage 和 current_stage 字段
      const newStage = message.data.stage || message.data.current_stage
      if (newStage) {
        stage.value = newStage
        
        // 如果状态变为结果揭晓，立即加载结果数据
        if (stage.value === 'RESULTS_REVEALED') {
          console.log('状态变为已揭晓，主动加载结果数据...')
          loadContestResults()
        }
      }
      
      if (message.data.current_team) {
        currentTeam.value = message.data.current_team
      }
      
      if (message.data.snatch_slots_remaining !== undefined) {
        snatchRemaining.value = message.data.snatch_slots_remaining
      }
      
      snatchStartTime.value = message.data.snatch_start_time || null
      
      if (message.data.countdown !== undefined) {
        countdown.value = message.data.countdown || 0
      }
      
      teacherAvgScore.value = message.data.teacher_avg_score ?? null
      studentAvgScore.value = message.data.student_avg_score ?? null
      teacherScoringCompleted.value = message.data.teacher_scoring_completed ?? false
      studentScoringCompleted.value = message.data.student_scoring_completed ?? false
      updateTime.value = message.data.update_time ?? updateTime.value
      
      // 正计时控制
      if (stage.value === 'PRESENTATION' && updateTime.value) {
        startElapsedTimer()
      } else {
        stopElapsedTimer()
      }
      
      // 如果不在提问阶段，清空问题列表
      if (stage.value !== 'QNA_SNATCH') {
        questions.value = []
      }
      break
      
    case 'debate_update':
      // 辩论赛状态更新
      stage.value = message.data.stage
      contestInfo.value = message.data.contest
      debateProgress.value = message.data.progress || {}
      
      // 如果结果已揭晓，加载比赛结果
      if (stage.value === 'RESULTS_REVEALED' && contestInfo.value) {
        loadContestResults()
      }
      break
      
    case 'vote_progress':
      // 投票进度更新（仅显示总数，不显示分布）
      totalVotes.value = message.data.total_votes
      break
      
    case 'results_reveal':
      // 结果揭晓
      console.log('收到results_reveal消息:', message.data)
      if (message.data.results) {
        contestResults.value = message.data.results
        console.log('更新比赛结果:', contestResults.value)
      }
      break
      
    case 'SNATCH_UPDATE':
      snatchRemaining.value = message.data.slots_remaining
      fetchQuestions()
      break
      
    case 'TIMER_UPDATE':
      // 收到后端实时倒计时更新
      countdown.value = message.data.countdown
      break
      
    case 'NEW_QUESTION':
      fetchQuestions()
      break
  }
}
</script>

<style scoped>
.screen-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: white;
  padding: 40px;
  position: relative;
}

.class-selector {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 100;
}

.class-selector :deep(.el-select) {
  width: 200px;
}

.class-selector :deep(.el-select__wrapper),
.class-selector :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
  backdrop-filter: blur(10px);
}

.class-selector :deep(.el-select__wrapper:hover),
.class-selector :deep(.el-input__wrapper:hover) {
  border-color: rgba(102, 126, 234, 0.6) !important;
}

.class-selector :deep(.el-select__selected-item),
.class-selector :deep(.el-input__inner) {
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 500;
}

.class-selector :deep(.el-select__placeholder),
.class-selector :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}


/* UI UX Pro Max Results Styles */
.results-state-max {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.8s ease-out;
}

.results-header {
  text-align: center;
  margin-bottom: 40px;
}

.winner-label {
  font-size: 24px;
  color: #ffd700;
  margin-bottom: 10px;
  text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
  letter-spacing: 4px;
}

.winner-name-max {
  font-size: 72px;
  font-weight: 900;
  background: linear-gradient(to right, #ffffff, #e0e0e0);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.3));
  animation: scaleIn 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.winner-name-max.pro {
  background: linear-gradient(to right, #409eff, #79bbff);
  background-clip: text;
  -webkit-background-clip: text;
  filter: drop-shadow(0 0 30px rgba(64, 158, 255, 0.6));
}

.winner-name-max.con {
  background: linear-gradient(to right, #f56c6c, #f89898);
  background-clip: text;
  -webkit-background-clip: text;
  filter: drop-shadow(0 0 30px rgba(245, 108, 108, 0.6));
}

.results-content-max {
  display: flex;
  gap: 40px;
  width: 90%;
  max-width: 1400px;
  height: 60vh;
}

.result-card {
  flex: 1;
  border-radius: 24px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.result-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
  border-color: rgba(255, 255, 255, 0.2);
}

.panel-title {
  font-size: 28px;
  margin-bottom: 30px;
  text-align: center;
  color: rgba(255, 255, 255, 0.9);
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 15px;
}

/* Vote Panel Styles */
.vote-swing-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
  gap: 30px;
}

.team-vote-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.2);
}

.team-vote-row.pro { border-left: 6px solid #409eff; }
.team-vote-row.con { border-left: 6px solid #f56c6c; }

.team-name-large {
  font-size: 32px;
  font-weight: bold;
}

.vs-divider-mini {
  text-align: center;
  font-size: 24px;
  color: rgba(255,255,255,0.3);
  font-style: italic;
  font-weight: 900;
}

.vote-change-box {
  font-size: 28px;
  font-weight: bold;
  padding: 10px 20px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
}

.vote-change-box.positive { color: #67c23a; background: rgba(103, 194, 58, 0.2); }
.vote-change-box.negative { color: #f56c6c; background: rgba(245, 108, 108, 0.2); }

/* Rank Panel Styles */
.rank-list-max {
  display: flex;
  flex-direction: column;
  gap: 15px;
  flex: 1;
  overflow-y: auto;
}

.rank-row {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  transition: all 0.3s ease;
  animation: slideInRight 0.6s ease-out backwards;
  animation-delay: var(--delay);
}

.rank-row:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(10px);
}

.rank-num {
  font-size: 24px;
  font-weight: 900;
  width: 40px;
  color: rgba(255, 255, 255, 0.5);
}

.rank-1 .rank-num { color: #ffd700; text-shadow: 0 0 10px rgba(255, 215, 0, 0.5); font-size: 32px; }
.rank-2 .rank-num { color: #c0c0c0; text-shadow: 0 0 10px rgba(192, 192, 192, 0.5); font-size: 28px; }
.rank-3 .rank-num { color: #cd7f32; text-shadow: 0 0 10px rgba(205, 127, 50, 0.5); font-size: 26px; }

.debater-avatar-placeholder {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  font-weight: bold;
  margin-right: 20px;
  border: 2px solid rgba(255,255,255,0.2);
}

.rank-1 .debater-avatar-placeholder { border-color: #ffd700; box-shadow: 0 0 15px rgba(255, 215, 0, 0.4); }

.debater-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.d-name {
  font-size: 20px;
  font-weight: bold;
}

.d-team-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  margin-top: 4px;
  width: fit-content;
}

.d-team-badge.pro { background: rgba(64, 158, 255, 0.3); color: #409eff; }
.d-team-badge.con { background: rgba(245, 108, 108, 0.3); color: #f56c6c; }

.final-score {
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

.final-score .unit {
  font-size: 14px;
  color: rgba(255,255,255,0.5);
  font-weight: normal;
}

@keyframes scaleIn {
  0% { transform: scale(0.5); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes slideInRight {
  0% { transform: translateX(50px); opacity: 0; }
  100% { transform: translateX(0); opacity: 1; }
}

@keyframes fadeIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

.no-class {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
}

.no-class h2 {
  font-size: 48px;
  opacity: 0.5;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 48px;
  font-weight: bold;
  margin: 0 0 16px 0;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.class-name {
  font-size: 24px;
  opacity: 0.8;
}

.status-panel {
  display: flex;
  justify-content: center;
  gap: 60px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.stage-display,
.team-display,
.topic-display,
.snatch-display,
.countdown-display {
  text-align: center;
}

.stage-label,
.team-label,
.topic-label,
.snatch-label,
.countdown-label {
  display: block;
  font-size: 18px;
  opacity: 0.6;
  margin-bottom: 8px;
}

.stage-value,
.team-value,
.topic-value,
.snatch-value,
.countdown-value,
.elapsed-value {
  display: block;
  font-size: 32px;
  font-weight: bold;
}

.countdown-value {
  color: #67c23a;
}

.countdown-value.urgent {
  color: #f56c6c;
  animation: pulse 1s infinite;
}

/* 正计时样式 */
.elapsed-display {
  text-align: center;
}

.elapsed-label {
  display: block;
  font-size: 18px;
  opacity: 0.6;
  margin-bottom: 8px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.stage-idle { color: #909399; }
.stage-presentation { color: #409eff; }
.stage-scoring_teacher { color: #67c23a; }
.stage-scoring_student { color: #e6a23c; }
.stage-qna_snatch { color: #f56c6c; }
.stage-finished { color: #909399; }

.main-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 400px;
}

.idle-state h2,
.big-text {
  font-size: 72px;
  font-weight: bold;
  text-align: center;
  margin: 0;
}

.sub-text {
  font-size: 32px;
  text-align: center;
  margin-top: 24px;
  opacity: 0.7;
}

.presentation-state,
.scoring-state,
.snatch-state,
.finished-state {
  text-align: center;
}

.snatch-state .big-text {
  color: #f56c6c;
}

.scoring-state .big-text {
  color: #67c23a;
}

/* 问题墙样式 */
.question-wall {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.question-card {
  background: rgba(255, 255, 255, 0.1) !important;
  border: none !important;
  border-radius: 12px !important;
}

.question-card.active {
  background: rgba(102, 126, 234, 0.15) !important;
  border: 1px solid rgba(102, 126, 234, 0.4) !important;
}

.question-card :deep(.el-card__header) {
  background: rgba(102, 126, 234, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 20px;
}

.question-card :deep(.el-card__body) {
  padding: 16px 20px;
  color: rgba(255, 255, 255, 0.9);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #a5b4fc;
  font-weight: 600;
  font-size: 16px;
}

.header-icon {
  font-size: 18px;
}

.question-text {
  font-size: 15px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.85);
}

.empty-slot {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.3);
  gap: 10px;
}

.waiting-icon {
  font-size: 20px;
}

.snatch-state {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

/* 平均分显示容器（用于结束阶段并排显示两个分数） */
.scores-container {
  display: flex;
  gap: 32px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 40px;
}

.scores-container .teacher-score-display {
  margin-top: 0;
}

/* 教师平均分显示样式 */
.teacher-score-display {
  margin-top: 40px;
  padding: 24px 48px;
  background: linear-gradient(135deg, rgba(103, 194, 58, 0.2) 0%, rgba(64, 158, 255, 0.2) 100%);
  border-radius: 16px;
  border: 1px solid rgba(103, 194, 58, 0.4);
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.teacher-score-display .score-label {
  font-size: 24px;
  color: rgba(255, 255, 255, 0.8);
}

.teacher-score-display .score-value {
  font-size: 56px;
  font-weight: bold;
  color: #67c23a;
  text-shadow: 0 0 20px rgba(103, 194, 58, 0.5);
}

.teacher-score-display .score-suffix {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.6);
}

/* 辩论赛样式 */
.debate-status-panel {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 40px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.contest-info {
  flex: 1;
}

.contest-topic {
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 20px 0;
  color: #fff;
  text-align: center;
}

.teams-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
}

.team {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.pro-team .team-label {
  color: #f56c6c;
}

.con-team .team-label {
  color: #409eff;
}

.team-label {
  font-size: 18px;
  font-weight: bold;
}

.team-name {
  font-size: 24px;
  font-weight: bold;
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
}

.vs-divider {
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

.stage-display {
  text-align: center;
}

.stage-label {
  display: block;
  font-size: 18px;
  opacity: 0.6;
  margin-bottom: 8px;
}

.stage-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
}

/* 辩论阶段颜色 */
.debate-stage-idle { color: #909399; }
.debate-stage-pre_voting { color: #e6a23c; }
.debate-stage-debate_in_progress { color: #409eff; }
.debate-stage-post_voting { color: #e6a23c; }
.debate-stage-judge_scoring { color: #67c23a; }
.debate-stage-results_sealed { color: #f56c6c; }
.debate-stage-results_revealed { color: #67c23a; }

/* 投票状态样式 */
.voting-state {
  display: flex;
  gap: 80px;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.qr-section {
  flex: 1;
  display: flex;
  justify-content: center;
}

.qr-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px;
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
}

.qr-icon {
  font-size: 120px;
  color: rgba(255, 255, 255, 0.6);
}

.qr-placeholder p {
  font-size: 24px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.voting-progress {
  flex: 1;
  text-align: center;
}

.voting-progress h3 {
  font-size: 36px;
  margin: 0 0 24px 0;
  color: #e6a23c;
}

.vote-count {
  margin-bottom: 20px;
}

.count-number {
  font-size: 72px;
  font-weight: bold;
  color: #67c23a;
  display: block;
}

.count-label {
  font-size: 24px;
  color: rgba(255, 255, 255, 0.8);
}

.progress-note p {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

/* 辩论进行中状态 */
.debate-progress-state {
  text-align: center;
}

.debate-progress-state .big-text {
  color: #409eff;
}

/* 评分状态 */
.scoring-state {
  text-align: center;
}

.scoring-progress {
  margin-top: 40px;
}

.progress-circle {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
}

.progress-number {
  font-size: 64px;
  font-weight: bold;
  color: #67c23a;
}

.progress-total {
  font-size: 32px;
  color: rgba(255, 255, 255, 0.8);
}

/* 结果封存状态 */
.sealed-state {
  text-align: center;
}

.loading-animation {
  margin-top: 40px;
}

.loading-icon {
  font-size: 64px;
  color: #409eff;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 结果揭晓样式 */
.results-state {
  text-align: center;
  width: 100%;
}

.results-title {
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 40px;
  color: #67c23a;
}

.results-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
  max-width: 1000px;
  margin: 0 auto;
}

.winner-section h3,
.vote-analysis h3,
.debater-rankings h3 {
  font-size: 28px;
  margin: 0 0 20px 0;
  color: rgba(255, 255, 255, 0.9);
}

.winner-display {
  padding: 20px 40px;
  border-radius: 16px;
  font-size: 36px;
  font-weight: bold;
  display: inline-block;
}

.winner-display.pro {
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.3), rgba(245, 108, 108, 0.1));
  border: 2px solid #f56c6c;
  color: #f56c6c;
}

.winner-display.con {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.3), rgba(64, 158, 255, 0.1));
  border: 2px solid #409eff;
  color: #409eff;
}

.winner-display:not(.pro):not(.con) {
  background: linear-gradient(135deg, rgba(144, 147, 153, 0.3), rgba(144, 147, 153, 0.1));
  border: 2px solid #909399;
  color: #909399;
}

.swing-votes {
  display: flex;
  justify-content: center;
  gap: 60px;
}

.swing-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
}

.swing-item .team {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.9);
}

.swing-value {
  font-size: 48px;
  font-weight: bold;
  color: #f56c6c;
}

.swing-value.positive {
  color: #67c23a;
}

.rankings-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  font-size: 18px;
}

.ranking-item.first {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.3), rgba(255, 215, 0, 0.1));
  border: 2px solid #ffd700;
}

.ranking-item.second {
  background: linear-gradient(135deg, rgba(192, 192, 192, 0.3), rgba(192, 192, 192, 0.1));
  border: 2px solid #c0c0c0;
}

.ranking-item.third {
  background: linear-gradient(135deg, rgba(205, 127, 50, 0.3), rgba(205, 127, 50, 0.1));
  border: 2px solid #cd7f32;
}

.ranking-item .rank {
  font-size: 24px;
  font-weight: bold;
  width: 40px;
  text-align: center;
}

.ranking-item .name {
  flex: 1;
  font-weight: 500;
}

.ranking-item .team-side {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: bold;
}

.ranking-item .team-side.pro {
  background: rgba(245, 108, 108, 0.3);
  color: #f56c6c;
}

.ranking-item .team-side.con {
  background: rgba(64, 158, 255, 0.3);
  color: #409eff;
}

.ranking-item .score {
  font-size: 20px;
  font-weight: bold;
  color: #67c23a;
}
.vote-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 15px;
  width: 100%;
}
.stat-box {
  background: rgba(255, 255, 255, 0.05);
  padding: 8px;
  border-radius: 8px;
  text-align: center;
}
.stat-box.highlight {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}
.stat-val {
  font-size: 18px;
  font-weight: bold;
  color: #fff;
}
.stat-val.positive { color: #f56c6c; }
.stat-val.negative { color: #67c23a; }

.team-topic {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 8px;
  max-width: 300px;
  line-height: 1.4;
  font-weight: normal;
}

.d-team-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.d-team-name-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

/* 二维码容器样式 */
.qr-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 30px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  border: 2px dashed rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
}

.qr-image {
  width: 250px;
  height: 250px;
  object-fit: contain;
  border-radius: 12px;
  background: white;
  padding: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.qr-text {
  font-size: 24px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  letter-spacing: 2px;
}

/* 进度条样式 */
.progress-bar-container {
  width: 100%;
  max-width: 600px;
  margin: 30px auto;
}

.progress-bar-bg {
  width: 100%;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #67c23a 0%, #85ce61 100%);
  border-radius: 20px;
  transition: width 0.5s ease;
  box-shadow: 0 0 15px rgba(103, 194, 58, 0.5);
  position: relative;
  overflow: hidden;
}

.progress-bar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  animation: shimmer 2s infinite;
}

.progress-bar-fill.scoring {
  background: linear-gradient(90deg, #409eff 0%, #79bbff 100%);
  box-shadow: 0 0 15px rgba(64, 158, 255, 0.5);
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-percentage {
  text-align: center;
  font-size: 32px;
  font-weight: bold;
  color: #fff;
  margin-top: 15px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}
</style>

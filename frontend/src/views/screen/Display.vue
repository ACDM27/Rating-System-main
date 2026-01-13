<template>
  <div class="screen-container">
    <!-- 左上角班级选择 -->
    <div class="class-selector">
      <el-select 
        v-model="currentClassId" 
        placeholder="选择班级" 
        size="large"
        @change="handleClassChange"
      >
        <el-option 
          v-for="cls in classes" 
          :key="cls.id" 
          :label="cls.name" 
          :value="cls.id"
        />
      </el-select>
    </div>
    
    <div v-if="!currentClassId" class="no-class">
      <h2>请选择班级</h2>
    </div>
    
    <template v-else>
      <!-- 头部信息 -->
      <div class="header">
        <div class="class-name">{{ currentClassName }}</div>
      </div>
      
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
              </div>
              <div class="vs-divider">VS</div>
              <div class="team con-team">
                <span class="team-label">反方</span>
                <span class="team-name">{{ contestInfo.con_team_name }}</span>
              </div>
            </div>
          </div>
          
          <div class="stage-display">
            <span class="stage-label">当前阶段</span>
            <span class="stage-value" :class="debateStageClass">{{ debateStageText }}</span>
          </div>
        </div>

        <!-- 主内容区域 - 辩论赛 -->
        <div class="main-content">
          <!-- 投票引导阶段 -->
          <div v-if="stage === 'PRE_VOTING' || stage === 'POST_VOTING'" class="voting-state">
            <div class="qr-section">
              <div class="qr-placeholder">
                <el-icon class="qr-icon"><QrCode /></el-icon>
                <p>扫码参与投票</p>
              </div>
            </div>
            
            <div class="voting-progress">
              <h3>{{ stage === 'PRE_VOTING' ? '赛前投票进行中' : '赛后投票进行中' }}</h3>
              <div class="vote-count">
                <span class="count-number">{{ totalVotes }}</span>
                <span class="count-label">人已投票</span>
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
            <div class="scoring-progress" v-if="debateProgress.judge_scoring_progress">
              <div class="progress-circle">
                <span class="progress-number">{{ debateProgress.judge_scoring_progress.submitted }}</span>
                <span class="progress-total">/ {{ debateProgress.judge_scoring_progress.total }}</span>
              </div>
              <p>评委已提交评分</p>
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
          <div v-else-if="stage === 'RESULTS_REVEALED'" class="results-state">
            <div class="results-title">比赛结果</div>
            
            <div v-if="contestResults" class="results-content">
              <!-- 获胜队伍 -->
              <div class="winner-section">
                <h3>获胜队伍</h3>
                <div class="winner-display" :class="contestResults.winning_team">
                  <span v-if="contestResults.winning_team === 'pro'" class="winner-name">
                    {{ contestInfo?.pro_team_name }} (正方)
                  </span>
                  <span v-else-if="contestResults.winning_team === 'con'" class="winner-name">
                    {{ contestInfo?.con_team_name }} (反方)
                  </span>
                  <span v-else class="winner-name">平局</span>
                </div>
              </div>

              <!-- 跑票统计 -->
              <div class="vote-analysis">
                <h3>跑票统计</h3>
                <div class="swing-votes">
                  <div class="swing-item pro">
                    <span class="team">{{ contestInfo?.pro_team_name }}</span>
                    <span class="swing-value" :class="{ positive: contestResults.pro_team_swing > 0 }">
                      {{ contestResults.pro_team_swing > 0 ? '+' : '' }}{{ contestResults.pro_team_swing }}
                    </span>
                  </div>
                  <div class="swing-item con">
                    <span class="team">{{ contestInfo?.con_team_name }}</span>
                    <span class="swing-value" :class="{ positive: contestResults.con_team_swing > 0 }">
                      {{ contestResults.con_team_swing > 0 ? '+' : '' }}{{ contestResults.con_team_swing }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 辞手排名 -->
              <div class="debater-rankings" v-if="contestResults.debater_rankings?.length > 0">
                <h3>辞手排名</h3>
                <div class="rankings-list">
                  <div 
                    v-for="(debater, index) in contestResults.debater_rankings.slice(0, 5)" 
                    :key="debater.debater_id"
                    class="ranking-item"
                    :class="{ first: index === 0, second: index === 1, third: index === 2 }"
                  >
                    <span class="rank">{{ debater.rank }}</span>
                    <span class="name">{{ debater.debater_name }}</span>
                    <span class="team-side" :class="debater.team_side">
                      {{ debater.team_side === 'pro' ? '正方' : '反方' }}
                    </span>
                    <span class="score">{{ debater.final_score }}</span>
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
import { QrCode, Loading } from '@element-plus/icons-vue'
import { getClasses } from '../../api/class'
import { getSystemState, getQuestions } from '../../api/admin'
import { getCurrentContest, getDebateResults } from '../../api/debate'

const route = useRoute()
const router = useRouter()

const classes = ref([])
const currentClassId = ref(null)
const currentClassName = ref('')
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
const isDebateMode = ref(false)
const contestInfo = ref(null)
const contestResults = ref(null)
const debateProgress = ref({})
const totalVotes = ref(0)

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
  await loadClasses()
  
  // 从 URL 参数获取 class_id
  const classIdFromUrl = route.query.class_id
  if (classIdFromUrl) {
    currentClassId.value = parseInt(classIdFromUrl)
    const cls = classes.value.find(c => c.id === currentClassId.value)
    if (cls) {
      currentClassName.value = cls.name
      await fetchState()
      await checkDebateMode()
      connectWebSocket()
    }
  }
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  stopElapsedTimer()
})

watch(currentClassId, (newVal) => {
  if (newVal) {
    router.replace({ query: { ...route.query, class_id: newVal } })
  }
})

// Removed watch for stage change and startCountdown

async function loadClasses() {
  try {
    const workspaceId = route.query.workspace_id || 1
    classes.value = await getClasses(workspaceId)
  } catch (error) {
    console.error('获取班级列表失败:', error)
  }
}

async function handleClassChange(classId) {
  const cls = classes.value.find(c => c.id === classId)
  if (cls) {
    currentClassName.value = cls.name
    
    if (ws) {
      ws.close()
    }
    
    await fetchState()
    await checkDebateMode()
    connectWebSocket()
  }
}

async function checkDebateMode() {
  try {
    const result = await getCurrentContest(currentClassId.value)
    if (result.contest) {
      isDebateMode.value = true
      contestInfo.value = result.contest
      
      // 如果结果已揭晓，获取比赛结果
      if (stage.value === 'RESULTS_REVEALED') {
        await loadContestResults()
      }
    } else {
      isDebateMode.value = false
      contestInfo.value = null
      contestResults.value = null
    }
  } catch (error) {
    console.error('检查辩论模式失败:', error)
    isDebateMode.value = false
  }
}

async function loadContestResults() {
  if (!contestInfo.value) return
  
  try {
    contestResults.value = await getDebateResults(contestInfo.value.id)
  } catch (error) {
    console.error('获取比赛结果失败:', error)
  }
}

async function fetchState() {
  try {
    const state = await getSystemState(currentClassId.value)
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
  if (!currentTeam.value) return
  try {
    const allQuestions = await getQuestions(currentClassId.value)
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

// 格式化已用时间（秒 -> 分:秒）
function formatElapsedTime(seconds) {
  if (seconds === null || seconds < 0) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function connectWebSocket() {
  const wsUrl = `ws://${window.location.hostname}:8000/ws?class_id=${currentClassId.value}`
  ws = new WebSocket(wsUrl)
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    handleMessage(message)
  }
  
  ws.onclose = () => {
    console.log('WebSocket 断开，5秒后重连...')
    setTimeout(() => {
      if (currentClassId.value) {
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
  switch (message.type) {
    case 'state_update':
      stage.value = message.data.stage
      currentTeam.value = message.data.current_team
      snatchRemaining.value = message.data.snatch_slots_remaining
      snatchStartTime.value = message.data.snatch_start_time || null
      countdown.value = message.data.countdown || 0
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
      if (message.data.results) {
        contestResults.value = message.data.results
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

.class-selector :deep(.el-select__caret),
.class-selector :deep(.el-select__suffix) {
  color: rgba(255, 255, 255, 0.7) !important;
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
  justify-content: space-between;
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
</style>

<template>
  <div class="mobile-container">
    <!-- 头部信息 -->
    <div class="header">
      <div class="contest-info">
        <h2 class="contest-title">{{ contestInfo?.topic || '辩论赛评分' }}</h2>
        <div class="teams">
          <div class="team-wrapper">
             <span class="team pro">{{ contestInfo?.pro_team_name || '正方' }}</span>
             <span class="sub-topic" v-if="contestInfo?.pro_topic">{{ contestInfo.pro_topic }}</span>
          </div>
          <span class="vs">VS</span>
          <div class="team-wrapper">
             <span class="team con">{{ contestInfo?.con_team_name || '反方' }}</span>
             <span class="sub-topic" v-if="contestInfo?.con_topic">{{ contestInfo.con_topic }}</span>
          </div>
        </div>
      </div>
      <div class="judge-info">
        <span class="judge-name">评委：{{ authStore.user?.display_name }}</span>
        <el-button size="small" type="danger" @click="handleLogout">退出</el-button>
      </div>
    </div>

    <!-- 状态提示 -->
    <div class="status-bar" v-if="!scoringEnabled">
      <el-alert 
        title="评分通道未开启，请等待管理员开启评委评分阶段" 
        type="warning" 
        :closable="false"
        show-icon
      />
    </div>

    <!-- 标签导航 -->
    <div class="tabs" v-if="scoringEnabled">
      <div 
        class="tab" 
        :class="{ active: activeTab === 'pro' }"
        @click="activeTab = 'pro'"
      >
        正方队伍
      </div>
      <div 
        class="tab" 
        :class="{ active: activeTab === 'con' }"
        @click="activeTab = 'con'"
      >
        反方队伍
      </div>
    </div>

    <!-- 辞手列表 -->
    <div class="debaters-container" v-if="scoringEnabled">
      <!-- 正方辞手 -->
      <div v-show="activeTab === 'pro'" class="debaters-list">
        <div 
          v-for="debater in proDebaters" 
          :key="debater.id"
          class="debater-card"
          :class="{ expanded: expandedDebater === debater.id }"
        >
          <div class="debater-header" @click="toggleDebater(debater.id)">
            <div class="debater-info">
              <span class="debater-name">{{ debater.display_name }}</span>
              <span class="debater-position">{{ getPositionText(debater.debater_position) }}</span>
            </div>
            <div class="score-status">
              <span v-if="getDebaterScore(debater.id)" class="scored">已评分</span>
              <span v-else class="not-scored">未评分</span>
              <i class="arrow" :class="{ rotated: expandedDebater === debater.id }">▼</i>
            </div>
          </div>
          
          <div v-show="expandedDebater === debater.id" class="scoring-form">
            <div class="score-dimensions">
              <div class="dimension">
                <label>语言表达 (0-20分)</label>
                <el-input-number
                  v-model="scores[debater.id].language_expression"
                  :min="0"
                  :max="20"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>逻辑推理 (0-20分)</label>
                <el-input-number
                  v-model="scores[debater.id].logical_reasoning"
                  :min="0"
                  :max="20"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>辩驳能力 (0-20分)</label>
                <el-input-number
                  v-model="scores[debater.id].debate_skills"
                  :min="0"
                  :max="20"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>临场反应 (0-15分)</label>
                <el-input-number
                  v-model="scores[debater.id].quick_response"
                  :min="0"
                  :max="15"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>整体意识 (0-15分)</label>
                <el-input-number
                  v-model="scores[debater.id].overall_awareness"
                  :min="0"
                  :max="15"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>综合印象 (0-10分)</label>
                <el-input-number
                  v-model="scores[debater.id].general_impression"
                  :min="0"
                  :max="10"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
            </div>
            
            <div class="total-score">
              <span>总分：{{ calculateTotal(debater.id) }} / 100</span>
            </div>
            
            <div class="form-actions">
              <el-button 
                type="primary" 
                size="large"
                :disabled="!isScoreComplete(debater.id) || getDebaterScore(debater.id)"
                @click="submitScore(debater.id)"
                :loading="submittingScore === debater.id"
              >
                {{ getDebaterScore(debater.id) ? '已提交' : '提交评分' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 反方辞手 -->
      <div v-show="activeTab === 'con'" class="debaters-list">
        <div 
          v-for="debater in conDebaters" 
          :key="debater.id"
          class="debater-card"
          :class="{ expanded: expandedDebater === debater.id }"
        >
          <div class="debater-header" @click="toggleDebater(debater.id)">
            <div class="debater-info">
              <span class="debater-name">{{ debater.display_name }}</span>
              <span class="debater-position">{{ getPositionText(debater.debater_position) }}</span>
            </div>
            <div class="score-status">
              <span v-if="getDebaterScore(debater.id)" class="scored">已评分</span>
              <span v-else class="not-scored">未评分</span>
              <i class="arrow" :class="{ rotated: expandedDebater === debater.id }">▼</i>
            </div>
          </div>
          
          <div v-show="expandedDebater === debater.id" class="scoring-form">
            <div class="score-dimensions">
              <div class="dimension">
                <label>语言表达 (0-20分)</label>
                <el-input-number
                  v-model="scores[debater.id].language_expression"
                  :min="0"
                  :max="20"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>逻辑推理 (0-20分)</label>
                <el-input-number
                  v-model="scores[debater.id].logical_reasoning"
                  :min="0"
                  :max="20"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>辩驳能力 (0-20分)</label>
                <el-input-number
                  v-model="scores[debater.id].debate_skills"
                  :min="0"
                  :max="20"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>临场反应 (0-15分)</label>
                <el-input-number
                  v-model="scores[debater.id].quick_response"
                  :min="0"
                  :max="15"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>整体意识 (0-15分)</label>
                <el-input-number
                  v-model="scores[debater.id].overall_awareness"
                  :min="0"
                  :max="15"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
              
              <div class="dimension">
                <label>综合印象 (0-10分)</label>
                <el-input-number
                  v-model="scores[debater.id].general_impression"
                  :min="0"
                  :max="10"
                  :step="0.5"
                  :precision="1"
                  size="large"
                  controls-position="right"
                />
              </div>
            </div>
            
            <div class="total-score">
              <span>总分：{{ calculateTotal(debater.id) }} / 100</span>
            </div>
            
            <div class="form-actions">
              <el-button 
                type="primary" 
                size="large"
                :disabled="!isScoreComplete(debater.id) || getDebaterScore(debater.id)"
                @click="submitScore(debater.id)"
                :loading="submittingScore === debater.id"
              >
                {{ getDebaterScore(debater.id) ? '已提交' : '提交评分' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部提交状态 -->
    <div class="bottom-status" v-if="scoringEnabled">
      <div class="completion-status">
        <span>评分进度：{{ completedScores }} / {{ totalDebaters }}</span>
        <el-progress 
          :percentage="completionPercentage" 
          :stroke-width="8"
          :show-text="false"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { useSystemStore } from '../../stores/system'
import { getCurrentContest } from '../../api/debate'
import { submitJudgeScore, getJudgeScores } from '../../api/judge_score'
import { getTeams } from '../../api/admin'

const router = useRouter()
const authStore = useAuthStore()
const systemStore = useSystemStore()

const activeTab = ref('pro')
const expandedDebater = ref(null)
const contestInfo = ref(null)
const allDebaters = ref([])
const submittedScores = ref([])
const submittingScore = ref(null)

// 评分数据
const scores = reactive({})

// 计算属性
const proDebaters = computed(() => 
  allDebaters.value.filter(d => d.team_side === 'pro')
)

const conDebaters = computed(() => 
  allDebaters.value.filter(d => d.team_side === 'con')
)

const totalDebaters = computed(() => allDebaters.value.length)

const completedScores = computed(() => 
  allDebaters.value.filter(d => getDebaterScore(d.id)).length
)

const completionPercentage = computed(() => 
  totalDebaters.value > 0 ? Math.round((completedScores.value / totalDebaters.value) * 100) : 0
)

const scoringEnabled = computed(() => {
  // 检查系统状态是否允许评委评分
  return systemStore.currentStage === 'JUDGE_SCORING' || 
         (systemStore.debateProgress && systemStore.debateProgress.voting_enabled?.judge_scoring)
})

onMounted(async () => {
  await loadContestInfo()
  await loadDebaters()
  await loadSubmittedScores()
  await systemStore.fetchState()
})

// 监听系统状态变化
watch(() => systemStore.currentStage, (newStage) => {
  if (newStage === 'RESULTS_REVEALED') {
    ElMessage.success('比赛结果已揭晓！')
  }
})

// 监听系统更新时间（用于同步比赛信息更迭）
watch(() => systemStore.updateTime, async () => {
  console.log('System state updated, reloading contest info...')
  await loadContestInfo()
  await loadDebaters()
  await loadSubmittedScores()
})

async function loadContestInfo() {
  try {
    const result = await getCurrentContest(authStore.currentClassId)
    contestInfo.value = result.contest
  } catch (error) {
    console.error('获取比赛信息失败:', error)
  }
}

async function loadDebaters() {
  try {
    const teams = await getTeams(authStore.currentClassId)
    // 筛选出有辞手角色的用户
    allDebaters.value = teams.filter(user => 
      user.team_side && user.debater_position
    )
    
    // 初始化评分数据
    allDebaters.value.forEach(debater => {
      scores[debater.id] = {
        language_expression: 0,
        logical_reasoning: 0,
        debate_skills: 0,
        quick_response: 0,
        overall_awareness: 0,
        general_impression: 0
      }
    })
  } catch (error) {
    console.error('获取辞手列表失败:', error)
    ElMessage.error('获取辞手列表失败')
  }
}

async function loadSubmittedScores() {
  try {
    if (contestInfo.value) {
      submittedScores.value = await getJudgeScores(contestInfo.value.id)
    }
  } catch (error) {
    console.error('获取已提交评分失败:', error)
  }
}

function toggleDebater(debaterId) {
  expandedDebater.value = expandedDebater.value === debaterId ? null : debaterId
}

function getPositionText(position) {
  const positions = {
    // 新格式
    first_debater: '一辩',
    second_debater: '二辩',
    third_debater: '三辩',
    fourth_debater: '四辩',
    // 旧格式（兼容）
    first_speaker: '一辩',
    second_speaker: '二辩',
    third_speaker: '三辩',
    fourth_speaker: '四辩'
  }
  return positions[position] || position
}

function calculateTotal(debaterId) {
  const score = scores[debaterId]
  if (!score) return 0
  
  return (
    (score.language_expression || 0) +
    (score.logical_reasoning || 0) +
    (score.debate_skills || 0) +
    (score.quick_response || 0) +
    (score.overall_awareness || 0) +
    (score.general_impression || 0)
  ).toFixed(1)
}

function isScoreComplete(debaterId) {
  const score = scores[debaterId]
  if (!score) return false
  
  return score.language_expression > 0 &&
         score.logical_reasoning > 0 &&
         score.debate_skills > 0 &&
         score.quick_response > 0 &&
         score.overall_awareness > 0 &&
         score.general_impression > 0
}

function getDebaterScore(debaterId) {
  return submittedScores.value.find(s => s.debater_id === debaterId)
}

async function submitScore(debaterId) {
  if (!isScoreComplete(debaterId)) {
    ElMessage.warning('请完成所有维度的评分')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定提交该辞手的评分吗？提交后将无法修改。',
      '确认提交',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    submittingScore.value = debaterId
    
    const scoreData = {
      contest_id: contestInfo.value.id,
      debater_id: debaterId,
      ...scores[debaterId]
    }
    
    await submitJudgeScore(scoreData)
    
    // 重新加载已提交的评分
    await loadSubmittedScores()
    
    ElMessage.success('评分提交成功')
    expandedDebater.value = null
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.detail || '提交评分失败')
    }
  } finally {
    submittingScore.value = null
  }
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
  background: #f5f5f5;
  padding-bottom: 80px;
}

.header {
  background: white;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.contest-info {
  margin-bottom: 12px;
}

.contest-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #333;
  text-align: center;
}

.teams {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.team {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
}

.team.pro {
  background: #fee;
  color: #c53030;
}

.team.con {
  background: #eff6ff;
  color: #2563eb;
}

.vs {
  font-weight: bold;
  color: #666;
}

.judge-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.judge-name {
  font-size: 14px;
  color: #666;
}

.status-bar {
  padding: 16px;
}

.tabs {
  display: flex;
  background: white;
  border-bottom: 1px solid #eee;
}

.tab {
  flex: 1;
  padding: 16px;
  text-align: center;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.tab.active {
  color: #409eff;
  border-bottom: 2px solid #409eff;
  background: #f8fbff;
}

.debaters-container {
  padding: 16px;
}

.debater-card {
  background: white;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s;
}

.debater-card.expanded {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.debater-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.debater-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.debater-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.debater-position {
  font-size: 12px;
  color: #666;
}

.score-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scored {
  color: #67c23a;
  font-size: 12px;
  font-weight: 500;
}

.not-scored {
  color: #e6a23c;
  font-size: 12px;
}

.arrow {
  font-size: 12px;
  color: #999;
  transition: transform 0.3s;
}

.arrow.rotated {
  transform: rotate(180deg);
}

.scoring-form {
  padding: 0 16px 16px;
  border-top: 1px solid #f0f0f0;
}

.score-dimensions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 16px 0;
}

.dimension {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dimension label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.total-score {
  text-align: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  margin: 16px 0;
}

.total-score span {
  font-size: 16px;
  font-weight: bold;
  color: #409eff;
}

.form-actions {
  display: flex;
  justify-content: center;
}

.bottom-status {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 16px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

.completion-status {
  text-align: center;
}

.completion-status span {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .dimension {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .dimension label {
    font-size: 13px;
  }
  
  :deep(.el-input-number) {
    width: 100%;
  }
  
  :deep(.el-input-number .el-input__inner) {
    text-align: center;
    font-size: 16px;
    height: 44px;
  }
}

.team-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sub-topic {
  font-size: 11px;
  color: rgba(255,255,255,0.7);
  margin-top: 2px;
  text-align: center;
  max-width: 140px;
  line-height: 1.2;
}
</style>
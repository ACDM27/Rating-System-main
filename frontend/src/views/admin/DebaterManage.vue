<template>
  <div class="page-container">
    <div class="header">
      <div class="header-left">
        <el-button @click="router.back()" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">辩手管理 ({{ currentClassName }})</h1>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showAddDialog = true">添加辩手</el-button>
      </div>
    </div>

    <!-- 比赛信息 -->
    <el-card v-if="contestInfo" class="contest-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>当前比赛</span>
        </div>
      </template>
      <div class="contest-info">
        <h3>{{ contestInfo.topic }}</h3>
        <div class="teams-info">
          <div class="team-badge pro">正方：{{ contestInfo.pro_team_name }}</div>
          <div class="team-badge con">反方：{{ contestInfo.con_team_name }}</div>
        </div>
      </div>
    </el-card>

    <!-- 正反方辩手列表 -->
    <div class="teams-grid">
      <!-- 正方 -->
      <el-card class="team-card pro-card">
        <template #header>
          <div class="team-header pro">
            <h2>正方辩手</h2>
            <span>{{ contestInfo?.pro_team_name }}</span>
          </div>
        </template>
        
        <el-table :data="proDebaters" stripe>
          <el-table-column prop="debater_position" label="位置" width="100">
            <template #default="scope">
              {{ getPositionName(scope.row.debater_position) }}
            </template>
          </el-table-column>
          <el-table-column prop="display_name" label="姓名" width="150" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-popconfirm title="确定移除此辩手吗？" @confirm="removeDebater(scope.row)">
                <template #reference>
                  <el-button type="danger" link size="small">移除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 反方 -->
      <el-card class="team-card con-card">
        <template #header>
          <div class="team-header con">
            <h2>反方辩手</h2>
            <span>{{ contestInfo?.con_team_name }}</span>
          </div>
        </template>
        
        <el-table :data="conDebaters" stripe>
          <el-table-column prop="debater_position" label="位置" width="100">
            <template #default="scope">
              {{ getPositionName(scope.row.debater_position) }}
            </template>
          </el-table-column>
          <el-table-column prop="display_name" label="姓名" width="150" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-popconfirm title="确定移除此辩手吗？" @confirm="removeDebater(scope.row)">
                <template #reference>
                  <el-button type="danger" link size="small">移除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 辩手分配对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      title="辩手分配" 
      width="900px"
    >
      <div class="assignment-container">
        <!-- 正方队伍 -->
        <div class="team-section">
          <h3 class="section-title">正方队伍 ({{ contestInfo?.pro_team_name }})</h3>
          <el-form label-width="60px">
            <el-form-item label="一辩：">
              <el-input v-model="assignmentForm.pro_first" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="二辩：">
              <el-input v-model="assignmentForm.pro_second" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="三辩：">
              <el-input v-model="assignmentForm.pro_third" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="四辩：">
              <el-input v-model="assignmentForm.pro_fourth" placeholder="请输入辩手姓名" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 反方队伍 -->
        <div class="team-section">
          <h3 class="section-title">反方队伍 ({{ contestInfo?.con_team_name }})</h3>
          <el-form label-width="60px">
            <el-form-item label="一辩：">
              <el-input v-model="assignmentForm.con_first" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="二辩：">
              <el-input v-model="assignmentForm.con_second" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="三辩：">
              <el-input v-model="assignmentForm.con_third" placeholder="请输入辩手姓名" />
            </el-form-item>
            <el-form-item label="四辩：">
              <el-input v-model="assignmentForm.con_fourth" placeholder="请输入辩手姓名" />
            </el-form-item>
          </el-form>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAssignment" :loading="saving">保存分配</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { getStudents, createStudent, updateUserDebateRole } from '../../api/admin'
import { getCurrentContest } from '../../api/debate'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const classId = computed(() => Number(route.query.class_id) || authStore.currentClassId)
const currentClassName = computed(() => {
  const cls = authStore.availableClasses.find(c => c.id === classId.value)
  return cls ? cls.name : '未知赛场'
})

const loading = ref(false)
const contestInfo = ref(null)
const allDebaters = ref([])
const showAddDialog = ref(false)
const saving = ref(false)

const assignmentForm = ref({
  pro_first: '',
  pro_second: '',
  pro_third: '',
  pro_fourth: '',
  con_first: '',
  con_second: '',
  con_third: '',
  con_fourth: ''
})

// 正方辩手
const proDebaters = computed(() => {
  return allDebaters.value
    .filter(d => d.team_side === 'pro')
    .sort((a, b) => getPositionOrder(a.debater_position) - getPositionOrder(b.debater_position))
})

// 反方辩手
const conDebaters = computed(() => {
  return allDebaters.value
    .filter(d => d.team_side === 'con')
    .sort((a, b) => getPositionOrder(a.debater_position) - getPositionOrder(b.debater_position))
})

onMounted(async () => {
  if (classId.value) {
    await loadContestInfo()
    await loadDebaters()
    loadCurrentAssignment()
  }
})

async function loadContestInfo() {
  try {
    const res = await getCurrentContest(classId.value)
    contestInfo.value = res.contest || res
  } catch (error) {
    console.error('获取比赛信息失败', error)
  }
}

async function loadDebaters() {
  loading.value = true
  try {
    // 获取所有学生，筛选出有辩手角色的
    const students = await getStudents(classId.value)
    allDebaters.value = students.filter(s => s.team_side && s.debater_position)
  } catch (error) {
    ElMessage.error('加载辩手列表失败')
  } finally {
    loading.value = false
  }
}

function loadCurrentAssignment() {
  // 将当前辩手信息填充到表单
  const positionMap = {
    'first_debater': 'first',
    'second_debater': 'second',
    'third_debater': 'third',
    'fourth_debater': 'fourth'
  }
  
  allDebaters.value.forEach(debater => {
    const posKey = positionMap[debater.debater_position]
    if (posKey && debater.team_side) {
      const formKey = `${debater.team_side}_${posKey}`
      assignmentForm.value[formKey] = debater.display_name
    }
  })
}

function getPositionName(position) {
  const names = {
    'first_debater': '一辩',
    'second_debater': '二辩',
    'third_debater': '三辩',
    'fourth_debater': '四辩'
  }
  return names[position] || position
}

function getPositionOrder(position) {
  const orders = {
    'first_debater': 1,
    'second_debater': 2,
    'third_debater': 3,
    'fourth_debater': 4
  }
  return orders[position] || 999
}

async function saveAssignment() {
  saving.value = true
  try {
    // 处理所有8个位置
    const positions = [
      { side: 'pro', pos: 'first_debater', name: assignmentForm.value.pro_first },
      { side: 'pro', pos: 'second_debater', name: assignmentForm.value.pro_second },
      { side: 'pro', pos: 'third_debater', name: assignmentForm.value.pro_third },
      { side: 'pro', pos: 'fourth_debater', name: assignmentForm.value.pro_fourth },
      { side: 'con', pos: 'first_debater', name: assignmentForm.value.con_first },
      { side: 'con', pos: 'second_debater', name: assignmentForm.value.con_second },
      { side: 'con', pos: 'third_debater', name: assignmentForm.value.con_third },
      { side: 'con', pos: 'fourth_debater', name: assignmentForm.value.con_fourth }
    ]
    
    for (const item of positions) {
      if (!item.name || !item.name.trim()) continue
      
      const name = item.name.trim()
      
      // 检查该位置是否已有辩手
      const existing = allDebaters.value.find(
        d => d.team_side === item.side && d.debater_position === item.pos
      )
      
      if (existing) {
        // 如果名字不同，更新
        if (existing.display_name !== name) {
          // 先清除旧辩手
          await updateUserDebateRole(existing.id, null, null)
          
          // 创建新辩手
          const newDebater = await createStudent({
            username: name,
            display_name: name,
            password: '123456',
            role: 'student',
            class_id: classId.value
          })
          
          await updateUserDebateRole(newDebater.id, item.side, item.pos)
        }
      } else {
        // 新增辩手
        const newDebater = await createStudent({
          username: name,
          display_name: name,
          password: '123456',
          role: 'student',
          class_id: classId.value
        })
        
        await updateUserDebateRole(newDebater.id, item.side, item.pos)
      }
    }
    
    ElMessage.success('保存成功')
    showAddDialog.value = false
    await loadDebaters()
    loadCurrentAssignment()
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.detail || error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

async function removeDebater(debater) {
  try {
    // 移除辩手角色（设为null）
    await updateUserDebateRole(debater.id, null, null)
    ElMessage.success('移除成功')
    await loadDebaters()
    loadCurrentAssignment()
  } catch (error) {
    ElMessage.error('移除失败')
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.contest-card {
  margin-bottom: 24px;
}

.contest-info h3 {
  margin: 0 0 16px 0;
  font-size: 20px;
  color: #303133;
}

.teams-info {
  display: flex;
  gap: 16px;
}

.team-badge {
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  color: white;
}

.team-badge.pro {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.team-badge.con {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.teams-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.team-card {
  min-height: 400px;
}

.team-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.team-header h2 {
  margin: 0;
  font-size: 18px;
}

.team-header span {
  font-size: 14px;
  opacity: 0.8;
}

.team-header.pro {
  color: #f5576c;
}

.team-header.con {
  color: #00f2fe;
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
  .teams-grid {
    grid-template-columns: 1fr;
  }
  
  .assignment-container {
    grid-template-columns: 1fr;
    gap: 24px;
  }
}
</style>

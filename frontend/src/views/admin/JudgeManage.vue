<template>
  <div class="page-container">
    <div class="header">
      <div class="header-left">
        <el-button @click="router.back()" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">评委管理 ({{ currentClassName }})</h1>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">添加评委</el-button>
        <el-button type="primary" plain @click="triggerFileInput">导入Excel</el-button>
        <el-button link type="primary" @click="downloadTemplate">下载模板</el-button>
        <el-button @click="showScoringCriteria = true">评分标准</el-button>
        <input 
          type="file" 
          ref="fileInput" 
          style="display: none" 
          accept=".xlsx, .xls"
          @change="handleFileChange"
        />
      </div>
    </div>

    <!-- 评委列表 -->
    <div class="card">
      <el-table :data="judges" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="180" />
        <el-table-column prop="display_name" label="显示名称" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-popconfirm title="确定要移除这个评委吗？" @confirm="handleRemove(scope.row)">
              <template #reference>
                <el-button type="danger" link size="small">移除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加评委对话框 -->
    <el-dialog v-model="showCreateDialog" title="添加评委" width="500px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="createForm.password" show-password placeholder="默认: 123456" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="saving">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 评分标准对话框 -->
    <el-dialog v-model="showScoringCriteria" title="评委评分标准" width="700px">
      <el-table :data="scoringCriteria" stripe border>
        <el-table-column prop="dimension" label="评分维度" width="200" />
        <el-table-column prop="maxScore" label="满分" width="100" align="center" />
        <el-table-column prop="description" label="评分说明" />
      </el-table>
      
      <template #footer>
        <div class="dialog-footer">
          <p style="color: #606266; font-size: 14px; margin: 10px 0;">
            <strong>总分：100分</strong> | 评委需对每位辩手按以上六个维度独立评分
          </p>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { getTeachers, createTeacher, removeTeacherFromClass, importTeachers } from '../../api/admin'
import * as XLSX from 'xlsx'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const classId = computed(() => Number(route.query.class_id) || authStore.currentClassId)
const currentClassName = computed(() => {
    const cls = authStore.availableClasses.find(c => c.id === classId.value)
    return cls ? cls.name : '未知赛场'
})

const loading = ref(false)
const judges = ref([])
const showCreateDialog = ref(false)
const showScoringCriteria = ref(false)
const saving = ref(false)
const fileInput = ref(null)

const createForm = ref({
  username: '',
  password: ''
})

const createRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }]
}

const createFormRef = ref(null)

// 评分标准数据
const scoringCriteria = [
  { dimension: '语言表达', maxScore: 20, description: '吐字清晰、语速适中、表达流畅' },
  { dimension: '逻辑推理', maxScore: 20, description: '论证严密、逻辑清晰、推理合理' },
  { dimension: '辩论技巧', maxScore: 20, description: '攻防有度、引用恰当、策略运用' },
  { dimension: '应变能力', maxScore: 15, description: '快速反应、灵活应对、临场发挥' },
  { dimension: '整体意识', maxScore: 15, description: '团队配合、大局观念、战略布局' },
  { dimension: '综合印象', maxScore: 10, description: '仪表风度、气场感染力、整体表现' }
]

onMounted(() => {
  if (classId.value) {
    loadJudges()
  }
})

async function loadJudges() {
  loading.value = true
  try {
    judges.value = await getTeachers(classId.value)
  } catch (error) {
    ElMessage.error('加载评委列表失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    if (!createFormRef.value) return
    await createFormRef.value.validate()
    
    await createTeacher({
      username: createForm.value.username,
      password: createForm.value.password || '123456',
      display_name: createForm.value.username, // 自动设置显示名称为用户名
      role: 'judge', // 设置角色为评委
      class_id: classId.value
    })
    ElMessage.success('创建并添加成功')
    showCreateDialog.value = false
    loadJudges()
    
    // 重置表单
    createForm.value = {
      username: '',
      password: ''
    }
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.detail || '未知错误'))
  } finally {
    saving.value = false
  }
}

async function handleRemove(user) {
  try {
    await removeTeacherFromClass(classId.value, user.id)
    ElMessage.success('移除成功')
    loadJudges()
  } catch (error) {
    ElMessage.error('移除失败')
  }
}

// 触发文件选择
function triggerFileInput() {
  fileInput.value.click()
}

// 下载Excel导入模板
function downloadTemplate() {
  const template = [
    ['用户名', '密码'],
    ['judge001', '123456'],
    ['judge002', '123456'],
  ]
  
  const ws = XLSX.utils.aoa_to_sheet(template)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '评委导入模板')
  XLSX.writeFile(wb, '评委导入模板.xlsx')
  ElMessage.success('模板下载成功')
}

// 处理Excel文件选择
async function handleFileChange(event) {
  const file = event.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const sheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[sheetName]
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      
      // 跳过表头
      const judges = jsonData.slice(1)
        .filter(row => row[0]) // 确保用户名存在
        .map(row => ({
          username: row[0],
          display_name: row[0], // 自动设置显示名称为用户名
          password: row[1] || '123456',
          role: 'judge', // 设置角色为评委
          class_id: classId.value
        }))
      
      if (judges.length === 0) {
        ElMessage.warning('Excel文件中没有有效数据')
        return
      }
      
      await ElMessageBox.confirm(
        `将导入 ${judges.length} 个评委账号，是否继续？`,
        '确认导入',
        { type: 'warning' }
      )
      
      const loadingMsg = ElMessage.loading('正在导入...')
      await importTeachers({ judges })
      loadingMsg.close()
      
      ElMessage.success(`成功导入 ${judges.length} 个评委账号`)
      loadJudges()
      
    } catch (error) {
      ElMessage.error('导入失败: ' + (error.message || '未知错误'))
    } finally {
      // 清空 input 允许重复选择同一文件
      event.target.value = ''
    }
  }
  reader.readAsArrayBuffer(file)
}

</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1200px;
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

.header-actions {
  display: flex;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
</style>

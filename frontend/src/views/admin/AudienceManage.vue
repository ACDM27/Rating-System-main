<template>
  <div class="page-container">
    <div class="header">
      <div class="header-left">
        <el-button @click="router.back()" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">观众管理 ({{ currentClassName }})</h1>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">添加观众</el-button>
        <el-button type="primary" plain @click="triggerFileInput">导入Excel</el-button>
        <el-button link type="primary" @click="downloadTemplate">下载模板</el-button>
        <!-- 移除批量生成按钮 -->
        <el-button type="info" @click="handleExport">导出账号</el-button>
        <input 
          type="file" 
          ref="fileInput" 
          style="display: none" 
          accept=".xlsx, .xls"
          @change="handleFileChange"
        />
      </div>
    </div>

    <!-- 观众列表 -->
    <div class="card">
      <el-table :data="audiences" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="180" />
        <!-- 显示名称如果和用户名一样，其实可以隐藏，但留着也没事 -->
        <el-table-column prop="display_name" label="显示名称" width="180" />
        <el-table-column label="状态" width="120">
          <template #default="scope">
            <el-tag type="success">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-popconfirm title="确定要删除这个观众吗？" @confirm="handleDelete(scope.row)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 单个/导入预览对话框 -->
    <el-dialog v-model="showCreateDialog" title="添加观众" width="500px">
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <!-- 移除显示名称输入 -->
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" show-password placeholder="默认: 123456" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreate" :loading="creating">添加</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 导入预览对话框 -->
    <el-dialog v-model="showImportDialog" title="确认导入数据" width="700px">
      <p>解析到 {{ parsedUsers.length }} 条数据，请确认：</p>
      <el-table :data="parsedUsers.slice(0, 10)" style="width: 100%; margin-bottom: 20px" border size="small">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="display_name" label="显示名称(自动生成)" /> <!-- 提示用户 -->
        <el-table-column prop="password" label="密码" />
      </el-table>
      <div v-if="parsedUsers.length > 10" style="text-align: center; color: #909399; margin-bottom: 20px">
        ... 共 {{ parsedUsers.length }} 条记录 ...
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showImportDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmImport" :loading="importing">确认导入</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { getStudents, deleteUser, createStudent, importStudents } from '../../api/admin'
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
const audiences = ref([])
const creating = ref(false)
const importing = ref(false)

// 单个创建相关
const showCreateDialog = ref(false)
const createFormRef = ref(null)
const createForm = reactive({
  username: '',
  password: ''
})
const createRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }]
}

// 导入相关
const fileInput = ref(null)
const showImportDialog = ref(false)
const parsedUsers = ref([])

onMounted(() => {
  if (classId.value) {
    loadAudiences()
  }
})

async function loadAudiences() {
  loading.value = true
  try {
    audiences.value = await getStudents(classId.value)
  } catch (error) {
    ElMessage.error('加载观众列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
    if (!createFormRef.value) return;
    await createFormRef.value.validate()
    
    creating.value = true
    try {
        await createStudent({
            username: createForm.username,
            password: createForm.password || '123456',
            display_name: createForm.username, // 默认显示名称同用户名
            role: 'audience',
            class_id: classId.value
        })
        ElMessage.success('添加成功')
        showCreateDialog.value = false
        // 重置表单
        createForm.username = ''
        createForm.password = ''
        loadAudiences()
    } catch (error) {
        ElMessage.error(error.detail || '添加失败')
    } finally {
        creating.value = false
    }
}

function triggerFileInput() {
    fileInput.value.click()
}

function handleFileChange(event) {
    const file = event.target.files[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (e) => {
        try {
            const data = new Uint8Array(e.target.result)
            const workbook = XLSX.read(data, { type: 'array' })
            const firstSheetName = workbook.SheetNames[0]
            const worksheet = workbook.Sheets[firstSheetName]
            const results = XLSX.utils.sheet_to_json(worksheet)
            
            if (results.length === 0) {
                ElMessage.warning('表格为空')
                return
            }
            
            // 解析数据，映射表头
            parsedUsers.value = results.map(row => {
                // 尝试多种可能的表头 keys
                const username = row['用户名'] || row['username'] || row['账号']
                const password = row['密码'] || row['password'] || '123456'
                // 显示名称自动生成，不再读取
                const display_name = String(username || '').trim()
                
                return {
                    username: String(username || '').trim(),
                    password: String(password || '').trim(),
                    display_name: display_name,
                    role: 'audience',
                    class_id: classId.value
                }
            }).filter(u => u.username) // 过滤无用户名的行
            
            if (parsedUsers.value.length > 0) {
                showImportDialog.value = true
            } else {
                ElMessage.warning('未识别到有效的用户数据，请检查表头是否包含"用户名"')
            }
            
        } catch (error) {
            console.error(error)
            ElMessage.error('解析Excel失败')
        } finally {
             // 清空 input 允许重复选择同一文件
             event.target.value = ''
        }
    }
    reader.readAsArrayBuffer(file)
}

async function confirmImport() {
    importing.value = true
    try {
        const result = await importStudents({
            class_id: classId.value,
            users: parsedUsers.value
        })
        
        if (result.errors && result.errors.length > 0) {
            ElMessage.warning({
                message: `导入部分成功：${result.message}。有 ${result.errors.length} 个失败`,
                duration: 5000
            })
        } else {
            ElMessage.success(result.message)
        }
        
        showImportDialog.value = false
        loadAudiences()
    } catch (error) {
        ElMessage.error(error.detail || '导入失败')
    } finally {
        importing.value = false
    }
}

async function handleDelete(user) {
  try {
    await deleteUser(user.id)
    ElMessage.success('删除成功')
    loadAudiences()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

function handleExport() {
  const header = '用户名,密码\n'
  const content = audiences.value.map(u => `${u.username},123456`).join('\n')
  // 添加 BOM 防止 Excel 中文乱码
  const bom = '\uFEFF'
  const blob = new Blob([bom + header + content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `观众账号_${currentClassName.value}.csv`
  link.click()
}

function downloadTemplate() {
    // 创建示例数据 - 移除显示名称列
    const data = [
        ['用户名', '密码'],
        ['audience001', '123456'],
        ['audience002', '123456']
    ]
    
    // 创建工作簿
    const ws = XLSX.utils.aoa_to_sheet(data)
    
    // 设置列宽
    ws['!cols'] = [
        { wch: 15 }, // 用户名
        { wch: 15 }  // 密码
    ]
    
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, "观众导入模板")
    
    // 导出文件
    XLSX.writeFile(wb, "观众导入模板.xlsx")
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

.hint {
    color: #909399;
    font-size: 13px;
    margin-left: 100px;
}
</style>

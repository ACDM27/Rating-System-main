import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSystemState } from '../api/admin'
import { getDebateProgress } from '../api/debate'
import { useAuthStore } from './auth'

export const useSystemStore = defineStore('system', () => {
    const currentStage = ref('IDLE')
    const currentTeam = ref(null)
    const snatchSlotsRemaining = ref(3)
    const snatchStartTime = ref(null)
    const countdown = ref(0)
    const scoreProgress = ref({ submitted: 0, total: 0 })
    const debateProgress = ref(null) // 辩论进度信息

    let ws = null
    let pingInterval = null
    // 标志位：是否正在连接中 / 是否手动断开
    let isConnecting = false
    let isManualDisconnect = false

    async function fetchState() {
        const authStore = useAuthStore()
        const classId = authStore.currentClassId

        if (!classId) {
            console.warn('未选择班级，无法获取系统状态')
            return
        }

        try {
            const state = await getSystemState(classId)
            currentStage.value = state.current_stage
            currentTeam.value = state.current_team_id ? {
                id: state.current_team_id,
                name: state.current_team_name,
                topic: state.current_team_topic
            } : null
            snatchSlotsRemaining.value = state.snatch_slots_remaining
            snatchStartTime.value = state.snatch_start_time || null

            // 设置倒计时（如果 API 返回了当前值）
            if (state.countdown !== null && state.countdown !== undefined) {
                countdown.value = state.countdown
            } else if (currentStage.value !== 'QNA_SNATCH') {
                countdown.value = 0
            }
        } catch (error) {
            console.error('获取系统状态失败:', error)
        }
    }

    async function fetchDebateProgress() {
        const authStore = useAuthStore()
        const classId = authStore.currentClassId

        console.log('[fetchDebateProgress] 开始获取辩论进度, classId:', classId)

        if (!classId) {
            console.warn('未选择班级，无法获取辩论进度')
            return
        }

        try {
            console.log('[fetchDebateProgress] 调用 API...')
            // 使用静态导入的函数
            const progress = await getDebateProgress(classId)
            console.log('[fetchDebateProgress] API 返回数据:', progress)

            // 确保 progress 是有效对象
            if (progress && typeof progress === 'object') {
                debateProgress.value = progress
                console.log('[fetchDebateProgress] debateProgress 已更新:', debateProgress.value)
            } else {
                throw new Error('API 返回数据格式无效')
            }
        } catch (error) {
            console.error('获取辩论进度失败 - 详细错误:', error)
            // 设置一个错误标记，方便前端显示
            debateProgress.value = { error: error.message || '未知错误' }
        }
    }

    function connectWebSocket() {
        const authStore = useAuthStore()
        const classId = authStore.currentClassId

        // 防止重复连接
        if (isConnecting) {
            return
        }

        // 如果没有选择班级，不进行连接
        if (!classId) {
            console.log('未选择班级，暂不连接 WebSocket')
            return
        }

        // 构建 WebSocket URL，带 class_id 参数
        // 修正：使用 location.host 包含端口，如果需要在开发环境使用特定端口需注意
        // 假设 socket 端口也是 8000 (根据之前的信息 python -m uvicorn ... --port 8000)
        // 如果前端是 5173，后端是 8000，则需要写死或配置
        // 之前代码是 `ws://${window.location.hostname}:8000/ws`，保持一致
        let wsUrl = `ws://${window.location.hostname}:8000/ws`
        if (classId) {
            wsUrl += `?class_id=${classId}`
        }

        // 如果已有连接，先关闭（标记为手动断开，防止触发自动重连）
        if (ws) {
            isManualDisconnect = true
            ws.close()
        }

        // 清除旧的 ping 定时器
        if (pingInterval) {
            clearInterval(pingInterval)
            pingInterval = null
        }

        isConnecting = true
        isManualDisconnect = false
        ws = new WebSocket(wsUrl)

        ws.onopen = () => {
            console.log('WebSocket 连接成功')
            isConnecting = false

            // 启动 ping 心跳
            pingInterval = setInterval(() => {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send('ping')
                }
            }, 5000)
        }

        ws.onmessage = (event) => {
            // 忽略 pong 响应
            if (event.data === 'pong') {
                return
            }
            try {
                const message = JSON.parse(event.data)
                // 忽略 pong 类型消息
                if (message.type === 'pong') {
                    return
                }
                handleMessage(message)
            } catch (e) {
                // 忽略非 JSON 消息
            }
        }

        ws.onclose = () => {
            isConnecting = false
            // 停止 ping
            if (pingInterval) {
                clearInterval(pingInterval)
                pingInterval = null
            }
            // 只有非手动断开时才自动重连
            if (!isManualDisconnect) {
                console.log('WebSocket 连接关闭，5秒后重连...')
                setTimeout(connectWebSocket, 5000)
            } else {
                console.log('WebSocket 连接已手动关闭')
            }
        }

        ws.onerror = (error) => {
            console.error('WebSocket 错误:', error)
            isConnecting = false
        }
    }

    function handleMessage(message) {
        console.log('WebSocket 收到消息:', message)

        switch (message.type) {
            case 'STATE_UPDATE':
            case 'state_update':
                console.log('处理状态更新:', message.data)
                // 支持两种字段名：stage 和 current_stage
                currentStage.value = message.data.current_stage || message.data.stage
                currentTeam.value = message.data.current_team
                snatchSlotsRemaining.value = message.data.snatch_slots_remaining
                snatchStartTime.value = message.data.snatch_start_time || null
                // 如果切换出提问阶段，倒计时归零
                if (currentStage.value !== 'QNA_SNATCH') {
                    countdown.value = 0
                }
                console.log('状态已更新, currentStage:', currentStage.value)
                break
            case 'debate_update':
                console.log('处理辩论状态更新:', message.data)
                currentStage.value = message.data.stage
                // 直接更新辩论进度，避免额外 API 请求
                if (message.data.progress) {
                    debateProgress.value = message.data.progress
                }
                console.log('辩论状态已更新, currentStage:', currentStage.value)
                break
            case 'SCORE_PROGRESS':
                scoreProgress.value = {
                    submitted: message.data.submitted_count,
                    total: message.data.total_count
                }
                break
            case 'SNATCH_UPDATE':
                snatchSlotsRemaining.value = message.data.slots_remaining
                break
            case 'TIMER_UPDATE':
                // 收到后端实时倒计时更新
                countdown.value = message.data.countdown
                break
            case 'NEW_QUESTION':
                // 触发自定义事件，让组件处理
                window.dispatchEvent(new CustomEvent('new-question', { detail: message.data }))
                break
        }
    }

    function disconnect() {
        // 清除 ping 定时器
        if (pingInterval) {
            clearInterval(pingInterval)
            pingInterval = null
        }
        if (ws) {
            isManualDisconnect = true
            ws.close()
            ws = null
        }
    }

    function reconnect() {
        disconnect()
        connectWebSocket()
    }

    return {
        currentStage,
        currentTeam,
        snatchSlotsRemaining,
        snatchStartTime,
        countdown,
        scoreProgress,
        debateProgress,
        fetchState,
        fetchDebateProgress,
        connectWebSocket,
        disconnect,
        reconnect
    }
})

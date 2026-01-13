import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSystemState } from '../api/admin'
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

    // 标志位：是否正在连接中 / 是否手动断开
    let isConnecting = false
    let isManualDisconnect = false
    let pingInterval = null

    function connectWebSocket() {
        const authStore = useAuthStore()
        const classId = authStore.currentClassId

        // 防止重复连接
        if (isConnecting) {
            return
        }

        // 构建 WebSocket URL，带 class_id 参数
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
        switch (message.type) {
            case 'state_update':
                currentStage.value = message.data.stage
                currentTeam.value = message.data.current_team
                snatchSlotsRemaining.value = message.data.snatch_slots_remaining
                snatchStartTime.value = message.data.snatch_start_time || null
                // 如果切换出提问阶段，倒计时归零
                if (currentStage.value !== 'QNA_SNATCH') {
                    countdown.value = 0
                }
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

    async function fetchDebateProgress() {
        const authStore = useAuthStore()
        const classId = authStore.currentClassId

        if (!classId) {
            console.warn('未选择班级，无法获取辩论进度')
            return
        }

        try {
            const { getDebateProgress } = await import('../api/debate')
            const progress = await getDebateProgress(classId)
            debateProgress.value = progress
        } catch (error) {
            console.error('获取辩论进度失败:', error)
        }
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

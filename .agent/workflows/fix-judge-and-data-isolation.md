---
description: 修复评委端问题并实现场次数据隔离
---

## 问题分析

### 1. 评委端422错误
- **原因**: API调用参数不匹配
- 前端调用: `getJudgeScores(contestInfo.value.id, authStore.user.id)` (2个参数)
- API定义: `getJudgeScores(contestId)` (1个参数)

### 2. 场次数据隔离问题
- 当前架构已经通过 `class_id` 实现了基本的场次隔离
- 但需要确保所有数据查询都正确使用 `class_id` 过滤

### 3. 控制台实时查看投票记录
- 需要WebSocket推送投票更新
- 需要增强控制台的投票记录显示

### 4. 大屏实时展示投票和评分进度
- 已有基础实现，需要增强实时性
- WebSocket消息需要包含详细进度信息

## 解决方案

### 步骤1: 修复评委端API调用
修改 `frontend/src/views/judge/Scoring.vue` 第418行

### 步骤2: 优化后端API，确保场次隔离
检查所有query都包含 `class_id` 或 `contest_id` 过滤

### 步骤3: 增强WebSocket实时推送
- 投票时广播投票进度
- 评分时广播评分进度

### 步骤4: 改进控制台投票记录显示
- 添加实时刷新按钮
- WebSocket自动更新投票记录

### 步骤5: 改进大屏实时显示
- 显示当前投票总数
- 显示评分进度百分比

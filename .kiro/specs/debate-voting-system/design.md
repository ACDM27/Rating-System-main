# 设计文档

## 概述

本设计将现有的AI课程答辩评分系统转换为综合性的辩论赛投票系统。转换过程保持当前的Vue 3 + FastAPI + PostgreSQL架构，同时调整数据模型、业务逻辑和用户界面，以支持带有评委打分、观众投票和跑票计算的辩论比赛。

## 架构

系统保持现有的B/S（浏览器/服务器）架构，包含以下组件：

### 后端架构
- **框架**: FastAPI with Python 3.8+
- **数据库**: PostgreSQL with SQLAlchemy ORM
- **实时通信**: WebSocket用于状态同步
- **身份验证**: 基于JWT的会话管理
- **迁移**: Alembic用于数据库模式管理

### 前端架构
- **框架**: Vue 3 with Composition API
- **构建工具**: Vite用于开发和打包
- **UI库**: Element Plus用于桌面端，自定义移动端组件
- **状态管理**: Pinia用于应用状态
- **HTTP客户端**: Axios用于API通信
- **路由**: Vue Router用于SPA导航

### 移动端优化
- **响应式设计**: CSS Grid和Flexbox，移动优先方法
- **触摸优化**: 大触摸目标（最小60px高度）
- **视口配置**: 适当的meta标签防止缩放
- **输入优化**: 数字输入类型触发数字键盘

## 组件和接口

### 角色转换映射

| 当前角色 | 新角色 | 界面变更 |
|----------|--------|----------|
| Admin | Admin | 流程控制的最小变更 |
| Teacher | Judge | 评分界面适配辩论标准 |
| Student | Audience | 投票界面替换评分 |
| Screen | Display_Screen | 显示投票进度而非问答 |

### 核心组件

#### 1. 管理员仪表板
- **目的**: 辩论流程管理的中央控制
- **主要功能**: 
  - 比赛配置（辩题、队伍、参与者）
  - 互斥流程控制（赛前投票、赛后投票、评委打分）
  - 实时监控与票数统计（仅管理员可见）
  - 结果揭晓控制
- **UI变更**: 将团队选择替换为正反方队伍配置

#### 2. 评委界面（移动端优化）
- **目的**: 个人辩手六维度评分
- **主要功能**:
  - 标签式导航（正方队伍/反方队伍）
  - 手风琴式辩手卡片避免横向滚动
  - 六个评分维度与范围验证
  - 提交前确认对话框
- **UI变更**: 将教师评分表单转换为辩论专用标准

#### 3. 观众界面（移动端优化）
- **目的**: 简单的队伍投票用于赛前/赛后阶段
- **主要功能**:
  - 分屏设计（正方红色/反方蓝色）
  - 大触摸友好投票按钮
  - 双投票系统（赛前和赛后）
  - 加载状态和确认反馈
- **UI变更**: 完全替换学生界面

#### 4. 展示屏幕
- **目的**: 带悬念管理的公共显示
- **主要功能**:
  - 二维码显示供观众访问
  - 投票计数显示但不显示分布详情
  - 动画结果揭晓
  - 实时进度更新
- **UI变更**: 将问答墙替换为投票进度

### 数据模型转换

#### 用户模型扩展
```python
class UserRole(str, enum.Enum):
    admin = "admin"
    judge = "judge"      # 从teacher重命名
    audience = "audience" # 从student重命名
    
class User(Base):
    # 保持现有字段
    id: Mapped[int]
    username: Mapped[str]
    password_hash: Mapped[str]
    role: Mapped[UserRole]
    display_name: Mapped[str]
    
    # 新的辩论专用字段
    debater_position: Mapped[str | None]  # "first_speaker", "second_speaker", 等
    team_side: Mapped[str | None]         # "pro" 或 "con"
```

#### 比赛配置模型
```python
class Contest(Base):
    __tablename__ = "contests"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    pro_team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    con_team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

#### 投票记录模型
```python
class VoteRecord(Base):
    __tablename__ = "vote_records"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"))
    voter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    team_side: Mapped[str] = mapped_column(String(10))  # "pro" 或 "con"
    vote_phase: Mapped[str] = mapped_column(String(20))  # "pre_debate" 或 "post_debate"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

#### 评委评分模型（从ScoreRecord适配）
```python
class JudgeScore(Base):
    __tablename__ = "judge_scores"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"))
    judge_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    debater_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # 六个评分维度
    language_expression: Mapped[float] = mapped_column(Float)      # /20
    logical_reasoning: Mapped[float] = mapped_column(Float)        # /20
    debate_skills: Mapped[float] = mapped_column(Float)           # /20
    quick_response: Mapped[float] = mapped_column(Float)          # /15
    overall_awareness: Mapped[float] = mapped_column(Float)       # /15
    general_impression: Mapped[float] = mapped_column(Float)      # /10
    
    total_score: Mapped[float] = mapped_column(Float)             # /100
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

#### 系统状态模型（适配）
```python
class SystemStage(str, enum.Enum):
    IDLE = "IDLE"
    PRE_VOTING = "PRE_VOTING"
    DEBATE_IN_PROGRESS = "DEBATE_IN_PROGRESS"
    POST_VOTING = "POST_VOTING"
    JUDGE_SCORING = "JUDGE_SCORING"
    RESULTS_SEALED = "RESULTS_SEALED"
    RESULTS_REVEALED = "RESULTS_REVEALED"

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"))
    current_stage: Mapped[SystemStage] = mapped_column(Enum(SystemStage))
    pre_voting_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    post_voting_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    judge_scoring_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    results_revealed: Mapped[bool] = mapped_column(Boolean, default=False)
    update_time: Mapped[int] = mapped_column(BigInteger, default=get_current_timestamp_ms)
```

## 数据模型

### 评分计算模型

#### 个人辩手排名
```python
class DebaterRanking:
    debater_id: int
    debater_name: str
    team_side: str
    final_score: float  # 所有评委评分的平均值（保留2位小数）
    logical_reasoning_avg: float  # 第一个平分决胜标准
    debate_skills_avg: float      # 第二个平分决胜标准
    rank: int
```

#### 队伍投票分析
```python
class TeamVoteResult:
    team_side: str
    team_name: str
    pre_debate_votes: int
    post_debate_votes: int
    swing_vote: int  # post - pre
    vote_percentage_change: float
```

#### 比赛结果
```python
class ContestResult:
    contest_id: int
    winning_team: str  # "pro", "con", 或 "tie"
    pro_team_swing: int
    con_team_swing: int
    total_votes_cast: int
    debater_rankings: List[DebaterRanking]
    vote_analysis: List[TeamVoteResult]
```

### API接口模型

#### 投票提交
```python
class VoteSubmission(BaseModel):
    contest_id: int
    team_side: str  # "pro" 或 "con"
    vote_phase: str  # "pre_debate" 或 "post_debate"
```

#### 评委评分提交
```python
class JudgeScoreSubmission(BaseModel):
    contest_id: int
    debater_id: int
    language_expression: float
    logical_reasoning: float
    debate_skills: float
    quick_response: float
    overall_awareness: float
    general_impression: float
```

#### 比赛配置
```python
class ContestConfig(BaseModel):
    topic: str
    pro_team_name: str
    con_team_name: str
    pro_debaters: List[DebaterInfo]
    con_debaters: List[DebaterInfo]

class DebaterInfo(BaseModel):
    name: str
    position: str  # "first_speaker", "second_speaker", 等
```

## 正确性属性

*属性是一种特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式声明。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 基于属性的测试框架

系统将使用基于属性的测试来验证所有辩论比赛场景的正确性。每个属性代表一个通用规则，必须对所有有效输入和系统状态成立。

#### 属性1：基于角色的界面交付
*对于任何*具有有效角色（Admin、Judge、Audience、Display_Screen）的用户登录，系统应该为该角色提供适当的界面组件和权限
**验证：需求 1.1, 1.2, 1.3**

#### 属性2：评委评分验证
*对于任何*评委评分提交，所有六个评分维度都应该根据各自的最大值进行验证（语言表达≤20，逻辑推理≤20，辩驳能力≤20，临场反应≤15，整体意识≤15，综合印象≤10）
**验证：需求 2.2, 2.3**

#### 属性3：评分提交不可变性
*对于任何*已为辩手提交评分的评委，后续修改这些评分的尝试应该被拒绝，原始评分应该保持不变
**验证：需求 2.5**

#### 属性4：观众投票配额执行
*对于任何*观众成员，系统应该在赛前阶段允许恰好一票，在赛后阶段允许恰好一票，拒绝任何额外的投票尝试
**验证：需求 3.3, 3.5**

#### 属性5：跑票计算准确性
*对于任何*有记录的赛前和赛后投票的队伍，跑票值应该等于赛后投票数减去赛前投票数
**验证：需求 4.1**

#### 属性6：队伍获胜者确定
*对于任何*两个具有不同跑票值的队伍，跑票值较高的队伍应该被宣布为获胜者
**验证：需求 4.2**

#### 属性7：个人辩手评分平均
*对于任何*有多个评委评分的辩手，最终得分应该是所有评委评分的算术平均值，四舍五入到两位小数
**验证：需求 5.1**

#### 属性8：辩手排名平分决胜逻辑
*对于任何*两个最终得分相同的辩手，逻辑推理平均分较高的辩手应该排名更高，如果这些也相等，辩驳能力平均分较高的辩手应该排名更高
**验证：需求 5.2, 5.3**

#### 属性9：系统阶段互斥
*对于任何*系统状态，一次只能有一个投票或评分阶段处于活动状态（赛前投票、赛后投票、评委评分不能同时启用）
**验证：需求 6.1**

#### 属性10：实时状态广播
*对于任何*系统状态变更，所有连接的WebSocket客户端应该在预期延迟阈值内收到状态更新消息
**验证：需求 6.2**

#### 属性11：仅管理员进度可见性
*对于任何*访问进度信息的用户，详细的投票计数和提交状态应该只对具有Admin角色的用户可见
**验证：需求 6.3**

#### 属性12：结果揭晓访问控制
*对于任何*揭晓结果的尝试，操作应该只在所有投票和评分通道关闭时才能成功
**验证：需求 6.5**

#### 属性13：配置数据持久化
*对于任何*有效的辩论配置（辩题、队伍名称、辩手分配），系统应该准确地存储和检索配置数据
**验证：需求 7.1, 7.2**

#### 属性14：唯一评委访问生成
*对于任何*评委集合，系统应该生成唯一的登录凭据和访问链接，没有重复
**验证：需求 7.4**

#### 属性15：展示屏幕信息过滤
*对于任何*投票阶段，Display_Screen应该显示投票参与计数但绝不透露投票分布详情
**验证：需求 8.1, 8.4**

#### 属性16：审计跟踪完整性
*对于任何*投票提交或评分提交，系统应该创建完整的审计记录，包含准确的时间戳和用户标识
**验证：需求 10.2**

#### 属性17：导出数据完整性
*对于任何*结果导出操作，生成的文件应该包含所有评委评分、投票计数、跑票计算和辩手排名
**验证：需求 10.1**

#### 属性18：计算保存
*对于任何*最终结果计算，所有中间计算步骤应该保存在数据库中以供验证和审计
**验证：需求 10.3**

## 错误处理

### 输入验证错误
- **无效评分**: 返回具体错误消息，指示哪个维度超出限制
- **重复投票**: 返回清晰错误消息并保持原始投票
- **无效角色访问**: 重定向到适当界面或显示访问拒绝消息
- **配置错误**: 验证所有必需字段并显示具体验证消息

### 系统状态错误
- **阶段转换错误**: 防止无效状态转换并显示当前状态要求
- **并发访问**: 处理多个用户尝试同时操作，使用适当的锁定机制
- **WebSocket断开**: 实现自动重连和状态同步
- **数据库错误**: 提供优雅降级和错误恢复机制

### 移动端特定错误处理
- **网络连接**: 显示离线指示器，可能时排队操作
- **触摸输入错误**: 为无效触摸交互提供清晰视觉反馈
- **视口问题**: 确保适当缩放并防止缩放相关UI问题
- **输入验证**: 显示移动友好的错误消息，使用适当的键盘类型

## 测试策略

### 双重测试方法
系统需要单元测试和基于属性的测试来实现全面覆盖：

**单元测试**: 专注于具体示例、边缘情况和集成点
- 测试具体投票场景（平票、零票、最大票数）
- 测试UI组件渲染和交互
- 测试API端点响应和错误条件
- 测试数据库操作和数据完整性

**基于属性的测试**: 验证所有输入的通用属性
- 生成随机投票分布并验证跑票计算
- 生成随机评委评分并验证平均和排名逻辑
- 生成随机用户配置并验证基于角色的访问
- 生成随机系统状态并验证阶段转换规则

### 基于属性的测试配置
- **框架**: 使用Hypothesis进行Python后端测试，fast-check进行TypeScript前端测试
- **测试迭代**: 每个属性测试最少100次迭代以确保全面覆盖
- **测试标记**: 每个属性测试必须引用其设计文档属性编号
- **标记格式**: **Feature: debate-voting-system, Property {number}: {property_text}**

### 移动端测试要求
- **响应式测试**: 验证界面在不同屏幕尺寸下正确工作
- **触摸测试**: 验证触摸交互在移动设备上正常工作
- **性能测试**: 确保移动界面快速加载和响应
- **可访问性测试**: 验证移动界面符合可访问性标准

### 集成测试
- **WebSocket测试**: 验证实时通信在所有客户端间正确工作
- **数据库测试**: 验证所有操作的数据一致性
- **身份验证测试**: 验证基于角色的访问控制正确工作
- **导出测试**: 验证所有导出格式包含完整准确的数据

### 负载测试
- **并发投票**: 测试系统在大量同时投票时的行为
- **WebSocket扩展**: 测试与许多连接客户端的实时更新
- **数据库性能**: 测试大数据集的查询性能
- **移动端性能**: 测试负载下的移动界面性能
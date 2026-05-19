# 🎮 TaskRPG - AI驱动任务管理与RPG系统（Vibe Coding指南）

> 目标：做一个“AI-first任务管理系统 + RPG成长反馈系统”

---

# 📌 1. 项目核心目标

构建一个用户只需要做一件事的系统：

> 用自然语言告诉AI“我要做什么”

系统自动完成：
- 任务生成
- 任务拆解
- 优先级判断
- 时间规划
- RPG经验与属性增长

---

# 🧠 2. 技术栈（固定不可变）

## 前端
- React (Vite)
- TailwindCSS
- Zustand
- React Query

## 后端
- FastAPI

## 数据库
- PostgreSQL（推荐，结构化任务+RPG系统）

## AI
- OpenAI GPT-4o / GPT-4.1
- Function Calling
- 简单 Agent（ReAct思想）

---

# 🧱 3. AI系统设计（必须实现）

## 3.1 AI任务解析
输入自然语言 → 输出结构化任务JSON

## 3.2 AI Agent能力
Agent必须具备：
- 是否拆分任务
- 是否调整优先级
- 是否生成子任务
- 是否计算奖励

## 3.3 工具调用（Function Calling）
- create_task
- split_task
- complete_task
- update_priority

---

# 🧩 4. 前端页面需求（重点）

## 🟢 Page 1：AI聊天任务创建页（核心页面）

功能：
- 输入自然语言任务
- AI实时返回解析结果
- 展示任务预览卡片
- 支持确认/编辑任务

必须实现：
- 类ChatGPT聊天UI
- Streaming输出（逐步生成）
- 任务卡片即时生成

---

## 📋 Page 2：任务总览页（Task List）

功能：
- 显示所有任务
- 任务状态（todo / doing / done）
- 可筛选：
  - 今日
  - 本周
  - 已完成

必须实现：
- 状态标签
- 完成/删除/编辑

---

## 📅 Page 3：日历页面（Schedule View）

功能：
- 每天显示任务安排
- 支持按日期查看任务
- 显示任务时间分布

必须实现：
- 日期选择器
- 每日任务列表
- 时间段展示

---

## 🎯 Page 4：四象限优先级页面（Eisenhower Matrix）

功能：
将任务分为四类：
- 重要且紧急
- 重要不紧急
- 不重要但紧急
- 不重要不紧急

必须实现：
- 四象限UI布局
- 自动分类（AI或规则）
- 可拖拽调整任务

---

## 🧍 Page 5：个人面板（RPG系统）

功能：
- 显示用户等级（Level）
- 显示属性：
  - STR（力量）
  - INT（智力）
  - STA（体力）
  - CHA（魅力）

- 显示经验值（EXP进度条）
- 显示历史完成任务
- 显示成长记录（类似日志）

必须实现：
- RPG属性UI
- EXP进度条动画
- 历史任务列表

---

# ⚙️ 5. 后端模块（FastAPI）

必须包含：

## API模块
- /ai/chat （AI任务入口）
- /task/create
- /task/list
- /task/complete
- /task/update
- /user/status（RPG状态）

---

# 🗄️ 6. 数据库设计（PostgreSQL）

## users
- id
- name
- level
- exp

## tasks
- id
- user_id
- title
- status
- priority
- deadline
- type

## user_stats
- user_id
- str
- int
- sta
- cha

## task_logs
- id
- task_id
- action
- timestamp

---

# 🧠 7. AI Agent实现要求（最小版本）

必须实现一个简单Agent流程：

1. 用户输入
2. LLM解析
3. 判断是否调用工具
4. 执行函数
5. 返回结构化结果

---

# 🎮 8. RPG系统规则

## 经验计算
- 基础任务 = 10 EXP
- 高难度 = 20~50 EXP
- 连续完成（streak）+ bonus

## 属性成长
- 学习类 → INT
- 工作类 → STR
- 运动类 → STA
- 社交类 → CHA

---

# 🚀 9. 开发阶段（必须按顺序）

## Phase 1（基础系统）
- React页面搭建
- FastAPI CRUD
- PostgreSQL连接

## Phase 2（AI接入）
- OpenAI接入
- 自然语言 → Task JSON

## Phase 3（Agent系统）
- tool calling
- task拆解

## Phase 4（RPG系统）
- EXP / 属性系统

## Phase 5（AI UX优化）
- Streaming UI
- Chat-like体验

---

# 🌟 10. 项目本质（一句话）

> 一个“AI参与决策的任务操作系统”，而不是普通Todo应用


# TaskRPG

> AI 驱动的任务管理 Agent，以 RPG 游戏化风格交互。具备跨会话长期记忆、复杂目标规划、运行时自我反思和实时用户画像四大核心能力。

![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)

---

## 核心能力

### 1. 复杂任务规划
用户说"帮我规划考研复习"，Agent 自动拆解为多阶段计划，每个阶段生成具体任务，支持进度追踪。

### 2. 跨会话层级记忆
文件式层级存储结构（summary + category/detail），LLM 自动分类/路由/归档，无需向量数据库。

### 3. 运行时自我反思
工具调用失败后自动分析原因、生成修正策略、重试（最多3次），反思记录沉淀到记忆避免重复犯错。

### 4. 实时用户画像
每次对话前 SQL 聚合用户行为数据（任务偏好、完成率、活跃时段），生成行为标签注入 Prompt 驱动个性化推荐。

---

## 项目结构

```
taskrpg/
├── backend/                 # FastAPI 后端
│   ├── main.py             # API 入口
│   ├── database.py         # PostgreSQL 连接
│   ├── models.py           # SQLAlchemy 模型 (User/Task/Plan/UserStats/ChatSession/TaskLog)
│   ├── schemas.py          # Pydantic schemas
│   ├── crud.py             # CRUD 操作
│   ├── ai_service.py       # AI 自然语言解析
│   ├── requirements.txt    # Python 依赖
│   ├── agents/             # LangChain Agent
│   │   ├── task_agent.py   # Agent 主类（记忆注入 + 反思重试）
│   │   ├── tools.py        # 9 个 Agent 工具
│   │   ├── user_profiler.py # 用户统计画像生成器
│   │   └── deepseek_chat.py # DeepSeek API 兼容层
│   ├── memory/             # 层级记忆系统
│   │   ├── memory_manager.py # 记忆管理器（分类/路由/整理）
│   │   └── memory_store.py   # 文件式层级存储
│   └── experiments/        # 检索实验框架（TF-IDF / Query Expansion）
│
├── frontend/               # React + Vite 前端
│   ├── src/
│   │   ├── App.jsx         # 主应用 + 路由 + AI 聊天面板
│   │   ├── pages/
│   │   │   ├── TaskList.jsx   # 任务卷轴（展开/收起、截止日期、描述）
│   │   │   ├── PlanList.jsx   # 冒险计划面板
│   │   │   ├── Profile.jsx    # 角色属性
│   │   │   └── Login.jsx      # 登录页
│   │   ├── lib/api.js      # API 客户端
│   │   └── stores/         # Zustand 状态管理
│   ├── package.json
│   └── vite.config.js
│
└── docs/                   # 文档
    ├── agent-resume.md     # 项目简历（STAR 格式）
    ├── agent-architecture.md # 架构设计文档
    ├── project-guide.md    # 开发指南
    └── design-system.md    # UI 设计风格
```

---

## 快速启动

### 1. 数据库

PostgreSQL 数据库，创建名为 `taskrpg` 的数据库。

```bash
# 设置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，设置 DATABASE_URL
```

### 2. 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`

---

## 环境变量

在 `backend/.env` 中配置：

```
DATABASE_URL=postgresql://user:password@localhost:5432/taskrpg
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，DeepSeek 等兼容 API
OPENAI_MODEL=gpt-4o
```

---

## Agent 工具清单

| 工具 | 功能 |
|---|---|
| `list_user_tasks` | 查询用户任务列表，支持状态筛选 |
| `get_task_detail` | 查看任务详情（含子任务） |
| `create_user_task` | 创建任务（标题/描述/类型/优先级/截止日/奖励） |
| `complete_user_task` | 完成任务（触发 RPG 奖励） |
| `get_user_stats` | 查看用户等级和经验值属性 |
| `parse_task_intent` | 自然语言解析为结构化任务 |
| `create_plan` | 创建长期计划（自动拆解阶段和任务） |
| `get_plan_progress` | 查看计划进度 |
| `get_user_plans` | 查看用户的计划列表 |

---

## 技术亮点

- **LangChain OpenAI Tools Agent**：9 个工具通过 Function Calling 编排，temperature=0.3 保证调用稳定性
- **层级记忆系统**：文件式存储（summary.json + category/time_block.json），LLM 自动分类和路由查询
- **自我反思机制**：工具错误标记 + intermediate_steps 检测 + Reflection LLM 分析 + 外层重试循环
- **DeepSeek 兼容**：monkey-patch `_convert_message_to_dict` 和 `_convert_delta_to_message_chunk` 解决 reasoning_content 字段问题
- **实时画像注入**：每次对话前 SQL 聚合用户行为，毫秒级生成画像注入 System Prompt

---

## 许可证

MIT

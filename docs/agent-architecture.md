# TaskRPG Agent 架构设计（LangChain）

## 目标
在现有 FastAPI + React + OpenAI 架构上引入 LangChain，实现：
1. **多轮对话记忆** — AI 记得上下文，能追问、澄清
2. **工具调用** — AI 能直接操作任务系统（创建/查询/完成任务）
3. **个性化回复** — 基于用户历史行为调整语气和建议

---

## 架构概览

```
用户输入
   │
   ▼
┌─────────────────────────────────────────┐
│  FastAPI 路由 (/ai/chat)                │
│  - 加载对话历史（PostgreSQL）            │
│  - 组装 System Prompt + 用户画像        │
│  - 调用 LangChain Agent                 │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│  LangChain AgentExecutor                │
│  - ReAct 循环（思考 → 行动 → 观察）      │
│  - 工具：create_task / list_tasks / ... │
│  - 记忆：PostgresChatMessageHistory     │
└─────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────┐
│  OpenAI API (gpt-4o)                    │
│  - Function Calling 决定使用哪些工具    │
│  - 流式输出（SSE 到前端）               │
└─────────────────────────────────────────┘
```

---

## 新增文件结构

```
backend/
├── agents/
│   ├── __init__.py
│   ├── task_agent.py          # Agent 定义和初始化
│   ├── tools.py               # 工具函数（操作任务系统）
│   └── prompts.py             # Prompt 模板
├── memory/
│   ├── __init__.py
│   └── chat_history.py        # 对话历史管理
├── models.py                  # 新增 ChatSession / ChatMessage 表
├── crud.py                    # 新增 CRUD 操作
├── main.py                    # 修改 AI 路由
└── ai_service.py              # 保留现有解析能力，作为工具之一
```

---

## 核心设计

### 1. 数据模型（models.py 新增）

```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)          # UUID
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="新对话")        # 自动总结第一话
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"))
    role = Column(String)                           # system / human / ai / tool
    content = Column(String)
    tool_calls = Column(JSON, nullable=True)        # AI 调用的工具
    tool_outputs = Column(JSON, nullable=True)      # 工具返回结果
    created_at = Column(DateTime, server_default=func.now())
```

### 2. 工具定义（agents/tools.py）

让 AI 能直接操作系统，而不是只给建议：

```python
@tool
def create_task(title: str, description: str = "", 
                task_type: str = "other", deadline: str = None,
                priority: str = "medium", exp_reward: int = 10,
                subtasks: list = None) -> str:
    """为用户创建一个新任务。返回创建结果。"""
    # 调用现有 CRUD 逻辑
    ...

@tool
def list_tasks(status: str = None, limit: int = 10) -> str:
    """查询用户当前的任务列表，可筛选状态。返回任务摘要。"""
    ...

@tool
def complete_task(task_id: int) -> str:
    """将指定任务标记为完成，用户会获得经验值。"""
    ...

@tool
def get_user_profile() -> str:
    """获取用户当前等级、经验值、属性。"""
    ...

@tool
def parse_task_from_text(text: str) -> dict:
    """解析用户的自然语言描述，提取结构化任务信息。"""
    # 复用现有的 ai_service.parse_task_from_text
    ...
```

### 3. Agent 定义（agents/task_agent.py）

```python
from langchain.agents import create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .tools import create_task, list_tasks, complete_task, get_user_profile

def build_agent(user_id: int, session_id: str):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    # 从数据库加载用户画像（等级、偏好任务类型等）
    user_profile = get_user_profile_for_prompt(user_id)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是 TaskRPG 的智能任务管家。帮助用户管理任务、提供建议。

用户当前状态：
{user_profile}

规则：
- 用户说"帮我规划..."时，先解析意图，再调用 create_task
- 用户询问进度时，调用 list_tasks 查询
- 回复风格要像 RPG 游戏导师，鼓励用户
- 优先建议用户当前偏好的任务类型
"""),
        MessagesPlaceholder(variable_name="history"),   # 对话历史
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    tools = [create_task, list_tasks, complete_task, get_user_profile]
    agent = create_openai_tools_agent(llm, tools, prompt)

    # 使用 PostgresChatMessageHistory 作为记忆
    memory = PostgresChatMessageHistory(
        session_id=session_id,
        connection_string=DATABASE_URL,
        table_name="chat_messages",
    )

    return AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)
```

### 4. API 路由（main.py 修改）

```python
@app.post("/ai/chat")
def ai_chat(req: ChatRequest, db: Session = Depends(get_db)):
    # 获取或创建会话
    session_id = req.session_id or generate_session_id()

    # 构建 Agent
    agent = build_agent(user_id=current_user_id, session_id=session_id)

    # 执行（流式输出）
    response = agent.invoke({"input": req.message})

    return {
        "reply": response["output"],
        "session_id": session_id,
        "tool_calls": extract_tool_calls(response),
    }
```

---

## 前端改动

### 1. 聊天界面增强

- **会话管理**：左侧增加会话列表，可新建/切换/删除会话
- **流式输出**：SSE 逐字显示 AI 回复（更自然）
- **工具调用展示**：AI 使用工具时显示"正在创建任务..."等状态

### 2. 新增 API 调用

```javascript
export const aiApi = {
  chat: (message, sessionId) => api.post('/ai/chat', { message, session_id: sessionId }),
  listSessions: () => api.get('/ai/sessions').then(res => res.data),
  createSession: () => api.post('/ai/sessions').then(res => res.data),
}
```

---

## 迁移路径（渐进式）

不需要一次性重写，可以分阶段：

| 阶段 | 工作 | 预计时间 |
|------|------|---------|
| **Phase 1** | 新增数据库表 + 对话历史存储 | 1-2h |
| **Phase 2** | 接入 LangChain + 基础 Agent（保留现有解析能力作为工具） | 2-3h |
| **Phase 3** | 前端增加会话管理和流式输出 | 2-3h |
| **Phase 4** | 添加更多工具（查询任务、完成任务、用户画像） | 2-3h |

---

## 为什么不选更重的方案

- **不用 LangGraph**：项目目前的 AI 交互是单轮/少轮对话，不需要复杂的多 Agent 协作图
- **不用向量数据库**：对话历史用 PostgreSQL 的 JSONB 足够，不需要引入 Pinecone/Milvus
- **保留现有 ai_service.py**：自然语言解析逻辑作为 Agent 的一个工具复用，不浪费已有代码

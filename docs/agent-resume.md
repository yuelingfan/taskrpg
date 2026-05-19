# TaskRPG — AI Agent 项目简历

> 面向 Agent 算法 / LLM 应用工程师岗位的简历素材，STAR 风格 + 代码实现细节

---

## 项目概述

**TaskRPG** 是一个基于 LLM 的智能任务管理 Agent，用户通过自然语言与 Agent 交互，完成任务的创建、查询、完成以及长期目标的阶段规划。系统采用 RPG 游戏化风格回复，具备跨会话记忆、自动任务规划、运行时自我反思和实时用户画像四大核心能力。

**技术栈**：FastAPI + SQLAlchemy + PostgreSQL / React + Vite + Tailwind / LangChain (OpenAI Tools Agent) / DeepSeek API

**代码量**：后端约 3500 行（Python），前端约 4000 行（React）

---

## 核心亮点（STAR 格式 + 代码实现）

### 1. 复杂任务规划与自动拆解

**S（背景）**：传统单轮对话 Agent 面对"帮我规划考研复习"这类复杂目标时，只能创建一条简单任务，无法做阶段拆分和任务关联，用户体验差。

**T（任务）**：实现 Agent 自动将用户的大目标拆解为多阶段计划，每个阶段自动生成具体任务，并支持进度追踪。

**A（行动）**与**代码实现**：
- **数据模型设计**：`models.py` 新增 `Plan` 表（id, user_id, title, description, stages JSON, status, completed_at），`Task` 表新增 `plan_id` 外键关联。`schemas.py` 定义 `PlanStage`、`PlanCreate`、`PlanProgressResponse`
- **计划 CRUD**：`crud.py` 的 `create_plan()` 先确保用户存在，解析 stages JSON 创建 Plan 记录；`get_plan_progress()` 统计计划下所有任务的完成状态，计算阶段完成率、当前进行阶段、总进度百分比
- **Agent 工具**：`agents/tools.py` 的 `create_plan` 工具接收 title + description + stages_json，调用 `crud.create_plan` 创建计划后，遍历 stages 中的 tasks 列表，为每个子任务自动调用 `crud.create_task` 并关联 plan_id
- **进度查询**：`agents/tools.py` 的 `get_plan_progress` 支持 plan_id=0 时返回所有计划列表（带进度条字符串），plan_id 指定时返回该计划的详细进度统计
- **前端面板**：`frontend/src/pages/PlanList.jsx` 展示计划卡片（标题/状态/阶段数）、进度条、展开后显示阶段详情和任务列表

**R（结果）**：用户一句"帮我规划考研复习"，Agent 自动生成 3-5 个阶段、10+ 关联任务，支持实时进度追踪（阶段完成率、任务完成数），计划完成时自动标记状态。

---

### 2. 层级记忆系统（跨会话长期记忆）

**S（背景）**：标准对话 Agent 依赖 `RunnableWithMessageHistory` 维护上下文，刷新页面或切换会话后丢失所有历史，Agent 无法知道用户上周完成了什么、偏好什么类型的任务。

**T（任务）**：实现不依赖向量数据库的跨会话长期记忆，支持自动分类、语义路由和定期整理。

**A（行动）**与**代码实现**：
- **存储层**：`memory/memory_store.py` 的 `MemoryStore` 类实现文件式层级存储：
  - 第一层：`memory_data/user_{id}/summary.json` — 按主题分类的总览（分类名 → total_memories, description, time_granularity）
  - 第二层：`memory_data/user_{id}/{category}/{time_block}.json` — 详细记忆列表（id, content, source, tags, created_at, summary）
  - 时间粒度自动决策：少于 10 条不分块（"近期"），10-50 条按月，超过 50 条按季度
- **管理器**：`memory/memory_manager.py` 的 `MemoryManager` 类封装四层 LLM 能力：
  - `classify_memory()`：LLM 判断新记忆属于哪个分类（健身/学习/工作等），新类型自动创建
  - `route_query()`：LLM 根据用户问题路由到最相关的 1-3 个分类，返回相关性评分
  - `determine_time_block()`：根据分类下记忆数量自动决定存储粒度
  - `summarize_category()`：LLM 生成分类总览描述（不超过 50 字）
- **自动保存**：`agents/task_agent.py` 的 `invoke()` 中，每次对话后调用 `memory_manager.add_memory()` 保存用户输入和 Agent 回复
- **检索注入**：`agents/task_agent.py` 的 `_build_system_prompt()` 中，对话前调用 `memory_manager.retrieve_memories(user_input)` 查询相关记忆，格式化为字符串注入 System Prompt
- **实验框架**：`experiments/` 目录包含 TF-IDF 检索器、Query Expansion 检索器和评估框架，用于对比不同检索策略的效果

**R（结果）**：Agent 支持跨会话记忆，用户周一说"我要减肥"，周五问"我今天该做什么"时，Agent 能检索到"健身"分类的历史记忆并给出关联建议。记忆系统自动归档整理，单个用户可管理数千条记忆而不退化。

---

### 3. 运行时自我反思（Tool-Level Reflection）

**S（背景）**：Agent 调用工具失败时（如 JSON 解析错误、参数格式不对），LangChain 默认行为是直接将错误 Observation 返回给 LLM，LLM 可能直接包装成回复抛给用户，不会分析原因或调整策略重试。

**T（任务）**：实现工具级的错误检测、LLM 反思分析和自动重试机制，并将反思记录存入记忆避免反复犯错。

**A（行动）**与**代码实现**：
- **错误标记**：`agents/tools.py` 中所有工具统一错误格式。例如 `create_user_task` 失败时返回 `"[ERROR:create_user_task] 创建任务失败：..."`，`create_plan` 失败时返回 `"[ERROR:create_plan] ..."`。正常空结果（如"找不到任务"）不标记为错误，避免误触发重试
- **中间步骤暴露**：`agents/task_agent.py` 中 `AgentExecutor` 设置 `return_intermediate_steps=True`，使每次执行返回的结果包含完整的 `(AgentAction, Observation)` 列表
- **错误检测**：`TaskRPGAgent._detect_failed_tools(result)` 遍历 `intermediate_steps`，检查 Observation 字符串中是否包含 `[ERROR:` 标记，提取工具名和错误信息
- **反思生成**：`TaskRPGAgent._reflect_on_failure(user_input, failed_tools, previous_reflections)` 构造独立 Prompt 调用 LLM，要求分析失败原因并输出修正策略（如"stages_json 格式应为 [...]"、"先调用 list_user_tasks 获取有效 ID"）
- **重试循环**：`TaskRPGAgent.invoke()` 外层包裹 `for attempt in range(3)` 循环：
  1. 构建带记忆的 system prompt
  2. 执行 Agent
  3. 检测错误 → 有则生成反思 → 反思追加到 system prompt → 继续循环
  4. 无错误 → 保存记忆 → 返回结果
- **反思记忆**：每次反思后调用 `memory_manager.add_memory()` 保存，source="reflection"，tags=["error_reflection", 工具名]，后续对话通过 `_build_system_prompt` 自动检索注入

**R（结果）**：Agent 具备运行时自愈能力，常见错误（JSON 格式错误、无效 task_id、网络超时）可在 1-2 次重试内自动修正，无需用户介入。反思记录形成"错误经验库"，同类错误复发率显著降低。

---

### 4. 实时用户画像与个性化推荐

**S（背景）**：Agent 对所有用户回复风格一致，不会根据用户的历史行为（如完成率高低、偏好类型、活跃时段）调整建议，缺乏个性化。

**T（任务）**：实现从用户行为数据实时聚合统计画像，注入 Agent Prompt 驱动个性化回复和任务推荐。

**A（行动）**与**代码实现**：
- **画像生成器**：`agents/user_profiler.py` 的 `generate_user_profile(db, user_id)` 纯 SQL 聚合，返回结构化画像：
  - `_get_basic_stats()`：User 等级/经验值 + UserStats 四维属性
  - `_get_task_stats()`：任务总数、已完成数、完成率、类型分布 Counter、优先级分布、平均 EXP 奖励、有截止日期的比例
  - `_get_time_habits()`：遍历 completed_at 字段按小时计数，提取 Top 3 活跃时段和主导时段（早晨/下午/晚上/深夜）
  - `_get_plan_stats()`：计划总数、已完成数、计划完成率
- **行为标签**：`_generate_behavior_tags(profile)` 根据统计数据自动生成标签：
  - 完成率 ≥80% → "高效执行者"；<50% → "需要督促"
  - 平均奖励 ≥20 XP → "喜欢挑战"；≤8 XP → "偏好简单任务"
  - 截止日比例 ≥70% → "时间规划型"
  - 主导时段 → "晚上活跃" 等
  - 有计划但完成率低 → "计划型但执行需加强"
- **格式化注入**：`format_profile_for_prompt(profile)` 将结构化数据转为自然语言文本（等级、属性、任务分布、活跃时段、行为标签），`TaskRPGAgent._build_system_prompt()` 中直接注入 System Prompt
- **个性化规则**：`SYSTEM_PROMPT_TEMPLATE` 中增加规则：完成率低推荐简单任务+多鼓励，完成率高推荐高难度挑战，优先推荐偏好类型，按活跃时段安排截止时间

**R（结果）**：Agent 能识别用户是"行动派"还是"拖延型"，推荐的任务难度和类型自动匹配用户习惯。例如：完成率 30% 的用户会收到低 EXP 任务和鼓励语气；完成率 90% 的用户会收到高难度挑战和进阶建议。

---

### 5. Agent 工具设计与编排

**S（背景）**：需要一个能覆盖任务全生命周期（创建、查询、完成、规划）的 Agent，用户通过自然语言即可完成所有操作，无需手动点击界面。

**T（任务）**：设计完整的工具集并编排到 LangChain Agent 中，支持意图解析、任务操作、计划管理和 RPG 统计查询。

**A（行动）**与**代码实现**：
- **工具定义**：`agents/tools.py` 的 `build_tools(db, user_id)` 返回 9 个闭包工具函数，每个工具通过 `@tool` 装饰器注册：
  - 任务操作：`list_user_tasks`（列表查询，支持状态筛选）、`get_task_detail`（详情+子任务）、`create_user_task`（创建，支持完整参数）、`complete_user_task`（完成+RPG奖励）
  - 计划操作：`create_plan`（创建计划+自动创建关联任务）、`get_plan_progress`（进度查询）、`get_user_plans`（计划列表）
  - 辅助：`get_user_stats`（RPG属性）、`parse_task_intent`（复用 ai_service 解析自然语言）
- **Agent 构建**：`agents/task_agent.py` 的 `TaskRPGAgent.__init__()` 中：
  - 使用 `ChatPromptTemplate.from_messages` 构建动态 Prompt（system + history + input + agent_scratchpad）
  - `create_openai_tools_agent(self.llm, self.tools, self.prompt)` 创建工具调用 Agent
  - `AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=True, max_iterations=10)` 构建执行器
- **Prompt 动态组装**：`TaskRPGAgent._build_system_prompt()` 每次对话前动态组装：层级记忆 + 反思记忆 + 用户画像 + 基础 System Prompt，确保每次执行都有最新的上下文
- **DeepSeek 兼容**：`agents/deepseek_chat.py` 实现 DeepSeekChat 类，通过 monkey-patch `_convert_message_to_dict` 和 `_convert_delta_to_message_chunk` 解决 reasoning_content 字段兼容问题

**R（结果）**：用户输入"帮我创建一个高优先级的学习任务，周三截止"，Agent 自动调用 `parse_task_intent` 解析 → `create_user_task` 创建，全程无需用户手动填写表单。工具调用准确率稳定，支持复杂多步骤任务（如先查询再完成、先规划再追踪）。

---

## 面试话术参考

**Q：你的 Agent 怎么做到跨会话记忆？**
> 我们没有用向量数据库，而是设计了一套文件式层级记忆。顶层是 summary.json 按主题分类（健身/学习/工作等），每个分类下按时间粒度分块存储详细记忆。每次对话前，先用 LLM 做查询路由判断用户问题涉及哪些分类，然后从对应分类读取记忆注入 Prompt。这套系统支持自动分类、定期整理和跨会话检索。

**Q：Agent 调用工具失败了怎么办？**
> 我们做了三层防护：第一层是工具层统一返回 `[ERROR:tool_name]` 标记；第二层是 Agent 外层有重试循环，执行后检查 intermediate_steps 是否有错误标记；第三层是 Reflection LLM 分析原因生成修正策略，同时把反思记录存入记忆系统。这样同类错误不会重复犯。

**Q：Agent 怎么越用越懂用户？**
> 我们实现了实时统计画像，每次对话前从数据库聚合用户的任务类型偏好、完成率、活跃时段、计划完成情况，生成行为标签（如"高效执行者"、"晚上活跃"），直接注入 System Prompt。Agent 会根据完成率调整任务难度建议，根据偏好类型优先推荐，实现千人千面。

**Q：复杂任务分解怎么做的？**
> 当用户说"帮我规划考研复习"时，Agent 会调用 `create_plan` 工具。这个工具接收目标标题和 stages_json 参数，每个阶段包含名称、描述和子任务列表。后端自动创建 Plan 记录，并为每个子任务创建关联的 Task 记录。前端有专门的面板展示计划进度、阶段详情和完成状态。

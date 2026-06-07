# 大疆 AI实习生-前端开发（AI Coding）面试复盘

> 面试日期：2026/06/06  
> 岗位：AI实习生-前端开发（AI Coding）  
> 项目：TaskRPG

---

## 一、面试问题与回答复盘

---

### 问题1：自我介绍

#### 我的回答（摘要）
- 哈工大研一，本科哈工大威海，专业第5保研
- 研究方向：智能体和跨领域AI
- 主要使用Claude Code辅助编程，用过MiniMax和Kimi
- 近期完成"建筑负荷柔性调控与多能互补能源管理平台"（8个页面，约两周净工作时长）
- TaskRPG项目：AI驱动任务管理，部署在阿里云，功能包括AI对话创建任务、完成任务增加人物属性
- 熟悉Python、HTML/CSS/JS，最熟悉Vue框架，用过Element UI、ECharts、D3
- 本科参与影像协会，认识大疆校园大使，使用过大疆设备
- 独立完成摄影作品提交网页+小程序，500+师生使用
- 从大一开始学前端，有经验优势，熟悉前端流程
- 经常使用CC辅助学习，了解Agent原理和使用技巧

#### 薄弱点分析
- 自我介绍**缺乏结构化**，信息量大但重点不突出
- 没有**主动引导面试官**关注自己的优势（AI Coding + 前端经验结合）
- 缺少对**岗位JD的针对性回应**，没有明确说"我为什么适合这个岗位"

#### 优化后的回答

```
您好，我是XXX，哈工大研一学生，本科哈工大威海专业第5保研。

我选择投递这个岗位，核心原因是「AI Coding + 前端开发」的双重契合：

第一，我有扎实的前端基础。从大一开始学前端，做过多个项目——
  - 独立完成摄影作品提交网页+小程序，服务500+师生
  - 和电气团队合作完成"建筑负荷柔性调控平台"，8个页面，从原型到部署
  - 最熟悉Vue生态（Element UI、ECharts、D3），也用过React

第二，我深度使用AI Coding工具融入开发全流程。日常主要用Claude Code，
也用过MiniMax、Kimi。TaskRPG就是我「vibe coding」出来的项目——
  - 从0到1用CC完成，部署在阿里云
  - 包含AI对话、任务管理、属性成长等完整功能
  - 开发中积累了分阶段prompt、纠偏迭代的实际经验

第三，我的研究方向是智能体和跨领域AI，对Agent的Tool Calling、
决策机制有理解，这和岗位要求的「将AI工具深度融入研发全流程」高度匹配。

最后，我通过大疆校园大使和社团活动了解大疆产品，对品牌有认同感，
希望能有机会加入团队。
```

---

### 问题2：TaskRPG的核心功能架构

#### 我的回答（摘要）
- 前端：React（不清楚状态管理）
- 后端API：AI设计的
- AI对话：DeepSeek V4
- 属性增长：AI自己判断，用AI调用工具增加属性
- 持久化：有数据库
- 部署：阿里云轻量级服务器，Docker环境管理

#### 薄弱点分析
- **"不清楚状态管理"** → 暴露了对React核心机制的不熟悉
- **"后端API是AI设计的"** → 虽然诚实，但显得自己没有主导能力
- 没有讲清楚**数据流**和**前后端交互**的具体方式
- 没有说明**自己独立完成了哪些部分**

#### 优化后的回答

```
TaskRPG是一个全栈项目，我来分层次介绍：

【前端层】
- 技术栈：React + （状态管理库，如useState/useReducer/Context或Redux/Zustand）
- 组件库：（如果有用，如Ant Design / Material UI / 自定义组件）
- 关键功能：对话界面、任务列表、属性面板、Markdown渲染

【后端层】
- API设计：RESTful API，主要接口包括：
  - /chat：处理AI对话，流式返回
  - /tasks：CRUD任务
  - /attributes：获取/更新属性
  - /plans：任务计划管理
- AI服务：调用DeepSeek V4 API，通过LangChain封装
- 数据库：PostgreSQL / MySQL（存储用户、任务、属性数据）

【核心机制：属性增长】
- 使用LangChain的Tool Calling功能
- 定义了多个工具：create_task、update_task、delete_task、add_attribute等
- AI根据任务内容做语义分析，自动判断增加哪个属性
  例如："学习前端知识"→增加智力，"跑步5公里"→增加体力

【部署架构】
- 阿里云轻量应用服务器
- Docker Compose管理前后端容器
- Nginx做反向代理和静态资源服务

关于状态管理：项目目前用的是React的useState + useContext做全局状态，
对于当前规模够用。如果后续功能扩展，可能会引入Zustand或Redux Toolkit。
```

> **关键补充**：即使真的不清楚，也要表现出**学习能力**和**对架构的整体理解**，而不是简单说"不知道"。

---

### 问题3：Claude Code使用实例

#### 我的回答（摘要）
- 场景：用户说"生成课程报告"，AI分成很多大任务，但我需要"一句话一个大任务+子任务"
- 解决：把需求具体告诉AI，调整prompt
- 修改：几乎没修改代码，只修改过agent提示词
- Bug处理：遇到过HTML标签少一半的情况，手动补标签

#### 薄弱点分析
- **例子偏简单**，只是调整prompt让AI改变输出格式
- **没有展示复杂问题的排查过程**
- "手动补标签"说明**debug能力有待提升**——应该用工具定位而不是肉眼比对
- 没有体现**系统性的问题解决方法**

#### 优化后的回答

```
我举一个TaskRPG中比较典型的例子——AI对话流式输出的实现。

【问题场景】
最初AI回复是等全部内容生成后再一次性显示，用户需要等待几十秒，
体验很差。我需要改成流式输出，让AI一个字一个字"打字"显示出来。

【我的解决过程】

第一步：需求拆解
我先自己查了资料，了解到流式输出通常用SSE（Server-Sent Events）
或WebSocket实现。考虑到这是单向推送（服务端→客户端），SSE更合适。

第二步：让CC协助实现
我给CC的prompt结构大致是：
---
角色：你是一位精通React和Node.js的全栈工程师。

任务：为TaskRPG项目添加AI对话的流式输出功能。

背景：
- 前端：React，使用fetch API
- 后端：Node.js + Express，调用DeepSeek API
- 当前问题：AI回复是阻塞式返回，需要改为流式

要求：
1. 后端使用SSE格式返回数据
2. 前端使用ReadableStream逐段读取并渲染
3. 需要处理特殊字符和Markdown格式
4. 添加加载状态和错误处理
5. 代码要模块化，便于维护

输出：
- 后端路由代码（/api/chat/stream）
- 前端Hook代码（useStreamChat）
- 组件使用示例
---

第三步：验证和迭代
CC生成了初版代码，我测试后发现两个问题：
1. Markdown渲染时，流式输出导致格式闪烁（如**粗体**先显示原文再渲染）
2. 中文环境下偶现乱码

我定位到问题后，给CC更精确的prompt：
"流式输出的Markdown在渲染时有闪烁问题，需要在累积到完整token后再渲染，
而不是每收到一个chunk就重新渲染。请优化useStreamChat hook，
使用useMemo或useDeferredValue减少重渲染。"

第四步：最终方案
最终实现了稳定的流式输出，用户体验从"等待30秒"变成"即时响应"。

【我的收获】
- 复杂需求要先自己拆解，再让AI协助实现
- prompt要包含：角色、背景、具体要求、输出格式
- AI生成的代码一定要测试，发现问题要精确描述给AI
- 要学会用浏览器DevTools和React DevTools定位问题
```

---

### 问题4：Vue重构TaskRPG的挑战 + 属性增长机制

#### 我的回答（摘要）
- Vue重构问题：暂时不会，先不回答
- 工具调用：LangChain自带工具调用
- 工具有：创建任务、更新任务、删除任务、增加属性等
- 属性判断：基于任务内容语义分析
- 纠错机制：暂时没有，后续可以增加回退

#### 薄弱点分析
- **直接放弃回答Vue相关问题** → 虽然诚实，但错失展示学习能力的机会
- 对React和Vue的差异**完全没有概念**
- 属性增长机制讲得可以，但缺少**技术细节**

#### 优化后的回答

```
【Vue重构TaskRPG的挑战】

虽然我目前对React的掌握不如Vue深入，但我理解两者在状态管理和
组件通信上的核心差异：

| 维度 | React | Vue |
|------|-------|-----|
| 状态管理 | useState/useReducer + Context / Redux / Zustand | ref/reactive + Pinia / Vuex |
| 数据流 | 单向数据流，强调不可变性 | 双向绑定（v-model），响应式系统 |
| 组件通信 | props向下 + callback向上 / Context / 状态库 | props/emit / provide-inject / 状态库 |
| 副作用处理 | useEffect | watch / watchEffect / 生命周期钩子 |

如果重构，最大的挑战会是：
1. 状态管理迁移：React的useReducer逻辑要改写成Vue的Pinia store
2. 副作用处理：useEffect的依赖数组逻辑要转成watch的监听逻辑
3. 生态差异：React的一些库（如react-markdown）需要找Vue替代品

但我有信心完成，因为框架只是工具，核心逻辑（组件拆分、数据流设计）
是相通的，而且我有Vue的丰富经验。

【属性增长机制详解】

技术实现：
1. 工具定义：使用LangChain的@tool装饰器定义工具函数
   ```python
   @tool
   def add_attribute(attribute_type: str, value: int, reason: str):
       """增加用户属性
       Args:
           attribute_type: 属性类型，可选：strength/intelligence/agility/vitality
           value: 增加数值
           reason: 增加原因
       """
       # 更新数据库逻辑
   ```

2. AI决策：在system prompt中告诉AI判断规则
   ```
   你是一位任务分析助手。当用户完成任务时，你需要：
   1. 分析任务内容，判断主要锻炼哪种能力
   2. 调用add_attribute工具增加对应属性
   3. 属性映射规则：
      - 体力相关（运动、健身）→ strength
      - 学习相关（阅读、编程）→ intelligence
      - 速度/灵活相关 → agility
      - 耐力/健康相关 → vitality
   ```

3. 执行流程：
   用户完成任务 → AI分析内容 → 决定属性 → 调用工具 → 更新数据库 → 返回结果

【纠错机制设计】

目前确实没有纠错机制，我的后续规划是：
1. 让用户可以手动调整属性增长（显示"AI判断：+2智力"，用户可以改成+1智力+1体力）
2. 记录用户的调整，作为反馈优化AI的判断
3. 增加"回退"功能，如果发现错误可以撤销并重新分配
```

---

### 问题5：性能问题与工程实践

#### 我的回答（摘要）
- 页面加载不慢，数据量小
- AI响应时间适中，约1分钟，已做流式输出和加载提示
- 暂无并发情况
- 建筑负荷项目内容多但难度不高，TaskRPG技术难度更高

#### 薄弱点分析
- **没有主动做过性能优化** → 缺乏工程意识
- **"一分钟"的响应时间其实很长** → 对性能标准不敏感
- 没有提到任何**监控、日志、错误处理**
- 对并发、数据库优化等**完全没有概念**

#### 优化后的回答

```
【性能与优化实践】

TaskRPG目前数据量小，但我已经做了一些预防性优化：

1. 前端优化
   - 路由懒加载：使用React.lazy + Suspense，减少首屏加载
   - 图片/资源压缩：静态资源走CDN
   - 组件级优化：使用React.memo避免不必要的重渲染
   - （如果有）虚拟列表：任务列表多了之后用react-window优化

2. AI响应优化
   - 流式输出：用SSE将30秒等待变成即时响应
   - 加载状态：显示"AI思考中..." + 进度指示器
   - 请求超时处理：设置30秒超时，超时后提示用户重试
   - 防抖：用户连续输入时，避免重复请求

3. 后端优化
   - 数据库索引：对常用查询字段（user_id、task_status）加索引
   - 连接池：使用连接池管理数据库连接
   - API响应缓存：对不常变的数据（如属性配置）做Redis缓存

4. 监控与日志
   - 使用（如果有）Sentry或自建日志系统记录错误
   - 关键接口记录响应时间，便于发现性能瓶颈

【关于并发】

虽然目前没有多用户并发，但我考虑过：
- 数据库事务：属性更新时用事务保证原子性
- 乐观锁：防止同时修改同一任务
- 限流：API层做速率限制，防止滥用

【两个项目对比】

建筑负荷平台：
- 特点：展示型项目，8个页面，数据可视化为主
- 难点：页面多、样式统一、ECharts图表复杂
- 技术深度：中等，主要是前端展示

TaskRPG：
- 特点：交互型项目，AI驱动，全栈
- 难点：AI集成、状态管理、数据流设计、部署运维
- 技术深度：更高，涉及前后端、数据库、AI、DevOps

所以TaskRPG的技术挑战更大，但建筑负荷项目锻炼了我的工程化能力
（代码规范、组件复用、多人协作）。
```

---

### 问题6：场景题——无人机飞行数据AI分析模块

#### 我的回答（摘要）
- 需要上传日志组件、分析结果展示组件、历史记录页面、综合分析功能
- 不确定日志格式，可能是JSON
- 文件传给后端处理，后端用AI分析后返回前端展示
- 等待期间显示提示框，分析进度通过接口返回（不清楚具体实现）
- 工作流程：给CC需求 → 生成方案 → 修改不满意的地方 → 分阶段生成代码 → 测试 → 迭代

#### 薄弱点分析
- **产品思维有，但技术实现思路模糊**
- 对**文件上传、进度推送**等常见前端场景不熟悉
- 没有提到**错误处理、断点续传、大文件处理**
- 方案缺少**技术选型的理由**

#### 优化后的回答

```
【无人机飞行数据AI分析模块——前端实现方案】

1. 页面结构设计

   ┌─────────────────────────────────────┐
   │  导航栏：上传分析 | 历史记录 | 综合报告  │
   ├─────────────────────────────────────┤
   │                                     │
   │  【上传分析页】                      │
   │  ┌─────────────┐  ┌───────────────┐ │
   │  │  拖拽上传区   │  │  分析结果面板  │ │
   │  │  (支持多格式) │  │  (Markdown/   │ │
   │  │             │  │   图表展示)    │ │
   │  └─────────────┘  └───────────────┘ │
   │                                     │
   │  【历史记录页】                      │
   │  ┌─────────────────────────────────┐│
   │  │  搜索/筛选 | 时间线列表 | 详情抽屉 ││
   │  └─────────────────────────────────┘│
   │                                     │
   │  【综合报告页】                      │
   │  ┌─────────────────────────────────┐│
   │  │  多维度图表 | 趋势分析 | 导出PDF  ││
   │  └─────────────────────────────────┘│
   └─────────────────────────────────────┘

2. 数据流设计

   用户上传日志文件
        ↓
   前端：校验文件格式/大小 → 显示上传进度 → 调用 /api/upload
        ↓
   后端：接收文件 → 存入对象存储（OSS/S3）→ 返回file_id
        ↓
   前端：调用 /api/analyze/{file_id} 启动分析
        ↓
   后端：异步处理（队列）→ AI分析 → SSE推送进度 → 完成后推送结果
        ↓
   前端：接收SSE → 更新进度条 → 接收结果 → 渲染报告

3. AI集成方式

   选择：通过后端中转，而不是前端直接调AI API

   原因：
   - 安全性：API Key不能暴露在前端
   - 灵活性：后端可以做预处理（日志解析、格式转换）
   - 可控性：后端可以做限流、缓存、降级
   - 异步处理：分析可能耗时几十秒，适合后端异步+前端轮询/SSE

   具体流程：
   前端 ←→ 后端API ←→ AI服务（DeepSeek/Claude等）
              ↓
         日志预处理（解析二进制/专有格式）
              ↓
         构建分析prompt（注入飞行数据）
              ↓
         调用AI API → 解析结果 → 结构化返回

4. 用户体验设计

   【等待期间】
   - 进度条：显示"正在解析日志..." → "AI分析中..." → "生成报告中..."
   - 实时日志：显示当前处理步骤（类似Docker构建日志）
   - 取消按钮：允许用户中途取消
   - 后台处理：用户可离开页面，通过通知或历史记录查看结果

   【结果展示】
   - 飞行轨迹：用Mapbox/Leaflet展示3D轨迹，异常点高亮
   - 电池健康：ECharts折线图展示电压/温度变化
   - 建议优化：卡片式列表，带优先级标签
   - 导出功能：支持PDF导出、分享链接

   【错误处理】
   - 文件格式错误：友好提示，说明支持的格式
   - 分析失败：显示错误原因，提供重试按钮
   - 网络中断：自动重连SSE，或提示用户刷新

5. 用CC完成这个模块的工作流

   阶段一：方案设计
   Prompt：
   "我要为大疆无人机飞行数据管理平台添加AI智能分析模块。
   请帮我设计一个完整的技术方案，包括：
   1. 页面结构和路由设计
   2. 组件拆分方案
   3. 数据流和状态管理设计
   4. 文件上传和进度推送的技术选型
   5. AI分析结果的数据结构设计
   6. 错误处理方案
   要求输出为Markdown格式，每个部分包含代码示例。"

   阶段二：基础框架
   - 让CC生成页面骨架、路由配置、基础组件
   - 我审查代码，确保符合项目规范

   阶段三：核心功能
   - 文件上传组件（拖拽、进度、校验）
   - SSE连接hook（useSSE）
   - 分析结果展示组件

   阶段四：优化迭代
   - 性能优化（懒加载、虚拟列表）
   - 错误边界（Error Boundary）
   - 响应式适配

   每个阶段完成后我会：
   1. 本地运行测试
   2. 检查控制台是否有错误
   3. 用React DevTools检查渲染性能
   4. 确认后再进入下一阶段
```

---

### 问题7：Prompt示例与技巧

#### 我的回答（摘要）
- 把具体需求写上去，细要求加在最后
- 纠偏：告诉AI哪里错了让它自己修改，记录在记忆中
- Prompt技巧：精简需求、写清楚要求和内容
- 认为现在模型能力很强，prompt不需要太复杂

#### 薄弱点分析
- **Prompt结构过于简单** → 没有利用结构化prompt提升质量
- **"靠记忆纠偏"不可靠** → CC上下文有限，复杂项目会丢失约束
- 对**prompt engineering的最佳实践**了解不足
- 没有形成**可复用的prompt模板**

#### 优化后的回答

```
【我的Prompt风格】

我目前使用结构化的prompt模板，包含以下几个部分：

1. 角色设定（Role）
   "你是一位精通React和Node.js的全栈工程师，有5年开发经验。"

2. 背景信息（Context）
   "我们在开发TaskRPG项目，这是一个AI驱动的任务管理系统。
   技术栈：React + Node.js + PostgreSQL + DeepSeek API。"

3. 任务描述（Task）
   "请帮我实现一个任务计划生成功能：
   用户输入自然语言描述，AI将其拆解为可执行的任务列表。"

4. 具体要求（Requirements）
   - 功能要求：支持多级任务（任务→子任务）
   - 格式要求：返回JSON格式，包含title、description、subtasks
   - 约束条件：最多3层嵌套，子任务不超过5个
   - 错误处理：输入模糊时，AI应询问澄清而不是猜测

5. 输出格式（Output Format）
   "请输出：
   1. 实现思路说明
   2. 前端组件代码（React）
   3. 后端API代码（Node.js）
   4. 使用示例"

6. 示例（Examples）—— 对于复杂任务
   "例如，用户输入'准备考研'，AI应返回：
   {示例JSON}"

【纠偏技巧】

当AI输出不符合预期时，我会：

1. 精确描述问题
   ❌ "这个不对"
   ✅ "生成的任务列表中，subtasks字段是字符串数组，但要求是对象数组，
      每个对象包含title和completed字段。请修正。"

2. 提供上下文
   "在TaskRPG的/src/components/TaskList.jsx文件中，第45行的useEffect
   依赖数组缺少tasks，导致任务更新时不重新渲染。"

3. 要求解释
   "请解释为什么这里要用useCallback而不是普通函数？"
   （这能帮助我理解AI的思路，也便于学习）

【Prompt技巧总结】

| 技巧 | 说明 | 示例 |
|------|------|------|
| 角色设定 | 让AI进入特定角色 | "你是一位资深前端工程师" |
| 分步骤 | 复杂任务拆解 | "第一步...第二步..." |
| 约束条件 | 明确限制 | "不要使用第三方库" |
| 输出格式 | 指定返回形式 | "用Markdown表格输出" |
| 少样本示例 | 给AI参考 | "例如：..." |
| 反向约束 | 告诉AI不要做什么 | "不要生成CSS，样式已存在" |

【我的认知更新】

虽然模型能力在变强，但好的prompt仍然能显著提升输出质量：
- 结构化prompt减少AI的"自由发挥"，降低出错概率
- 清晰的约束条件避免反复纠偏，节省时间
- 示例（few-shot）对格式要求严格的场景特别有效

我正在学习更高级的prompt技巧，如Chain-of-Thought、ReAct模式等，
希望在Agent开发中应用。
```

---

### 问题8：智能体与前端的结合 + AI Coding未来趋势

#### 我的回答（摘要）
- 智能体可能需要在前端展示，前端是展示平台
- 未来前端基本都是用AI写，画好页面用AI生成，很快很便捷
- 前端结构性强、基本在调整，用AI更方便

#### 薄弱点分析
- **观点过于片面** → "前端基本都是用AI写"忽略了复杂场景
- **缺少深度思考** → 没有分析AI Coding的边界和局限性
- **没有结合自己的研究方向** → 智能体+前端可以讲得更深入
- **缺少对大疆业务的思考** → 没有联系岗位实际

#### 优化后的回答

```
【智能体与前端的结合】

我的研究方向是智能体和跨领域AI，我认为两者的结合点远不止"展示"：

1. 智能体即界面（Agent as UI）
   - 传统前端：固定界面，用户点击操作
   - Agent前端：对话式界面，AI理解意图后动态生成界面
   - 例子：用户说"帮我看看上周的飞行数据"，AI自动调取数据、
     生成图表、展示分析结果——界面是根据需求动态构建的

2. 前端作为Agent的"手脚"
   - Agent有推理能力，但需要前端来"执行"和"呈现"
   - Tool Calling的可视化：前端展示Agent调用了哪些工具、
     执行了什么操作、结果如何
   - 例子：TaskRPG中，AI决定"增加智力属性"，前端实时展示
     属性变化动画，让用户感知AI的决策

3. 人机协作界面
   - 不是完全替代，而是增强：AI生成初稿，人类审核修改
   - 前端需要提供"可编辑的AI输出"：比如AI生成的任务列表，
     用户可以拖拽调整、修改内容
   - 反馈回路：用户的修改作为训练数据，优化AI后续输出

【AI Coding改变前端开发的趋势】

我认为未来3-5年，前端开发会呈现以下变化：

1. 开发模式转变
   - 从"手写代码"到"AI辅助生成 + 人工审核调优"
   - 开发者角色从"编码者"转向"架构设计者"和"质量把控者"
   - 低代码/无代码平台会借助AI变得更强大

2. 但不会完全替代
   - 复杂交互逻辑：AI生成的基础代码没问题，但复杂的业务逻辑、
     性能优化仍需人工
   - 设计系统：组件库的一致性、可访问性（a11y）、跨端适配
   - 创新性UI：AI擅长模式复用，不擅长创新设计

3. 对大疆这类硬件公司的特殊意义
   - 大疆有复杂的硬件-软件协同场景（飞控参数、传感器数据、
     实时视频流等），这类前端开发需要深厚的领域知识
   - AI Coding可以帮助快速搭建原型，但生产级代码仍需工程师
     理解硬件协议、性能约束、安全要求

4. 我的定位
   - 短期：用AI Coding工具提升效率，快速交付功能
   - 中期：深入理解AI生成代码的原理，做到"知其然更知其所以然"
   - 长期：成为"AI+前端"的复合型人才，既能用好AI工具，
     又能在关键时刻做技术决策和质量把控

【总结】

AI Coding是强大的工具，但工具的使用者决定了上限。
我希望在这个岗位上，既能发挥AI Coding的效率优势，
又能通过实际项目积累不可替代的工程经验。
```

---

## 二、需要补充的知识点

### 1. React核心概念

#### 1.1 状态管理

**useState**
```jsx
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>+1</button>
    </div>
  );
}
```

**useReducer（复杂状态）**
```jsx
import { useReducer } from 'react';

const initialState = { count: 0 };

function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { count: state.count + 1 };
    case 'decrement':
      return { count: state.count - 1 };
    default:
      throw new Error();
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, initialState);
  
  return (
    <div>
      Count: {state.count}
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
    </div>
  );
}
```

**Context（跨组件共享状态）**
```jsx
import { createContext, useContext, useState } from 'react';

const ThemeContext = createContext(null);

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function ThemedButton() {
  const { theme, setTheme } = useContext(ThemeContext);
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Current: {theme}
    </button>
  );
}
```

#### 1.2 副作用处理

**useEffect**
```jsx
import { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    // 组件挂载或userId变化时执行
    fetchUser(userId).then(data => setUser(data));
    
    // 清理函数：组件卸载或依赖变化前执行
    return () => {
      // 取消请求、清除定时器等
    };
  }, [userId]); // 依赖数组
  
  return <div>{user?.name}</div>;
}
```

#### 1.3 性能优化

**React.memo（避免不必要的重渲染）**
```jsx
import { memo } from 'react';

const ExpensiveComponent = memo(function ExpensiveComponent({ data }) {
  // 只有data变化时才重新渲染
  return <div>{/* 复杂渲染 */}</div>;
});
```

**useMemo / useCallback**
```jsx
import { useMemo, useCallback } from 'react';

function Parent({ items }) {
  // 缓存计算结果
  const sortedItems = useMemo(() => {
    return items.sort((a, b) => a.price - b.price);
  }, [items]);
  
  // 缓存函数引用
  const handleClick = useCallback((id) => {
    console.log('Clicked:', id);
  }, []);
  
  return <Child items={sortedItems} onClick={handleClick} />;
}
```

---

### 2. Vue vs React 核心差异

| 特性 | Vue 3 | React |
|------|-------|-------|
| **响应式原理** | Proxy-based 响应式系统 | 显式状态更新（useState） |
| **模板语法** | 模板（HTML-like） | JSX（JavaScript） |
| **状态管理** | ref/reactive + Pinia | useState/useReducer + Redux/Zustand/Context |
| **计算属性** | computed | useMemo |
| **侦听器** | watch/watchEffect | useEffect |
| **组件通信** | props/emit, provide/inject | props/callback, Context |
| **生命周期** | onMounted/onUnmounted等 | useEffect |
| **双向绑定** | v-model | 受控组件（value + onChange） |

**Vue 组合式 API 示例**
```vue
<script setup>
import { ref, computed, watch, onMounted } from 'vue';

const count = ref(0);
const double = computed(() => count.value * 2);

watch(count, (newVal) => {
  console.log('Count changed:', newVal);
});

onMounted(() => {
  console.log('Component mounted');
});

function increment() {
  count.value++;
}
</script>

<template>
  <div>
    <p>Count: {{ count }}</p>
    <p>Double: {{ double }}</p>
    <button @click="increment">+1</button>
  </div>
</template>
```

---

### 3. 前端工程实践

#### 3.1 文件上传

```jsx
function FileUpload() {
  const [progress, setProgress] = useState(0);
  
  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const xhr = new XMLHttpRequest();
    
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        setProgress((e.loaded / e.total) * 100);
      }
    };
    
    xhr.onload = () => {
      const response = JSON.parse(xhr.responseText);
      console.log('Upload complete:', response);
    };
    
    xhr.open('POST', '/api/upload');
    xhr.send(formData);
  };
  
  return (
    <div>
      <input 
        type="file" 
        onChange={(e) => handleUpload(e.target.files[0])}
      />
      <progress value={progress} max={100} />
    </div>
  );
}
```

#### 3.2 SSE（Server-Sent Events）实时推送

```jsx
function useSSE(url) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  
  useEffect(() => {
    const eventSource = new EventSource(url);
    
    eventSource.onopen = () => setConnected(true);
    
    eventSource.onmessage = (event) => {
      const parsed = JSON.parse(event.data);
      setData(parsed);
    };
    
    eventSource.onerror = () => {
      setConnected(false);
      eventSource.close();
    };
    
    return () => eventSource.close();
  }, [url]);
  
  return { data, connected };
}

// 使用
function AnalysisProgress({ taskId }) {
  const { data, connected } = useSSE(`/api/analysis/${taskId}/progress`);
  
  return (
    <div>
      <div>Status: {connected ? 'Connected' : 'Disconnected'}</div>
      <div>Progress: {data?.progress}%</div>
      <div>Step: {data?.currentStep}</div>
    </div>
  );
}
```

#### 3.3 前端性能优化清单

```
□ 代码分割（Code Splitting）
  - React.lazy + Suspense
  - 路由级分割
  
□ 资源优化
  - 图片：WebP格式、懒加载、响应式图片
  - 字体：font-display: swap、子集化
  - JS/CSS：压缩、Tree Shaking
  
□ 缓存策略
  - HTTP缓存头（Cache-Control）
  - Service Worker（PWA）
  - 本地存储（localStorage/IndexedDB）
  
□ 渲染优化
  - 虚拟列表（react-window/react-virtualized）
  - 防抖/节流（搜索、滚动）
  - 骨架屏（Skeleton Screen）
  
□ 网络优化
  - CDN加速
  - HTTP/2 或 HTTP/3
  - 预加载关键资源（preload/prefetch）
```

---

### 4. Prompt Engineering 最佳实践

#### 4.1 结构化Prompt模板

```markdown
# 角色（Role）
你是一位[具体角色]，拥有[相关经验]。

# 背景（Context）
- 项目：[项目名称]
- 技术栈：[技术栈]
- 当前问题：[问题描述]

# 任务（Task）
[具体要做什么]

# 要求（Requirements）
## 功能要求
- [要求1]
- [要求2]

## 技术要求
- [约束1]
- [约束2]

## 格式要求
- [输出格式]

# 示例（Examples）
## 输入
[示例输入]

## 输出
[示例输出]

# 注意事项
- [注意1]
- [注意2]
```

#### 4.2 常用技巧

| 技巧 | 用法 | 效果 |
|------|------|------|
| Chain-of-Thought | "请一步一步思考" | 提升推理任务准确率 |
| Few-shot | 提供2-3个示例 | 让AI理解期望的输出格式 |
| Role-playing | "你是一位资深工程师" | 提升专业性和准确性 |
| Constraints | "不要使用第三方库" | 限制AI的发挥范围 |
| Output format | "用JSON格式返回" | 获得结构化输出 |
| Self-correction | "检查你的答案是否有错误" | 让AI自我纠错 |

#### 4.3 针对代码生成的Prompt优化

```markdown
# 代码生成Prompt示例

你是一位精通React和TypeScript的前端工程师。

请帮我实现一个[功能名称]组件。

## 背景
- 项目使用React 18 + TypeScript + Tailwind CSS
- 状态管理使用Zustand
- 组件库使用shadcn/ui

## 功能需求
1. [需求1]
2. [需求2]
3. [需求3]

## 技术要求
1. 使用TypeScript，定义完整的类型
2. 使用React Hooks，避免类组件
3. 组件要可复用，props接口清晰
4. 添加JSDoc注释
5. 处理loading和error状态
6. 遵循a11y规范

## 输出格式
请输出：
1. 组件代码（完整的.tsx文件）
2. 类型定义
3. 使用示例
4. 测试用例（React Testing Library）

## 示例
[如果有参考实现，贴在这里]
```

---

### 5. LangChain Tool Calling 深入理解

```python
from langchain.tools import BaseTool, StructuredTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# 1. 定义工具参数模型
class AddAttributeInput(BaseModel):
    attribute_type: str = Field(description="属性类型: strength/intelligence/agility/vitality")
    value: int = Field(description="增加数值")
    reason: str = Field(description="增加原因")

# 2. 定义工具函数
def add_attribute(attribute_type: str, value: int, reason: str) -> str:
    """增加用户属性"""
    # 实际的数据库操作
    # db.update_attribute(attribute_type, value)
    return f"成功增加 {attribute_type} +{value}，原因：{reason}"

# 3. 创建工具
attribute_tool = StructuredTool.from_function(
    func=add_attribute,
    name="add_attribute",
    description="当用户完成任务时，调用此工具增加对应属性",
    args_schema=AddAttributeInput,
)

# 4. 创建Agent
tools = [attribute_tool]
llm = ChatOpenAI(model="gpt-4")

# 5. 定义System Prompt
system_prompt = """你是一位任务分析助手。

当用户完成任务时，你需要：
1. 分析任务内容，判断主要锻炼哪种能力
2. 调用add_attribute工具增加对应属性

属性映射规则：
- 体力相关（运动、健身、体力劳动）→ strength
- 学习相关（阅读、编程、研究）→ intelligence  
- 速度/灵活相关（跑步、球类运动）→ agility
- 耐力/健康相关（长跑、冥想）→ vitality

注意：
- 必须调用工具，不要只返回文本
- 给出明确的reason说明判断依据
"""

# 6. 执行
agent = create_openai_tools_agent(llm, tools, system_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

result = agent_executor.invoke({"input": "我今天跑了5公里"})
print(result)
```

---

### 6. Docker部署基础

```dockerfile
# Dockerfile (前端)
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

```dockerfile
# Dockerfile (后端)
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/taskrpg
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=taskrpg

volumes:
  postgres_data:
```

---

### 7. 浏览器调试工具使用

#### 7.1 Chrome DevTools 常用功能

| 面板 | 功能 | 使用场景 |
|------|------|----------|
| Elements | 查看/修改DOM和CSS | 调试样式问题 |
| Console | 执行JS、查看日志 | 调试逻辑、测试代码 |
| Network | 监控网络请求 | 调试API、分析加载性能 |
| Performance | 性能分析 | 找出卡顿原因 |
| Application | 查看存储、Service Worker | 调试缓存、PWA |
| Lighthouse | 性能评分 | 生成优化报告 |

#### 7.2 React DevTools

```
□ Components面板
  - 查看组件树结构
  - 检查组件props和state
  - 查看组件渲染次数（Highlight updates）
  
□ Profiler面板
  - 记录渲染性能
  - 找出渲染瓶颈
  - 分析commit时间
```

#### 7.3 快速定位HTML结构问题

```javascript
// 在Console中执行
// 1. 检查未闭合标签（简化版）
$$('*').forEach(el => {
  const html = el.outerHTML;
  const open = (html.match(/<div/g) || []).length;
  const close = (html.match(/<\/div>/g) || []).length;
  if (open !== close) console.log('可能未闭合:', el);
});

// 2. 使用W3C验证器
// https://validator.w3.org/

// 3. 使用ESLint + jsx-a11y插件
// 自动检查JSX结构问题
```

---

## 三、学习路线建议

### 短期（1-2周）
- [ ] 系统学习React Hooks（useState/useEffect/useMemo/useCallback/useReducer/Context）
- [ ] 了解Zustand或Redux Toolkit状态管理
- [ ] 学习Chrome DevTools和React DevTools的高级用法
- [ ] 整理自己的Prompt模板库

### 中期（1个月）
- [ ] 用React重构TaskRPG的一个小模块，实践所学
- [ ] 学习TypeScript基础，给TaskRPG添加类型
- [ ] 了解Next.js或Vite等现代前端工具链
- [ ] 学习前端性能优化的系统方法

### 长期（持续）
- [ ] 深入理解AI Agent架构（ReAct、Plan-and-Execute等）
- [ ] 学习系统设计和架构知识
- [ ] 关注前端新技术（RSC、Server Components等）
- [ ] 积累大疆相关业务领域知识（无人机、机器人等）

---

> 文档生成时间：2026/06/06  
> 用途：大疆AI实习生-前端开发（AI Coding）面试复盘与知识补充

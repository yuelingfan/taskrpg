"""TaskRPG Agent 定义（集成层级记忆 + 自我反思）"""
import os
from sqlalchemy.orm import Session
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import SQLChatMessageHistory

from .tools import build_tools
from .deepseek_chat import DeepSeekChat
from .user_profiler import generate_user_profile, format_profile_for_prompt
from database import DATABASE_URL
from memory.memory_manager import MemoryManager


SYSTEM_PROMPT_TEMPLATE = """你是 TaskRPG 的智能任务导师，帮助用户管理日常任务，用 RPG 游戏的风格与用户互动。

你的能力：
1. 查看用户的任务列表（list_user_tasks）
2. 查看某个任务的详情（get_task_detail）
3. 为用户创建新任务（create_user_task）
4. 帮用户完成任务（complete_user_task）
5. 删除任务（delete_user_task）
6. 查看用户等级和属性（get_user_stats）
7. 解析用户的自然语言意图（parse_task_intent）
8. 创建长期计划，自动拆解为阶段和任务（create_plan）
9. 查看计划进度（get_plan_progress）
10. 查看用户的计划列表（get_user_plans）

交互风格：
- 像 RPG 游戏中的导师一样，鼓励用户
- 用中文回复，语气友好但有代入感
- 提到经验值、等级、属性时用游戏化语言

规则：
- 【关键区分】判断用户说的是"单个具体任务"还是"一个整体大目标"：
  - 单个任务（如"明天去跑步"、"写周报"）→ 调用 create_user_task
  - 整体目标（如"我要考研"、"准备面试"、"减肥"、"学Python"）→ 调用 create_plan 拆解为带时间节点的小任务
- 用户提到"做完了/完成了..."时，先查询任务列表找到对应任务，然后调用 complete_user_task
- 用户说"删除/删掉/去掉...任务"时，先查询任务列表找到对应任务，然后调用 delete_user_task
- 用户询问进度时，调用 list_user_tasks 或 get_plan_progress 查看
- 使用 create_plan 时，必须做到：
  1. 把用户的大目标拆成多个具体小任务（不是笼统的阶段名）
  2. 每个小任务分配明确的 deadline（格式：YYYY-MM-DD），按时间顺序排列
  3. stages_json 中的每个 task 都要包含 title + deadline
  4. 示例：{"name": "第1周", "tasks": [{"title": "背完高频词汇", "deadline": "2026-05-26"}]}
  5. 创建后告知用户计划总览、各阶段时间和任务清单
- 如果工具返回 [ERROR:xxx] 错误信息，分析原因并尝试修正（如参数修正、换用工具、分步执行）
- 不确定用户意图时，可以追问澄清

个性化建议规则（基于用户画像）：
- 如果用户完成率低（<50%），任务建议更简单（低EXP），多鼓励
- 如果用户完成率高（>80%），可以推荐高难度任务或挑战
- 优先推荐用户偏好类型的任务（画像中的类型分布）
- 考虑用户活跃时段安排任务截止时间
- 如果用户偏好"计划型"，多推荐阶段性目标；如果偏好"单线作战"，推荐单个任务

{memory_context}

{user_profile}
"""


def get_session_history(session_id: str):
    """获取指定会话的历史记录"""
    return SQLChatMessageHistory(session_id=session_id, connection=DATABASE_URL)


class TaskRPGAgent:
    """带层级记忆 + 自我反思的 TaskRPG Agent"""

    def __init__(self, db: Session, user_id: int, session_id: str):
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self.memory_manager = MemoryManager(user_id)
        self.message_history = SQLChatMessageHistory(session_id=session_id, connection=DATABASE_URL)

        # 构建 LLM 和工具
        self.llm = DeepSeekChat(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        )
        self.tools = build_tools(db, user_id)

        # 构建 Agent（prompt 会在 invoke 时动态组装）
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=True,  # 启用中间步骤返回，用于错误检测
        )

    def _build_system_prompt(self, user_input: str) -> str:
        """构建带层级记忆的 system prompt（包含常规记忆 + 反思记忆 + 用户画像）"""
        # 1. 查询常规层级记忆
        memories = self.memory_manager.retrieve_memories(user_input, max_per_category=3)
        memory_context = self.memory_manager.format_memories_for_prompt(memories)

        # 2. 额外查询反思/错误经验记忆（避免反复犯错）
        reflection_query = f"错误 失败 反思 {user_input}"
        reflection_memories = self.memory_manager.retrieve_memories(reflection_query, max_per_category=2)
        reflection_context = self.memory_manager.format_memories_for_prompt(reflection_memories)

        # 3. 生成统计画像
        profile = generate_user_profile(self.db, self.user_id)
        user_profile = format_profile_for_prompt(profile)

        # 4. 合并记忆上下文
        sections = []
        if memory_context:
            sections.append(memory_context)
        if reflection_context:
            # 去掉外层标记，加上错误经验标题
            lines = reflection_context.split("\n")
            filtered = [l for l in lines if l.strip() and "=== 记忆结束 ===" not in l and "=== 用户相关历史记忆 ===" not in l]
            if filtered:
                sections.append("\n=== 历史错误经验（避免重蹈覆辙） ===\n" + "\n".join(filtered))

        full_context = "\n".join(sections) if sections else "（暂无相关历史记忆）"

        return SYSTEM_PROMPT_TEMPLATE.replace("{memory_context}", full_context).replace("{user_profile}", user_profile)

    def _detect_failed_tools(self, result: dict) -> list:
        """检测 intermediate_steps 中是否有工具执行失败
        返回: [{"tool": 工具名, "error": 错误信息}, ...]
        """
        failed = []
        steps = result.get("intermediate_steps", [])
        for step in steps:
            if len(step) < 2:
                continue
            action, observation = step[0], step[1]
            if isinstance(observation, str) and "[ERROR:" in observation:
                tool_name = getattr(action, "tool", "unknown")
                # 提取错误信息（去掉 [ERROR:xxx] 前缀）
                error_msg = observation.split("]", 1)[1].strip() if "]" in observation else observation
                failed.append({"tool": tool_name, "error": error_msg, "raw": observation})
        return failed

    def _reflect_on_failure(self, user_input: str, failed_tools: list, previous_reflections: list) -> str:
        """调用 LLM 进行反思，分析失败原因并给出修正策略"""
        reflections_str = "\n".join([f"- {r}" for r in previous_reflections]) if previous_reflections else "无"

        failed_info = "\n".join([
            f"- 工具：{f['tool']}，错误：{f['error']}" for f in failed_tools
        ])

        prompt = f"""你是 TaskRPG Agent 的自我反思模块。Agent 在执行用户请求时遇到了工具调用失败，请分析原因并给出修正策略。

用户原始请求：{user_input}

失败的工具调用：
{failed_info}

之前的反思（如有）：
{reflections_str}

请输出简洁的反思（不超过80字）：
1. 失败原因分析
2. 下次执行时应如何修正（如：参数修正、改用其他工具、先做什么再做什么）

直接输出反思内容，不要加标题："""

        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            return f"反思生成失败：{str(e)}。建议检查参数后重试。"

    def _save_success_memory(self, original_input: str, result: dict):
        """保存成功的执行记录到记忆和对话历史"""
        output = result.get("output", "")

        # 保存到长期记忆
        self.memory_manager.add_memory(
            content=f"用户说：{original_input}",
            source="chat",
            tags=["user_input"],
        )
        self.memory_manager.add_memory(
            content=f"Agent回复：{output[:200]}",
            source="chat",
            tags=["agent_response"],
        )

        # 保存到对话历史（用于后续上下文）
        self.message_history.add_user_message(original_input)
        self.message_history.add_ai_message(output)

    def invoke(self, user_input: str) -> dict:
        """执行 Agent，自动注入层级记忆 + 自我反思 + 自动重试

        执行流程：
        1. 构建带记忆的 system prompt
        2. 执行 Agent
        3. 检测是否有工具调用失败
        4. 如果失败 → LLM 反思 → 保存反思到记忆 → 重试（最多3次）
        5. 如果成功 → 保存到记忆和历史 → 返回结果
        """
        max_attempts = 3
        reflection_notes = []
        original_input = user_input
        last_result = None

        for attempt in range(max_attempts):
            # 1. 构建带记忆的 system prompt
            system_prompt = self._build_system_prompt(original_input)

            # 如果有之前的反思，追加到 system prompt
            if reflection_notes:
                note_text = "\n".join([f"{i + 1}. {r}" for i, r in enumerate(reflection_notes)])
                system_prompt += f"\n\n【之前尝试的反思】\n{note_text}\n请注意以上问题，避免重复犯错。"

            # 2. 获取对话历史（使用原始历史，不包含之前失败尝试的交互）
            history = self.message_history.messages

            # 3. 执行 Agent
            result = self.executor.invoke({
                "system_prompt": system_prompt,
                "history": history,
                "input": original_input,
            })
            last_result = result

            # 4. 检测是否有工具执行失败
            failed_tools = self._detect_failed_tools(result)

            if not failed_tools:
                # 成功！保存对话到历史和记忆，然后返回
                self._save_success_memory(original_input, result)
                return result

            # --- 工具执行失败，触发反思 ---

            if attempt < max_attempts - 1:
                # 生成反思
                reflection = self._reflect_on_failure(original_input, failed_tools, reflection_notes)
                reflection_notes.append(reflection)

                # 保存反思到长期记忆（避免反复犯错的关键）
                self.memory_manager.add_memory(
                    content=(
                        f"错误反思：处理「{original_input}」时，"
                        f"工具「{failed_tools[0]['tool']}」报错：{failed_tools[0]['error']}。"
                        f"反思结论：{reflection}"
                    ),
                    source="reflection",
                    tags=["error_reflection", failed_tools[0]["tool"]],
                )

                print(f"[TaskRPGAgent] 第{attempt + 1}次尝试失败，反思：{reflection[:60]}...")
            else:
                # 最后一次尝试也失败了
                final_reflection = self._reflect_on_failure(original_input, failed_tools, reflection_notes)
                reflection_notes.append(final_reflection)

                self.memory_manager.add_memory(
                    content=(
                        f"错误反思（最终失败）：处理「{original_input}」，"
                        f"经过{max_attempts}次尝试仍未成功。"
                        f"最后错误：{failed_tools[0]['error']}。反思：{final_reflection}"
                    ),
                    source="reflection",
                    tags=["error_reflection", "failed", failed_tools[0]["tool"]],
                )

                print(f"[TaskRPGAgent] 最终失败，已保存反思到记忆")

                # 最终失败也要保存到对话历史
                self._save_success_memory(original_input, result)
                return result

        return last_result if last_result else {"output": "执行失败，请稍后重试"}


def build_agent(db: Session, user_id: int, session_id: str) -> TaskRPGAgent:
    """构建带层级记忆 + 自我反思的 Agent"""
    return TaskRPGAgent(db, user_id, session_id)

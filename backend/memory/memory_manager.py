"""Memory Manager Agent — 负责记忆的分类、整理、归档"""
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .memory_store import MemoryStore, MemoryEntry


SYSTEM_PROMPT_CLASSIFY = """你是 TaskRPG 的记忆分类专家。你的任务是把用户的记忆/对话内容分类归档。

分类规则：
1. 先判断这条记忆属于哪个大类（如：健身、学习、工作、生活、社交、情绪、饮食等）
2. 如果是新类型，创建新分类
3. 给出分类理由

输出格式（严格 JSON）：
{
  "category": "分类名称",
  "reason": "分类理由",
  "is_new_category": false
}"""


SYSTEM_PROMPT_TIME_GRANULARITY = """你是时间管理专家。根据记忆的数量和时间跨度，决定如何划分时间粒度。

规则：
- 记忆少（<10条）：不分块，统一放"近期"
- 记忆中等（10-50条）：按月分块（2024-01, 2024-02）
- 记忆多（>50条）：按季度分块（2024-Q1, 2024-Q2）
- 时间跨度大（>1年）：按年+季度分块

输出格式（严格 JSON）：
{
  "granularity": "daily/weekly/monthly/quarterly/yearly",
  "blocks": {
    "2024-Q1": ["memory_id_1", "memory_id_2"],
    "2024-Q2": ["memory_id_3"]
  },
  "reason": "划分理由"
}"""


SYSTEM_PROMPT_SUMMARIZE = """你是记忆总结专家。根据一类记忆的内容，生成简洁的总览描述。

要求：
- 不超过50字
- 突出用户的核心目标和当前状态
- 语气客观

输入：一组同类记忆
输出：直接输出总结文本，不要 JSON"""


SYSTEM_PROMPT_QUERY_ROUTE = """你是记忆查询路由专家。根据用户的问题，判断应该查询哪些分类的记忆。

规则：
1. 先看问题涉及的主题
2. 返回最相关的1-3个分类
3. 给出相关性评分（0-1）

输入格式：
问题：{query}
可用分类：{categories}

输出格式（严格 JSON）：
{
  "relevant_categories": [
    {"category": "健身", "relevance": 0.9, "reason": "用户问健身计划"}
  ],
  "needs_detail": true
}"""


class MemoryManager:
    """记忆管理器 — 负责分类、整理、归档、查询路由"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.store = MemoryStore(user_id)
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            max_tokens=500,
        )

    def _parse_json_response(self, content: str) -> dict:
        """解析 LLM 的 JSON 响应"""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        return json.loads(content)

    # ── 核心功能：分类 ──────────────────────────────

    def classify_memory(self, content: str) -> Tuple[str, bool]:
        """对新记忆进行分类，返回 (分类名, 是否新分类)"""
        existing_categories = self.store.get_categories()
        categories_str = ", ".join(existing_categories) if existing_categories else "暂无分类"

        prompt = f"""{SYSTEM_PROMPT_CLASSIFY}

现有分类：{categories_str}

新记忆内容：
{content}

请输出 JSON："""

        try:
            response = self.llm.invoke(prompt)
            result = self._parse_json_response(response.content)
            category = result.get("category", "其他")
            is_new = result.get("is_new_category", False)

            if is_new or category not in existing_categories:
                self.store.create_category(category, description=result.get("reason", ""))
                is_new = True

            return category, is_new
        except Exception as e:
            print(f"[MemoryManager] Classify failed: {e}, fallback to '其他'")
            return "其他", False

    def determine_time_block(self, category: str, memory_time: datetime) -> str:
        """根据分类的时间粒度决定存储到哪个时间块"""
        summary = self.store.get_summary()
        cat_info = summary.get(category, {})
        granularity = cat_info.get("time_granularity", "auto")

        if granularity == "auto":
            # 根据记忆数量自动决定
            count = cat_info.get("total_memories", 0)
            if count < 10:
                return "近期"
            elif count < 50:
                return memory_time.strftime("%Y-%m")
            else:
                quarter = (memory_time.month - 1) // 3 + 1
                return f"{memory_time.year}-Q{quarter}"

        if granularity == "daily":
            return memory_time.strftime("%Y-%m-%d")
        elif granularity == "weekly":
            return f"{memory_time.year}-W{memory_time.isocalendar()[1]}"
        elif granularity == "monthly":
            return memory_time.strftime("%Y-%m")
        elif granularity == "quarterly":
            quarter = (memory_time.month - 1) // 3 + 1
            return f"{memory_time.year}-Q{quarter}"
        elif granularity == "yearly":
            return str(memory_time.year)

        return "近期"

    def add_memory(self, content: str, source: str = "chat", tags: List[str] = None):
        """添加一条记忆（自动分类+归档）"""
        # 1. 分类
        category, is_new = self.classify_memory(content)

        # 2. 确定时间块
        now = datetime.now()
        time_block = self.determine_time_block(category, now)

        # 3. 创建记忆条目
        entry = MemoryEntry(
            id=str(uuid.uuid4())[:8],
            content=content,
            source=source,
            created_at=now.isoformat(),
            tags=tags or [],
            summary="",
        )

        # 4. 保存
        self.store.add_memory(entry, category, time_block)

        print(f"[MemoryManager] Memory added to [{category}/{time_block}]: {content[:30]}...")
        return category, time_block

    # ── 核心功能：查询路由 ──────────────────────────────

    def route_query(self, query: str) -> Tuple[List[Dict], bool]:
        """
        根据用户问题，路由到相关分类
        返回: (相关分类列表, 是否需要读取详细记忆)
        """
        summary = self.store.get_summary()
        if not summary:
            return [], False

        categories_str = "\n".join([
            f"- {cat}: {info.get('description', '无描述')} (共{info.get('total_memories', 0)}条)"
            for cat, info in summary.items()
        ])

        prompt = SYSTEM_PROMPT_QUERY_ROUTE.replace("{query}", query).replace("{categories}", categories_str)

        try:
            response = self.llm.invoke(prompt)
            result = self._parse_json_response(response.content)
            categories = result.get("relevant_categories", [])
            needs_detail = result.get("needs_detail", True)

            # 过滤掉不存在的分类
            valid_cats = [c for c in categories if c.get("category") in summary]
            return valid_cats, needs_detail
        except Exception as e:
            print(f"[MemoryManager] Route failed: {e}, fallback to all categories")
            # fallback: 返回所有分类
            return [{"category": cat, "relevance": 0.5} for cat in summary.keys()], True

    def retrieve_memories(self, query: str, max_per_category: int = 3) -> Dict[str, List[MemoryEntry]]:
        """
        检索与 query 相关的记忆
        返回: {分类: [记忆列表]}
        """
        categories, needs_detail = self.route_query(query)
        if not categories:
            return {}

        results = {}
        for cat_info in categories:
            category = cat_info["category"]
            relevance = cat_info.get("relevance", 0.5)

            if relevance < 0.3:  # 相关性太低跳过
                continue

            if needs_detail:
                # 读取该分类下所有时间块的详细记忆
                all_memories = self.store.get_all_detail_memories(category)
                # 简单按时间倒序取前 N 条（后续可替换为更智能的排序）
                results[category] = all_memories[-max_per_category:]
            else:
                # 只返回总览信息
                summary = self.store.get_summary().get(category, {})
                results[category] = [MemoryEntry(
                    id="summary",
                    content=summary.get("description", ""),
                    source="summary",
                    created_at=summary.get("latest_update", ""),
                )]

        return results

    def format_memories_for_prompt(self, memories_dict: Dict[str, List[MemoryEntry]]) -> str:
        """把检索到的记忆格式化成字符串，用于注入 Agent Prompt"""
        if not memories_dict:
            return ""

        lines = ["\n=== 用户相关历史记忆 ==="]
        for category, entries in memories_dict.items():
            lines.append(f"\n【{category}】")
            for e in entries:
                lines.append(f"  - {e.content}")
        lines.append("=== 记忆结束 ===\n")

        return "\n".join(lines)

    # ── 定期整理 ──────────────────────────────

    def consolidate_category(self, category: str):
        """整理某个分类的记忆（由定期任务调用）"""
        all_memories = self.store.get_all_detail_memories(category)
        if len(all_memories) < 5:
            return  # 记忆太少，不需要整理

        # 生成新的时间粒度建议
        memories_json = json.dumps([{"id": m.id, "content": m.content, "time": m.created_at} for m in all_memories], ensure_ascii=False)

        prompt = f"""{SYSTEM_PROMPT_TIME_GRANULARITY}

分类：{category}
共有 {len(all_memories)} 条记忆

记忆列表：
{memories_json}

请输出 JSON："""

        try:
            response = self.llm.invoke(prompt)
            result = self._parse_json_response(response.content)
            new_blocks = result.get("blocks", {})

            # 按新时间块重新组织
            organized = {}
            for block_name, memory_ids in new_blocks.items():
                block_memories = []
                for mid in memory_ids:
                    for m in all_memories:
                        if m.id == mid:
                            block_memories.append({
                                "id": m.id,
                                "content": m.content,
                                "source": m.source,
                                "created_at": m.created_at,
                                "tags": m.tags,
                                "summary": m.summary,
                            })
                organized[block_name] = block_memories

            self.store.consolidate_category(category, organized)

            # 更新分类总览
            granularity = result.get("granularity", "auto")
            self.store.update_category_summary(category, f"已整理，粒度：{granularity}", granularity)

            print(f"[MemoryManager] Consolidated [{category}]: {len(new_blocks)} blocks")
        except Exception as e:
            print(f"[MemoryManager] Consolidate failed for [{category}]: {e}")

    def consolidate_all(self):
        """整理所有分类"""
        categories = self.store.get_categories()
        for cat in categories:
            self.consolidate_category(cat)

    def summarize_category(self, category: str) -> str:
        """生成某分类的总览描述"""
        memories = self.store.get_all_detail_memories(category)
        if not memories:
            return ""

        contents = "\n".join([f"- {m.content}" for m in memories[-10:]])  # 取最近10条

        prompt = f"""{SYSTEM_PROMPT_SUMMARIZE}

分类：{category}
记忆内容：
{contents}

请输出总结："""

        try:
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            self.store.update_category_summary(category, summary)
            return summary
        except Exception as e:
            print(f"[MemoryManager] Summarize failed for [{category}]: {e}")
            return ""

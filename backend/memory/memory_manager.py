"""Memory Manager Agent — 负责记忆的分类、查询路由"""
import json
import os
from typing import List, Dict, Tuple

from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

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
    """记忆管理器 — 负责分类、查询路由"""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.store = MemoryStore(user_id, db)
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

    def classify_memory(self, summary: str) -> Tuple[str, bool]:
        """对新记忆进行分类，返回 (分类名, 是否新分类)"""
        existing_categories = self.store.get_categories()
        categories_str = ", ".join(existing_categories) if existing_categories else "暂无分类"

        prompt = f"""{SYSTEM_PROMPT_CLASSIFY}

现有分类：{categories_str}

新记忆内容：
{summary}

请输出 JSON："""

        try:
            response = self.llm.invoke(prompt)
            result = self._parse_json_response(response.content)
            category = result.get("category", "其他")
            is_new = result.get("is_new_category", False)
            return category, is_new
        except Exception as e:
            print(f"[MemoryManager] Classify failed: {e}, fallback to '其他'")
            return "其他", False

    def add_memory(self, speaker: str, summary: str):
        """添加一条记忆（自动分类 + 写入数据库）"""
        category, _ = self.classify_memory(summary)
        self.store.add_memory(category, speaker, summary)
        print(f"[MemoryManager] Memory added [{category}] {speaker}: {summary[:30]}...")
        return category

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

            if relevance < 0.3:
                continue

            if needs_detail:
                memories = self.store.get_memories(category=category, limit=max_per_category)
                results[category] = [
                    MemoryEntry(
                        id=m.id,
                        summary=m.summary,
                        speaker=m.speaker,
                        category=m.category,
                        created_at=m.created_at.isoformat() if m.created_at else "",
                    )
                    for m in memories
                ]
            else:
                summary_info = self.store.get_summary().get(category, {})
                results[category] = [MemoryEntry(
                    id="summary",
                    summary=summary_info.get("description", ""),
                    speaker="system",
                    category=category,
                    created_at=summary_info.get("latest_update", ""),
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
                lines.append(f"  - [{e.speaker}] {e.summary}")
        lines.append("=== 记忆结束 ===\n")

        return "\n".join(lines)

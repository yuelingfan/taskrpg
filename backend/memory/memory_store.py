"""记忆存储层 — 数据库版本

将记忆持久化到 PostgreSQL，替代原有的 JSON 文件存储。
每个记忆条目包含：时间、说话对象、对话内容的总结。
"""
from typing import List, Dict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models import Memory


@dataclass
class MemoryEntry:
    """单条记忆（供 MemoryManager 使用）"""
    id: int
    summary: str
    speaker: str
    category: str
    created_at: str


class MemoryStore:
    """基于数据库的记忆存储"""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def add_memory(self, category: str, speaker: str, summary: str) -> Memory:
        """添加一条记忆到数据库"""
        mem = Memory(
            user_id=self.user_id,
            category=category,
            speaker=speaker,
            summary=summary,
        )
        self.db.add(mem)
        self.db.commit()
        self.db.refresh(mem)
        return mem

    def get_categories(self) -> List[str]:
        """获取该用户所有分类（去重）"""
        rows = (
            self.db.query(Memory.category)
            .filter(Memory.user_id == self.user_id)
            .distinct()
            .all()
        )
        return [r[0] for r in rows if r[0]]

    def get_memories(self, category: str = None, limit: int = None) -> List[Memory]:
        """获取记忆列表，支持按分类过滤和数量限制"""
        query = (
            self.db.query(Memory)
            .filter(Memory.user_id == self.user_id)
            .order_by(Memory.created_at.desc())
        )
        if category:
            query = query.filter(Memory.category == category)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_total_memory_count(self) -> int:
        """获取该用户总记忆数"""
        return (
            self.db.query(Memory)
            .filter(Memory.user_id == self.user_id)
            .count()
        )

    def get_summary(self) -> Dict[str, dict]:
        """获取分类总览（替代原来的 summary.json）

        返回: {category: {"description": str, "total_memories": int, "latest_update": str}}
        """
        from sqlalchemy import func

        rows = (
            self.db.query(
                Memory.category,
                func.count(Memory.id).label("count"),
                func.max(Memory.created_at).label("latest"),
            )
            .filter(Memory.user_id == self.user_id)
            .group_by(Memory.category)
            .all()
        )

        return {
            cat: {
                "description": "",
                "total_memories": count,
                "latest_update": latest.isoformat() if latest else "",
                "time_granularity": "auto",
            }
            for cat, count, latest in rows
        }

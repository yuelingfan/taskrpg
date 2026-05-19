"""层级记忆存储层

存储结构:
memory_data/
├── summary.json              # 第一层：总览
│   {
│     "健身": {"description": "用户健身相关目标和进展", "total_memories": 5, "latest_update": "2024-01-15"},
│     "学习": {"description": "考研复习、技能学习", "total_memories": 8, "latest_update": "2024-01-14"},
│     ...
│   }
├── 健身/
│   ├── 2024-Q1.json         # 按时间分块
│   └── 2024-Q2.json
├── 学习/
│   ├── 2024-Q1.json
│   └── 近期.json
└── 其他/
    └── 未分类.json
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory_data")


@dataclass
class MemoryEntry:
    """单条记忆"""
    id: str
    content: str
    source: str  # 来源：chat / task / user_action
    created_at: str
    tags: List[str] = None
    summary: str = ""  # LLM 生成的摘要

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class CategorySummary:
    """分类总览"""
    description: str  # LLM 生成的分类描述
    total_memories: int
    latest_update: str
    time_granularity: str  # 时间粒度：daily/weekly/monthly/quarterly


class MemoryStore:
    """层级记忆存储"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.base_dir = os.path.join(MEMORY_DIR, f"user_{user_id}")
        self.summary_path = os.path.join(self.base_dir, "summary.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保目录存在"""
        os.makedirs(self.base_dir, exist_ok=True)
        if not os.path.exists(self.summary_path):
            self._save_summary({})

    def _save_summary(self, summary: Dict[str, dict]):
        """保存总览文件"""
        with open(self.summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    def _load_summary(self) -> Dict[str, dict]:
        """加载总览文件"""
        if not os.path.exists(self.summary_path):
            return {}
        with open(self.summary_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _category_dir(self, category: str) -> str:
        """获取分类目录"""
        d = os.path.join(self.base_dir, category)
        os.makedirs(d, exist_ok=True)
        return d

    def _detail_path(self, category: str, time_block: str) -> str:
        """获取详细文件路径"""
        return os.path.join(self._category_dir(category), f"{time_block}.json")

    def _load_detail(self, category: str, time_block: str) -> List[dict]:
        """加载详细记忆"""
        path = self._detail_path(category, time_block)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_detail(self, category: str, time_block: str, memories: List[dict]):
        """保存详细记忆"""
        path = self._detail_path(category, time_block)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)

    # ── 公开接口 ──────────────────────────────

    def get_summary(self) -> Dict[str, dict]:
        """获取总览（第一层）"""
        return self._load_summary()

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._load_summary().keys())

    def get_detail_blocks(self, category: str) -> List[str]:
        """获取某分类下的所有时间块"""
        cat_dir = self._category_dir(category)
        if not os.path.exists(cat_dir):
            return []
        files = [f.replace(".json", "") for f in os.listdir(cat_dir) if f.endswith(".json")]
        return sorted(files)

    def get_detail_memories(self, category: str, time_block: str) -> List[MemoryEntry]:
        """获取某分类某时间块的详细记忆"""
        raw = self._load_detail(category, time_block)
        return [MemoryEntry(**m) for m in raw]

    def get_all_detail_memories(self, category: str) -> List[MemoryEntry]:
        """获取某分类下的所有详细记忆"""
        all_memories = []
        for block in self.get_detail_blocks(category):
            all_memories.extend(self.get_detail_memories(category, block))
        return all_memories

    def add_memory(self, entry: MemoryEntry, category: str, time_block: str):
        """添加一条记忆到指定分类和时间块"""
        # 1. 保存详细记忆
        memories = self._load_detail(category, time_block)
        memories.append(asdict(entry))
        self._save_detail(category, time_block, memories)

        # 2. 更新总览
        summary = self._load_summary()
        if category not in summary:
            summary[category] = {
                "description": "",
                "total_memories": 0,
                "latest_update": entry.created_at,
                "time_granularity": "auto",
            }
        summary[category]["total_memories"] = summary[category].get("total_memories", 0) + 1
        summary[category]["latest_update"] = entry.created_at
        self._save_summary(summary)

    def update_category_summary(self, category: str, description: str, granularity: str = "auto"):
        """更新分类总览描述（由 MemoryManager 调用）"""
        summary = self._load_summary()
        if category in summary:
            summary[category]["description"] = description
            summary[category]["time_granularity"] = granularity
            self._save_summary(summary)

    def create_category(self, category: str, description: str = "", granularity: str = "auto"):
        """创建新分类"""
        summary = self._load_summary()
        if category not in summary:
            summary[category] = {
                "description": description,
                "total_memories": 0,
                "latest_update": datetime.now().isoformat(),
                "time_granularity": granularity,
            }
            self._save_summary(summary)
            # 创建默认时间块
            self._save_detail(category, "近期", [])

    def consolidate_category(self, category: str, new_blocks: Dict[str, List[dict]]):
        """整理归档：重新划分时间块（由 MemoryManager 调用）"""
        cat_dir = self._category_dir(category)
        # 删除旧文件
        for f in os.listdir(cat_dir):
            if f.endswith(".json"):
                os.remove(os.path.join(cat_dir, f))
        # 写入新时间块
        for block_name, memories in new_blocks.items():
            self._save_detail(category, block_name, memories)

    def get_total_memory_count(self) -> int:
        """获取总记忆数"""
        summary = self._load_summary()
        return sum(s.get("total_memories", 0) for s in summary.values())

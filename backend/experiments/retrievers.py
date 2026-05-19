"""三种记忆检索方案（纯 Python 实现，无需 PostgreSQL 中文配置）"""
import os
import time
from typing import List, Tuple

from experiments.test_cases import MEMORY_POOL


class BaseRetriever:
    """检索器基类"""
    name = "base"

    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        """返回 [(记忆文本, 相似度分数), ...]"""
        raise NotImplementedError

    def close(self):
        pass


class BaselineFTSRetriever(BaseRetriever):
    """方案1: 基础关键词匹配，直接用原始 query 中的每个字去匹配"""
    name = "baseline_fts"

    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        # 提取 query 中所有字（去重）
        query_chars = set(query)
        results = []

        for memory in MEMORY_POOL:
            # 计算 query 中有多少个字出现在记忆中
            matched = sum(1 for c in query_chars if c in memory)
            score = matched / len(query_chars) if query_chars else 0
            if score > 0:
                results.append((memory, score))

        # 按分数降序，取前 K
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]


class QueryExpansionRetriever(BaseRetriever):
    """方案2: LLM 扩展关键词 + 匹配"""
    name = "query_expansion"

    def __init__(self):
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            max_tokens=100,
        )

    def _expand_keywords(self, query: str) -> List[str]:
        """用 LLM 扩展关键词"""
        prompt = f"""把用户的问题扩展成3-5个最可能相关的关键词，用于搜索历史记忆。
规则：
- 包含同义词和相关概念
- 保留原始意图
- 只输出关键词，用逗号分隔，不要解释

用户输入：{query}
关键词："""
        try:
            response = self.llm.invoke(prompt)
            keywords = [k.strip() for k in response.content.split(",") if k.strip()]
            # 去重，原始词放最前面
            all_terms = list(dict.fromkeys([query] + keywords))
            return all_terms[:6]
        except Exception as e:
            print(f"  Keyword expansion failed: {e}")
            return [query]

    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        keywords = self._expand_keywords(query)

        results = []
        for memory in MEMORY_POOL:
            # 计算每个关键词与记忆的匹配度
            total_score = 0
            for i, kw in enumerate(keywords):
                # 原始 query 权重更高
                weight = 2.0 if i == 0 else 1.0
                # 计算关键词中多少字出现在记忆中
                matched = sum(1 for c in kw if c in memory)
                score = (matched / len(kw)) * weight if kw else 0
                total_score += score

            # 归一化
            avg_score = total_score / sum(2.0 if i == 0 else 1.0 for i in range(len(keywords)))
            if avg_score > 0:
                results.append((memory, avg_score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]


class VectorRetriever(BaseRetriever):
    """方案3: TF-IDF 向量检索（scikit-learn，无需外部模型/API）"""
    name = "vector"

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        self.np = np

        # 用 jieba 做中文分词（如果可用），否则按字分词
        try:
            import jieba
            def tokenizer(text):
                return list(jieba.cut(text))
        except ImportError:
            def tokenizer(text):
                return list(text)  # 按字分词

        self.vectorizer = TfidfVectorizer(
            tokenizer=tokenizer,
            token_pattern=None,  # 使用自定义 tokenizer
            lowercase=False,
        )

        # 拟合并转换记忆池
        self.memory_vectors = self.vectorizer.fit_transform(MEMORY_POOL)
        print(f"  Vector retriever (TF-IDF) loaded, vocab size: {len(self.vectorizer.vocabulary_)}")

    def search(self, query: str, limit: int = 5) -> List[Tuple[str, float]]:
        # 转换 query
        query_vec = self.vectorizer.transform([query])

        # 计算余弦相似度
        similarities = (self.memory_vectors @ query_vec.T).toarray().flatten()

        # 取 top K
        top_indices = similarities.argsort()[::-1][:limit]
        return [(MEMORY_POOL[i], float(similarities[i])) for i in top_indices]


# 统一的检索器注册表
RETRIEVERS = {
    "baseline": BaselineFTSRetriever,
    "expansion": QueryExpansionRetriever,
    "vector": VectorRetriever,
}

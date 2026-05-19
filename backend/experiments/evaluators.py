"""评估指标计算"""
import time
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """单个测试用例的评估结果"""
    query: str
    label: str
    retrieved: List[str]
    relevant: List[str]
    recall: float
    precision: float
    mrr: float
    latency_ms: float


def compute_metrics(
    retrieved: List[str],
    relevant: List[str],
    latency_ms: float,
    k: int = 5,
) -> Tuple[float, float, float, float]:
    """计算 Recall@K, Precision@K, MRR

    Returns: (recall, precision, mrr, latency)
    """
    relevant_set = set(relevant)
    retrieved_set = set(retrieved[:k])

    # Recall@K
    recall = len(relevant_set & retrieved_set) / len(relevant_set) if relevant_set else 0.0

    # Precision@K
    precision = len(relevant_set & retrieved_set) / len(retrieved_set) if retrieved_set else 0.0

    # MRR (Mean Reciprocal Rank)
    mrr = 0.0
    for i, item in enumerate(retrieved, 1):
        if item in relevant_set:
            mrr = 1.0 / i
            break

    return recall, precision, mrr, latency_ms


def evaluate_retriever(retriever, test_cases: List[dict], k: int = 5) -> Dict:
    """评估一个检索器在所有测试用例上的表现"""
    results = []
    all_recalls = []
    all_precisions = []
    all_mrrs = []
    all_latencies = []

    for case in test_cases:
        from experiments.test_cases import MEMORY_POOL
        relevant = [MEMORY_POOL[i] for i in case["relevant_indices"]]

        # 执行检索，计时
        start = time.perf_counter()
        raw_results = retriever.search(case["query"], limit=k)
        latency_ms = (time.perf_counter() - start) * 1000

        retrieved = [r[0] for r in raw_results]

        recall, precision, mrr, _ = compute_metrics(
            retrieved, relevant, latency_ms, k=k
        )

        results.append(EvaluationResult(
            query=case["query"],
            label=case.get("label", ""),
            retrieved=retrieved,
            relevant=relevant,
            recall=recall,
            precision=precision,
            mrr=mrr,
            latency_ms=latency_ms,
        ))

        all_recalls.append(recall)
        all_precisions.append(precision)
        all_mrrs.append(mrr)
        all_latencies.append(latency_ms)

    n = len(test_cases)
    return {
        "results": results,
        "summary": {
            f"Recall@{k}": round(sum(all_recalls) / n, 3),
            f"Precision@{k}": round(sum(all_precisions) / n, 3),
            "MRR": round(sum(all_mrrs) / n, 3),
            "Latency(ms)": round(sum(all_latencies) / n, 1),
            "Latency_P99(ms)": round(sorted(all_latencies)[int(n * 0.99)] if n > 1 else all_latencies[0], 1),
        },
    }


def print_detailed_results(eval_result: Dict, k: int = 5):
    """打印每个 case 的详细结果"""
    print(f"\n{'='*60}")
    print(f"Detailed Results (K={k})")
    print(f"{'='*60}")

    for r in eval_result["results"]:
        print(f"\n[{r.label}] Query: {r.query}")
        print(f"  Recall@{k}: {r.recall:.2f} | Precision@{k}: {r.precision:.2f} | MRR: {r.mrr:.2f} | Latency: {r.latency_ms:.0f}ms")
        print("  Retrieved:")
        for i, item in enumerate(r.retrieved, 1):
            mark = "[OK]" if item in r.relevant else "[MISS]"
            print(f"    {i}. {mark} {item}")
        if r.recall < 1.0:
            missed = [m for m in r.relevant if m not in r.retrieved]
            print(f"  Missed: {missed}")


def print_comparison(all_results: Dict[str, Dict], k: int = 5):
    """打印多方案对比表"""
    print(f"\n{'='*70}")
    print(f"Comparison Table (K={k})")
    print(f"{'='*70}")
    print(f"{'Method':<20} {'Recall@'+str(k):<12} {'Precision@'+str(k):<14} {'MRR':<8} {'Latency':<12}")
    print("-" * 70)

    for name, result in all_results.items():
        s = result["summary"]
        print(f"{name:<20} {s[f'Recall@{k}']:<12} {s[f'Precision@{k}']:<14} {s['MRR']:<8} {s['Latency(ms)']}ms")

    print(f"{'='*70}")

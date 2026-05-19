"""记忆检索实验主脚本

用法:
    python run_experiment.py --methods baseline,expansion --k 5
    python run_experiment.py --methods all --k 5 --detail
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量（API Key）
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from experiments.test_cases import TEST_CASES
from experiments.retrievers import RETRIEVERS
from experiments.evaluators import evaluate_retriever, print_detailed_results, print_comparison


def run_experiment(methods: list[str], k: int, detail: bool = False):
    """运行实验"""
    all_results = {}

    for method_name in methods:
        if method_name not in RETRIEVERS:
            print(f"Unknown method: {method_name}, skipping")
            continue

        RetrieverClass = RETRIEVERS[method_name]
        retriever = RetrieverClass()

        print(f"\nRunning {retriever.name}...")
        result = evaluate_retriever(retriever, TEST_CASES, k=k)
        all_results[retriever.name] = result

        s = result["summary"]
        print(f"  Recall@{k}: {s[f'Recall@{k}']}")
        print(f"  Precision@{k}: {s[f'Precision@{k}']}")
        print(f"  MRR: {s['MRR']}")
        print(f"  Latency: {s['Latency(ms)']}ms (P99: {s['Latency_P99(ms)']}ms)")

        if detail:
            print_detailed_results(result, k=k)

        retriever.close()

    # 打印对比表
    if len(all_results) > 1:
        print_comparison(all_results, k=k)

    # 打印失败案例分析
    if detail and len(all_results) > 0:
        print_failure_analysis(all_results, k=k)

    return all_results


def print_failure_analysis(all_results: dict, k: int = 5):
    """分析每个方案失败最多的 case"""
    print(f"\n{'='*70}")
    print("Failure Case Analysis (Top 3 per method)")
    print(f"{'='*70}")

    for name, result in all_results.items():
        failures = [r for r in result["results"] if r.recall < 1.0]
        if not failures:
            print(f"\n{name}: No failures!")
            continue

        print(f"\n{name}: {len(failures)} failure cases out of {len(result['results'])}")
        for r in failures[:3]:
            missed = [m for m in r.relevant if m not in r.retrieved]
            print(f"  [{r.label}] '{r.query}'")
            print(f"    Recall@{k}={r.recall:.2f}, Missed {len(missed)}/{len(r.relevant)} memories")


def main():
    parser = argparse.ArgumentParser(description="Memory Retrieval Experiment")
    parser.add_argument("--methods", default="baseline,expansion",
                        help="Comma-separated methods: baseline,expansion,vector or 'all'")
    parser.add_argument("--k", type=int, default=5, help="Top K results")
    parser.add_argument("--detail", action="store_true", help="Show detailed per-case results")

    args = parser.parse_args()

    if args.methods == "all":
        methods = ["baseline", "expansion", "vector"]
    else:
        methods = [m.strip() for m in args.methods.split(",")]

    print(f"Experiment config: methods={methods}, K={args.k}")
    run_experiment(methods, k=args.k, detail=args.detail)


if __name__ == "__main__":
    main()

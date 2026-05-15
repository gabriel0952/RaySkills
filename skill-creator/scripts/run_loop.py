#!/usr/bin/env python3
"""Description 優化迴圈：反覆測試與改善 skill description 直到達標或達到上限。

將 eval set 分成訓練集（60%）和測試集（40%），在訓練集上迭代改善，
以測試集分數選出最佳版本（避免過度擬合）。

用法：
    python -m scripts.run_loop \\
        --eval-set evals.json \\
        --skill-path . \\
        --model claude-sonnet-4-5 \\
        --max-iterations 5 \\
        --verbose
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

from scripts.improve_description import improve_description
from scripts.run_eval import find_project_root, run_eval
from scripts.utils import parse_skill_md


def split_eval_set(
    eval_set: list[dict], holdout: float, seed: int = 42
) -> tuple[list[dict], list[dict]]:
    """將 eval set 依 should_trigger 分層後，拆成訓練集與測試集。"""
    random.seed(seed)
    trigger = [e for e in eval_set if e["should_trigger"]]
    no_trigger = [e for e in eval_set if not e["should_trigger"]]
    random.shuffle(trigger)
    random.shuffle(no_trigger)

    n_trigger_test = max(1, int(len(trigger) * holdout))
    n_no_trigger_test = max(1, int(len(no_trigger) * holdout))

    test_set = trigger[:n_trigger_test] + no_trigger[:n_no_trigger_test]
    train_set = trigger[n_trigger_test:] + no_trigger[n_no_trigger_test:]
    return train_set, test_set


def _print_results(label: str, results: list[dict], elapsed: float = 0) -> None:
    """印出一組 eval 結果的摘要。"""
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    tp = sum(r["triggers"] for r in results if r["should_trigger"])
    pos_runs = sum(r["runs"] for r in results if r["should_trigger"])
    fp = sum(r["triggers"] for r in results if not r["should_trigger"])
    neg_runs = sum(r["runs"] for r in results if not r["should_trigger"])
    fn = pos_runs - tp
    tn = neg_runs - fp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

    time_str = f"（{elapsed:.1f}s）" if elapsed else ""
    print(
        f"  {label}: {passed}/{total} 通過 | "
        f"precision={precision:.0%} recall={recall:.0%} accuracy={accuracy:.0%} {time_str}",
        file=sys.stderr,
    )
    for r in results:
        status = "✅" if r["pass"] else "❌"
        direction = "↑" if r["should_trigger"] else "↓"
        print(
            f"    {status}{direction} [{r['triggers']}/{r['runs']}] {r['query'][:65]}",
            file=sys.stderr,
        )


def run_loop(
    eval_set: list[dict],
    skill_path: Path,
    description_override: str | None,
    num_workers: int,
    timeout: int,
    max_iterations: int,
    runs_per_query: int,
    trigger_threshold: float,
    holdout: float,
    model: str | None,
    verbose: bool,
    log_dir: Path | None = None,
) -> dict:
    """執行 eval + 改善迴圈，回傳最佳結果字典。"""
    project_root = find_project_root()
    name, original_description, content = parse_skill_md(skill_path)
    current_description = description_override or original_description

    # 分割訓練 / 測試集
    if holdout > 0 and len(eval_set) >= 4:
        train_set, test_set = split_eval_set(eval_set, holdout)
        if verbose:
            print(
                f"\n📊 Eval set 分割：{len(train_set)} 訓練、{len(test_set)} 測試（holdout={holdout}）",
                file=sys.stderr,
            )
    else:
        train_set = eval_set
        test_set = []
        if verbose:
            print(f"\n📊 Eval set 太小，使用全部 {len(eval_set)} 筆（不做 holdout）", file=sys.stderr)

    history: list[dict] = []
    exit_reason = "unknown"

    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"\n{'─'*60}", file=sys.stderr)
            print(f"迭代 {iteration}/{max_iterations}", file=sys.stderr)
            print(f"Description：{current_description[:100]}{'...' if len(current_description) > 100 else ''}", file=sys.stderr)

        # 訓練集 + 測試集一起跑（並行效率最高）
        all_queries = train_set + test_set
        t0 = time.time()
        all_results = run_eval(
            eval_set=all_queries,
            skill_name=name,
            description=current_description,
            num_workers=num_workers,
            timeout=timeout,
            project_root=project_root,
            runs_per_query=runs_per_query,
            trigger_threshold=trigger_threshold,
            model=model,
        )
        elapsed = time.time() - t0

        # 拆回訓練 / 測試結果
        train_queries = {q["query"] for q in train_set}
        train_result_list = [r for r in all_results["results"] if r["query"] in train_queries]
        test_result_list = [r for r in all_results["results"] if r["query"] not in train_queries]

        train_passed = sum(1 for r in train_result_list if r["pass"])
        train_total = len(train_result_list)
        test_passed = sum(1 for r in test_result_list if r["pass"]) if test_result_list else None
        test_total = len(test_result_list) if test_result_list else None

        history.append({
            "iteration": iteration,
            "description": current_description,
            "train_passed": train_passed,
            "train_total": train_total,
            "train_results": train_result_list,
            "test_passed": test_passed,
            "test_total": test_total,
            "test_results": test_result_list,
            # backward compat
            "passed": train_passed,
            "total": train_total,
            "results": train_result_list,
        })

        if verbose:
            _print_results("訓練集", train_result_list, elapsed)
            if test_result_list:
                _print_results("測試集", test_result_list)

        # 訓練集全過 → 提前結束
        if train_passed == train_total:
            exit_reason = f"all_passed（第 {iteration} 迭代）"
            if verbose:
                print(f"\n🎉 訓練集全部通過！", file=sys.stderr)
            break

        if iteration == max_iterations:
            exit_reason = f"max_iterations（{max_iterations}）"
            if verbose:
                print(f"\n⏹️  已達最大迭代次數。", file=sys.stderr)
            break

        # 根據訓練集失敗案例改善 description（不讓模型看到測試集分數）
        if verbose:
            print(f"\n🔧 改善 description...", file=sys.stderr)

        blinded_history = [
            {k: v for k, v in h.items() if not k.startswith("test_")}
            for h in history
        ]
        train_eval_results = {
            "results": train_result_list,
            "summary": {"passed": train_passed, "failed": train_total - train_passed, "total": train_total},
            "description": current_description,
        }

        t0 = time.time()
        new_description = improve_description(
            skill_name=name,
            skill_content=content,
            current_description=current_description,
            eval_results=train_eval_results,
            history=blinded_history,
            model=model,
            log_dir=log_dir,
            iteration=iteration,
        )
        if verbose:
            print(f"  → 新 description（{time.time()-t0:.1f}s）：{new_description[:80]}...", file=sys.stderr)

        current_description = new_description

    # 選最佳迭代（以測試集分數為準；無測試集則用訓練集）
    if test_set:
        best = max(history, key=lambda h: h["test_passed"] or 0)
        best_score = f"{best['test_passed']}/{best['test_total']} (測試集)"
    else:
        best = max(history, key=lambda h: h["train_passed"])
        best_score = f"{best['train_passed']}/{best['train_total']} (訓練集)"

    return {
        "skill_name": name,
        "exit_reason": exit_reason,
        "original_description": original_description,
        "best_description": best["description"],
        "best_score": best_score,
        "best_iteration": best["iteration"],
        "final_description": current_description,
        "iterations_run": len(history),
        "holdout": holdout,
        "train_size": len(train_set),
        "test_size": len(test_set),
        "history": history,
    }


def main():
    parser = argparse.ArgumentParser(description="Description 優化迴圈")
    parser.add_argument("--eval-set", required=True, help="測試集 JSON 路徑")
    parser.add_argument("--skill-path", required=True, help="Skill 目錄路徑")
    parser.add_argument("--description", default=None, help="覆蓋起始 description")
    parser.add_argument("--num-workers", type=int, default=5, help="並行執行數（預設 5）")
    parser.add_argument("--timeout", type=int, default=30, help="每查詢逾時秒數（預設 30）")
    parser.add_argument("--max-iterations", type=int, default=5, help="最大迭代次數（預設 5）")
    parser.add_argument("--runs-per-query", type=int, default=3, help="每查詢重複跑幾次（預設 3）")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="觸發率門檻（預設 0.5）")
    parser.add_argument("--holdout", type=float, default=0.4, help="測試集比例（預設 0.4，設 0 停用）")
    parser.add_argument("--model", default=None, help="指定改善用的模型（預設使用 claude -p 預設模型）")
    parser.add_argument("--verbose", action="store_true", help="顯示詳細進度")
    parser.add_argument("--output", default=None, help="結果 JSON 儲存路徑（預設印到 stdout）")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not (skill_path / "SKILL.md").exists():
        print(f"❌ 找不到 SKILL.md：{skill_path}", file=sys.stderr)
        sys.exit(1)

    eval_set = json.loads(Path(args.eval_set).read_text())
    log_dir = Path(args.output).parent / "logs" if args.output else None

    output = run_loop(
        eval_set=eval_set,
        skill_path=skill_path,
        description_override=args.description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        max_iterations=args.max_iterations,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        holdout=args.holdout,
        model=args.model,
        verbose=args.verbose,
        log_dir=log_dir,
    )

    if args.verbose:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"結束原因：{output['exit_reason']}", file=sys.stderr)
        print(f"最佳分數：{output['best_score']}（第 {output['best_iteration']} 迭代）", file=sys.stderr)
        print(f"\n🏆 最佳 description：\n{output['best_description']}", file=sys.stderr)

    json_output = json.dumps(output, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(json_output)
        print(f"\n結果已儲存至：{args.output}", file=sys.stderr)
    else:
        print(json_output)


if __name__ == "__main__":
    main()

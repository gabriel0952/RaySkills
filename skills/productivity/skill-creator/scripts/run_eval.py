#!/usr/bin/env python3
"""測試 skill description 的觸發準確率。

透過在 commands 目錄建立暫時指令檔，並以 AI CLI 的 `-p` 模式跑各個測試查詢，
偵測 agent 是否選擇讀取（觸發）該 skill。預設使用 `claude` CLI；
可透過 `--cli` 指定其他工具（需支援相同的 `-p` 與 `stream-json` 介面）。

用法：
    python -m scripts.run_eval --eval-set evals.json --skill-path .
"""

import argparse
import json
import os
import select
import subprocess
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md


def find_project_root(cli: str = "claude") -> Path:
    """往上找對應 CLI 的 commands 目錄所在的專案根目錄；找不到就用 cwd。"""
    commands_subdir = _commands_subdir(cli)
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / commands_subdir).is_dir():
            return parent
    return current


def _commands_subdir(cli: str) -> str:
    """回傳該 CLI 預設的 commands 目錄相對路徑。"""
    mapping = {
        "claude": ".claude/commands",
    }
    return mapping.get(cli, f".{cli}/commands")


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
    cli: str = "claude",
    commands_dir: str | None = None,
) -> bool:
    """執行單一查詢，回傳 skill 是否被觸發。

    在 commands 目錄建立暫時的 skill 指令檔，讓 agent 看到這個 skill，
    然後跑 `<cli> -p <query>` 並解析 stream-json 輸出來判斷是否觸發。
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    if commands_dir:
        project_commands_dir = Path(commands_dir)
    else:
        project_commands_dir = Path(project_root) / _commands_subdir(cli)
    command_file = project_commands_dir / f"{clean_name}.md"

    try:
        project_commands_dir.mkdir(parents=True, exist_ok=True)
        indented_desc = "\n  ".join(skill_description.split("\n"))
        command_content = (
            f"---\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        command_file.write_text(command_content)

        cmd = [
            cli, "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        # 移除 CLAUDECODE 以允許在 Claude Code session 內嵌套執行
        env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CODEX_ENV")}

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_root,
            env=env,
        )

        triggered = False
        start_time = time.time()
        buffer = ""
        pending_tool_name = None
        accumulated_json = ""

        try:
            while time.time() - start_time < timeout:
                if process.poll() is not None:
                    remaining = process.stdout.read()
                    if remaining:
                        buffer += remaining.decode("utf-8", errors="replace")
                    break

                ready, _, _ = select.select([process.stdout], [], [], 1.0)
                if not ready:
                    continue

                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if event.get("type") == "stream_event":
                        se = event.get("event", {})
                        se_type = se.get("type", "")

                        if se_type == "content_block_start":
                            cb = se.get("content_block", {})
                            if cb.get("type") == "tool_use":
                                tool_name = cb.get("name", "")
                                if tool_name in ("Skill", "Read"):
                                    pending_tool_name = tool_name
                                    accumulated_json = ""
                                else:
                                    return False

                        elif se_type == "content_block_delta" and pending_tool_name:
                            delta = se.get("delta", {})
                            if delta.get("type") == "input_json_delta":
                                accumulated_json += delta.get("partial_json", "")
                                if clean_name in accumulated_json:
                                    return True

                        elif se_type in ("content_block_stop", "message_stop"):
                            if pending_tool_name:
                                return clean_name in accumulated_json
                            if se_type == "message_stop":
                                return False

                    elif event.get("type") == "assistant":
                        message = event.get("message", {})
                        for item in message.get("content", []):
                            if item.get("type") != "tool_use":
                                continue
                            tool_name = item.get("name", "")
                            tool_input = item.get("input", {})
                            if tool_name == "Skill" and clean_name in tool_input.get("skill", ""):
                                triggered = True
                            elif tool_name == "Read" and clean_name in tool_input.get("file_path", ""):
                                triggered = True
                            return triggered

                    elif event.get("type") == "result":
                        return triggered
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

        return triggered
    finally:
        if command_file.exists():
            command_file.unlink()


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
    cli: str = "claude",
    commands_dir: str | None = None,
) -> dict:
    """跑完整 eval set，回傳結果字典。"""
    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info: dict = {}
        for item in eval_set:
            for _ in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                    cli,
                    commands_dir,
                )
                future_to_info[future] = item

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            query_triggers.setdefault(query, [])
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"警告：查詢執行失敗：{e}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        did_pass = (trigger_rate >= trigger_threshold) if should_trigger else (trigger_rate < trigger_threshold)
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {"total": total, "passed": passed, "failed": total - passed},
    }


def main():
    parser = argparse.ArgumentParser(description="測試 skill description 的觸發準確率")
    parser.add_argument("--eval-set", required=True, help="測試集 JSON 路徑")
    parser.add_argument("--skill-path", required=True, help="Skill 目錄路徑")
    parser.add_argument("--description", default=None, help="覆蓋要測試的 description")
    parser.add_argument("--num-workers", type=int, default=5, help="並行執行數（預設 5）")
    parser.add_argument("--timeout", type=int, default=30, help="每個查詢的逾時秒數（預設 30）")
    parser.add_argument("--runs-per-query", type=int, default=3, help="每個查詢跑幾次（預設 3）")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="觸發率門檻（預設 0.5）")
    parser.add_argument("--model", default=None, help="指定模型（預設使用 CLI 工具的預設模型）")
    parser.add_argument("--cli", default="claude", help="使用的 AI CLI 工具（預設 claude）")
    parser.add_argument("--commands-dir", default=None, help="覆蓋 commands 目錄路徑（預設依 --cli 自動決定）")
    parser.add_argument("--verbose", action="store_true", help="顯示詳細進度")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not (skill_path / "SKILL.md").exists():
        print(f"❌ 找不到 SKILL.md：{skill_path}", file=sys.stderr)
        sys.exit(1)

    eval_set = json.loads(Path(args.eval_set).read_text())
    name, original_description, _ = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root(args.cli)

    if args.verbose:
        print(f"測試 description：{description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
        cli=args.cli,
        commands_dir=args.commands_dir,
    )

    if args.verbose:
        s = output["summary"]
        print(f"\n結果：{s['passed']}/{s['total']} 通過", file=sys.stderr)
        for r in output["results"]:
            status = "✅ PASS" if r["pass"] else "❌ FAIL"
            print(f"  {status} [{r['triggers']}/{r['runs']}次觸發] {r['query'][:60]}", file=sys.stderr)

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

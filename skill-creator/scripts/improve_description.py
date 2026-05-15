#!/usr/bin/env python3
"""根據 eval 結果改善 skill description。

呼叫 `claude -p` 分析哪些查詢觸發失敗，並產生更好的 description。

用法：
    python -m scripts.improve_description --eval-results results.json --skill-path .
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from scripts.utils import parse_skill_md


def _call_claude(prompt: str, model: str | None, timeout: int = 300) -> str:
    """呼叫 `claude -p`，prompt 透過 stdin 傳入，回傳文字回應。"""
    cmd = ["claude", "-p", "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])

    # 移除 CLAUDECODE 以允許在 Claude Code session 內嵌套執行
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude -p 執行失敗（exit {result.returncode}）\nstderr: {result.stderr}"
        )
    return result.stdout


def improve_description(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list[dict],
    model: str | None,
    log_dir: Path | None = None,
    iteration: int | None = None,
) -> str:
    """呼叫 Claude 根據 eval 結果改善 description，回傳新的 description 字串。"""
    failed_triggers = [r for r in eval_results["results"] if r["should_trigger"] and not r["pass"]]
    false_triggers = [r for r in eval_results["results"] if not r["should_trigger"] and not r["pass"]]

    train_score = f"{eval_results['summary']['passed']}/{eval_results['summary']['total']}"

    prompt = f"""你正在為一個名為 "{skill_name}" 的 Claude Code skill 優化 description。

Skill 的 description 出現在 Claude 的 available_skills 清單中。當使用者發送查詢時，Claude 僅根據 skill 的 name 和 description 來決定是否觸發該 skill。你的目標是寫出一個能讓正確查詢觸發、不相關查詢不觸發的 description。

目前的 description：
<current_description>
"{current_description}"
</current_description>

目前分數（{train_score}）：
<eval_results>
"""

    if failed_triggers:
        prompt += "❌ 應觸發但未觸發：\n"
        for r in failed_triggers:
            prompt += f'  - "{r["query"]}" （觸發 {r["triggers"]}/{r["runs"]} 次）\n'
        prompt += "\n"

    if false_triggers:
        prompt += "⚠️ 不應觸發但觸發了：\n"
        for r in false_triggers:
            prompt += f'  - "{r["query"]}" （觸發 {r["triggers"]}/{r["runs"]} 次）\n'
        prompt += "\n"

    if not failed_triggers and not false_triggers:
        prompt += "（目前沒有失敗案例）\n"

    if history:
        prompt += "\n先前的嘗試（請勿重複，嘗試不同的結構或措辭）：\n\n"
        for h in history:
            score_str = f"{h.get('train_passed', h.get('passed', 0))}/{h.get('train_total', h.get('total', 0))}"
            prompt += f'<attempt score="{score_str}">\n'
            prompt += f'Description: "{h["description"]}"\n'
            prompt += "</attempt>\n\n"

    prompt += f"""</eval_results>

Skill 內容（供參考）：
<skill_content>
{skill_content[:3000]}{"..." if len(skill_content) > 3000 else ""}
</skill_content>

請根據失敗案例寫出更好的 description。注意：
- 從失敗中歸納**通用規律**，不要針對特定查詢加入太具體的規則（避免過度擬合）
- Description 長度控制在 100-200 字以內，絕對不超過 1024 字元
- 用祈使語氣：「Use this skill when...」
- 聚焦於使用者的**意圖**，而非實作細節
- 要有鑑別度，避免讓 skill 在不相關情境下觸發

請只在 <new_description> 標籤內回傳新的 description，不要包含其他文字。"""

    text = _call_claude(prompt, model)
    match = re.search(r"<new_description>(.*?)</new_description>", text, re.DOTALL)
    description = match.group(1).strip().strip('"') if match else text.strip().strip('"')

    # 若超過 1024 字元，重新要求縮短
    if len(description) > 1024:
        shorten_prompt = (
            f"{prompt}\n\n---\n\n"
            f"上一次的回答有 {len(description)} 字元，超過 1024 字元的限制：\n\n"
            f'"{description}"\n\n'
            f"請重新寫一個 1024 字元以內的版本，保留最重要的觸發條件。"
            f"只在 <new_description> 標籤內回傳結果。"
        )
        shorten_text = _call_claude(shorten_prompt, model)
        match = re.search(r"<new_description>(.*?)</new_description>", shorten_text, re.DOTALL)
        description = match.group(1).strip().strip('"') if match else shorten_text.strip().strip('"')

    # 儲存 log（供除錯用）
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"improve_iter_{iteration or 'unknown'}.json"
        log_file.write_text(
            json.dumps(
                {
                    "iteration": iteration,
                    "prompt": prompt,
                    "response": text,
                    "final_description": description,
                    "char_count": len(description),
                },
                indent=2,
                ensure_ascii=False,
            )
        )

    return description


def main():
    parser = argparse.ArgumentParser(description="根據 eval 結果改善 skill description")
    parser.add_argument("--eval-results", required=True, help="eval 結果 JSON 路徑（來自 run_eval.py）")
    parser.add_argument("--skill-path", required=True, help="Skill 目錄路徑")
    parser.add_argument("--history", default=None, help="先前嘗試歷史 JSON 路徑（選用）")
    parser.add_argument("--model", default=None, help="指定改善用的模型")
    parser.add_argument("--verbose", action="store_true", help="顯示詳細資訊")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not (skill_path / "SKILL.md").exists():
        print(f"❌ 找不到 SKILL.md：{skill_path}", file=sys.stderr)
        sys.exit(1)

    eval_results = json.loads(Path(args.eval_results).read_text())
    history = json.loads(Path(args.history).read_text()) if args.history else []
    name, _, content = parse_skill_md(skill_path)
    current_description = eval_results.get("description", "")

    if args.verbose:
        s = eval_results["summary"]
        print(f"目前分數：{s['passed']}/{s['total']}", file=sys.stderr)
        print(f"目前 description：{current_description}", file=sys.stderr)

    new_description = improve_description(
        skill_name=name,
        skill_content=content,
        current_description=current_description,
        eval_results=eval_results,
        history=history,
        model=args.model,
    )

    if args.verbose:
        print(f"\n改善後 description：{new_description}", file=sys.stderr)

    output = {
        "description": new_description,
        "char_count": len(new_description),
        "history": history + [{
            "description": current_description,
            "train_passed": eval_results["summary"]["passed"],
            "train_total": eval_results["summary"]["total"],
        }],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Marp 投影片建置工具。

自動設定 --theme-set、處理 PDF/PPTX 輸出，並在建置前做基本密度檢查。

用法：
    python -m scripts.build slides.md --pdf
    python -m scripts.build slides.md --pptx
    python -m scripts.build slides.md --check    # 只做預檢，不建置
    python -m scripts.build slides.md --html -o output/
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
THEMES_DIR = SKILL_DIR / "assets" / "themes"

# 密度上限（超過時警告，不阻止建置）
MAX_BULLETS_PER_SLIDE = 6
MAX_CHARS_CJK_PER_SLIDE = 300   # 中文字元數
MAX_CHARS_EN_PER_SLIDE = 500    # 英文字元數
MAX_CODE_LINES_PER_SLIDE = 20


def check_marp() -> bool:
    """檢查 marp CLI 是否已安裝。"""
    try:
        result = subprocess.run(["marp", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_browser() -> tuple[bool, str]:
    """檢查是否有可用的 Chrome/Chromium/Edge（Marp PDF/PPTX 需要）。"""
    candidates = [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for browser in candidates:
        try:
            result = subprocess.run([browser, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                return True, version
        except FileNotFoundError:
            continue
    return False, ""


def parse_slides(content: str) -> list[str]:
    """將 Marp Markdown 拆成個別投影片（以 --- 分隔，忽略 frontmatter）。"""
    # 移除 frontmatter
    stripped = re.sub(r"^---\n.*?\n---\n", "", content, count=1, flags=re.DOTALL)
    slides = re.split(r"\n---\n", stripped)
    return [s.strip() for s in slides if s.strip()]


def count_cjk(text: str) -> int:
    """計算字串中的 CJK 字元數。"""
    return sum(1 for c in text if "\u4e00" <= c <= "\u9fff" or "\u3000" <= c <= "\u303f")


def preflight_check(input_file: Path) -> list[dict]:
    """對每張投影片做密度預檢，回傳警告清單。"""
    content = input_file.read_text(encoding="utf-8")
    slides = parse_slides(content)
    warnings = []

    for i, slide in enumerate(slides, 1):
        lines = slide.split("\n")

        # 條列數量
        bullets = [l for l in lines if re.match(r"^\s*[-*+]\s", l)]
        if len(bullets) > MAX_BULLETS_PER_SLIDE:
            warnings.append({
                "slide": i,
                "type": "too_many_bullets",
                "msg": f"第 {i} 張：{len(bullets)} 個條列（建議 ≤ {MAX_BULLETS_PER_SLIDE}），考慮拆成兩張",
            })

        # CJK 字元密度
        cjk_count = count_cjk(slide)
        total_chars = len(re.sub(r"\s+", "", slide))
        is_cjk_heavy = total_chars > 0 and (cjk_count / total_chars) > 0.4

        if is_cjk_heavy and cjk_count > MAX_CHARS_CJK_PER_SLIDE:
            warnings.append({
                "slide": i,
                "type": "cjk_overflow_risk",
                "msg": f"第 {i} 張：CJK 字元 {cjk_count} 個，有溢出風險（建議 ≤ {MAX_CHARS_CJK_PER_SLIDE}）",
            })
        elif not is_cjk_heavy and total_chars > MAX_CHARS_EN_PER_SLIDE:
            warnings.append({
                "slide": i,
                "type": "en_overflow_risk",
                "msg": f"第 {i} 張：字元數 {total_chars}，有溢出風險（建議 ≤ {MAX_CHARS_EN_PER_SLIDE}）",
            })

        # 代碼區塊行數
        code_blocks = re.findall(r"```.*?```", slide, re.DOTALL)
        for block in code_blocks:
            code_lines = block.count("\n")
            if code_lines > MAX_CODE_LINES_PER_SLIDE:
                warnings.append({
                    "slide": i,
                    "type": "long_code_block",
                    "msg": f"第 {i} 張：代碼區塊 {code_lines} 行（建議 ≤ {MAX_CODE_LINES_PER_SLIDE}），可能溢出",
                })

    return warnings


def build(
    input_file: Path,
    output_format: str,
    output_path: Path | None,
    allow_local_files: bool,
    verbose: bool,
) -> int:
    """執行 Marp 建置，回傳 exit code。"""
    cmd = [
        "marp",
        "--theme-set", str(THEMES_DIR),
        "--",                    # 分隔符，避免 input 被誤解為 theme-set 的一部分
        str(input_file),
        f"--{output_format}",
    ]

    if output_path:
        cmd.extend(["-o", str(output_path)])

    if allow_local_files:
        cmd.append("--allow-local-files")

    if verbose:
        print(f"執行：{' '.join(str(c) for c in cmd)}\n")

    result = subprocess.run(cmd, text=True)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="建置 Marp 投影片")
    parser.add_argument("input", help="輸入 Marp Markdown 檔案")
    parser.add_argument("--pdf", action="store_true", help="輸出 PDF")
    parser.add_argument("--pptx", action="store_true", help="輸出 PPTX")
    parser.add_argument("--html", action="store_true", help="輸出 HTML")
    parser.add_argument("--check", action="store_true", help="只做預檢，不建置")
    parser.add_argument("-o", "--output", help="輸出路徑（檔案或目錄）")
    parser.add_argument("--allow-local-files", action="store_true", help="允許本地圖片（受信任環境才使用）")
    parser.add_argument("--verbose", action="store_true", help="顯示詳細資訊")
    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ 找不到檔案：{input_file}", file=sys.stderr)
        sys.exit(1)

    # --- 預檢 ---
    print(f"🔍 預檢 {input_file.name}...")
    warnings = preflight_check(input_file)
    if warnings:
        print(f"\n⚠️  發現 {len(warnings)} 個排版風險：")
        for w in warnings:
            print(f"   • {w['msg']}")
        print()
    else:
        print("   ✅ 密度檢查通過\n")

    if args.check:
        return

    # --- 確定輸出格式 ---
    if args.pptx:
        output_format = "pptx"
    elif args.html:
        output_format = "html"
    else:
        output_format = "pdf"  # 預設 PDF

    # --- 環境檢查 ---
    if not check_marp():
        print("❌ 找不到 marp CLI，請先安裝：npm install -g @marp-team/marp-cli", file=sys.stderr)
        sys.exit(1)

    if output_format in ("pdf", "pptx"):
        browser_ok, browser_ver = check_browser()
        if not browser_ok:
            print("❌ 找不到 Chrome/Chromium/Edge，Marp PDF/PPTX 需要瀏覽器。", file=sys.stderr)
            print("   請安裝 Google Chrome 或 Chromium 後重試。", file=sys.stderr)
            sys.exit(1)
        elif args.verbose:
            print(f"   瀏覽器：{browser_ver}")

    # --- 主題目錄提示 ---
    if args.verbose:
        print(f"   主題目錄：{THEMES_DIR}")
        themes = list(THEMES_DIR.glob("*.css"))
        for t in themes:
            print(f"   　・{t.name}")
        print()

    # --- 建置 ---
    output_path = Path(args.output) if args.output else None
    print(f"🔨 建置中（{output_format.upper()}）...")
    exit_code = build(input_file, output_format, output_path, args.allow_local_files, args.verbose)

    if exit_code == 0:
        print("✅ 建置完成！")
    else:
        print(f"❌ 建置失敗（exit code {exit_code}）", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

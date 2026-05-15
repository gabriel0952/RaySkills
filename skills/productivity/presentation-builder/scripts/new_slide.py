#!/usr/bin/env python3
"""從 templates/ 建立新的 Marp 投影片檔案。

用法：
    python -m scripts.new_slide                    # 互動模式
    python -m scripts.new_slide -t zh -o my.md    # 直接指定
    python -m scripts.new_slide --list             # 列出可用模板
"""

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = SKILL_DIR / "templates"

TEMPLATES = {
    "zh": {
        "file": "marp-zh.md",
        "desc": "中文投影片（skills-zh 主題）",
    },
    "en": {
        "file": "marp-en.md",
        "desc": "English slides (skills-en theme)",
    },
    "bilingual": {
        "file": "marp-bilingual.md",
        "desc": "中英雙語投影片（skills-bilingual 主題）",
    },
}


def slugify(text: str) -> str:
    """把標題轉成適合檔名的格式。"""
    text = text.lower().strip()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^\w\-\u4e00-\u9fff]", "", text)  # 保留 CJK
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "slides"


def fill_template(content: str, title: str, author: str, today: str) -> str:
    """將模板中的佔位符替換為實際值。"""
    content = re.sub(r"標題 / Title|標題|Title", title, content, count=1)
    content = re.sub(r"作者 Author|作者|Author", author, content, count=1)
    content = re.sub(r"日期 Date|日期|Date", today, content, count=1)
    return content


def main():
    parser = argparse.ArgumentParser(description="建立新的 Marp 投影片")
    parser.add_argument("-t", "--template", choices=list(TEMPLATES.keys()), help="模板類型")
    parser.add_argument("-o", "--output", help="輸出檔案路徑（預設：<title>.md）")
    parser.add_argument("--title", help="投影片標題")
    parser.add_argument("--author", default="", help="作者姓名")
    parser.add_argument("--list", action="store_true", help="列出可用模板")
    args = parser.parse_args()

    if args.list:
        print("\n可用模板：")
        for key, info in TEMPLATES.items():
            print(f"  {key:12} {info['desc']}")
        print(f"\n模板位置：{TEMPLATES_DIR}\n")
        return

    # 互動模式：未提供參數時詢問
    template_key = args.template
    if not template_key:
        print("\n請選擇模板類型：")
        for i, (key, info) in enumerate(TEMPLATES.items(), 1):
            print(f"  {i}. {key:12} {info['desc']}")
        choice = input("\n輸入編號或名稱（預設 zh）：").strip() or "1"
        keys = list(TEMPLATES.keys())
        if choice.isdigit():
            idx = int(choice) - 1
            template_key = keys[idx] if 0 <= idx < len(keys) else "zh"
        elif choice in TEMPLATES:
            template_key = choice
        else:
            template_key = "zh"

    title = args.title
    if not title:
        title = input("投影片標題：").strip() or "Untitled"

    author = args.author or input("作者（可留空）：").strip()
    today = date.today().strftime("%Y-%m-%d")

    # 確定輸出路徑
    output_path = Path(args.output) if args.output else Path(f"{slugify(title)}.md")

    # 讀取並填充模板
    template_file = TEMPLATES_DIR / TEMPLATES[template_key]["file"]
    if not template_file.exists():
        print(f"❌ 找不到模板：{template_file}", file=sys.stderr)
        sys.exit(1)

    content = template_file.read_text(encoding="utf-8")
    content = fill_template(content, title, author or "Your Name", today)

    if output_path.exists():
        overwrite = input(f"⚠️  {output_path} 已存在，覆蓋？[y/N] ").strip().lower()
        if overwrite != "y":
            print("已取消。")
            return

    output_path.write_text(content, encoding="utf-8")
    print(f"\n✅ 已建立：{output_path}")
    print(f"   模板：{template_key}（{TEMPLATES[template_key]['desc']}）")
    print(f"\n建置指令：")
    theme_dir = SKILL_DIR / "assets" / "themes"
    print(f"   python -m scripts.build {output_path} --pdf")
    print(f"   # 或直接用 marp：")
    print(f"   marp --theme-set {theme_dir} -- {output_path} --pdf\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""快速驗證 skill 結構是否符合 RaySkills 規範。

用法：
    python -m scripts.quick_validate <skill_directory>
    python -m scripts.quick_validate .  # 從 skill 目錄內執行
"""

import re
import sys
from pathlib import Path

import yaml


def validate_skill(skill_path: Path) -> tuple[bool, list[str], list[str]]:
    """驗證 skill，回傳 (is_valid, errors, warnings)。"""
    errors: list[str] = []
    warnings: list[str] = []
    skill_path = Path(skill_path).resolve()

    # --- 檢查 SKILL.md 存在 ---
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        errors.append("找不到 SKILL.md")
        return False, errors, warnings

    content = skill_md.read_text(encoding="utf-8")

    # --- 檢查 frontmatter ---
    if not content.startswith("---"):
        errors.append("SKILL.md 缺少 YAML frontmatter（沒有開頭的 ---）")
        return False, errors, warnings

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        errors.append("SKILL.md frontmatter 格式不正確（找不到結尾的 ---）")
        return False, errors, warnings

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            errors.append("Frontmatter 必須是 YAML 字典格式")
            return False, errors, warnings
    except yaml.YAMLError as e:
        errors.append(f"Frontmatter YAML 解析失敗：{e}")
        return False, errors, warnings

    # --- 檢查允許的 frontmatter 欄位 ---
    ALLOWED = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
    unexpected = set(frontmatter.keys()) - ALLOWED
    if unexpected:
        errors.append(
            f"Frontmatter 含有未知欄位：{', '.join(sorted(unexpected))}。"
            f"允許的欄位：{', '.join(sorted(ALLOWED))}"
        )

    # --- 必要欄位 ---
    if "name" not in frontmatter:
        errors.append("Frontmatter 缺少 'name' 欄位")
    else:
        name = str(frontmatter["name"]).strip()
        if not re.match(r"^[a-z0-9-]+$", name):
            errors.append(f"name '{name}' 必須是 kebab-case（小寫英數字與連字號）")
        elif name.startswith("-") or name.endswith("-") or "--" in name:
            errors.append(f"name '{name}' 不能以連字號開頭/結尾，或包含連續連字號")
        elif len(name) > 64:
            errors.append(f"name 過長（{len(name)} 字元），最多 64 字元")

    if "description" not in frontmatter:
        errors.append("Frontmatter 缺少 'description' 欄位")
    else:
        desc = str(frontmatter["description"]).strip()
        if "<" in desc or ">" in desc:
            errors.append("description 不能包含角括號（< 或 >）")
        if len(desc) > 1024:
            errors.append(f"description 過長（{len(desc)} 字元），最多 1024 字元")
        elif len(desc) < 20:
            warnings.append("description 可能太短，建議描述清楚觸發情境")

    # --- 本文檢查 ---
    body = content[match.end():].strip()
    if not body:
        warnings.append("SKILL.md 本文是空的，建議加入說明內容")
    else:
        lines = body.split("\n")
        if len(lines) > 500:
            warnings.append(f"SKILL.md 本文有 {len(lines)} 行，建議保持在 500 行以內，超出部分移至 references/")

    # --- 目錄結構建議 ---
    for subdir in ["scripts", "references", "assets"]:
        subpath = skill_path / subdir
        if subpath.exists() and not any(subpath.iterdir()):
            warnings.append(f"{subdir}/ 目錄是空的，可以移除")

    return len(errors) == 0, errors, warnings


def main():
    if len(sys.argv) < 2:
        # 嘗試用當前目錄
        skill_path = Path.cwd()
    else:
        skill_path = Path(sys.argv[1])

    if not skill_path.exists():
        print(f"❌ 路徑不存在：{skill_path}")
        sys.exit(1)

    is_valid, errors, warnings = validate_skill(skill_path)

    skill_name = skill_path.name
    print(f"\n🔍 驗證 skill：{skill_name}")
    print(f"   路徑：{skill_path.resolve()}\n")

    if errors:
        print("❌ 錯誤（必須修正）：")
        for e in errors:
            print(f"   • {e}")

    if warnings:
        print("⚠️  警告（建議改善）：")
        for w in warnings:
            print(f"   • {w}")

    if is_valid:
        print("✅ Skill 結構有效！" + (" 但有上述警告需留意。" if warnings else ""))
    else:
        print("\n請修正以上錯誤後再重新驗證。")

    print()
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()

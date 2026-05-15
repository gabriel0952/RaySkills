# skills

**[English](./README.en.md) | 繁體中文**

Ray 的個人 AI Agent skill 庫，適用於 Claude、GitHub Copilot CLI、OpenAI Codex 等支援 skill/instruction 機制的 AI agent。

## 什麼是 Skill？

Skill 是一份 `SKILL.md` 文件，告訴 AI agent 在什麼情境下要做什麼事。當你說出符合 skill 描述的話時，agent 會自動載入對應的指令、模板與工具。

- **frontmatter**（`name` + `description`）：觸發條件，永遠在 context 中
- **SKILL.md 本文**：詳細指令，觸發後載入
- **scripts / references / assets**：輔助資源，需要時才載入

## Skill 清單

| Skill | 說明 | 觸發方式 |
|-------|------|----------|
| [skill-creator](./skill-creator/) | 建立、改善或優化新的 skill | 「幫我建立一個 skill」、「把這個工作流程做成 skill」 |
| [presentation-builder](./presentation-builder/) | 從素材建立投影片/簡報 | 「幫我做簡報」、「把這些內容做成投影片」 |

## 如何使用

### 在 AI Agent 中使用

1. 將 skill 加入到你的 agent 對應的 commands 目錄（例如 Claude CLI 使用 `.claude/commands/`，Copilot CLI 則由工具自動探索）
2. 直接說出觸發詞，skill 會自動載入

### 新增 Skill

使用 `skill-creator` skill：

```
幫我建立一個 skill，用來...
```

或手動建立：
1. 在 `skills/<skill-name>/` 建立目錄
2. 撰寫 `SKILL.md`（參考現有 skill 格式）
3. 用 `quick_validate` 驗證結構：
   ```bash
   cd skill-creator
   python -m scripts.quick_validate ../<skill-name>
   ```

### 優化 Skill 觸發描述

```bash
cd skill-creator
python -m scripts.run_loop \
  --eval-set ../<skill-name>/evals/trigger_evals.json \
  --skill-path ../<skill-name> \
  --model <模型名稱> \
  --verbose
```

## 環境需求

- Python 3.9+（建議 3.13）
- 支援 `-p` 模式的 AI CLI 工具（如 `claude`、`codex` 等，用於 description 優化迴圈）
- Marp CLI（用於 presentation-builder 建置投影片）
- Chrome / Chromium / Edge（Marp 輸出 PDF/PPTX 時需要）

## License

[Apache License 2.0](./LICENSE) © 2026 Ray Chen

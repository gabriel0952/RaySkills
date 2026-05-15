---
name: handoff
description: 將當前 session 壓縮成結構化 handoff 文件，讓下一個 agent 無縫接力。當使用者說「handoff」、「幫我建立交接文件」、「我要結束這個 session」、「下一個 agent 要接」時觸發。
---

# Session Handoff

將當前對話壓縮為結構化 Markdown 文件，使下一個 agent 能快速理解現況並繼續工作。

## 執行步驟

1. **建立暫存檔**
   ```bash
   HANDOFF=$(mktemp /tmp/handoff-XXXXXX.md)
   ```

2. **掃描對話** — 提取：
   - 已完成的工作
   - 未完成事項與 open questions
   - 關鍵決策與其原因
   - 現有文件的路徑（PRD、ADR、issues）

3. **撰寫文件** — 以下方模板填入內容，寫入 `$HANDOFF`

4. **回報路徑** — 告知使用者：
   > `Handoff written to: /tmp/handoff-XXXXXX.md`

## 引用規則

- **不重複**現有的 PRD、ADR、GitHub Issues、tasks.md 內容
- 以 reference（路徑或 URL）指向這些文件
- 只記錄對話中產生的、尚未被文件化的資訊

---

## Handoff 文件模板

```markdown
# Handoff — <專案/功能簡述>

> 建立時間：<ISO 8601>
> 產出自：<使用的 skill / 工作脈絡>

## 現況摘要

<!-- 已完成什麼，現在在哪個階段 -->

## 未完成事項

<!-- 剩餘 tasks、open questions、待決策事項 -->
- [ ] ...

## 重要決策

<!-- 對話中產生的關鍵決定，未記錄在其他文件中 -->
| 決策 | 原因 |
|------|------|
| ... | ... |

## 現有文件參考

<!-- 指向已存在的文件，不重複內容 -->
- PRD：...
- Tasks：...
- ADR：...

## 建議下一步

<!-- 下一個 session 應從哪裡開始、優先做什麼 -->

## 建議 Skills

<!-- 下一個 session 推薦使用的 1–3 個 skills -->
- `/...`：因為...
```

---
name: presentation-builder
description: 幫使用者從零或現有素材建立投影片/簡報。當使用者說「幫我做簡報」、「把這些內容做成投影片」、「我需要 slides」、「幫我整理成 presentation」、「做個報告用的 deck」，或是想把筆記/大綱/文件轉成簡報格式時觸發。支援 Marp、Reveal.js、PowerPoint、純文字大綱等格式。
---

# Presentation Builder

從任何素材（主題、筆記、大綱、文件）建立結構清晰的投影片。

## 工具與資源

| 類型 | 路徑 | 用途 |
|------|------|------|
| 腳本 | `scripts/new_slide.py` | 從模板建立新投影片（互動或參數模式） |
| 腳本 | `scripts/build.py` | Marp → PDF/PPTX，含預檢與瀏覽器檢查 |
| 模板 | `templates/marp-zh.md` | 中文 Marp 起始模板 |
| 模板 | `templates/marp-en.md` | 英文 Marp 起始模板 |
| 模板 | `templates/marp-bilingual.md` | 雙語 Marp 起始模板 |
| 主題 | `assets/themes/rayskills-zh.css` | 中文優化 Marp 主題 |
| 主題 | `assets/themes/rayskills-en.css` | 英文 Marp 主題 |
| 主題 | `assets/themes/rayskills-bilingual.css` | 雙語 Marp 主題 |
| 參考 | `references/formats.md` | 各格式語法速查 |
| 參考 | `references/cjk-layout.md` | CJK 排版問題與解法 |

---

## Step 1: 收集關鍵資訊

從對話中提取已有的資訊，不足的部分詢問使用者：

1. **主題與目的** — 這份簡報要傳達什麼核心訊息？
2. **對象** — 技術人員？主管？客戶？學生？（影響用語深度與細節）
3. **時間 / 頁數** — 預計幾分鐘？幾張投影片？（沒說就預設 10–15 張）
4. **起始素材** — 有現成筆記 / 大綱 / 文件？還是從零開始？
5. **語言** — 中文？英文？雙語？（影響主題選擇，見下方）
6. **輸出格式** — 不確定時用這個判斷表：

| 情況 | 建議格式 |
|------|----------|
| 習慣在 terminal / 編輯器工作 | **Marp**（Markdown → PDF/PPTX） |
| 需要交給別人編輯 | **PPTX 架構**（提供結構讓使用者貼入） |
| 技術演講 / 網頁展示 | **Reveal.js** |
| 只需要內容大綱，格式自理 | **純文字大綱** |

### Marp 語言與主題對應

| 內容語言 | 使用主題 | 說明 |
|---------|----------|------|
| 中文為主（> 80%） | `rayskills-zh` | CJK 行高、字型、斷行優化 |
| 英文為主（> 80%） | `rayskills-en` | 標準西文排版 |
| 中英混排 / 有大量代碼 | `rayskills-bilingual` | 英文字型優先，CJK fallback |

---

## Step 2: 建立大綱

在產出完整投影片前，先確認大綱結構。這樣能快速確認內容方向，避免花大量時間產出錯誤方向的內容。

**標準簡報結構：**
```
1. 封面（標題 + 副標題）
2. Agenda / 目錄（3–5 點）
3. 問題 / 背景（Why）
4. 主體（3–5 節，每節 1–3 張）
5. 結論 / 重點整理
6. 下一步 / Q&A
```

對技術分享微調：Background → Demo/Code → Lessons Learned
對商業提案微調：Problem → Solution → Evidence → Ask

把大綱告知使用者並請他確認再繼續。

---

## Step 3: 產出投影片

確認大綱後，依所選格式產出完整內容。詳細語法見 `references/formats.md`。

### Marp 格式（使用自訂主題）

**優先建議使用模板**：請使用者執行 `python -m scripts.new_slide` 選模板，
或直接複製對應的 `templates/marp-*.md` 作為起點。

產出時使用對應主題（**不要用預設的 `default`**）：

```markdown
---
marp: true
theme: rayskills-zh       ← 依語言選擇 zh / en / bilingual
paginate: true
backgroundColor: #ffffff
---

## 標題即結論（不是主題名稱）

- 重點一（3–5 個條列為佳）
- 重點二
- 重點三

---
```

**CJK 排版注意事項（詳見 `references/cjk-layout.md`）：**
- 每張條列 ≤ 6 個，中文字元 ≤ 300，英文字元 ≤ 500
- 全型標點用於中文句，半型標點用於英文句
- 代碼區塊 ≤ 20 行，超過就截取並加 `// ...`
- 雙語時：em/斜體改用**粗體**（CJK 斜體效果差）

### Reveal.js 格式

詳見 `references/formats.md`。

### PPTX 架構

以清單形式列出每張投影片的標題與條列內容：

```
【第 1 張】標題
  標題：XXX  副標題：XXX

【第 2 張】問題背景
  主標（結論句）：一句話說明
  ・現況 A  ・痛點 B  ・影響 C
  備注欄（演講稿）：口頭說明要點
```

### 純文字大綱

```markdown
## 投影片 1：封面
## 投影片 2：背景
- 現況  - 問題
```

---

## Step 4: 投影片內容原則

每張投影片產出時遵循這些原則，品質會更好：

- **每張只傳達一個核心概念** — 避免資訊過量
- **標題是結論，不是主題** — 「效能提升 40%」比「效能測試結果」更有力
- **3–5 個條列為佳** — 超過就考慮拆成兩張
- **數字 > 形容詞** — 「快很多」→「從 2s 降至 300ms」
- **視覺化提示** — 若適合加圖表 / 示意圖，在內容中標記 `[圖：XXX]`

---

## Step 5: 完成後的建議

產出後主動提供：
1. **演講稿要點** — 每張投影片的口頭說明重點（1–2 句）
2. **簡化建議** — 指出哪幾張可以合併或刪除
3. **補強建議** — 哪裡適合加入數據、截圖、或 demo
4. **建置指令**（若使用 Marp）：
   ```bash
   cd RaySkills/presentation-builder
   python -m scripts.build <檔案>.md --check  # 先預檢排版風險
   python -m scripts.build <檔案>.md --pdf    # 或 --pptx
   ```

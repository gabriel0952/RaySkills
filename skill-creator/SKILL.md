---
name: skill-creator
description: 幫助使用者為 RaySkills 庫建立、改善或優化 skill。當使用者想建立一個新的 skill、把某個工作流程包裝成 skill、修改現有 skill、或優化 skill 的觸發描述時，請使用這個 skill。即使使用者只說「建立一個 skill」、「幫我包裝這個流程」、「我想把這個做成 skill」也應觸發。
---

# Skill Creator

協助建立與迭代 RaySkills 個人 skill 庫的 skill。

## 可用工具腳本

從 `RaySkills/skill-creator/` 目錄執行（需先 `pip install -r requirements.txt`）：

| 腳本 | 功能 | 指令 |
|------|------|------|
| `quick_validate` | 驗證 skill 結構 | `python -m scripts.quick_validate <skill路徑>` |
| `run_eval` | 測試 description 觸發準確率 | `python -m scripts.run_eval --eval-set evals.json --skill-path <路徑> --verbose` |
| `improve_description` | 單次改善 description | `python -m scripts.improve_description --eval-results results.json --skill-path <路徑> --verbose` |
| `run_loop` | 自動化優化迴圈（最推薦） | `python -m scripts.run_loop --eval-set evals.json --skill-path <路徑> --model <模型> --verbose` |

## 何時建立 skill？

**適合建立 skill 的情況：**
- 重複性任務，每次做法大同小異
- 有明確的觸發情境（使用者會說某些特定的話）
- 需要結構化步驟或參考資料
- 可以搭配腳本或模板來節省時間

**不適合建立 skill：**
- 一次性任務
- 太模糊的偏好（更適合放在 project docs 或系統提示）
- 簡單到直接回答就好的任務

---

## 建立流程概覽

```
捕捉意圖 → 撰寫 SKILL.md → 產生測試案例 → 迭代改善 → 優化 Description
```

完成時交付：
1. 完整的 SKILL.md 草稿
2. 建議的檔案路徑（`RaySkills/<skill-name>/SKILL.md`）
3. 2–3 個應觸發此 skill 的測試提示
4. 1–2 個不應觸發的反例提示
5. 下一步迭代的建議

---

## Step 1: Capture Intent / 捕捉意圖

先從對話中提取資訊——使用者可能已經描述了他們的工作流程。若資訊不足，詢問：

1. **這個 skill 要解決什麼重複性任務？**
2. **使用者通常會說什麼話來觸發它？**（舉例越具體越好）
3. **最終輸出的格式是什麼？**（文字、程式碼、檔案、報告？）
4. **有沒有需要搭配的參考資料或腳本？**

確認理解後再進行下一步。

---

## Step 2: Write the SKILL.md / 撰寫 SKILL.md

### 目錄結構

```
skill-name/
├── SKILL.md              # 必要
├── scripts/              # 可執行腳本（選用）
├── references/           # 按需載入的參考文件（選用）
└── assets/               # 模板、靜態資源（選用）
```

### 三層漸進式載入

| 層級 | 載入時機 | 建議長度 |
|------|----------|----------|
| frontmatter（name + description） | 永遠在 context | ~50 字 |
| SKILL.md 本文 | skill 觸發時 | < 300 行 |
| scripts / references / assets | 需要時才載入 | 不限 |

### 撰寫原則

- **說明原因，而非只給規則**：與其寫「必須做 X」，不如解釋「因為 Y，所以要做 X」
- **使用祈使句**：「列出...」、「詢問...」而非「應該列出」
- **保持精簡**：超過 300 行時，考慮把細節移到 `references/`
- **舉例勝過規則**：用具體例子說明格式比長串規定更有效

### 關於 Description（關鍵！）

Description 是 Claude 決定是否觸發 skill 的主要依據，寫法要「積極」：

```yaml
# 太被動（壞）
description: 幫助建立 SKILL.md 文件

# 積極具體（好）
description: 幫使用者建立 RaySkills skill。當使用者想建立新 skill、
  包裝工作流程、或說「做成 skill」、「建立 skill」時觸發。
```

### SKILL.md 模板

使用這個模板作為起點：

```markdown
---
name: skill-name
description: [說明何時觸發、做什麼。包含使用者可能說的話。]
---

# Skill 標題

一句話說明這個 skill 的用途。

## 使用時機

[什麼情況下應該使用這個 skill]

## 步驟

[主要執行流程]

## 輸出格式

[最終輸出應該長什麼樣子]
```

---

## Step 3: Generate Test Cases / 建立測試案例

為每個 skill 產生：

**應觸發（2–3 個）**：模擬真實使用者的語氣，包含具體細節
```
好例子：「我每次 code review 都要手動檢查同樣的東西，可以幫我做成 skill 嗎？」
壞例子：「建立一個 code review skill」（太抽象）
```

**不應觸發（1–2 個）**：選用近似但不該觸發的情境，而非完全無關的問題
```
好例子：「這個 code review checklist 要放進 README 嗎？」（涉及 checklist，但不是要建立 skill）
壞例子：「寫一個 fibonacci function」（太明顯不相關）
```

把測試案例告知使用者，請他們確認或補充，再動手執行。

---

## Step 4: Iterate / 迭代改善

執行測試案例後，根據結果改善 skill：

1. **分析問題根源**：是 description 沒觸發？是指令不夠清楚？還是缺少範例？
2. **泛化而非修補**：避免針對單一例子加規則，優先改善通用性
3. **精簡優先**：如果輸出品質相同，選擇更短的版本
4. **檢查每個 MUST**：如果你寫了「必須」，想想能否改成解釋原因

---

## Step 5: Optimize Description / 優化觸發描述

### 手動 Checklist（快速）

- [ ] 說明了**何時**使用（情境、觸發條件）
- [ ] 包含使用者可能實際說的話（口語、縮寫都算）
- [ ] 說明了 skill **做什麼**（輸出是什麼）
- [ ] 不會被太廣泛地觸發（有足夠的限定條件）
- [ ] 避免「幫助」、「協助」等模糊動詞作為開頭

### 自動化優化迴圈（推薦，需要支援 `-p` 模式的 AI CLI）

**1. 建立觸發測試集** `evals/trigger_evals.json`：

```json
[
  {"query": "我每次做 code review 都要手動檢查同樣的清單，幫我做成 skill", "should_trigger": true},
  {"query": "把我剛才說的 git 提交流程包裝成 skill", "should_trigger": true},
  {"query": "explain what a skill is", "should_trigger": false},
  {"query": "這個 checklist 放在 README 好還是 SKILL.md 好", "should_trigger": false}
]
```

應觸發和不應觸發各 4–6 筆；查詢要口語、具體，選有鑑別度的邊界案例。

**2. 執行優化迴圈**（從 `RaySkills/skill-creator/` 執行）：

```bash
python -m scripts.run_loop \
  --eval-set <skill路徑>/evals/trigger_evals.json \
  --skill-path <skill路徑> \
  --model <模型名稱> \
  --max-iterations 5 \
  --verbose
```

腳本自動：拆 60/40 訓練/測試集 → 迭代改善 → 以**測試集**選最佳版本（防過度擬合）→ 印出最佳 description。

**3. 驗證結構**：

```bash
python -m scripts.quick_validate <skill路徑>
```

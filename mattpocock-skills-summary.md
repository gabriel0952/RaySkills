# mattpocock/skills 完整解析

> 原始 repo：https://github.com/mattpocock/skills
>
> 這是 **Matt Pocock**（TypeScript 大師）為 AI coding agent（Claude Code、Codex 等）設計的 slash command 集合。核心理念：**不是 vibe coding，而是 real engineering**。Skills 設計小、可組合、可客製化。

---

## 🏗️ 架構概覽

每個 skill 是一個資料夾，裡面放 `SKILL.md`，定義 agent 被呼叫時的行為。

```
skills/
├── engineering/     ← 日常開發用
├── productivity/    ← 非程式碼的工作流
├── misc/            ← 偶爾用到
├── personal/        ← 作者個人設定，不對外推廣
├── in-progress/     ← 草稿
└── deprecated/      ← 已廢棄
```

---

## 🚀 快速安裝

```bash
npx skills@latest add mattpocock/skills
```

安裝後執行 `/setup-matt-pocock-skills`，設定：
- 使用的 issue tracker（GitHub、Linear、或本地檔案）
- triage 標籤詞彙
- 文件儲存位置

---

## 🔬 Engineering Skills 詳解

### `/grill-with-docs` ⭐ 最重要

**功能**：每次開始新功能前，讓 agent 問你問題直到雙方完全對齊，同時維護專案文件。

**實際行為**：
1. **一次問一個問題**，等你回答再問下一個
2. 能自己從 codebase 找答案的就不問你
3. 發現術語衝突時立刻指出：「你說的 'account' 是指 Customer 還是 User？」
4. 決策確定後**立刻更新 `CONTEXT.md`**（不批次處理，當下就更新）
5. 只有在「難以回頭、不看 context 會困惑、真正有取捨」三條件都滿足時，才建立 ADR

**搭配使用的文件**：
- `CONTEXT.md` — 專案術語表（純 glossary，不放實作細節）
- `docs/adr/` — 架構決策記錄（Architecture Decision Records）

**為什麼重要**：共享語言讓 agent 用更精準術語、變數與函式命名一致、agent 花更少 token 思考。

---

### `/tdd`

**功能**：紅綠重構的 TDD 開發迴圈。

**核心哲學**：
- ✅ 測試透過**公開介面**驗證**行為**（refactor 後測試不應該壞掉）
- ❌ 不測試內部實作細節、不 mock 內部 collaborators

**最重要的反模式警告 — Horizontal Slicing**：

```
❌ 錯誤（水平切）：
  RED:   先寫完所有 tests
  GREEN: 再寫完所有 implementation

✅ 正確（垂直切）：
  test1 → impl1 → test2 → impl2 → test3 → impl3 ...
```

水平切的問題：你在寫測試時還不知道實作長什麼樣，會寫出測試「形狀」而非「行為」的測試。

**工作流程**：
1. 先確認介面設計與測試優先順序（問使用者）
2. 寫一個 Tracer Bullet（第一個端到端的測試）
3. 循環：一個測試 → 最小實作 → 通過
4. 全部通過後才重構（永遠不在 RED 狀態重構）

---

### `/diagnose`

**功能**：系統性除錯六步驟。

#### Phase 1 — 建立 feedback loop（最重要！）
> 如果有快速、確定性的 pass/fail 信號，就能找到原因。沒有的話，再多看 code 也沒用。

依序嘗試：
1. Failing test
2. Curl / HTTP script
3. CLI invocation + diff stdout
4. Headless browser script（Playwright / Puppeteer）
5. Replay captured trace
6. Throwaway harness
7. Property / fuzz loop
8. Bisection harness
9. Differential loop（新舊版本 diff）
10. HITL bash script（最後手段）

目標：**2 秒內確定性 pass/fail 信號**，這佔了除錯的 90%。

#### Phase 2 — Reproduce
確認重現的是使用者描述的 bug，不是附近另一個 bug。

#### Phase 3 — Hypothesise
先列出 **3–5 個可偽證的假說**，再開始測試。格式：
> 「如果 X 是原因，那改變 Y 會讓 bug 消失」

先給使用者看，他可能已知道哪個假說是錯的。

#### Phase 4 — Instrument
每次只改一個變數。所有 debug log 加獨特前綴（如 `[DEBUG-a4f2]`），方便最後一次 grep 清除。

#### Phase 5 — Fix + 回歸測試
先寫 failing test，再修，再看它過。只在有「正確的 seam」時才寫回歸測試。

#### Phase 6 — Cleanup
- 移除所有 `[DEBUG-...]` log
- 在 commit message 記錄正確假說
- 問「什麼能預防這個 bug？」，若涉及架構問題則交給 `/improve-codebase-architecture`

---

### `/to-prd`

**功能**：把現有對話內容轉成 PRD，直接發布到 issue tracker。

> 注意：**不問使用者問題**，直接從對話 context 合成。

**PRD 模板包含**：
- Problem Statement（從使用者角度）
- Solution（從使用者角度）
- User Stories（大量、完整）
- Implementation Decisions（模組設計，不寫具體 file path）
- Testing Decisions（哪些模組要測、什麼是好測試）
- Out of Scope
- Further Notes

---

### `/to-issues`

**功能**：把 PRD 或計畫拆解成 GitHub Issues。

**切割原則 — 垂直切（Tracer Bullets）**：
- 每個 issue 是跨越所有層的薄切片（schema + API + UI + tests）
- 完成後可以獨立 demo 或驗證
- 分類為 **HITL**（需要人類決策）或 **AFK**（agent 可自主完成，優先選這個）
- 依賴順序發布（blockers 先發）

每個 issue 格式：
```
## What to build
## Acceptance criteria
## Blocked by
```

---

### `/improve-codebase-architecture`

**功能**：找出 codebase 的「淺模組」，提出「加深」機會。

**核心術語**：
| 術語 | 定義 |
|------|------|
| **Module** | 任何有介面與實作的東西 |
| **Deep module** | 小介面、大實作（高 leverage）|
| **Shallow module** | 介面幾乎跟實作一樣複雜（低 leverage）|
| **Seam** | 介面所在之處，可以替換行為的地方 |
| **Deletion test** | 想像刪掉這個模組，複雜度是消失還是轉移到 N 個 caller？|

**流程**：
1. 探索 codebase，找出感覺有 friction 的地方
2. 列出編號的「加深機會」候選，每個包含問題、解法、好處
3. 使用者選一個，展開 grilling 對話
4. 決策過程中隨時更新 `CONTEXT.md`

建議每幾天跑一次，預防 codebase 變成 ball of mud。

---

### `/zoom-out`

**功能**：當你不熟悉一段程式碼時，讓 agent 往上抽象一層，畫出相關模組與呼叫者的地圖。

使用情境：進入陌生的程式碼區域，需要先建立整體認識再深入。

---

### `/triage`

**功能**：透過 state machine 的 triage 角色來分類 issues。

需先執行 `/setup-matt-pocock-skills` 設定 triage 標籤詞彙（e.g. `needs-triage`, `ready-for-agent`）。

---

### `/prototype`

**功能**：建立一次性 prototype 來釐清設計。

兩種模式：
- **Terminal app**：適合釐清 state/business-logic 問題
- **UI 變體**：建立多個截然不同的 UI 版本，可從同一路由切換

---

## 🛠️ Productivity Skills 詳解

### `/grill-me`

`/grill-with-docs` 的簡化版，沒有 docs 整合，適合非程式碼的計畫討論。一次問一個問題，走完整個決策樹。

---

### `/caveman`

**功能**：壓縮 token 約 75%，但保留完整技術精度。

**規則**：
- 刪除：冠詞（a/an/the）、廢話（just/really/basically）、客套話（sure/certainly）、hedging
- 保留：技術術語完整、程式碼不動、錯誤訊息原文引用
- 用箭頭表達因果：`X → Y`

**範例**：
```
❌「Sure! I'd be happy to help you with that. The issue you're
   experiencing is likely caused by...」

✅「Bug in auth middleware. Token expiry check use < not <=. Fix:」
```

一旦啟動就持續到說「stop caveman」，在安全警告或破壞性操作時暫時切回正常語氣。

---

### `/handoff`

**功能**：把當前對話壓縮成 handoff 文件，讓下一個 agent 接力。

- 使用 `mktemp` 建立暫存檔
- 不重複已有的 PRD/ADR/issues，只用 reference 指向它們
- 建議下一個 session 應使用哪些 skills

---

### `/write-a-skill`

用來建立新 skill 的 meta-skill，確保格式正確、有漸進式揭露（progressive disclosure）、有打包附加資源。

---

## 🔩 Misc Skills

| Skill | 功能 |
|-------|------|
| `/git-guardrails-claude-code` | 設定 Claude Code hooks，封鎖危險 git 指令（push、reset --hard、clean 等） |
| `/migrate-to-shoehorn` | 把測試檔的 `as` 型別斷言遷移到 `@total-typescript/shoehorn` |
| `/scaffold-exercises` | 建立練習題目錄結構（sections、problems、solutions、explainers） |
| `/setup-pre-commit` | 設定 Husky pre-commit hooks（lint-staged、Prettier、型別檢查、tests） |

---

## 📚 整體設計哲學

這套 skills 的精髓是把以下經典書籍的精華，包裝成 AI agent 可以直接執行的 slash commands：

- 📖 *The Pragmatic Programmer* — 小步驟、快速反饋
- 📖 *Domain-Driven Design* — 共享語言（Ubiquitous Language）
- 📖 *A Philosophy of Software Design* — 深模組（Deep Modules）
- 📖 *Extreme Programming Explained* — 每天投資設計

### 解決的核心問題

| 傳統 AI 開發問題 | 本 repo 的解法 |
|---|---|
| Agent 做的不是你要的 | `/grill-with-docs` — 先對齊，後開工 |
| 每次 session 重新解釋術語 | `CONTEXT.md` — 共享語言，一次建立永久有效 |
| 測試爛掉 | `/tdd` — 垂直切片 + 行為測試 |
| Bug 除不掉 | `/diagnose` — 六步驟強制 feedback loop |
| Code 越來越爛 | `/improve-codebase-architecture` — 定期加深模組 |
| Token 爆炸 | `/caveman` — 75% 壓縮 |
| 跨 session 失憶 | `/handoff` — 交接文件 |

---

## 🔑 關鍵概念：CONTEXT.md

整個 skills 生態系的核心文件。

**是什麼**：專案的術語表（glossary），幫助 agent 使用精確的領域語言。

**不是什麼**：不是 spec、不是 scratch pad、不是實作細節的記錄。

**效果**：
- 「There's a problem when a lesson inside a section of a course is made 'real'」→ 「There's a problem with the materialization cascade」
- Agent 回應更簡潔、變數命名一致、codebase 更好導航

在 `CONTEXT.md` 存在前，幾乎所有 engineering skills 的效果都會打折扣。建議第一步先執行 `/grill-with-docs` 來建立它。

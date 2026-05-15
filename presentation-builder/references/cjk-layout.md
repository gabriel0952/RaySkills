# CJK 排版指南

中英文混排在投影片中常見的跑版問題，以及如何使用 RaySkills 主題解決。

---

## 常見問題與原因

### 1. 文字溢出邊界

**原因：** 預設主題未設定 `overflow-wrap`，長中文段落或長英文 URL 不會自動換行。

**解法（已內建於主題）：**
```css
/* 雙語：允許任意位置斷行 */
overflow-wrap: anywhere;

/* 純中文：CJK 標準斷行規則 */
line-break: strict;
```

---

### 2. CJK 文字被 CJK 字型的 Latin 字元覆蓋

**原因：** 許多 CJK 字型（如 PingFang、黑體）內含 Latin 字元，但品質不如 Helvetica / Arial。

**策略：英文字型優先，CJK 字型作 fallback**

```css
/* ✅ 雙語主題（rayskills-bilingual）的做法 */
font-family:
  'Helvetica Neue',     /* 渲染 ASCII 字元 */
  'Arial',
  'PingFang TC',        /* fallback：渲染 CJK */
  'Microsoft JhengHei',
  sans-serif;

/* ❌ 錯誤做法：CJK 字型在前，Latin 字元會變醜 */
font-family: 'PingFang TC', 'Helvetica Neue', sans-serif;
```

---

### 3. 行距不一致（中英混排時某行特別高）

**原因：** CJK 字元的行高通常比 Latin 高，混排時某些行會撐大行距。

**解法：**
```css
/* 純中文：給足夠行高 */
line-height: 1.8;

/* 雙語：取中間值 */
line-height: 1.7;

/* 避免用固定 px 行高（會在 CJK 行溢出）*/
/* ❌ line-height: 24px; */
```

---

### 4. 全型與半型標點混用

**問題範例：** 「這是問題,因為用了半型逗號.」

**規則：**
| 語言 | 逗號 | 句號 | 括號 |
|------|------|------|------|
| 中文 | ，（全型） | 。（全型） | （）（全型） |
| 英文 | , (半型) | . (半型) | () (半型) |
| 混排中文句 | ，（全型） | 。（全型） | 英文詞後用半型 |

**中文句含英文詞的例外：**
```
✅ 使用 React 和 Vue.js，效能提升 40%。
❌ 使用 React 和 Vue.js,效能提升 40%.
```

---

### 5. 代碼區塊破壞行高

**原因：** 代碼字型和正文字型行高不同，導致視覺上不一致。

**解法（已內建於主題）：**
```css
code {
  font-size: 0.82em;    /* 稍微縮小避免溢出 */
  line-height: 1.5;
  letter-spacing: 0;    /* 代碼不需要字距 */
}
```

**投影片中代碼的建議：**
- 每張最多 15–20 行代碼
- 超過就截取關鍵部分，加 `// ...` 省略號
- 代碼文字足夠大，後排觀眾能讀

---

## 主題選擇指南

| 內容組成 | 使用主題 | 備注 |
|---------|----------|------|
| > 80% 中文 | `rayskills-zh` | 針對 CJK 行高、斷行優化 |
| > 80% 英文 | `rayskills-en` | 標準西文排版 |
| 中英各佔一定比例 | `rayskills-bilingual` | 英文字型優先，CJK fallback |
| 有大量代碼 | `rayskills-bilingual` | em/斜體改為粗體，代碼字型正確 |

---

## Marp 使用自訂主題的方式

### 方法一：用 `build.py`（推薦）
```bash
# 自動載入 assets/themes/ 下的所有主題
python -m scripts.build my-slides.md --pdf
```

### 方法二：直接用 marp CLI
```bash
# 注意：--theme-set 後面要加 -- 分隔符
marp --theme-set /path/to/themes -- my-slides.md --pdf
```

### 方法三：VS Code Marp 套件
在 `settings.json` 加入：
```json
"markdown.marp.themes": [
  "/absolute/path/to/RaySkills/presentation-builder/assets/themes/rayskills-zh.css",
  "/absolute/path/to/RaySkills/presentation-builder/assets/themes/rayskills-en.css",
  "/absolute/path/to/RaySkills/presentation-builder/assets/themes/rayskills-bilingual.css"
]
```

---

## 預檢工具（自動偵測溢出風險）

```bash
python -m scripts.build my-slides.md --check
```

偵測項目：
- 每張條列數 > 6（建議拆成兩張）
- CJK 字元 > 300 / 英文字元 > 500（溢出風險）
- 代碼區塊 > 20 行（可能超出畫面）

**注意：預檢只是建議，不阻止建置。最終以實際渲染為準。**

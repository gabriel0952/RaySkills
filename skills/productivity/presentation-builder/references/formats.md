# 簡報格式速查

## Marp

**安裝：** `npm install -g @marp-team/marp-cli`
**轉換：** `marp slides.md --pdf` 或 `marp slides.md --pptx`

### Frontmatter 設定

```yaml
---
marp: true
theme: default          # default | gaia | uncover
paginate: true
backgroundColor: #fff
---
```

### 常用語法

```markdown
# 封面大標題
副標題文字

---

## 章節標題

- 條列一
- 條列二
  - 子條列

---

<!-- 分欄 -->
<div class="columns">
<div>

左欄內容

</div>
<div>

右欄內容

</div>
</div>

---

<!-- 圖片 -->
![bg right:40%](image.png)

## 文字在左，圖片在右
```

### 主題說明

| 主題 | 適合場景 |
|------|----------|
| `default` | 技術分享、工程簡報 |
| `gaia` | 正式商業簡報 |
| `uncover` | 演講、學術 |

---

## Reveal.js

**快速啟動：** Clone [reveal.js](https://github.com/hakimel/reveal.js)，編輯 `index.html`

### 基本結構

```html
<div class="reveal">
  <div class="slides">

    <!-- 水平切換 -->
    <section>
      <h1>標題</h1>
      <p>副標題</p>
    </section>

    <!-- 垂直子頁（按 ↓ 展開） -->
    <section>
      <section><h2>主節</h2></section>
      <section><h3>子節 A</h3></section>
      <section><h3>子節 B</h3></section>
    </section>

    <!-- 程式碼區塊 -->
    <section>
      <pre><code data-trim data-noescape>
function hello() {
  console.log("Hello!");
}
      </code></pre>
    </section>

    <!-- 逐步顯示（Fragment） -->
    <section>
      <ul>
        <li class="fragment">第一點（先出現）</li>
        <li class="fragment">第二點</li>
        <li class="fragment">第三點</li>
      </ul>
    </section>

  </div>
</div>
```

### 常用主題

`black` / `white` / `league` / `sky` / `moon` / `solarized`

```html
<link rel="stylesheet" href="dist/theme/black.css">
```

---

## PowerPoint / Google Slides 架構格式

當使用者需要 PPTX 但不使用程式產生時，輸出此格式讓使用者手動建立：

```
【投影片 1】封面
  標題：[簡報標題]
  副標題：[日期 / 部門 / 姓名]

【投影片 2】目錄
  ・章節一標題
  ・章節二標題
  ・章節三標題

【投影片 3】[章節標題]
  主標（結論句）：[一句話說明重點]
  ・條列一
  ・條列二
  ・條列三
  備註欄（演講稿）：[口頭說明的要點]

【投影片 N】結論
  重點整理：
  ・要點一
  ・要點二
  下一步：[行動呼籲]
```

---

## 格式選擇建議

| 需求 | 推薦 | 原因 |
|------|------|------|
| 純文字工具流程（VS Code、terminal） | Marp | 直接從 Markdown 轉出 |
| 需要自訂動畫、高度互動 | Reveal.js | JS 生態豐富 |
| 需要交給非技術人員編輯 | PPTX 架構 | 大家都會用 PowerPoint |
| 只需要內容，格式晚點再說 | 純文字大綱 | 最快，不受格式限制 |
| 技術文件 → 簡報 | Marp | 與文件同源，易維護 |

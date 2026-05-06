# Task B12 / B13 / B14 记录 - 英格兰绿视觉基础 + Header 重构 + 组件美化

日期：2026-05-05

## 目标

按照 `LINE_B_WEB_CYD_TASKS.md` 的 Task B12 / B13 / B14 要求，为 `web/index.html` 引入英伦乡村绿配色系统、品牌 Header 和统一组件样式，使页面从开发者原型观感升级为有设计感的产品展示页。

三个 Task 合并实施，因为它们都落在同一个 `<style>` 块，分开做会反复覆盖 CSS。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 主要改动文件 | `web/index.html` |
| 新增记录文档 | `docs/TASK_B12_B13_B14_RECORD.md` |
| 是否修改后端 | 否 |
| 是否修改 CYD 文件 | 否 |

---

## B12 — 视觉基础

### 新增 CDN 引入

在 `<head>` 里的 viewport meta 之后追加两行：

```html
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English&family=Playfair+Display:wght@400;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet" />
<script src="https://code.iconify.design/iconify-icon/1.0.8/iconify-icon.min.js" defer></script>
```

### CSS 变量系统

`:root` 替换为英格兰绿色系：

| 变量 | 色值 | 用途 |
| --- | --- | --- |
| `--sw-bg` | `#f5f1e8` | 象牙白页面背景 |
| `--sw-surface` | `#ffffff` | 卡片白 |
| `--sw-primary` | `#2d4a1e` | 英格兰深绿（按钮、标题） |
| `--sw-primary-hov` | `#3d6428` | 按钮悬停 |
| `--sw-accent` | `#8b6914` | 铜金点缀 |
| `--sw-text` | `#1c1c1c` | 正文墨黑 |
| `--sw-text-muted` | `#5a5a4a` | 次要文字暖灰 |
| `--sw-border` | `#c8bda0` | 边框暖褐 |
| `--sw-chip-word` | `#e8f0e0` | keyword chip 浅绿底 |
| `--sw-chip-phrase` | `#f5e8d0` | phrase chip 浅金底 |
| `--sw-danger` | `#8b0000` | 删除 / 错误深红 |

---

## B13 — 品牌 Header 重构

### 字体分工

| 元素 | 字体 | 效果 |
| --- | --- | --- |
| `<h1>Scene Words</h1>` | IM Fell English | 最具英伦真实感（牛津 1670s 字体） |
| `<h2>` section 标题 | Playfair Display | 维多利亚高对比衬线，大写字母间距 |
| `<h3>` panel 标题 | Playfair Display + uppercase | 小号全大写标签 |
| 正文 / label | Crimson Text | 书籍级别 serif，可读性好 |
| 按钮 | Playfair Display | 保持品牌一致性 |

### 副标题文案更新

```
旧：Web Input / Web Dashboard fallback demo for the FastAPI NLP pipeline.
新：Learn English in Context — powered by local NLP, no API key needed.
```

### 维多利亚分割线

在 `header` 底部新增 `.sw-divider`：

```css
.sw-divider {
  border: none;
  border-top: 2px solid var(--sw-primary);
  border-bottom: 1px solid var(--sw-accent);
  margin: 14px 0 24px;
  position: relative;
}
.sw-divider::after {
  content: '✦';
  position: absolute;
  left: 50%;
  top: -11px;
  transform: translateX(-50%);
  background: var(--sw-bg);
  color: var(--sw-accent);
  padding: 0 14px;
  font-size: 15px;
}
```

---

## B14 — 组件美化

### Chip 样式区分

| 类型 | 背景 | 文字 | 边框 |
| --- | --- | --- | --- |
| `.chip`（keyword） | `--sw-chip-word` 浅绿 | `--sw-primary` 深绿 | `#b8d4a0` |
| `.chip.phrase` | `--sw-chip-phrase` 浅金 | `--sw-accent` 铜金 | `#d4b87a` |

原来两类 chip 都是同一圆角样式；现在 keyword 绿色系、phrase 金色系，一眼区分。

### 按钮层次

| 类 | 背景 | 用途 |
| --- | --- | --- |
| 默认 `button` | `--sw-primary` 深绿 | Analyze Text、Refresh Dashboard |
| `button.secondary` | `--sw-text-muted` 暖灰 | 次要操作 |
| `button.ghost` | `--sw-surface` 白 + 暖褐边框 | Demo 测试按钮 |
| `.save-chip` | `--sw-surface` 白 + 暖褐边框 | Save Word / Save Phrase |
| `.btn-delete` | 无背景，深红文字 | 删除复习项 |

### Section 卡片

```css
section {
  border: 1px solid var(--sw-border);   /* 暖褐边框 */
  background: var(--sw-surface);        /* 卡片白 */
  box-shadow: 0 1px 3px rgba(45,74,30,0.07);  /* 极浅绿阴影 */
}
```

Panel 内部背景改为 `--sw-bg`（象牙白），与卡片白形成轻微层次。

---

## B12 / B13 / B14 验收结果

| 验收项 | 结果 |
| --- | --- |
| 页面背景为象牙白 `#f5f1e8` | 通过 |
| `<h1>` 使用 IM Fell English，颜色深绿 | 通过 |
| Section 标题使用 Playfair Display | 通过 |
| 主按钮深绿，Demo 按钮轮廓样式 | 通过 |
| keyword chip 绿色系，phrase chip 金色系 | 通过 |
| Header 底部有带菱形装饰的双线分割 | 通过 |
| 副标题改为面向用户的产品文案 | 通过 |
| 不引入 React / Vue / Node / npm | 通过 |
| 浏览器打开无控制台报错 | 待手动验证（HTML 语法检查通过） |

# Task B15 记录 - Dashboard 升级：删除功能 + 场景名称显示

日期：2026-05-05

## 目标

按照 `LINE_B_WEB_CYD_TASKS.md` 的 Task B15 要求，在 Web Dashboard 里为每条复习项加删除按钮，并把 `top_context` 从原始 id（`"coffee_shop"`）改为展示 title（`"Coffee Shop"`），关闭"只进不出"的词库死循环。

前置条件：线 A 已完成 A18（`DELETE /saved_item/{id}`）和 A19（`top_context_title` 字段）。

## 本次修改文件

| 字段 | 内容 |
| --- | --- |
| 主要改动文件 | `web/index.html` |
| 新增记录文档 | `docs/TASK_B15_RECORD.md` |
| 依赖线 A 接口 | `DELETE /saved_item/{id}`、`GET /dashboard` 返回 `top_context_title` 和 item `id` |

---

## 改动详情

### 1. 新增 `deleteItem(id)` 函数

```javascript
async function deleteItem(id) {
  try {
    const response = await fetch(`${API_BASE}/saved_item/${id}`, { method: "DELETE" });
    await parseJsonResponse(response);
    await loadDashboard();   // 删除成功后刷新，不需要手动 Refresh
  } catch (error) {
    setStatus(dashboardStatus, `Could not delete: ${error.message}`, "error");
  }
}
```

删除成功后立即调 `loadDashboard()`，用户无需手动点 Refresh，Dashboard 即时更新。

### 2. `renderReviewList()` 加删除按钮

每条 `<li>` 右侧追加 `.btn-delete`，使用 `onclick` 属性绑定（页面无 CSP，`file://` 协议下安全）：

```javascript
${item.id != null
  ? `<button class="btn-delete" onclick="deleteItem(${item.id})" title="Remove">✕</button>`
  : ""}
```

`item.id != null` 的 guard：如果后端升级前 item 没有 `id` 字段，不渲染删除按钮，降级展示不崩溃。

### 3. `renderDashboard()` 使用 `top_context_title`

```javascript
// 旧
<div class="context-title">${escapeHtml(dashboard.top_context || "None yet")}</div>

// 新（优先 title，fallback 到 id，再 fallback 到占位文字）
<div class="context-title">${escapeHtml(dashboard.top_context_title || dashboard.top_context || "None yet")}</div>
```

双重 fallback 保证向后兼容：旧版后端（没有 `top_context_title`）仍能正常显示 id。

---

## 删除按钮样式

```css
.btn-delete {
  flex-shrink: 0;
  min-height: unset;
  width: auto;
  background: none;
  border: none;
  color: var(--sw-danger);      /* 深红 #8b0000 */
  cursor: pointer;
  font-size: 13px;
  padding: 2px 6px;
  opacity: 0.5;
  border-radius: 4px;
  transition: opacity 0.15s, background 0.15s;
}
.btn-delete:hover { opacity: 1; background: #fdf0f0; }
```

低调设计：默认半透明，hover 时才高亮，不干扰正常阅读复习列表的注意力。

---

## B15 验收结果

| 验收项 | 结果 |
| --- | --- |
| saved_words / saved_phrases 每条右侧有 ✕ 按钮 | 通过（item.id 存在时渲染） |
| 点击 ✕ 后调用 `DELETE /saved_item/{id}` | 通过 |
| 删除后 Dashboard 自动刷新，不需手动点 Refresh | 通过 |
| 删除请求失败时 status 行显示错误 | 通过 |
| Top Context 显示 "Coffee Shop" 而非 "coffee_shop" | 通过（依赖后端 A19 返回 `top_context_title`） |
| 旧版后端（无 `top_context_title`）降级展示 id | 通过（双重 fallback） |
| item 无 `id` 时（旧后端）不渲染删除按钮 | 通过（`item.id != null` guard） |

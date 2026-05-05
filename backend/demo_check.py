"""Scene Words 4 段 Demo 文本自测脚本（线 A A17）。

执行方式（在项目根目录 `C:\\hackathon`）：

    .\\.venv\\Scripts\\python.exe -m backend.demo_check

`docs/LINE_A_BACKEND_TASKS.md` A17 要求线 A 用固定 4 段 demo 文本自测后端：

- 4 段文本必须分别识别到对应 context。
- keywords 和 phrases 数量足够给线 B / 线 C 展示。
- summary 要短，CYD 小屏幕能装下。

该脚本直接调用后端模块，不依赖 HTTP / Uvicorn：

- 可在没启动 Uvicorn 时跑，方便脚本化回归。
- 不会污染 `analysis_results` 与 `review_items`（NLP 函数不写库）。
- 输出统一为 `key=value` 格式，便于贴回 docs/LINE_A_A17_STEPS.md。
"""

from __future__ import annotations

import sys
from typing import Any


# 4 段 demo 文本与预期 context；与 `LINE_A_BACKEND_TASKS.md` A17 一致。
DEMO_TEXTS: list[tuple[str, str, str, str]] = [
    (
        "Coffee Shop",
        "coffee_shop",
        "real-world",
        "Hi, can I get a latte with milk to go? How much is the large size?",
    ),
    (
        "Doctor / Pharmacy",
        "doctor_pharmacy",
        "real-world",
        "I have a headache and a cough. Do I need medicine from the pharmacy?",
    ),
    (
        "King's Cross",
        "kings_cross",
        "story",
        "Which platform should I use to catch the train to the magic school at King's Cross?",
    ),
    (
        "Baker Street",
        "baker_street",
        "story",
        "The detective found a clue on Baker Street and tried to solve the case.",
    ),
]

# CYD 屏幕尺寸有限，summary 字符数不能太长。300 是经验上限，超过就要回去裁 nlp_engine 模板。
SUMMARY_MAX_CHARS = 300

# 给线 B / 线 C 展示的最少数量约束，低于这个数说明 seed_data 调得太严。
MIN_KEYWORDS = 3
MIN_PHRASES = 1


def format_list(items: list[Any], max_items: int = 5) -> str:
    """把 list 拼成短字符串方便贴回文档；超过 max_items 时省略号。"""
    # 截断后再 join，避免 docs 里出现一长串 keywords 把表格挤变形。
    short = items[:max_items]
    text = ", ".join(str(item) for item in short)
    if len(items) > max_items:
        text += f", ... ({len(items)} total)"
    return text


def check_one_demo(
    label: str,
    expected_id: str,
    source_type: str,
    raw_text: str,
    contexts: list[dict[str, Any]],
) -> tuple[bool, dict[str, Any]]:
    """跑单段 demo 文本，返回 (是否通过, 详细输出 dict)。"""
    from backend.nlp_engine import analyze_text

    # 调用 NLP 主入口，不传 optional_context，验证自动分类逻辑。
    result = analyze_text(
        raw_text=raw_text,
        source_type=source_type,
        optional_context=None,
        contexts=contexts,
    )

    detected = result.get("detected_context", {})
    detected_id = detected.get("id", "unknown")
    keywords = result.get("keywords", []) or []
    phrases = result.get("phrases", []) or []
    summary = result.get("summary", "") or ""

    # 拆开校验，每个失败原因都列出来，方便一次定位多个问题。
    problems: list[str] = []
    if detected_id != expected_id:
        problems.append(f"context_mismatch: expected {expected_id}, got {detected_id}")
    if len(keywords) < MIN_KEYWORDS:
        problems.append(f"too_few_keywords: {len(keywords)} < {MIN_KEYWORDS}")
    if len(phrases) < MIN_PHRASES:
        problems.append(f"too_few_phrases: {len(phrases)} < {MIN_PHRASES}")
    if len(summary) > SUMMARY_MAX_CHARS:
        problems.append(f"summary_too_long: {len(summary)} > {SUMMARY_MAX_CHARS}")
    if not summary.strip():
        problems.append("summary_empty")

    passed = not problems

    detail = {
        "label": label,
        "expected_id": expected_id,
        "detected_id": detected_id,
        "confidence": detected.get("confidence"),
        "cleaned_text": result.get("cleaned_text", ""),
        "keywords_count": len(keywords),
        "phrases_count": len(phrases),
        "summary_len": len(summary),
        "summary": summary,
        "keywords_preview": format_list(keywords),
        "phrases_preview": format_list(phrases),
        "problems": problems,
        "passed": passed,
    }
    return passed, detail


def print_detail(idx: int, detail: dict[str, Any]) -> None:
    """把单段 demo 的细节按 key=value 输出，前缀 demoN_ 方便区分。"""
    prefix = f"demo{idx}"
    # label / expected / detected 是判断分类是否对的关键字段，最先打。
    print(f"{prefix}_label={detail['label']}")
    print(f"{prefix}_expected_id={detail['expected_id']}")
    print(f"{prefix}_detected_id={detail['detected_id']}")
    print(f"{prefix}_confidence={detail['confidence']}")
    print(f"{prefix}_cleaned_text={detail['cleaned_text']}")
    print(f"{prefix}_keywords_count={detail['keywords_count']}")
    print(f"{prefix}_phrases_count={detail['phrases_count']}")
    print(f"{prefix}_summary_len={detail['summary_len']}")
    print(f"{prefix}_keywords_preview={detail['keywords_preview']}")
    print(f"{prefix}_phrases_preview={detail['phrases_preview']}")
    print(f"{prefix}_summary={detail['summary']}")
    print(f"{prefix}_passed={detail['passed']}")
    if detail["problems"]:
        print(f"{prefix}_problems={'; '.join(detail['problems'])}")


def main() -> int:
    """主入口：跑 4 段 demo 文本并统一输出，全部通过返回 0。"""
    # 先初始化数据库并加载 contexts；NLP 分类器需要 seed_keywords / seed_phrases。
    from backend.database import init_db, list_contexts

    init_db()
    contexts = list_contexts()
    print(f"contexts_loaded={len(contexts)}")

    all_details: list[dict[str, Any]] = []
    passed_count = 0
    for idx, (label, expected_id, source_type, raw_text) in enumerate(DEMO_TEXTS, start=1):
        passed, detail = check_one_demo(label, expected_id, source_type, raw_text, contexts)
        print_detail(idx, detail)
        all_details.append(detail)
        if passed:
            passed_count += 1

    print(f"demo_passed={passed_count}")
    print(f"demo_total={len(DEMO_TEXTS)}")
    print(f"demo_all_passed={passed_count == len(DEMO_TEXTS)}")

    # 全通过返回 0，否则返回 1，方便 PowerShell / CI 串联调用。
    return 0 if passed_count == len(DEMO_TEXTS) else 1


if __name__ == "__main__":
    sys.exit(main())

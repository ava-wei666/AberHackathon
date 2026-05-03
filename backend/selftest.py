"""SceneLingo 线 A 后端自测脚本。

执行方式（在项目根目录 `C:\\hackathon`）：

    .\\.venv\\Scripts\\python.exe -m backend.selftest

该脚本是 `LINE_A_BACKEND_TASKS.md` 中 A14 后端自测清单的可重复执行版本。
每次改完线 A 的代码后，跑一遍这个脚本能在不到一秒内确认基本功能没坏。

设计目标：
- 不依赖 HTTP / Uvicorn，直接调用后端模块，避免端口占用或网络抖动。
- 不依赖外网或 LLM，所有规则都基于 seed_data.json + nlp_engine.py。
- 输出统一为 `key=value` 形式，方便贴回 docs/LINE_A_A14_STEPS.md。
- 任何一个检查项失败都会让进程以非 0 退出码结束，便于纳入 CI 或 PowerShell 链式调用。
"""

from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path
from typing import Any, Callable


# 后端关键文件清单：A14 自测清单首先要保证这些文件能编译通过。
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
SOURCE_FILES = [
    BACKEND_DIR / "__init__.py",
    BACKEND_DIR / "main.py",
    BACKEND_DIR / "nlp_engine.py",
    BACKEND_DIR / "database.py",
    BACKEND_DIR / "selftest.py",
]


# 4 段 demo 文本对应预期的 detected_context.id，与 A17 demo 验收一致。
DEMO_TEXTS: list[tuple[str, str, str]] = [
    (
        "coffee_shop",
        "real-world",
        "Hi, can I get a latte with milk to go? How much is the large size?",
    ),
    (
        "doctor_pharmacy",
        "real-world",
        "I have a headache and a cough. Do I need medicine from the pharmacy?",
    ),
    (
        "kings_cross",
        "story",
        "Which platform should I use to catch the train to the magic school at King's Cross?",
    ),
    (
        "baker_street",
        "story",
        "The detective found a clue on Baker Street and tried to solve the case.",
    ),
]


# Dashboard 必须返回的字段，缺一不可，否则 CYD / Web 会渲染失败。
REQUIRED_DASHBOARD_FIELDS = (
    "saved_words",
    "saved_phrases",
    "top_context",
    "recent_keywords",
    "review_today",
)


# 单次 analyze_text 返回值必须包含的字段，与 /analyze_text API 合约保持一致。
REQUIRED_ANALYSIS_FIELDS = (
    "cleaned_text",
    "keywords",
    "phrases",
    "detected_context",
    "summary",
    "suggested_review_items",
)


def run_check(name: str, fn: Callable[[], Any]) -> tuple[bool, Any]:
    """执行单个检查项并以统一格式输出。

    返回 (通过与否, 函数返回值)。函数返回值会作为 details 行输出，方便对比。
    """
    # 任何异常都视为失败；保留异常信息方便复现。
    try:
        result = fn()
        print(f"check_{name}=pass")
        if result is not None:
            print(f"detail_{name}={result}")
        return True, result
    except AssertionError as exc:
        print(f"check_{name}=fail")
        print(f"detail_{name}=AssertionError: {exc}")
        return False, exc
    except Exception as exc:  # noqa: BLE001
        print(f"check_{name}=fail")
        print(f"detail_{name}={type(exc).__name__}: {exc}")
        return False, exc


def check_py_compile() -> str:
    # 逐个文件做 py_compile，确保所有线 A 维护的 Python 源码语法正确。
    for source_file in SOURCE_FILES:
        py_compile.compile(str(source_file), doraise=True)
    return f"compiled={len(SOURCE_FILES)}"


def check_contexts_count() -> str:
    # 初始化数据库并确认 seed_data.json 里 4 个 MVP context 全部就位。
    from backend.database import init_db, list_contexts

    init_db()
    contexts = list_contexts()
    expected_ids = {"coffee_shop", "doctor_pharmacy", "kings_cross", "baker_street"}
    actual_ids = {context["id"] for context in contexts}
    assert len(contexts) == 4, f"expected 4 contexts, got {len(contexts)}"
    assert actual_ids == expected_ids, f"context ids mismatch: {actual_ids}"
    return f"contexts_count={len(contexts)}"


def check_coffee_shop_detection() -> str:
    # A14 清单里的核心快速检查：Coffee Shop 文本应被识别为 coffee_shop。
    from backend.database import init_db, list_contexts
    from backend.nlp_engine import analyze_text

    init_db()
    result = analyze_text(
        "Hi, can I get a latte with milk to go?",
        "real-world",
        None,
        list_contexts(),
    )
    detected_id = result["detected_context"]["id"]
    assert detected_id == "coffee_shop", f"expected coffee_shop, got {detected_id}"
    return f"detected_context_id={detected_id}"


def check_demo_texts() -> str:
    # 扩展检查：把 A17 demo 的 4 段文本一次性跑一遍，确保分类规则没退化。
    from backend.database import init_db, list_contexts
    from backend.nlp_engine import analyze_text

    init_db()
    contexts = list_contexts()
    failures: list[str] = []
    for expected_id, source_type, text in DEMO_TEXTS:
        result = analyze_text(text, source_type, None, contexts)
        actual_id = result["detected_context"]["id"]
        if actual_id != expected_id:
            failures.append(f"{expected_id}!={actual_id}")
    assert not failures, "demo classification failures: " + ", ".join(failures)
    return f"demo_texts_passed={len(DEMO_TEXTS)}"


def check_analyze_fields() -> str:
    # 校验 analyze_text 返回结构，避免有人改 NLP 时漏掉字段名。
    from backend.database import init_db, list_contexts
    from backend.nlp_engine import analyze_text

    init_db()
    result = analyze_text(
        "Hi, can I get a latte with milk to go?",
        "real-world",
        None,
        list_contexts(),
    )
    missing = [field for field in REQUIRED_ANALYSIS_FIELDS if field not in result]
    assert not missing, f"missing analyze fields: {missing}"
    assert isinstance(result["keywords"], list), "keywords must be list"
    assert isinstance(result["phrases"], list), "phrases must be list"
    return "analyze_fields_ok=True"


def check_dashboard_shape() -> str:
    # 校验 dashboard 返回结构，CYD 直接消费这些字段，不能少。
    from backend.database import get_dashboard, init_db

    init_db()
    dashboard = get_dashboard()
    missing = [field for field in REQUIRED_DASHBOARD_FIELDS if field not in dashboard]
    assert not missing, f"missing dashboard fields: {missing}"

    saved_words_unique = len({item["item_text"] for item in dashboard["saved_words"]}) == len(
        dashboard["saved_words"],
    )
    saved_phrases_unique = len(
        {item["item_text"] for item in dashboard["saved_phrases"]},
    ) == len(dashboard["saved_phrases"])
    recent_unique = len(set(dashboard["recent_keywords"])) == len(dashboard["recent_keywords"])
    assert saved_words_unique, "saved_words item_text not unique"
    assert saved_phrases_unique, "saved_phrases item_text not unique"
    assert recent_unique, "recent_keywords not unique"
    assert isinstance(dashboard["review_today"], int), "review_today must be int"
    return (
        f"saved_words={len(dashboard['saved_words'])},"
        f"saved_phrases={len(dashboard['saved_phrases'])},"
        f"recent_keywords={len(dashboard['recent_keywords'])},"
        f"review_today={dashboard['review_today']}"
    )


def check_seed_data_loadable() -> str:
    # 直接加载 seed_data.json，确保格式合法且字段齐全；JSON 里禁止写注释。
    seed_path = BACKEND_DIR / "seed_data.json"
    contexts = json.loads(seed_path.read_text(encoding="utf-8"))
    required_keys = {"id", "title", "type", "tag", "summary", "seed_keywords", "seed_phrases"}
    for context in contexts:
        missing = required_keys - set(context.keys())
        assert not missing, f"seed context {context.get('id')} missing keys: {missing}"
        assert context["type"] in {"real-world", "story"}, f"bad type: {context['type']}"
    return f"seed_contexts={len(contexts)}"


def main() -> int:
    """主入口：依次运行所有自测项，返回值 0 表示全部通过。"""
    # 把项目根目录加进 sys.path，确保 `python backend/selftest.py` 直接运行也能 import backend.*。
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

    # 检查项执行顺序：先静态语法，再 seed/数据库，再 NLP，再 dashboard。
    checks = [
        ("py_compile", check_py_compile),
        ("seed_data_loadable", check_seed_data_loadable),
        ("contexts_count", check_contexts_count),
        ("coffee_shop_detection", check_coffee_shop_detection),
        ("demo_texts", check_demo_texts),
        ("analyze_fields", check_analyze_fields),
        ("dashboard_shape", check_dashboard_shape),
    ]

    results = [run_check(name, fn) for name, fn in checks]
    passed = sum(1 for ok, _ in results if ok)
    total = len(results)
    print(f"selftest_passed={passed}")
    print(f"selftest_total={total}")
    print(f"selftest_all_passed={passed == total}")
    # 全部通过返回 0；任何一项失败返回 1，便于在 PowerShell / CI 里链式判断。
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

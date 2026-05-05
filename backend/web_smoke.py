"""Scene Words Web 闭环冒烟脚本（线 A 给线 B 联调用）。

执行方式（在项目根目录 `C:\\hackathon`，前提是 Uvicorn 已经启动）：

    .\\.venv\\Scripts\\python.exe -m backend.web_smoke
    .\\.venv\\Scripts\\python.exe -m backend.web_smoke http://10.88.0.183:8000

该脚本完全用 `urllib` 调用 HTTP，不依赖 `requests` 或 `httpx` 这些三方库，
保持线 A 现有依赖不膨胀；同时模拟线 B 网页里 `fetch` 的整套调用顺序，
让线 B 在接 API 之前先有一份 "Python 版的参考调用流程"。

闭环顺序与 `LINE_A_BACKEND_TASKS.md` A15 中给线 B 的 Web 闭环一致：

    输入文本 -> POST /analyze_text -> 显示结果 -> POST /save_item -> GET /dashboard

设计目标：
- 任何字段缺失或返回结构不合预期，立刻报错，避免线 B 浪费时间排查。
- 所有输出统一为 `key=value` 文本，方便贴回 docs/LINE_A_A15_STEPS.md。
- 默认 base URL 是 `http://localhost:8000`，命令行第一个参数可改为局域网 IP。
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any


# 本地默认地址；命令行第一个参数可覆盖为局域网地址，方便线 B 模拟手机访问。
DEFAULT_BASE_URL = "http://localhost:8000"

# Web 闭环用的 4 段 demo 文本，与 A17 / 自测脚本保持一致，避免出现"自测过、Web 没过"的尴尬。
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

# /analyze_text 必须返回的字段；线 B 结果区直接消费这些字段。
REQUIRED_ANALYSIS_FIELDS = (
    "id",
    "cleaned_text",
    "keywords",
    "phrases",
    "detected_context",
    "summary",
    "suggested_review_items",
)

# /dashboard 必须返回的字段；线 B Refresh Dashboard 按钮直接渲染这些字段。
REQUIRED_DASHBOARD_FIELDS = (
    "saved_words",
    "saved_phrases",
    "top_context",
    "recent_keywords",
    "review_today",
)


def http_get(base_url: str, path: str) -> Any:
    """发送 GET 请求并解析 JSON；用 urllib 而不是 requests 避免新增依赖。"""
    # 拼接 URL 时直接字符串相加；线 A 接口都是简单 path，没有 query 编码需求。
    request = urllib.request.Request(base_url + path, method="GET")
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def http_post(base_url: str, path: str, payload: dict[str, Any]) -> Any:
    """发送 JSON POST 请求并解析 JSON 返回；与线 B 网页 fetch 行为保持一致。"""
    # 显式声明 `Content-Type: application/json`，否则 FastAPI 会按 form 解析报 422。
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_keys(name: str, payload: dict[str, Any], required: tuple[str, ...]) -> None:
    """统一的字段缺失断言，错误信息能直接指出缺哪几个字段。"""
    missing = [field for field in required if field not in payload]
    assert not missing, f"{name} missing fields: {missing}"


def run_smoke(base_url: str) -> bool:
    """跑完整 Web 闭环；任何一步失败直接抛异常，main() 会兜住并返回非 0。"""
    # Step 1: 健康检查，确认后端已经起来。
    health = http_get(base_url, "/")
    print(f"step1_health_status={health.get('status')}")
    print(f"step1_health_service={health.get('service')}")
    assert health.get("status") == "ok", "health check failed"

    # Step 2: GET /contexts，模拟网页加载下拉框。
    contexts = http_get(base_url, "/contexts")
    real_world_ids = [item["id"] for item in contexts.get("real_world", [])]
    story_ids = [item["id"] for item in contexts.get("story", [])]
    print(f"step2_real_world_ids={','.join(real_world_ids)}")
    print(f"step2_story_ids={','.join(story_ids)}")
    assert set(real_world_ids) == {"coffee_shop", "doctor_pharmacy"}, "real_world ids mismatch"
    assert set(story_ids) == {"kings_cross", "baker_street"}, "story ids mismatch"

    # Step 3: 用 4 段 demo 文本依次跑 /analyze_text，模拟用户输入并点击 Analyze。
    analyze_results: dict[str, dict[str, Any]] = {}
    for expected_id, source_type, text in DEMO_TEXTS:
        result = http_post(
            base_url,
            "/analyze_text",
            {"raw_text": text, "source_type": source_type, "optional_context": None},
        )
        assert_keys(f"/analyze_text[{expected_id}]", result, REQUIRED_ANALYSIS_FIELDS)
        actual_id = result["detected_context"]["id"]
        print(f"step3_{expected_id}_detected={actual_id}")
        assert actual_id == expected_id, f"{expected_id} classified as {actual_id}"
        analyze_results[expected_id] = result

    # Step 4: 用 Coffee Shop 的分析结果挑一个 keyword 和一个 phrase，模拟点击 Save 按钮。
    coffee_shop_result = analyze_results["coffee_shop"]
    word_to_save = coffee_shop_result["keywords"][0]
    phrase_to_save = coffee_shop_result["phrases"][0] if coffee_shop_result["phrases"] else "to go"

    save_word = http_post(
        base_url,
        "/save_item",
        {"item_text": word_to_save, "item_type": "word", "source_context": "coffee_shop"},
    )
    print(f"step4_save_word_text={word_to_save}")
    print(f"step4_save_word_id={save_word.get('id')}")
    print(f"step4_save_word_saved={save_word.get('saved')}")
    assert save_word.get("saved") is True, "save word failed"

    save_phrase = http_post(
        base_url,
        "/save_item",
        {"item_text": phrase_to_save, "item_type": "phrase", "source_context": "coffee_shop"},
    )
    print(f"step4_save_phrase_text={phrase_to_save}")
    print(f"step4_save_phrase_id={save_phrase.get('id')}")
    print(f"step4_save_phrase_saved={save_phrase.get('saved')}")
    assert save_phrase.get("saved") is True, "save phrase failed"

    # Step 5: GET /dashboard，模拟 Refresh Dashboard 按钮，验证刚保存的 item 出现。
    dashboard = http_get(base_url, "/dashboard")
    assert_keys("/dashboard", dashboard, REQUIRED_DASHBOARD_FIELDS)
    saved_word_texts = [item["item_text"] for item in dashboard["saved_words"]]
    saved_phrase_texts = [item["item_text"] for item in dashboard["saved_phrases"]]
    print(f"step5_dashboard_saved_words_count={len(saved_word_texts)}")
    print(f"step5_dashboard_saved_phrases_count={len(saved_phrase_texts)}")
    print(f"step5_dashboard_top_context={dashboard.get('top_context')}")
    print(f"step5_dashboard_review_today={dashboard.get('review_today')}")
    print(f"step5_word_visible={(word_to_save in saved_word_texts)}")
    print(f"step5_phrase_visible={(phrase_to_save in saved_phrase_texts)}")
    assert word_to_save in saved_word_texts, f"saved word {word_to_save} not visible in dashboard"
    assert phrase_to_save in saved_phrase_texts, (
        f"saved phrase {phrase_to_save} not visible in dashboard"
    )

    # 全部断言通过，闭环完整。
    return True


def main() -> int:
    """命令行入口；第一个参数可覆盖默认 base URL，方便切到局域网地址。"""
    # 优先使用命令行参数指定的 base URL；没有就用本机默认。
    base_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE_URL
    base_url = base_url.rstrip("/")
    print(f"base_url={base_url}")

    try:
        run_smoke(base_url)
    except urllib.error.HTTPError as exc:
        # 后端返回 4xx / 5xx；把 status 一并打印，方便定位是哪个 endpoint 出问题。
        print(f"smoke_status=fail")
        print(f"smoke_error=HTTPError {exc.code}: {exc.reason}")
        return 1
    except urllib.error.URLError as exc:
        # 多半是后端没启动或地址错；线 B 看到这类错应先确认 Uvicorn 是否在跑。
        print(f"smoke_status=fail")
        print(f"smoke_error=URLError: {exc.reason}")
        return 1
    except AssertionError as exc:
        # 字段缺失或值不符合预期；说明 API 合约出现回归，需要线 A 先修。
        print(f"smoke_status=fail")
        print(f"smoke_error=AssertionError: {exc}")
        return 1

    print("smoke_status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

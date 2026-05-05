"""Scene Words CYD 闭环冒烟脚本（线 A 给线 C 联调用）。

执行方式（在项目根目录 `C:\\hackathon`，前提是 Uvicorn 已经监听 0.0.0.0:8000）：

    .\\.venv\\Scripts\\python.exe -m backend.cyd_smoke
    .\\.venv\\Scripts\\python.exe -m backend.cyd_smoke http://10.88.0.183:8000

CYD 端用 MicroPython + `urequests` 调 HTTP，能力比 PC 更弱。线 A 这一侧的冒烟脚本
做两件事：

1. 模拟 CYD 的真实调用顺序（只用 CYD 关心的 4 个接口），提前把 API 合约跑一遍。
2. 模拟 "Web 保存 -> CYD Refresh dashboard" 与 "CYD 保存 -> Web Refresh dashboard"
   双向闭环，确认数据是同一份。

CYD 关心的接口（与 `LINE_A_BACKEND_TASKS.md` A16 一致）：

    GET  /contexts
    GET  /context/{id}
    POST /save_item
    GET  /dashboard

设计目标：
- 不依赖 `requests` / `httpx`，只用标准库 `urllib`，与 `web_smoke.py` 风格一致。
- 输出统一为 `key=value` 文本，方便贴回 docs/LINE_A_A16_STEPS.md。
- 任何字段缺失或值不符都立刻报错，避免 CYD 端反查后端问题。
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any


# 默认调本机；命令行第一个参数可换成局域网 IP，模拟真实 CYD 视角。
DEFAULT_BASE_URL = "http://localhost:8000"

# 4 个 MVP context 的 id，必须能逐个 GET /context/{id}。
CONTEXT_IDS = ("coffee_shop", "doctor_pharmacy", "kings_cross", "baker_street")

# CYD 场景卡片所需的字段；缺一项 CYD UI 都会渲染失败。
REQUIRED_CONTEXT_FIELDS = (
    "id",
    "title",
    "type",
    "tag",
    "summary",
    "seed_keywords",
    "seed_phrases",
)

# CYD dashboard 直接渲染的字段；与 /dashboard 合约一致。
REQUIRED_DASHBOARD_FIELDS = (
    "saved_words",
    "saved_phrases",
    "top_context",
    "recent_keywords",
    "review_today",
)


def http_get(base_url: str, path: str) -> Any:
    """用 urllib 发 GET 请求；CYD 上的 urequests.get() 行为等价。"""
    # 直接拼字符串；CYD 端 path 都是简单 ASCII，不需要再 quote。
    request = urllib.request.Request(base_url + path, method="GET")
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def http_post(base_url: str, path: str, payload: dict[str, Any]) -> Any:
    """用 urllib 发 JSON POST 请求；与 CYD urequests.post(json=...) 等价。"""
    # 显式 Content-Type，否则 FastAPI 会按 form 解析直接 422。
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
    """统一字段缺失断言，错误信息能直接指出缺哪几个字段。"""
    missing = [field for field in required if field not in payload]
    assert not missing, f"{name} missing fields: {missing}"


def run_cyd_loop(base_url: str) -> bool:
    """模拟 CYD 的完整调用顺序，并校验双向同步。"""
    # Step 1: GET /contexts，模拟 CYD Context Select 页加载。
    contexts = http_get(base_url, "/contexts")
    real_world_ids = [item["id"] for item in contexts.get("real_world", [])]
    story_ids = [item["id"] for item in contexts.get("story", [])]
    print(f"step1_real_world_ids={','.join(real_world_ids)}")
    print(f"step1_story_ids={','.join(story_ids)}")
    assert set(real_world_ids) == {"coffee_shop", "doctor_pharmacy"}, "real_world ids mismatch"
    assert set(story_ids) == {"kings_cross", "baker_street"}, "story ids mismatch"

    # Step 2: 逐个 GET /context/{id}，模拟 CYD 进入每个场景卡片。
    for context_id in CONTEXT_IDS:
        card = http_get(base_url, f"/context/{context_id}")
        assert_keys(f"/context/{context_id}", card, REQUIRED_CONTEXT_FIELDS)
        # CYD 上 keywords / phrases 直接当 chip 渲染，必须是 list。
        assert isinstance(card["seed_keywords"], list), f"{context_id} seed_keywords not list"
        assert isinstance(card["seed_phrases"], list), f"{context_id} seed_phrases not list"
        print(
            f"step2_{context_id}_card_ok=True"
            f",keywords={len(card['seed_keywords'])}"
            f",phrases={len(card['seed_phrases'])}"
        )

    # Step 3: GET /dashboard，记录 CYD 第一次刷新拿到的状态。
    dashboard_before = http_get(base_url, "/dashboard")
    assert_keys("/dashboard", dashboard_before, REQUIRED_DASHBOARD_FIELDS)
    saved_words_before = {item["item_text"] for item in dashboard_before["saved_words"]}
    saved_phrases_before = {item["item_text"] for item in dashboard_before["saved_phrases"]}
    review_today_before = dashboard_before["review_today"]
    print(f"step3_review_today_before={review_today_before}")
    print(f"step3_saved_words_count_before={len(saved_words_before)}")
    print(f"step3_saved_phrases_count_before={len(saved_phrases_before)}")

    # Step 4: 模拟 "CYD 点击保存 word"，使用一个明显属于 doctor_pharmacy 的词。
    cyd_word_text = "cyd_smoke_word"
    save_word = http_post(
        base_url,
        "/save_item",
        {
            "item_text": cyd_word_text,
            "item_type": "word",
            "source_context": "doctor_pharmacy",
        },
    )
    print(f"step4_cyd_save_word_id={save_word.get('id')}")
    print(f"step4_cyd_save_word_saved={save_word.get('saved')}")
    assert save_word.get("saved") is True, "CYD save word failed"

    # Step 5: 模拟 "CYD 点击保存 phrase"。
    cyd_phrase_text = "cyd smoke phrase"
    save_phrase = http_post(
        base_url,
        "/save_item",
        {
            "item_text": cyd_phrase_text,
            "item_type": "phrase",
            "source_context": "kings_cross",
        },
    )
    print(f"step5_cyd_save_phrase_id={save_phrase.get('id')}")
    print(f"step5_cyd_save_phrase_saved={save_phrase.get('saved')}")
    assert save_phrase.get("saved") is True, "CYD save phrase failed"

    # Step 6: 再次 GET /dashboard，模拟 CYD 点 Refresh，验证刚保存的 item 出现。
    dashboard_after = http_get(base_url, "/dashboard")
    saved_words_after = {item["item_text"] for item in dashboard_after["saved_words"]}
    saved_phrases_after = {item["item_text"] for item in dashboard_after["saved_phrases"]}
    review_today_after = dashboard_after["review_today"]
    print(f"step6_review_today_after={review_today_after}")
    print(f"step6_word_visible={cyd_word_text in saved_words_after}")
    print(f"step6_phrase_visible={cyd_phrase_text in saved_phrases_after}")
    print(f"step6_review_today_delta={review_today_after - review_today_before}")
    assert cyd_word_text in saved_words_after, "CYD-saved word not visible in dashboard"
    assert cyd_phrase_text in saved_phrases_after, "CYD-saved phrase not visible in dashboard"
    # CYD 保存 2 条，review_today 应该正好 +2（默认情况下今天没有其他写入）。
    assert review_today_after - review_today_before == 2, "review_today did not increase by 2"

    # Step 7: 模拟 "Web 保存 word -> CYD Refresh 看到"，验证反方向同步。
    web_word_text = "web_smoke_to_cyd"
    web_save = http_post(
        base_url,
        "/save_item",
        {
            "item_text": web_word_text,
            "item_type": "word",
            "source_context": "coffee_shop",
        },
    )
    print(f"step7_web_save_word_id={web_save.get('id')}")
    dashboard_after_web = http_get(base_url, "/dashboard")
    saved_words_after_web = {item["item_text"] for item in dashboard_after_web["saved_words"]}
    print(f"step7_web_word_visible_on_cyd={web_word_text in saved_words_after_web}")
    assert web_word_text in saved_words_after_web, "Web-saved word not visible from CYD view"

    return True


def main() -> int:
    """命令行入口；第一个参数可覆盖默认 base URL。"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE_URL
    base_url = base_url.rstrip("/")
    print(f"base_url={base_url}")

    try:
        run_cyd_loop(base_url)
    except urllib.error.HTTPError as exc:
        # 4xx / 5xx；CYD 上对应 urequests.Response.status_code != 200。
        print("smoke_status=fail")
        print(f"smoke_error=HTTPError {exc.code}: {exc.reason}")
        return 1
    except urllib.error.URLError as exc:
        # 多半是 Wi-Fi / 防火墙问题；CYD 上对应连接超时或 EHOSTUNREACH。
        print("smoke_status=fail")
        print(f"smoke_error=URLError: {exc.reason}")
        return 1
    except AssertionError as exc:
        # 字段缺失或值不符；说明 API 合约出现回归，需要线 A 先修。
        print("smoke_status=fail")
        print(f"smoke_error=AssertionError: {exc}")
        return 1

    print("smoke_status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())

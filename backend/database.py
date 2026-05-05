import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "scene_words.db"
SEED_PATH = Path(__file__).with_name("seed_data.json")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    # 每次按需打开 SQLite 连接；显式提交和关闭，避免 Windows 联调时残留数据库文件占用。
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    # 初始化三张 MVP 核心表：contexts、analysis_results、review_items。
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS contexts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                tag TEXT NOT NULL,
                summary TEXT NOT NULL,
                seed_keywords_json TEXT NOT NULL,
                seed_phrases_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_text TEXT NOT NULL,
                cleaned_text TEXT NOT NULL,
                detected_context TEXT NOT NULL,
                keywords_json TEXT NOT NULL,
                phrases_json TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS review_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_text TEXT NOT NULL,
                item_type TEXT NOT NULL CHECK (item_type IN ('word', 'phrase')),
                source_context TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _seed_contexts(connection)


def list_contexts() -> list[dict[str, Any]]:
    # 给 /contexts 和 NLP 分类器使用的 context 列表。
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM contexts ORDER BY type, title").fetchall()
    return [_context_from_row(row) for row in rows]


def get_context_by_id(context_id: str) -> dict[str, Any] | None:
    # 根据 id 返回一个场景卡片，供 CYD 的 context detail 页面展示。
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM contexts WHERE id = ?", (context_id,)).fetchone()
    return _context_from_row(row) if row else None


def insert_analysis(raw_text: str, result: dict[str, Any]) -> int:
    # 保存每次文本分析结果，Dashboard 后续可以统计 top context 和 recent keywords。
    detected_context = result.get("detected_context", {})
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO analysis_results (
                raw_text,
                cleaned_text,
                detected_context,
                keywords_json,
                phrases_json,
                summary
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                raw_text,
                result.get("cleaned_text", ""),
                detected_context.get("id", "unknown"),
                json.dumps(result.get("keywords", [])),
                json.dumps(result.get("phrases", [])),
                result.get("summary", ""),
            ),
        )
        return int(cursor.lastrowid)


def save_review_item(item_text: str, item_type: str, source_context: str | None = None) -> int:
    # 保存用户选择复习的单词或短语。
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO review_items (item_text, item_type, source_context)
            VALUES (?, ?, ?)
            """,
            (item_text, item_type, source_context),
        )
        return int(cursor.lastrowid)


def get_dashboard() -> dict[str, Any]:
    # 汇总 CYD dashboard 需要的五类信息：saved_words、saved_phrases、top_context、recent_keywords、review_today。
    with get_connection() as connection:
        # 取最近的 word 复习项；多取一些是为了在按 item_text 去重后仍能凑够 CYD 展示数量。
        word_rows = connection.execute(
            """
            SELECT item_text, source_context, created_at
            FROM review_items
            WHERE item_type = 'word'
            ORDER BY created_at DESC, id DESC
            LIMIT 60
            """
        ).fetchall()
        # 同样处理 phrase；CYD 屏幕窄，重复的 item_text 会挤占空间，统一在下方去重。
        phrase_rows = connection.execute(
            """
            SELECT item_text, source_context, created_at
            FROM review_items
            WHERE item_type = 'phrase'
            ORDER BY created_at DESC, id DESC
            LIMIT 60
            """
        ).fetchall()
        # top_context 基于分析历史里 detected_context 出现次数最多的 id。
        top_context = connection.execute(
            """
            SELECT detected_context, COUNT(*) AS count
            FROM analysis_results
            GROUP BY detected_context
            ORDER BY count DESC
            LIMIT 1
            """
        ).fetchone()
        # recent_keywords 取自最近 10 次分析的 keywords_json。
        recent_rows = connection.execute(
            """
            SELECT keywords_json
            FROM analysis_results
            ORDER BY created_at DESC, id DESC
            LIMIT 10
            """
        ).fetchall()
        # review_today 直接从 SQL 用本地日期过滤，避免 Python 端再做时区换算。
        review_today_row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM review_items
            WHERE DATE(created_at, 'localtime') = DATE('now', 'localtime')
            """
        ).fetchone()

    # 按 item_text 去重，保留最近一次保存记录，CYD dashboard 上不会出现重复条目。
    saved_words = _deduplicate_review_rows(word_rows, limit=20)
    saved_phrases = _deduplicate_review_rows(phrase_rows, limit=20)

    # recent_keywords 按出现顺序去重，过滤掉空字符串，保证 CYD 直接显示不需要再过滤。
    recent_keywords: list[str] = []
    for row in recent_rows:
        for keyword in json.loads(row["keywords_json"]):
            cleaned_keyword = keyword.strip() if isinstance(keyword, str) else ""
            if cleaned_keyword and cleaned_keyword not in recent_keywords:
                recent_keywords.append(cleaned_keyword)

    return {
        "saved_words": saved_words,
        "saved_phrases": saved_phrases,
        "top_context": top_context["detected_context"] if top_context else None,
        "recent_keywords": recent_keywords[:10],
        "review_today": int(review_today_row["count"]) if review_today_row else 0,
    }


def _seed_contexts(connection: sqlite3.Connection) -> None:
    # 每次启动都同步 seed data，方便比赛现场临时改 seed_data.json 后直接重启生效。
    contexts = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for context in contexts:
        connection.execute(
            """
            INSERT INTO contexts (
                id,
                title,
                type,
                tag,
                summary,
                seed_keywords_json,
                seed_phrases_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                type = excluded.type,
                tag = excluded.tag,
                summary = excluded.summary,
                seed_keywords_json = excluded.seed_keywords_json,
                seed_phrases_json = excluded.seed_phrases_json
            """,
            (
                context["id"],
                context["title"],
                context["type"],
                context["tag"],
                context["summary"],
                json.dumps(context["seed_keywords"]),
                json.dumps(context["seed_phrases"]),
            ),
        )


def _context_from_row(row: sqlite3.Row) -> dict[str, Any]:
    # SQLite 里 JSON 字段转回 Python list，保持 API 返回结构清晰。
    return {
        "id": row["id"],
        "title": row["title"],
        "type": row["type"],
        "tag": row["tag"],
        "summary": row["summary"],
        "seed_keywords": json.loads(row["seed_keywords_json"]),
        "seed_phrases": json.loads(row["seed_phrases_json"]),
    }


def _review_from_row(row: sqlite3.Row) -> dict[str, Any]:
    # 统一 review item 的 API 输出格式。
    return {
        "item_text": row["item_text"],
        "source_context": row["source_context"],
        "created_at": row["created_at"],
    }


def _deduplicate_review_rows(rows: list[sqlite3.Row], limit: int) -> list[dict[str, Any]]:
    # 按 item_text 去重，保留最近一次保存（rows 已按 created_at DESC 排序），最多返回 limit 个。
    seen_item_texts: set[str] = set()
    unique_items: list[dict[str, Any]] = []
    for row in rows:
        item_text = row["item_text"]
        if item_text in seen_item_texts:
            continue
        seen_item_texts.add(item_text)
        unique_items.append(_review_from_row(row))
        if len(unique_items) >= limit:
            break
    return unique_items

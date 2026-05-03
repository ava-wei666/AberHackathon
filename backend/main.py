from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .database import (
    get_context_by_id,
    get_dashboard,
    init_db,
    insert_analysis,
    list_contexts,
    save_review_item,
)
from .nlp_engine import analyze_text


# 请求模型：网页端或 CYD 端把原始文本和来源类型发给后端。
class AnalyzeTextRequest(BaseModel):
    raw_text: str = Field(..., min_length=1)
    source_type: Literal["real-world", "story"] = "real-world"
    optional_context: str | None = None

    @field_validator("raw_text")
    @classmethod
    def normalize_raw_text(cls, value: str) -> str:
        # 去掉用户输入前后的空白，避免纯空格文本进入 NLP 分析流程。
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("raw_text cannot be empty")
        return stripped_value

    @field_validator("optional_context")
    @classmethod
    def normalize_optional_context(cls, value: str | None) -> str | None:
        # 空字符串和纯空格都按未指定 context 处理，方便 Web / CYD 直接传表单值。
        if value is None:
            return None
        stripped_value = value.strip()
        return stripped_value or None


# 请求模型：保存一个单词或短语到复习列表。
class SaveItemRequest(BaseModel):
    item_text: str = Field(..., min_length=1)
    item_type: Literal["word", "phrase"]
    source_context: str | None = None

    @field_validator("item_text")
    @classmethod
    def normalize_item_text(cls, value: str) -> str:
        # 保存复习项前统一裁剪空白，确保 review_items 里不会出现空内容。
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("item_text cannot be empty")
        return stripped_value

    @field_validator("source_context")
    @classmethod
    def normalize_source_context(cls, value: str | None) -> str | None:
        # source_context 允许为空；传空字符串时写入 NULL，保持 Dashboard 数据干净。
        if value is None:
            return None
        stripped_value = value.strip()
        return stripped_value or None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动时自动建表并写入 4 个 MVP context seed data。
    init_db()
    yield


app = FastAPI(title="Scene Words API", version="0.1.0", lifespan=lifespan)

# Hackathon 本地联调阶段允许跨域，方便手机网页、电脑网页和 CYD 同时访问 laptop 后端。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check() -> dict[str, str]:
    # 最简单的健康检查接口，用来确认后端服务已经起来。
    return {"status": "ok", "service": "Scene Words API"}


@app.post("/analyze_text")
def analyze_text_endpoint(payload: AnalyzeTextRequest) -> dict:
    # 统一分析入口：Input -> NLP Engine -> Context Tagging -> Storage -> API response。
    contexts = list_contexts()
    result = analyze_text(
        raw_text=payload.raw_text,
        source_type=payload.source_type,
        optional_context=payload.optional_context,
        contexts=contexts,
    )
    analysis_id = insert_analysis(payload.raw_text, result)
    return {"id": analysis_id, **result}


@app.get("/contexts")
def contexts_endpoint() -> dict:
    # CYD 和网页端用这个接口渲染 Real-world / Story 两类 context 选择页。
    contexts = list_contexts()
    return {
        "real_world": [context for context in contexts if context["type"] == "real-world"],
        "story": [context for context in contexts if context["type"] == "story"],
    }


@app.get("/context/{context_id}")
def context_endpoint(context_id: str) -> dict:
    # 返回某个预设 context 的地点卡片 / 场景卡片内容。
    context = get_context_by_id(context_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Context not found")
    return context


@app.post("/save_item")
def save_item_endpoint(payload: SaveItemRequest) -> dict:
    # 用户点 Save Word / Save Phrase 后，保存到 SQLite 复习表。
    item_id = save_review_item(
        item_text=payload.item_text,
        item_type=payload.item_type,
        source_context=payload.source_context,
    )
    return {"id": item_id, "saved": True}


@app.get("/dashboard")
def dashboard_endpoint() -> dict:
    # Dashboard 汇总接口：CYD 最终主要轮询或手动刷新这个接口。
    return get_dashboard()

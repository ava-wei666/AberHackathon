import re
from collections import Counter
from typing import Any


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "could",
    "for",
    "from",
    "have",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "please",
    "that",
    "the",
    "this",
    "to",
    "we",
    "with",
    "you",
}

FILLER_WORDS = {"um", "uh", "erm", "hmm", "like", "actually", "basically", "okay", "ok"}

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z']*")


def analyze_text(
    raw_text: str,
    source_type: str = "real-world",
    optional_context: str | None = None,
    contexts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    # MVP 的主 NLP 管线：分词 -> 清洗 -> 关键词 -> 情境分类 -> 短语 -> 学习总结。
    contexts = contexts or []
    tokens = _tokenize(raw_text)
    cleaned_tokens = _clean_tokens(tokens)
    keywords = _extract_keywords(cleaned_tokens)
    detected_context = _classify_context(cleaned_tokens, source_type, optional_context, contexts)
    phrases = _extract_phrases(raw_text, cleaned_tokens, detected_context)
    summary = _build_summary(detected_context, keywords, phrases)

    return {
        "cleaned_text": " ".join(cleaned_tokens),
        "keywords": keywords,
        "phrases": phrases,
        "detected_context": detected_context,
        "summary": summary,
        "suggested_review_items": keywords[:3] + phrases[:2],
    }


def _tokenize(text: str) -> list[str]:
    # 只保留英文词 token，先满足本次英语学习 MVP 的演示范围。
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def _clean_tokens(tokens: list[str]) -> list[str]:
    # 清理 filler words、stopwords 和连续重复词，得到更适合统计的 token。
    cleaned: list[str] = []
    previous = None

    for token in tokens:
        token = token.strip("'")
        if not token or token in STOPWORDS or token in FILLER_WORDS:
            continue
        if token == previous:
            continue
        cleaned.append(token)
        previous = token

    return cleaned


def _extract_keywords(tokens: list[str], limit: int = 5) -> list[str]:
    # 关键词先用词频做，稳定、透明，而且没有外部模型依赖。
    counts = Counter(token for token in tokens if len(token) > 2)
    return [word for word, _ in counts.most_common(limit)]


def _extract_phrases(
    raw_text: str,
    tokens: list[str],
    detected_context: dict[str, Any],
    limit: int = 3,
) -> list[str]:
    # 短语优先匹配当前 context 的 seed phrases，再从清洗后的 token 里拼 2-3 词短语。
    raw_lower = raw_text.lower()
    phrases: list[str] = []

    for phrase in detected_context.get("seed_phrases", []):
        if phrase.lower() in raw_lower:
            phrases.append(_title_phrase(phrase))

    for size in (3, 2):
        for index in range(0, max(len(tokens) - size + 1, 0)):
            candidate_tokens = tokens[index : index + size]
            if any(len(token) <= 2 for token in candidate_tokens):
                continue
            candidate = " ".join(candidate_tokens)
            if candidate not in phrases:
                phrases.append(candidate)
            if len(phrases) >= limit:
                return phrases[:limit]

    return phrases[:limit]


def _classify_context(
    tokens: list[str],
    source_type: str,
    optional_context: str | None,
    contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    # 如果前端已经指定 context，就直接信任这个选择；否则按 seed keywords 做简单打分。
    context_pool = [context for context in contexts if context.get("type") == source_type] or contexts

    if optional_context:
        selected = next((context for context in contexts if context.get("id") == optional_context), None)
        if selected:
            return _public_context(selected, confidence=1.0)

    token_counts = Counter(tokens)
    best_context: dict[str, Any] | None = None
    best_score = 0

    for context in context_pool:
        keywords = set(context.get("seed_keywords", []))
        title_words = set(_tokenize(context.get("title", "")))
        tag_words = set(_tokenize(context.get("tag", "")))
        signal_words = keywords | title_words | tag_words
        score = sum(token_counts[word] for word in signal_words)

        # 分数最高的 context 就是本次输入的 detected context。
        if score > best_score:
            best_context = context
            best_score = score

    if best_context is None and context_pool:
        best_context = context_pool[0]

    confidence = min(0.95, 0.45 + best_score * 0.12) if best_score else 0.35
    return _public_context(best_context or {}, confidence=confidence)


def _public_context(context: dict[str, Any], confidence: float) -> dict[str, Any]:
    # 只暴露前端需要展示的 context 字段，避免把内部结构直接泄露出去。
    return {
        "id": context.get("id", "unknown"),
        "title": context.get("title", "Unknown Context"),
        "type": context.get("type", "unknown"),
        "tag": context.get("tag", "unknown"),
        "summary": context.get("summary", ""),
        "seed_phrases": context.get("seed_phrases", []),
        "confidence": round(confidence, 2),
    }


def _title_phrase(phrase: str) -> str:
    # 展示用的小工具：把短语首字母做轻量格式化。
    small_words = {"a", "an", "and", "for", "in", "of", "the", "to", "with"}
    words = phrase.split()
    return " ".join(word if word in small_words else word.capitalize() for word in words)


def _build_summary(
    detected_context: dict[str, Any],
    keywords: list[str],
    phrases: list[str],
) -> str:
    # LLM 接入前先用模板生成 summary，保证没有网络和 API key 时仍然能演示。
    title = detected_context.get("title", "this context")
    focus_terms = ", ".join(keywords[:3]) if keywords else "core vocabulary"
    phrase_tip = f" Practice phrases like '{phrases[0]}'." if phrases else ""
    return f"This looks like {title}. Focus on {focus_terms}.{phrase_tip}"

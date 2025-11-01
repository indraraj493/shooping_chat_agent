import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from rapidfuzz import fuzz, process


BRANDS = [
    "Samsung",
    "OnePlus",
    "Xiaomi",
    "Redmi",
    "Realme",
    "Poco",
    "Google",
    "Pixel",
    "Motorola",
    "iQOO",
    "Nothing",
]

FEATURE_SYNONYMS: Dict[str, Set[str]] = {
    "camera": {"camera", "ois", "eis", "stabilization", "photo", "photos"},
    "battery": {"battery", "battery life", "battery king", "screen on", "sot"},
    "charging": {"charging", "fast charging", "charger", "warp", "supervooc", "watt"},
    "display": {"display", "screen", "amoled", "oled", "lcd", "hdr"},
    "performance": {"performance", "gaming", "processor", "chip", "snapdragon", "dimensity"},
    "compact": {"compact", "one-hand", "one hand", "small", "6.1", "6 inch"},
}

EXPLAIN_TOPICS = {
    "ois": "OIS (Optical Image Stabilization) uses moving lens/sensor hardware to counter hand shake, improving sharpness in low light and longer exposures.",
    "eis": "EIS (Electronic Image Stabilization) crops and warps frames in software to smooth video. It helps with video jitter but can reduce FOV/detail.",
    "ois vs eis": "OIS is hardware-based stabilization that helps photos and low-light; EIS is software-based and helps video smoothing. Many phones combine both.",
}


@dataclass
class ParsedQuery:
    original: str
    mode: str = "recommend"  # recommend | compare | explain
    # Backward-compat: budget kept for old callers; new logic uses min_price/max_price
    budget: Optional[int] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    brand: Optional[str] = None
    features: List[str] = field(default_factory=list)
    compact: Optional[bool] = None
    compare_models: List[str] = field(default_factory=list)
    topic: Optional[str] = None


def _normalize_num(token: str) -> Optional[int]:
    tok = token.lower().replace(",", "").strip()
    m = re.match(r"₹?\s*(\d{2,7})(?:\s*k)?", tok)
    if not m:
        return None
    val = int(m.group(1))
    if tok.endswith("k"):
        return val * 1000
    return val


def _parse_price_span(text: str) -> (Optional[int], Optional[int]):
    t = text.lower().replace(",", " ")

    # between X and Y / from X to Y / X to Y / X - Y
    range_patterns = [
        r"between\s+([₹\d\s]+)\s+and\s+([₹\d\s]+)",
        r"from\s+([₹\d\s]+)\s+to\s+([₹\d\s]+)",
        r"([₹\d\s]+)\s*(?:to|-)\s*([₹\d\s]+)",
    ]
    for pat in range_patterns:
        m = re.search(pat, t)
        if m:
            a = _normalize_num(m.group(1))
            b = _normalize_num(m.group(2))
            if a and b:
                lo, hi = (a, b) if a <= b else (b, a)
                return lo, hi

    # under/below/<=/less than/up to
    m = re.search(r"(?:under|below|<=|less than|up to|upto)\s*([₹\d\s]+)", t)
    if m:
        hi = _normalize_num(m.group(1))
        return None, hi

    # above/over/>=/more than
    m = re.search(r"(?:above|over|>=|more than)\s*([₹\d\s]+)", t)
    if m:
        lo = _normalize_num(m.group(1))
        return lo, None

    # lone number implies a budget cap (max)
    m = re.search(r"₹?\s*(\d{2,7})\s*k?", t)
    if m:
        num = _normalize_num(m.group(0))
        return None, num

    return None, None


def _parse_brand(text: str, index: Dict[str, List[str]]) -> Optional[str]:
    # Strict word-boundary brand detection first
    lowered = text.lower()
    explicit_found: List[str] = []
    for b in set(BRANDS) | set(index.get("brands", [])):
        pattern = rf"\b{re.escape(b.lower())}\b"
        if re.search(pattern, lowered):
            name = "Google" if b.lower() == "pixel" else b
            explicit_found.append(name)
    if explicit_found:
        # If multiple brands explicitly mentioned, prefer the first occurrence order
        # Find first by position in text
        positions = []
        for b in explicit_found:
            key = "pixel" if b.lower() == "google" else b.lower()
            m = re.search(rf"\b{re.escape(key)}\b", lowered)
            positions.append((m.start() if m else 0, b))
        positions.sort(key=lambda x: x[0])
        return positions[0][1]

    # Fallback: fuzzy brand match only if highly confident and brand-like query
    candidates = list(set(BRANDS) | set(index.get("brands", [])))
    best = process.extractOne(text, candidates, scorer=fuzz.token_set_ratio)
    if best and best[1] >= 92:
        if best[0].lower() == "pixel":
            return "Google"
        return best[0]
    return None


def _parse_features(text: str) -> List[str]:
    t = text.lower()
    feats: Set[str] = set()
    for feat, synonyms in FEATURE_SYNONYMS.items():
        for s in synonyms:
            if s in t:
                feats.add(feat)
    return list(feats)


def _parse_compact(text: str) -> Optional[bool]:
    if re.search(r"\b(one[-\s]?hand|compact|small)\b", text, re.I):
        return True
    return None


def _parse_compare(text: str, index: Dict[str, List[str]]) -> List[str]:
    # Detect patterns: "A vs B", "compare A and B"
    models = []
    if " vs " in text.lower() or " compare " in text.lower():
        # naive split by vs/and, then fuzzy match to model names
        raw_parts = re.split(r"\bvs\b|\band\b|,|/", text, flags=re.I)
        raw_parts = [p.strip() for p in raw_parts if p.strip()]
        model_index = index.get("models", [])
        for p in raw_parts:
            best = process.extractOne(p, model_index, scorer=fuzz.token_set_ratio)
            if best and best[1] >= 80:
                models.append(best[0])
    # Limit to top 3
    return list(dict.fromkeys(models))[:3]


def _parse_explain(text: str) -> Optional[str]:
    lowered = text.lower()
    if "explain" in lowered or "what is" in lowered:
        if "ois" in lowered and "eis" in lowered:
            return "ois vs eis"
        if "ois" in lowered:
            return "ois"
        if "eis" in lowered:
            return "eis"
    # Direct topic queries like "OIS vs EIS"
    if "ois vs eis" in lowered:
        return "ois vs eis"
    return None


def parse_query(text: str, index: Dict[str, List[str]]) -> ParsedQuery:
    pq = ParsedQuery(original=text)

    topic = _parse_explain(text)
    if topic:
        pq.mode = "explain"
        pq.topic = topic
        return pq

    compare_models = _parse_compare(text, index)
    if compare_models:
        pq.mode = "compare"
        pq.compare_models = compare_models
        return pq

    min_price, max_price = _parse_price_span(text)
    pq.min_price = min_price
    pq.max_price = max_price
    # legacy field for downstream rationale that might still read budget
    pq.budget = max_price
    pq.brand = _parse_brand(text, index)
    pq.features = _parse_features(text)
    pq.compact = _parse_compact(text)
    return pq



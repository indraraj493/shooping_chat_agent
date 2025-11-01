from typing import Dict, List
from app.services.retrieval import Phone


def _format_price(p: int) -> str:
    # Format as ₹xx,xxx
    s = f"{p:,}"
    return f"₹{s}"


def _summarize_phone(p: Phone) -> str:
    parts: List[str] = []
    parts.append(f"{p.camera_mp}MP camera" + (" with OIS" if p.ois else ""))
    parts.append(f"{p.battery_mah}mAh, {p.charging_w}W fast charging")
    parts.append(("AMOLED" if p.amoled else "LCD") + f" {p.display_inches:.1f}\" display")
    parts.append(p.soc)
    return ", ".join(parts)


def build_recommendations_response(query, phones: List[Phone], top_k: int = 3) -> Dict:
    top = phones[:top_k]
    items = []
    for p in top:
        items.append({
            "id": p.id,
            "name": f"{p.brand} {p.model}",
            "price": _format_price(p.price),
            "summary": _summarize_phone(p),
            "pros": p.pros,
            "cons": p.cons,
        })

    rationale_bits: List[str] = []
    if getattr(query, 'min_price', None) and not getattr(query, 'max_price', None):
        rationale_bits.append(f"over {_format_price(query.min_price)}")
    if getattr(query, 'max_price', None) and not getattr(query, 'min_price', None):
        rationale_bits.append(f"under {_format_price(query.max_price)}")
    if getattr(query, 'min_price', None) and getattr(query, 'max_price', None):
        rationale_bits.append(f"in {_format_price(query.min_price)}–{_format_price(query.max_price)} range")
    if query.brand:
        rationale_bits.append(f"from {query.brand}")
    if query.features:
        rationale_bits.append("focused on " + ", ".join(query.features))
    if query.compact:
        rationale_bits.append("compact, one-hand friendly")

    rationale = "; ".join(rationale_bits) if rationale_bits else "best overall picks"

    return {
        "type": "recommendations",
        "rationale": f"Top {len(items)} matches {rationale}:",
        "items": items,
    }


def build_comparison_response(phones: List[Phone]) -> Dict:
    items = []
    for p in phones[:3]:
        items.append({
            "id": p.id,
            "name": f"{p.brand} {p.model}",
            "price": _format_price(p.price),
            "camera": f"{p.camera_mp}MP{" with OIS" if p.ois else ""}",
            "battery": f"{p.battery_mah}mAh, {p.charging_w}W",
            "display": f"{'AMOLED' if p.amoled else 'LCD'} {p.display_inches:.1f}\"",
            "soc": p.soc,
            "pros": p.pros,
            "cons": p.cons,
        })
    return {"type": "comparison", "items": items}


def build_explainer_response(topic: str) -> Dict:
    if topic == "ois vs eis":
        text = (
            "OIS is hardware stabilization that helps photos and low light; "
            "EIS is software stabilization that smooths video. Many phones combine both."
        )
    elif topic == "ois":
        text = (
            "OIS (Optical Image Stabilization) uses moving lens/sensor to reduce hand shake, "
            "improving sharpness in low light and longer exposures."
        )
    else:
        text = (
            "EIS (Electronic Image Stabilization) crops/warps frames in software to smooth video; "
            "it helps with jitter but can reduce field of view."
        )

    return {"type": "explainer", "message": text}



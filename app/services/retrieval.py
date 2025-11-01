import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
from rapidfuzz import fuzz, process


@dataclass
class Phone:
    id: str
    brand: str
    model: str
    price: int
    camera_mp: int
    ois: bool
    eis: bool
    battery_mah: int
    charging_w: int
    display_inches: float
    amoled: bool
    soc: str
    compact: bool
    summary: str
    pros: List[str]
    cons: List[str]


class PhoneCatalog:
    def __init__(self, data_path: str):
        self._data_path = Path(data_path)
        self._phones: List[Phone] = []
        self._index: Dict[str, List[str]] = {}
        self._load()

    def _load(self):
        raw = json.loads(self._data_path.read_text(encoding="utf-8"))
        self._phones = [Phone(**p) for p in raw]
        brands = sorted(list({p.brand for p in self._phones}))
        models = [f"{p.brand} {p.model}" for p in self._phones]
        self._index = {"brands": brands, "models": models}

    def get_index(self) -> Dict[str, List[str]]:
        return self._index

    def all(self) -> List[Phone]:
        return list(self._phones)

    def match_by_names(self, names: List[str]) -> List[Phone]:
        items: List[Phone] = []
        full_names = [f"{p.brand} {p.model}" for p in self._phones]
        for name in names:
            best = process.extractOne(name, full_names, scorer=fuzz.token_set_ratio)
            if best and best[1] >= 80:
                idx = full_names.index(best[0])
                items.append(self._phones[idx])
        # Dedupe
        seen = set()
        unique = []
        for p in items:
            if p.id not in seen:
                unique.append(p)
                seen.add(p.id)
        return unique

    def search(
        self,
        min_price: Optional[int],
        max_price: Optional[int],
        brand: Optional[str],
        features: List[str],
        compact: Optional[bool],
    ) -> List[Phone]:
        candidates = self._phones
        if min_price is not None:
            candidates = [p for p in candidates if p.price >= min_price]
        if max_price is not None:
            candidates = [p for p in candidates if p.price <= max_price]
        if brand:
            candidates = [p for p in candidates if p.brand.lower() == brand.lower()]
        if compact is True:
            candidates = [p for p in candidates if p.compact]

        # Simple feature filters
        def has_feature(p: Phone, feat: str) -> bool:
            if feat == "camera":
                return p.camera_mp >= 50
            if feat == "battery":
                return p.battery_mah >= 5000
            if feat == "charging":
                return p.charging_w >= 30
            if feat == "display":
                return p.amoled is True
            if feat == "performance":
                return any(x in p.soc.lower() for x in ["snapdragon", "dimensity", "tensor"])  # noqa
            if feat == "compact":
                return p.compact
            return True

        for feat in features:
            candidates = [p for p in candidates if has_feature(p, feat)]

        # Rank by simple heuristic score
        def score(p: Phone) -> float:
            s = 0.0
            # value for money
            s += min(1.0, 30000 / max(1.0, p.price)) * 2.0
            # camera
            s += (p.camera_mp / 108) * 1.2 + (1.0 if p.ois else 0.0)
            # battery/charging
            s += (p.battery_mah / 6000) * 1.0 + (p.charging_w / 120) * 0.8
            # display
            s += (1.0 if p.amoled else 0.0) * 0.6
            # compact bonus if requested
            if compact:
                s += (1.0 if p.compact else 0.0)
            return s

        ranked = sorted(candidates, key=score, reverse=True)
        return ranked



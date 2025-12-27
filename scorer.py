import json
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

@dataclass
class ItemResult:
    section: str
    item: str
    pattern: str
    count: int
    unit_points: float
    raw_points: float
    capped_item_points: float
    item_max_points: float
    evidence: str

def load_criteria(path: str = "criteria.json") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _compile(pattern: str) -> re.Pattern:
    # Tus patterns ya traen (?is) etc. Si no traen, igual funcionan.
    return re.compile(pattern)

def _pick_evidence(text: str, m: re.Match, max_chars: int = 260) -> str:
    start = max(0, m.start() - 80)
    end = min(len(text), m.end() + 120)
    snippet = text[start:end]
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet[:max_chars]

def score_text(
    text: str,
    criteria: Dict[str, Any],
    evidence_max_chars: int = 260
) -> Tuple[List[ItemResult], Dict[str, float], float, str, Dict[str, Any]]:
    """
    Regla EXACTA solicitada en meta.counting:
    - contar cada match
    - aplicar tope por item (max_points del item)
    - sumar a sección
    - aplicar tope por sección (max_points de la sección)
    - sumar al total
    """
    sections = criteria.get("sections", {})
    categorias = criteria.get("categorias", {})

    results: List[ItemResult] = []
    section_totals: Dict[str, float] = {}
    total_points = 0.0

    for section_name, sec in sections.items():
        sec_max = float(sec.get("max_points", 10**9))
        sec_sum = 0.0

        items = sec.get("items", {})
        for item_name, item in items.items():
            pattern = item.get("pattern", "")
            if not pattern:
                continue

            unit_points = float(item.get("unit_points", 0))
            item_max = float(item.get("max_points", 0))

            rx = _compile(pattern)
            matches = list(rx.finditer(text))
            count = len(matches)

            raw_points = count * unit_points

            # Tope por ítem (si max_points=0, queda en 0; si es >0, aplica)
            capped_item_points = raw_points
            if item_max >= 0:
                capped_item_points = min(raw_points, item_max)

            evidence = ""
            if matches:
                evidence = _pick_evidence(text, matches[0], max_chars=evidence_max_chars)

            results.append(
                ItemResult(
                    section=section_name,
                    item=item_name,
                    pattern=pattern,
                    count=count,
                    unit_points=unit_points,
                    raw_points=raw_points,
                    capped_item_points=capped_item_points,
                    item_max_points=item_max,
                    evidence=evidence,
                )
            )

            sec_sum += capped_item_points

        # Tope por sección
        sec_sum = min(sec_sum, sec_max)
        section_totals[section_name] = sec_sum
        total_points += sec_sum

    # Categoría: toma el mayor min_points que sea <= total_points
    category = "VI"
    if categorias:
        ordered = sorted(
            categorias.items(),
            key=lambda kv: float(kv[1].get("min_points", 0)),
            reverse=True
        )
        for cat, info in ordered:
            if total_points >= float(info.get("min_points", 0)):
                category = cat
                break

    return results, section_totals, total_points, category, categorias

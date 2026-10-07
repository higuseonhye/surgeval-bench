"""Heuristic failure tags. These tags are review aids, not clinical findings."""

from __future__ import annotations

from surgeval.labels import PHASES, canonical_phase
from surgeval.metrics import abstained, is_correct
from surgeval.schema import Item, Prediction

OVERCONFIDENCE = 0.85
OCCLUSION = {"smoke", "blood", "fog"}


def _phase_index(text: str | None) -> int | None:
    if text is None:
        return None
    name = canonical_phase(text)
    if name is None:
        return None
    return PHASES.index(name)


def annotate(items: list[Item], preds: dict[str, Prediction]) -> dict[str, list[str]]:
    """Return failure tags keyed by item id.

    Explicit tags already stored on a prediction are kept. Heuristics fire only
    when the answer is wrong:

    - confidence >= 0.85 -> overconfidence_hallucination
    - item.occlusion in {smoke, blood, fog} -> visual_occlusion
    - item.ambiguity -> anatomical_ambiguity
    - phase prediction jumps more than one phase from the previous prediction
      on the same video -> temporal_inconsistency
    - otherwise -> unclassified_error
    """
    tags: dict[str, list[str]] = {}
    phase_rows = [
        item
        for item in items
        if item.task == "phase" and item.video_id is not None and item.frame_idx is not None
    ]
    phase_rows.sort(key=lambda item: (item.video_id or "", item.frame_idx or 0))
    previous_pred_index: dict[str, int] = {}

    temporal_ids: set[str] = set()
    for item in phase_rows:
        pred = preds.get(item.id)
        current = _phase_index(None if pred is None else pred.pred)
        previous = previous_pred_index.get(item.video_id or "")
        if (
            pred is not None
            and not is_correct(item, pred)
            and current is not None
            and previous is not None
            and abs(current - previous) > 1
        ):
            temporal_ids.add(item.id)
        if current is not None and item.video_id is not None:
            previous_pred_index[item.video_id] = current

    for item in items:
        pred = preds.get(item.id)
        found: list[str] = []
        if pred is not None:
            found.extend(pred.failure_tags)
        if pred is None or abstained(item.task, pred) or is_correct(item, pred):
            tags[item.id] = _unique(found)
            continue
        if pred.confidence is not None and pred.confidence >= OVERCONFIDENCE:
            found.append("overconfidence_hallucination")
        if item.occlusion in OCCLUSION:
            found.append("visual_occlusion")
        if item.ambiguity:
            found.append("anatomical_ambiguity")
        if item.id in temporal_ids:
            found.append("temporal_inconsistency")
        if not found:
            found.append("unclassified_error")
        tags[item.id] = _unique(found)
    return tags


def _unique(tags: list[str]) -> list[str]:
    seen: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.append(tag)
    return seen


def counts(tag_map: dict[str, list[str]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for tags in tag_map.values():
        for tag in tags:
            totals[tag] = totals.get(tag, 0) + 1
    return dict(sorted(totals.items()))

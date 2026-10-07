"""Scoring. Abstention is kept separate from a wrong answer."""

from __future__ import annotations

from surgeval.labels import (
    PHASES,
    canonical_phase,
    canonical_tool,
    canonical_yes_no,
    compact,
)
from surgeval.schema import Item, Prediction

GROUNDING_IOU = 0.5


def iou(box_a: list[float], box_b: list[float]) -> float:
    if len(box_a) != 4 or len(box_b) != 4:
        raise ValueError("bounding boxes must contain four numbers, xyxy")
    ax1, ay1, ax2, ay2 = (float(v) for v in box_a)
    bx1, by1, bx2, by2 = (float(v) for v in box_b)
    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


def normalize_answer(task: str, text: str | None) -> str | None:
    if text is None:
        return None
    raw = compact(text)
    if raw in {"", "abstain", "unknown", "unsure"}:
        return None
    if task == "phase":
        return canonical_phase(raw)
    if task in {"tool_presence", "safety"}:
        return canonical_yes_no(raw)
    if task == "tool_count":
        digits = "".join(ch for ch in raw if ch.isdigit())
        return digits or None
    if task == "grounding":
        return canonical_tool(raw) or raw
    return raw


def is_correct(item: Item, pred: Prediction) -> bool:
    if item.task == "grounding":
        if not item.gold_bbox or not pred.pred_bbox:
            return False
        label_ok = normalize_answer("grounding", item.gold) == normalize_answer(
            "grounding", pred.pred
        )
        return label_ok and iou(item.gold_bbox, pred.pred_bbox) >= GROUNDING_IOU
    gold = normalize_answer(item.task, item.gold)
    answer = normalize_answer(item.task, pred.pred)
    if gold is None or answer is None:
        return False
    return gold == answer


def _f1(gold: list[str], pred: list[str], label: str) -> float:
    tp = sum(g == label and p == label for g, p in zip(gold, pred))
    fp = sum(g != label and p == label for g, p in zip(gold, pred))
    fn = sum(g == label and p != label for g, p in zip(gold, pred))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def macro_f1(gold: list[str | None], pred: list[str | None]) -> float | None:
    labels = sorted({g for g in gold if g is not None})
    if not labels:
        return None
    filled_pred = [p if p is not None else "" for p in pred]
    filled_gold = [g if g is not None else "" for g in gold]
    scores = [_f1(filled_gold, filled_pred, label) for label in labels]
    return sum(scores) / len(scores)


def abstained(task: str, pred: Prediction | None) -> bool:
    return _answered(task, pred) is None


def _answered(task: str, pred: Prediction | None) -> str | None:
    if pred is None:
        return None
    if task == "grounding":
        if not pred.pred_bbox:
            return None
        return normalize_answer(task, pred.pred) or "box"
    return normalize_answer(task, pred.pred)


def score(items: list[Item], preds: dict[str, Prediction]) -> dict:
    by_task: dict[str, dict] = {}
    grouped: dict[str, list[tuple[Item, Prediction | None]]] = {}
    for item in items:
        grouped.setdefault(item.task, []).append((item, preds.get(item.id)))

    for task, pairs in grouped.items():
        gold_norm: list[str | None] = []
        pred_norm: list[str | None] = []
        correct = 0
        abstain = 0
        ious: list[float] = []
        hits = 0
        false_alarms = 0
        misses = 0
        for item, pred in pairs:
            gold_norm.append(normalize_answer(task, item.gold))
            answer = _answered(task, pred)
            pred_norm.append(answer)
            if answer is None:
                abstain += 1
                continue
            assert pred is not None
            if task == "grounding" and item.gold_bbox and pred.pred_bbox:
                overlap = iou(item.gold_bbox, pred.pred_bbox)
                ious.append(overlap)
                if overlap >= GROUNDING_IOU:
                    hits += 1
            if is_correct(item, pred):
                correct += 1
            elif task == "safety":
                gold_yn = normalize_answer(task, item.gold)
                if gold_yn == "no" and answer == "yes":
                    false_alarms += 1
                if gold_yn == "yes" and answer == "no":
                    misses += 1
        n = len(pairs)
        answered = n - abstain
        block = {
            "n": n,
            "correct": correct,
            "abstain": abstain,
            "accuracy_strict": correct / n if n else None,
            "accuracy_answered": correct / answered if answered else None,
            "macro_f1": macro_f1(gold_norm, pred_norm),
        }
        if task == "grounding":
            block["mean_iou"] = sum(ious) / len(ious) if ious else None
            block["success_at_0_5"] = hits / n if n else None
            # Name-only F1 hides a wrong box. Localization is reported as IoU.
            block["macro_f1"] = None
        if task == "safety":
            block["false_alarms"] = false_alarms
            block["confident_misses"] = misses
        if task == "phase":
            block["label_set"] = list(PHASES)
        by_task[task] = block

    n = len(items)
    correct = sum(block["correct"] for block in by_task.values())
    abstain = sum(block["abstain"] for block in by_task.values())
    return {
        "n": n,
        "correct": correct,
        "abstain": abstain,
        "accuracy_strict": correct / n if n else None,
        "by_task": by_task,
    }

"""JSONL records for items and model predictions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Item:
    id: str
    task: str
    query: str
    gold: str
    video_id: str | None = None
    frame_idx: int | None = None
    target: str | None = None
    choices: list[str] | None = None
    image: str | None = None
    gold_bbox: list[float] | None = None
    occlusion: str | None = None
    ambiguity: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Prediction:
    id: str
    pred: str | None
    confidence: float | None = None
    pred_bbox: list[float] | None = None
    failure_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no} is not valid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no} must be a JSON object")
        rows.append(row)
    return rows


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(body + ("\n" if body else ""), encoding="utf-8")


def item_from_dict(row: dict) -> Item:
    if "id" not in row or "task" not in row or "gold" not in row:
        raise ValueError(f"item {row.get('id', '?')} needs id, task, and gold")
    return Item(
        id=str(row["id"]),
        task=str(row["task"]),
        query=str(row.get("query") or ""),
        gold=str(row["gold"]),
        video_id=row.get("video_id"),
        frame_idx=None if row.get("frame_idx") is None else int(row["frame_idx"]),
        target=row.get("target"),
        choices=row.get("choices"),
        image=row.get("image"),
        gold_bbox=row.get("gold_bbox"),
        occlusion=row.get("occlusion"),
        ambiguity=bool(row.get("ambiguity", False)),
    )


def prediction_from_dict(row: dict) -> Prediction:
    if "id" not in row:
        raise ValueError("prediction needs an id")
    pred = row.get("pred")
    if pred is not None:
        pred = str(pred)
    confidence = row.get("confidence")
    if confidence is not None:
        confidence = float(confidence)
    tags = row.get("failure_tags") or []
    return Prediction(
        id=str(row["id"]),
        pred=pred,
        confidence=confidence,
        pred_bbox=row.get("pred_bbox"),
        failure_tags=[str(tag) for tag in tags],
    )

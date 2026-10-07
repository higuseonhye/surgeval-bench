"""Build evaluation items from local Cholec80 phase and tool annotation files.

Expected columns match the CAMMA release:
phase file, one row per video frame: Frame, Phase (0-6 or a phase name)
tool file, one row per second: Frame, then seven tool flags.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from surgeval.labels import PHASES, TOOLS, canonical_phase
from surgeval.schema import Item

TOOL_QUESTION = (
    "Is the {tool} present in this laparoscopic frame? "
    "Count it as present only if at least half of the tool tip is visible."
)
PHASE_QUESTION = "What is the current phase of this laparoscopic cholecystectomy?"
COUNT_QUESTION = (
    "How many of these instrument types are present: "
    + ", ".join(TOOLS)
    + "? Count a tool only if at least half of its tip is visible."
)


def _rows(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    sample = text.splitlines()[0] if text else ""
    delimiter = "\t" if "\t" in sample else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    if reader.fieldnames is None:
        raise ValueError(f"{path} has no header")
    return list(reader)


def _phase_name(raw: str) -> str:
    name = canonical_phase(raw)
    if name is None:
        known = ", ".join(PHASES)
        raise ValueError(f"unknown phase value {raw!r}. Expected 0-6 or one of: {known}")
    return name


def _flag(raw: str) -> bool:
    value = raw.strip().lower()
    if value in {"1", "true", "yes"}:
        return True
    if value in {"0", "false", "no"}:
        return False
    raise ValueError(f"tool flag must be 0 or 1, got {raw!r}")


def items_from_annotations(
    phase_path: Path,
    tool_path: Path,
    video_id: str,
    stride: int = 1,
    max_frames: int | None = None,
    seed: int = 42,
) -> list[Item]:
    if stride < 1:
        raise ValueError("stride must be >= 1")
    phases = {
        int(row["Frame"]): _phase_name(row["Phase"])
        for row in _rows(phase_path)
    }
    tool_rows = _rows(tool_path)
    if not tool_rows:
        return []
    columns = {name.lower().replace(" ", ""): name for name in tool_rows[0].keys()}
    tool_columns: dict[str, str] = {}
    for tool in TOOLS:
        key = tool.replace(" ", "")
        if key not in columns:
            raise ValueError(f"{tool_path} is missing a {tool} column")
        tool_columns[tool] = columns[key]

    rng = random.Random(seed)
    selected = tool_rows[::stride]
    if max_frames is not None:
        selected = selected[:max_frames]

    items: list[Item] = []
    for row in selected:
        frame = int(row["Frame"])
        if frame not in phases:
            continue
        phase = phases[frame]
        present = [tool for tool, column in tool_columns.items() if _flag(row[column])]
        absent = [tool for tool in TOOLS if tool not in present]
        stem = f"{video_id}_f{frame:06d}"
        items.append(
            Item(
                id=f"{stem}_phase",
                task="phase",
                query=PHASE_QUESTION,
                gold=phase,
                video_id=video_id,
                frame_idx=frame,
                choices=list(PHASES),
            )
        )
        items.append(
            Item(
                id=f"{stem}_count",
                task="tool_count",
                query=COUNT_QUESTION,
                gold=str(len(present)),
                video_id=video_id,
                frame_idx=frame,
            )
        )
        for tool in present:
            items.append(
                Item(
                    id=f"{stem}_{tool.replace(' ', '_')}_yes",
                    task="tool_presence",
                    query=TOOL_QUESTION.format(tool=tool),
                    gold="yes",
                    target=tool,
                    video_id=video_id,
                    frame_idx=frame,
                    choices=["yes", "no"],
                )
            )
        if absent:
            tool = rng.choice(absent)
            items.append(
                Item(
                    id=f"{stem}_{tool.replace(' ', '_')}_no",
                    task="tool_presence",
                    query=TOOL_QUESTION.format(tool=tool),
                    gold="no",
                    target=tool,
                    video_id=video_id,
                    frame_idx=frame,
                    choices=["yes", "no"],
                )
            )
    return items

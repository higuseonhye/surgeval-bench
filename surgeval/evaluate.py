"""Command line for the demo run, local annotation build, and scoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from surgeval.cholec80 import items_from_annotations
from surgeval.failure_modes import annotate, counts
from surgeval.metrics import score
from surgeval.report import render
from surgeval.schema import dump_jsonl, item_from_dict, load_jsonl, prediction_from_dict

ROOT = Path(__file__).resolve().parents[1]
DEMO_ITEMS = ROOT / "data" / "examples" / "items.jsonl"
DEMO_PREDS = ROOT / "data" / "examples" / "preds.jsonl"
DEMO_SOURCE = "data/examples 합성 예측. VLM을 돌린 결과가 아니다."


def _load_pairs(items_path: Path, preds_path: Path):
    items = [item_from_dict(row) for row in load_jsonl(items_path)]
    preds = {row["id"]: prediction_from_dict(row) for row in load_jsonl(preds_path)}
    missing = [item.id for item in items if item.id not in preds]
    if missing:
        raise ValueError("predictions missing for: " + ", ".join(missing))
    return items, preds


def _write_report(items, preds, out: Path, source: str) -> dict:
    summary = score(items, preds)
    tag_map = annotate(items, preds)
    text = render(summary, counts(tag_map), source=source)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return summary


def demo(out: Path) -> dict:
    items, preds = _load_pairs(DEMO_ITEMS, DEMO_PREDS)
    return _write_report(items, preds, out, DEMO_SOURCE)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="surgeval",
        description="Score surgical VQA items. Does not download video or call a model.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo_cmd = sub.add_parser("demo", help="score the bundled synthetic predictions")
    demo_cmd.add_argument("--out", type=Path, default=ROOT / "reports" / "demo_report.md")

    eval_cmd = sub.add_parser("eval", help="score a local item file against predictions")
    eval_cmd.add_argument("--items", type=Path, required=True)
    eval_cmd.add_argument("--preds", type=Path, required=True)
    eval_cmd.add_argument("--out", type=Path, required=True)

    build_cmd = sub.add_parser("build", help="turn local Cholec80 annotation files into items")
    build_cmd.add_argument("--phase", type=Path, required=True)
    build_cmd.add_argument("--tool", type=Path, required=True)
    build_cmd.add_argument("--video", required=True)
    build_cmd.add_argument("--out", type=Path, required=True)
    build_cmd.add_argument("--stride", type=int, default=25)
    build_cmd.add_argument("--max-frames", type=int, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        summary = demo(args.out)
        print(f"wrote {args.out}")
        print(json.dumps({"n": summary["n"], "accuracy_strict": summary["accuracy_strict"]}))
        return 0
    if args.command == "eval":
        items, preds = _load_pairs(args.items, args.preds)
        summary = _write_report(items, preds, args.out, source=str(args.items))
        print(f"wrote {args.out}")
        print(json.dumps({"n": summary["n"], "accuracy_strict": summary["accuracy_strict"]}))
        return 0
    if args.command == "build":
        items = items_from_annotations(
            args.phase,
            args.tool,
            video_id=args.video,
            stride=args.stride,
            max_frames=args.max_frames,
        )
        dump_jsonl(args.out, [item.to_dict() for item in items])
        print(f"wrote {len(items)} items to {args.out}")
        return 0
    return 2

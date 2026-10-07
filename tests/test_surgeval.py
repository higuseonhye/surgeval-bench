from pathlib import Path

import pytest

from surgeval.cholec80 import items_from_annotations
from surgeval.evaluate import demo
from surgeval.failure_modes import annotate
from surgeval.labels import canonical_phase
from surgeval.metrics import iou, is_correct, score
from surgeval.report import DISCLAIMER
from surgeval.schema import Item, Prediction, item_from_dict, load_jsonl, prediction_from_dict

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "data" / "examples"


def _pairs():
    items = [item_from_dict(row) for row in load_jsonl(EXAMPLES / "items.jsonl")]
    preds = {
        row["id"]: prediction_from_dict(row) for row in load_jsonl(EXAMPLES / "preds.jsonl")
    }
    return items, preds


def test_iou_overlap_and_miss():
    assert iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1
    assert iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0
    overlap = iou([10, 10, 50, 50], [12, 12, 48, 48])
    assert overlap == pytest.approx(1296 / 1600)


def test_phase_alias_rejects_bare_dissection():
    assert canonical_phase("the phase is preparation") == "Preparation"
    assert canonical_phase("3") == "Gallbladder dissection"
    assert canonical_phase("dissection") is None


def test_demo_scores_and_tags():
    items, preds = _pairs()
    summary = score(items, preds)
    tags = annotate(items, preds)
    assert summary["n"] == 11
    assert summary["correct"] == 5
    assert summary["abstain"] == 1
    assert summary["accuracy_strict"] == pytest.approx(5 / 11)
    assert tags["p3"] == ["overconfidence_hallucination", "temporal_inconsistency"]
    assert tags["p4"] == ["visual_occlusion"]
    assert tags["p1"] == []
    assert tags["s1"] == []
    assert tags["s2"] == ["overconfidence_hallucination"]
    assert tags["t2"] == ["unclassified_error"]
    assert summary["by_task"]["safety"]["false_alarms"] == 1
    assert summary["by_task"]["safety"]["confident_misses"] == 0
    assert summary["by_task"]["grounding"]["success_at_0_5"] == pytest.approx(0.5)
    assert summary["by_task"]["grounding"]["macro_f1"] is None


def test_abstain_text_is_not_an_error_tag():
    item = Item(id="a", task="safety", query="bleeding?", gold="yes")
    pred = Prediction(id="a", pred="abstain", confidence=0.99)
    assert is_correct(item, pred) is False
    assert annotate([item], {"a": pred})["a"] == []


def test_ambiguity_tag_requires_a_wrong_answer():
    item = Item(
        id="q",
        task="phase",
        query="phase?",
        gold="Preparation",
        ambiguity=True,
        video_id="v",
        frame_idx=1,
    )
    pred = Prediction(id="q", pred="Calot triangle dissection", confidence=0.2)
    assert annotate([item], {"q": pred})["q"] == ["anatomical_ambiguity"]


def test_cholec80_builder_balances_absent_tools():
    items = items_from_annotations(
        EXAMPLES / "video01-phase.txt",
        EXAMPLES / "video01-tool.txt",
        video_id="video01",
        stride=1,
    )
    phases = [item for item in items if item.task == "phase"]
    presence = [item for item in items if item.task == "tool_presence"]
    assert [item.gold for item in phases] == [
        "Preparation",
        "Calot triangle dissection",
        "Calot triangle dissection",
        "Gallbladder dissection",
    ]
    assert sum(item.gold == "yes" for item in presence) == 5
    assert sum(item.gold == "no" for item in presence) == 4
    assert len([item for item in items if item.task == "tool_count"]) == 4


def test_demo_report_names_the_fixture(tmp_path: Path):
    out = tmp_path / "report.md"
    demo(out)
    text = out.read_text(encoding="utf-8")
    assert DISCLAIMER in text
    assert "합성 예측" in text
    assert "VLM을 돌린 결과가 아니다" in text

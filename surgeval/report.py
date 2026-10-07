"""Markdown report. Numbers come from the scorer; this file does not invent them."""

from __future__ import annotations

from surgeval.labels import FAILURE_LABELS

DISCLAIMER = (
    "이 문서는 평가 절차를 실행한 결과다. "
    "점수가 합성 예측에서 나왔으면 모델 성능이 아니고, "
    "어느 경우에도 수술 판단이나 임상 사용의 근거가 아니다."
)

TASK_LABELS = {
    "phase": "수술 단계",
    "tool_presence": "기구 존재",
    "tool_count": "기구 개수",
    "grounding": "위치 지정",
    "safety": "안전 확인",
}


def _pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def _num(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.3f}"


def render(
    summary: dict,
    tag_counts: dict[str, int],
    *,
    source: str,
    title: str = "SurgEval-Bench 평가 결과",
) -> str:
    lines = [
        f"# {title}",
        "",
        DISCLAIMER,
        "",
        f"- 입력: {source}",
        f"- 문항 수: {summary['n']}",
        f"- 엄격 정확도 (무응답을 오답으로 계산): {_pct(summary['accuracy_strict'])}",
        f"- 무응답: {summary['abstain']}",
        "",
        "## 태스크별 점수",
        "",
        "| 태스크 | 문항 | 정답 | 무응답 | 엄격 정확도 | 응답만 정확도 | Macro-F1 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for task, block in summary["by_task"].items():
        label = TASK_LABELS.get(task, task)
        lines.append(
            "| {label} | {n} | {correct} | {abstain} | {strict} | {answered} | {f1} |".format(
                label=label,
                n=block["n"],
                correct=block["correct"],
                abstain=block["abstain"],
                strict=_pct(block["accuracy_strict"]),
                answered=_pct(block["accuracy_answered"]),
                f1=_num(block["macro_f1"]),
            )
        )
    grounding = summary["by_task"].get("grounding")
    if grounding:
        lines.extend(
            [
                "",
                "## 위치 지정",
                "",
                f"- 평균 IoU: {_num(grounding.get('mean_iou'))}",
                f"- IoU 0.5 이상 비율: {_pct(grounding.get('success_at_0_5'))}",
                "- 표의 정답은 기구 이름과 IoU 0.5를 함께 만족한 문항이다.",
            ]
        )
    safety = summary["by_task"].get("safety")
    if safety:
        lines.extend(
            [
                "",
                "## 안전 문항",
                "",
                f"- 위양성 (없는 출혈·위험을 있다고 답함): {safety.get('false_alarms', 0)}",
                f"- 확신 있는 미검출 (있는데 없다고 답함): {safety.get('confident_misses', 0)}",
                "- 무응답은 위 두 칸에 넣지 않는다. 불명확한 프레임에서 답을 보류하는 편이 오답보다 안전하다.",
            ]
        )
    lines.extend(["", "## 실패 유형", ""])
    if not tag_counts:
        lines.append("오답에 붙은 태그가 없다.")
    else:
        lines.append("| 태그 | 뜻 | 건수 |")
        lines.append("| --- | --- | ---: |")
        for tag, count in tag_counts.items():
            lines.append(f"| `{tag}` | {FAILURE_LABELS.get(tag, tag)} | {count} |")
        lines.extend(
            [
                "",
                "차폐와 해부학적 모호성은 문항에 그 단서가 있을 때만 붙는다. "
                "과신과 단계 도약은 예측값으로 계산한 휴리스틱이다. "
                "수술 영상의 실제 오류 원인은 사람이 프레임을 보고 확인해야 한다.",
            ]
        )
    lines.extend(
        [
            "",
            "## 이 결과로 말할 수 있는 범위",
            "",
            "- Cholec80 단계·기구 라벨로 만든 문항은, 공개 라벨과 예측이 얼마나 맞는지를 잰다.",
            "- 위치 지정과 출혈 확인은 Cholec80에 정답이 없다. 별도 상자 좌표나 임상 표정이 있는 문항만 채점한다.",
            "- 템플릿 질문의 높은 정확도는 장면 이해의 증거가 아니다. 단계 이름이 질문 안에 이미 정해져 있으면 모델이 영상을 덜 보고도 맞출 수 있다.",
            "",
        ]
    )
    return "\n".join(lines)

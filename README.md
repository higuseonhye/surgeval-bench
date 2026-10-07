# SurgEval-Bench

Evaluation harness for visual questions on laparoscopic cholecystectomy frames. It scores phase, tool, grounding, and safety items, and it tags wrong answers with review labels. It does not train a model, call an API, or control a robot.

The demo runs with no video and no API key. `reports/demo_report.md` is a score of 11 synthetic predictions (strict accuracy 45.5%). That number is a pipeline check, not a VLM result.

## Design

Cholec80 labels support three questions: surgical phase, tool presence, and tool count. Asking all seven tools on every frame makes "absent" the majority answer, so accuracy rises while rare tools are missed. The builder asks every tool that is present and one absent tool per frame. Scores include accuracy and macro-F1.

Refusals (`null`, `abstain`, `unknown`, `unsure`) are counted separately from wrong answers.

Spatial boxes and bleeding are not in Cholec80. Those items are scored only when the file supplies a box or a clinical label.

Wrong answers can receive these tags. Occlusion and ambiguity are applied only when the item already carries that flag. The harness does not detect smoke or blood in pixels.

| Tag | When it is applied |
| --- | --- |
| `overconfidence_hallucination` | Wrong, and confidence is at least 0.85 |
| `visual_occlusion` | Wrong, and `occlusion` is `smoke`, `blood`, or `fog` |
| `anatomical_ambiguity` | Wrong, and `ambiguity` is set |
| `temporal_inconsistency` | Wrong phase whose predicted index jumps by more than one phase from the previous prediction on the same video |
| `unclassified_error` | Wrong, with none of the conditions above |

Surgical-VQA (Seenivasan et al., MICCAI 2022) reports classification accuracy 0.898 on Cholec80-VQA. That figure is closed-set phase and tool classification. It is not a grounding or bleeding score.

A score from this harness is not evidence for clinical use.

## Quick start

```bash
git clone https://github.com/higuseonhye/surgeval-bench.git
cd surgeval-bench
python -m pip install -r requirements.txt
python -m pytest
python -m surgeval demo
```

## Local Cholec80 annotations

Phase and tool text files are enough. Do not commit the videos. Cholec80 is CC BY-NC-SA 4.0 (Twinanda et al., IEEE TMI 2016): https://camma.unistra.fr/datasets/

```bash
python -m surgeval build --phase video01-phase.txt --tool video01-tool.txt --video video01 --stride 1 --out items.jsonl
python -m surgeval eval --items items.jsonl --preds preds.jsonl --out reports/report.md
```

`--stride` steps through tool-annotation rows. Those rows are already one per second, so `--stride 25` keeps about one frame every 25 seconds.

Predictions use the same `id`. A missing answer is `null` or `"abstain"`.

```json
{"id": "video01_f000000_phase", "pred": "Preparation", "confidence": 0.8}
```

## Layout

```text
surgeval/cholec80.py        build items from phase and tool files
surgeval/metrics.py         accuracy, abstention, macro-F1, IoU
surgeval/failure_modes.py   review tags for wrong answers
surgeval/evaluate.py        demo, build, and eval commands
surgeval/prompts.py         prompt text for a later VLM run
data/examples/              synthetic items used by the demo and tests
docs/01_task_definition.md  tasks, labels, and metrics
docs/TECHNICAL_REPORT.md    method note
reports/demo_report.md      synthetic score report
```

## License

The code is MIT. See [LICENSE](LICENSE).

Cholec80 videos and frames are not in this repository. If you obtain them, their CC BY-NC-SA 4.0 terms still apply. This MIT license does not relicense that dataset.

Seonhye Gu · https://www.linkedin.com/in/seonhyegu

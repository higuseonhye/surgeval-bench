# SurgEval-Bench

담낭절제술 프레임에 대한 시각-언어 질문을 채점하는 도구다. 모델 학습 코드는 없고, 문항과 예측을 받아 정확도, 무응답, 실패 유형을 계산한다.

Cholec80 영상은 포함하지 않는다. CAMMA 공개본은 CC BY-NC-SA 4.0이라 저장소에 프레임을 넣지 않는다. 라벨 파일을 이미 가지고 있으면 로컬에서 문항만 만들 수 있다.

## 실행

```bash
py -m pip install -r requirements.txt
py -m pytest
py -m surgeval demo
```

`reports/demo_report.md`는 `data/examples`의 합성 예측을 채점한 결과다. VLM을 돌린 점수가 아니다.

## 로컬 라벨로 문항 만들기

Cholec80의 `videoXX-phase.txt`, `videoXX-tool.txt`가 있을 때:

```bash
py -m surgeval build --phase video01-phase.txt --tool video01-tool.txt --video video01 --stride 1 --out items.jsonl
```

`--stride`는 기구 라벨 행 간격이다. 공개본의 기구 라벨은 이미 1초 간격이라, `--stride 25`는 약 25초마다 한 프레임이다.

예측 파일은 같은 `id`를 가진 JSONL이다.

```json
{"id": "video01_f000000_phase", "pred": "Preparation", "confidence": 0.8}
```

모르겠으면 `pred`를 `null` 또는 `"abstain"`으로 둔다. 무응답은 오답과 따로 센다.

```bash
py -m surgeval eval --items items.jsonl --preds preds.jsonl --out reports/report.md
```

## 문서

- `docs/01_task_definition.md` — 문항, 정답 출처, 지표
- `docs/TECHNICAL_REPORT.md` — 포트폴리오용 방법 설명

## 라벨이 커버하는 범위

| 태스크 | 정답 출처 |
| --- | --- |
| 수술 단계, 기구 존재, 기구 개수 | Cholec80 단계·기구 라벨 |
| 위치 지정 | 상자 좌표가 있는 문항만. Cholec80에는 없다 |
| 출혈 등 안전 확인 | 별도 임상 표정만. Cholec80에는 없다 |

점수는 임상 사용 근거가 아니다.

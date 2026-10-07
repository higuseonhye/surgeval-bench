# SurgEval-Bench 기술 노트

담낭절제 장면을 자연어로 묻는 질문을, 공개 라벨이 실제로 답할 수 있는 범위 안에서 채점하기 위한 절차다. 수술 로봇을 움직이게 하는 시스템이 아니다.

## 질문

"이 프레임의 단계는 무엇인가", "이 기구가 보이는가"는 Cholec80 라벨로 정답을 만들 수 있다. "그래스퍼의 상자 좌표는 어디인가", "지금 출혈이 있는가"는 그 라벨에 없다. 없는 정답을 단계 이름에서 지어내면 평가가 아니라 가정이 된다.

그래서 문항을 둘로 나눈다.

- 라벨 문항: 수술 단계, 기구 존재, 기구 개수. 빌더가 로컬 주석 파일에서 만든다.
- 추가 표정 문항: 위치 지정, 안전 확인. 상자 좌표나 임상 표정을 가진 JSONL을 직접 넣어야 채점된다.

## 채점에서 지키는 것

기구 존재 질문을 프레임마다 7개 전부 내면, 대부분 정답이 no다. 정확도만 높이고 희귀한 기구를 놓쳐도 점수가 좋아 보인다. 빌더는 존재하는 기구는 모두 묻고, 없는 기구는 프레임당 하나만 묻는다. 점수는 정확도와 함께 macro-F1을 낸다.

무응답은 오답과 분리한다. 연기나 혈액으로 가려진 프레임에서 모델이 abstain하면, 없는 출혈을 있다고 단정한 경우와 같은 칸에 넣지 않는다. 안전 문항은 위양성과 확신 있는 미검출을 따로 센다.

위치는 이름만 맞으면 정답이 아니다. 정답 상자와 예측 상자의 IoU가 0.5 이상이고 기구 이름이 같을 때만 맞았다고 본다. 두 상자 모두 xyxy이며 같은 단위여야 한다.

실패 유형 네 가지는 리뷰용 태그다.

- 과신 환각: 틀렸는데 신뢰도 0.85 이상
- 시각적 차폐: 문항에 smoke, blood, fog가 적혀 있고 틀림
- 해부학적 모호성: 문항에 모호성 표시가 있고 틀림
- 시간적 불일치: 같은 영상에서 예측 단계가 직전보다 두 단계 이상 건너뜀

태그가 없으면 미분류 오답이다. 차폐와 모호성은 자동으로 영상을 판독해서 붙이지 않는다.

## 이미 발표된 숫자

Surgical-VQA(Seenivasan et al., MICCAI 2022)의 Cholec80-VQA 분류 정확도 0.898은 단계·기구 라벨에서 만든 닫힌 문항의 수치다. 같은 논문의 문장형 답은 BLEU, CIDEr, METEOR로 따로 보고되어 있고, 그 점수가 분류 정확도를 대신하지 않는다.

이 저장소의 `reports/demo_report.md`는 합성 예측 11문항을 채점기에 넣어 계산한 값이다. 모델 성능으로 인용하면 안 된다. 데모에서 확인하는 것은 계산이 재현된다는 점이다. 예를 들어 단계를 Preparation에서 Calot으로 갔다가 Gallbladder retraction으로 뛴 오답에는 과신과 시간적 불일치가 함께 붙고, 출혈 문항의 무응답은 위양성으로 세지 않는다.

## 숫자를 제품 판단으로 옮길 때

점수가 나와도 바로 제어 기능의 근거가 되지는 않는다. 순서를 이렇게 둔다.

1. 기록. 음성이나 장면으로 수술 기록의 단계를 채우는 관찰 기능. 기구는 움직이지 않는다.
2. 정합. "그래스퍼가 어디 있는가"에 상자로 답하고, IoU와 무응답률을 공개한다.
3. 그 다음에야, 가장 좁은 보조 동작 하나를 따로 정한다. 그 동작의 실패 조건과 사람이 즉시 끊는 규칙을 문항으로 먼저 만들고, 위 두 단계의 오답 유형이 줄어든 뒤에 논의한다.

1단계의 평가에도 위양성 기준이 필요하다. 없는 단계를 있다고 하면 기록이 오염되고, 가려진 프레임에서 단정하면 과신 태그가 쌓인다.

## 재현

```bash
py -m pytest
py -m surgeval demo
py -m surgeval build --phase <phase.txt> --tool <tool.txt> --video video01 --stride 1 --out items.jsonl
py -m surgeval eval --items items.jsonl --preds preds.jsonl --out reports/report.md
```

예측 JSONL은 사람이 적어도 되고, 나중에 VLM 출력으로 바꿔도 된다. 프롬프트 원문은 `surgeval/prompts.py`다. 호출부는 일부러 두지 않았다. 키와 프레임이 갖춰진 뒤에 같은 문항 파일로 채점하면 된다.

## 참고

- Twinanda AP, Shehata S, Mutter D, Marescaux J, de Mathelin M, Padoy N. EndoNet: A Deep Architecture for Recognition Tasks on Laparoscopic Videos. IEEE TMI, 2016. Cholec80, CC BY-NC-SA 4.0, https://camma.unistra.fr/datasets/
- Seenivasan L, Islam M, Krishna AK, Ren H. Surgical-VQA: Visual Question Answering in Surgical Scenes using Transformer. MICCAI, 2022.

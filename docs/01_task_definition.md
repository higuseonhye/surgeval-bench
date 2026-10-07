# 문항과 지표

평가 대상은 담낭절제 복강경 프레임 한 장과 질문 하나다. 로봇 제어 명령은 문항이 아니다.

## 공개 라벨로 만들 수 있는 문항

Cholec80(Twinanda et al., IEEE TMI 2016)은 담낭절제 영상 80개, 집도의 13명이다. 영상은 25 fps이고, 수술 단계는 프레임마다, 기구는 1초마다 표시되어 있다. 기구는 끝의 절반 이상이 보일 때만 존재로 친다.

단계 7개:

1. Preparation
2. Calot triangle dissection
3. Clipping and cutting
4. Gallbladder dissection
5. Gallbladder packaging
6. Cleaning and coagulation
7. Gallbladder retraction

기구 7개: grasper, bipolar, hook, scissors, clipper, irrigator, specimen bag.

이 라벨로 만드는 질문:

- 단계: "What is the current phase of this laparoscopic cholecystectomy?" 정답은 위 7개 중 하나.
- 기구 존재: "Is the {tool} present?" 정답은 yes 또는 no. 존재하는 기구는 모두 내고, 없는 기구는 프레임당 하나 뽑는다. 매 프레임에 7개를 전부 물으면 정답이 no인 문항이 점수를 끌어올린다.
- 기구 개수: 그 프레임에서 켜진 기구 종류의 수.

문항 생성은 `surgeval/cholec80.py`가 한다.

## 공개 라벨만으로는 만들 수 없는 문항

위치 지정("Locate the grasper")은 상자 좌표 `gold_bbox`가 있어야 채점한다. Cholec80 기구 라벨은 존재 여부만 있다.

안전 확인("Is there active bleeding in the surgical field?")은 출혈 표정이 있어야 한다. 단계 이름에서 출혈을 추정하지 않는다. Cleaning and coagulation 단계라고 해서 출혈이 보이는 것은 아니다.

`data/examples/items.jsonl`의 위치·안전 문항은 채점기 동작 확인용이다. 실제 프레임과 연결되어 있지 않다.

## 지표

- 엄격 정확도: 무응답을 오답으로 넣는다.
- 응답만 정확도: 답을 한 문항만 분모로 쓴다.
- Macro-F1: 정답에 등장한 라벨마다 F1을 내어 평균한다. 다수 클래스 no의 정확도만 보고 넘어가지 않기 위한 값이다.
- 위치: 같은 좌표계의 xyxy 상자로 IoU를 계산한다. 0.5 이상을 위치로 맞춘 것으로 본다. 기구 이름과 위치가 둘 다 맞아야 정답이다.
- 안전 문항의 위양성: 없는데 있다고 답한 경우. 있는데 없다고 답하면 확신 있는 미검출. 무응답은 둘 다 아니다.

무응답은 `pred`가 비었거나 `abstain`, `unknown`, `unsure`일 때다.

## 실패 유형

오답에만 붙인다. 무응답에는 붙이지 않는다.

| 태그 | 붙는 조건 |
| --- | --- |
| `overconfidence_hallucination` | 틀렸고 confidence가 0.85 이상 |
| `visual_occlusion` | 틀렸고 문항에 occlusion이 smoke, blood, fog |
| `anatomical_ambiguity` | 틀렸고 문항에 ambiguity가 표시됨 |
| `temporal_inconsistency` | 같은 영상에서 직전 예측 단계와 2단계 이상 벌어진 오답 |
| `unclassified_error` | 위 조건에 없는 오답 |

차폐와 모호성은 사람이 문항에 적어 준 단서다. 과신과 단계 도약은 예측 숫자로 계산한 휴리스틱이라, 프레임을 보기 전에는 오류의 원인으로 단정하지 않는다.

## 프롬프트

모델을 나중에 붙일 때의 문안은 `surgeval/prompts.py`에 있다. 이 저장소는 API를 호출하지 않는다. 지시에 포함된 내용은 세 가지다.

- 보이는 것만 답한다.
- 연기, 혈액, 불명확하면 abstain.
- 기구는 끝의 절반 이상이 보일 때만 존재로 센다.

Few-shot 문안에는 7개 단계의 짧은 정의가 들어 있다. 단계 정의를 프롬프트에 넣으면 점수가 오를 수 있으므로, zero-shot과 few-shot은 따로 채점한다.

## 논문 수치를 읽는 기준

Seenivasan et al., MICCAI 2022 (Surgical-VQA)는 Cholec80 영상 40개를 0.25 fps로 뽑아 Cholec80-VQA를 만들었다. 분류 문항의 정답은 단계, 기구 상태, 기구 개수에서 온 14개 단어다. 논문 표의 VisualBERT ResMLP 분류 정확도는 Cholec80-VQA (C)에서 0.898이다.

이 0.898은 템플릿으로 만든 닫힌 분류의 정확도다. 기구 위치, 출혈, 다음 동작 예측의 정확도가 아니다. SSG-VQA 계열 연구가 지적한 것처럼, 질문과 정답이 같은 라벨에서 생성되면 장면 이해 없이 맞출 여지가 있다. 그래서 이 벤치는 정확도 하나 대신 태스크별 F1, 무응답, 안전 문항의 위양성을 같이 낸다.

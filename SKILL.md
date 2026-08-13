---
name: consensus-code-review
description: "Multi-AI collaborative review validation and consensus. The runtime that invokes this skill is the coordinator, not a reviewer. It sends the prepared review to peer runtimes: Claude invokes Codex and agy; Codex invokes Claude and agy; agy invokes Claude and Codex. Optional external reviewers such as Grok, Ollama Cloud GLM-5.2, or vLLM may be added. Uses resume/continue or summary reconstruction for token efficiency."
---

# AI Code Review - Multi-AI Consensus Validation

이미 작성된 코드 리뷰를 여러 AI들에게 검증받고 합의를 도출하는 스킬입니다.

## 컨텍스트 관리

> 멀티 AI 합의 과정에서 품질 평가가 필요하면 `context-evaluation` 스킬의 Probe 기반 검증, Weighted Voting, Debate Protocol을 참조하세요.

## 핵심 개념

이 스킬은 **리뷰를 생성하지 않습니다**. 대신:

1. **사용자가 준비한 리뷰**를 받습니다
2. 현재 실행 런타임을 제외한 여러 **peer 검증자**(Claude, Codex, agy, 필요 시 Grok/vLLM)에게 검토 요청합니다
3. **피드백을 수집**하고 분석합니다
4. **합의 프로세스**를 진행합니다
5. **최종 검증된 리뷰**를 생성합니다

## Blind 1차 검토 원칙 (앵커링 방지)

Round 1에서는 peer 검증자에게 **준비된 리뷰(결론)를 전달하지 않는다**. 결론을 먼저 주면 검증자가 그 결론을 추인하는 쪽으로 앵커링되기 때문이다.

- Round 1 전달물: **아티팩트**(diff/코드) + **계약**(요구사항·제약 요약) + 적대적 프롬프트("저자가 과신한다고 가정하고 이슈를 찾아라. 검증하지 말 것")
- Round 1 피드백은 준비된 리뷰와 **대조(reconcile)** 하여 동의/수정/반대/추가를 산출한다
- Round 2부터는 수정된 리뷰를 전달해 합의율을 계산한다 (기존 방식)
- diff/코드 아티팩트를 확보할 수 없으면 blind round를 생략하고 기존 방식(리뷰 전달)으로 진행하되, 그 사실을 사용자에게 보고한다

## 실행 표면 선택

peer 검증자를 어디에 띄울지는 현재 세션이 Orca 관리 터미널인지로 자동 판단한다.

```bash
[ -n "${ORCA_TERMINAL_HANDLE:-}" ] || [ "${TERM_PROGRAM:-}" = "Orca" ]
```

- 참이면(또는 사용자가 orca를 명시적으로 언급하면) `orca orchestration` task/dispatch로 검증자를 배치하고, 각 검증자의 실행은 Orca 터미널 탭에서 사용자가 볼 수 있게 한다. 결과는 stdout이 아니라 지정된 파일로 받는다. 절차: [references/orca-surface.md](references/orca-surface.md)
- 거짓이면 기존 헤드리스 peer helper를 그대로 쓴다.

판별식과 기본 원칙은 `phase-harness`의 orca adapter와 동일하다. Orca surface에서는 직접 터미널/checkout lifecycle 명령으로 끝내지 말고 `orca orchestration`의 task/dispatch provenance를 남긴다.

## Token 절약 전략

Resume/Continue 기능, 파일 참조, Delta Updates로 평균 45~61% token 절감.
상세 전략: [references/token-strategy.md](references/token-strategy.md)

## 런타임 주체 원칙

현재 이 스킬을 실행하는 runtime은 **조정자(coordinator)** 이며 검증자가 아니다. 자기 자신에게 다시 검토를 맡겨 합의율에 포함하지 않는다.

| 실행 주체 | 기본 협조 요청 대상 |
|---|---|
| Claude | Codex, agy |
| Codex | Claude, agy |
| agy | Claude, Codex |
| pi | Claude, Codex |
| 기타/불명확 | 사용 가능한 Claude, Codex, agy 중 현재 주체로 확인되지 않은 runtime |

Grok, Ollama Cloud GLM-5.2, vLLM 같은 추가 검증자는 선택 사항이다. 최소 1개 이상의 peer 검증자가 동작해야 하며, 0개면 consensus를 수행하지 않고 사용 가능한 검증자가 없다고 보고한다.

## Peer 모델 및 추론 강도

peer 검증자를 호출할 때 다음 값을 명시한다. 현재 실행 주체와 같은 runtime은 기존 원칙대로 검증자에서 제외한다.

| Peer | 기본 호출 | 실패 시 fallback |
|---|---|---|
| Claude | `fable`, effort `medium` | `opus`, effort `high` |
| Codex | `gpt-5.6-sol`, reasoning effort `high` | 없음 |
| Grok | `grok-4.5`, reasoning effort `high` | `grok models`의 default model |
| pi | `ollama-cloud/deepseek-v4-flash:0731` | 없음 |


- Claude 기본 호출이 non-zero exit로 실패하면 같은 prompt를 `opus` + `high`로 한 번 재호출한다.
- Claude prompt는 fallback에서 동일하게 재사용할 수 있도록 파일로 보존한 뒤 두 호출에 전달한다.
- Codex는 모든 동작 확인, Round 1, Round 2+ 호출에 `-m gpt-5.6-sol -c model_reasoning_effort=high`를 명시한다.
- Grok CLI는 현재 headless `--prompt-file`과 `--model`을 사용한다. 오래된 `echo ... | grok "prompt"` 호출은 사용하지 않는다.
- Ollama Cloud는 `scripts/ollama_cloud_review.py`로 호출해 `OLLAMA_API_KEY`를 process argv나 로그에 노출하지 않는다. 환경변수가 없으면 helper가 `~/.hermes/.env`의 해당 key만 읽는다.

## 언제 사용하나요?

- **작성한 리뷰 검증**: 내가 작성한 코드 리뷰가 정확한지 확인
- **다각도 검토**: 여러 AI 모델의 관점으로 리뷰 품질 검증
- **놓친 이슈 발견**: 다른 AI가 발견한 추가 문제점 확인
- **합의 도출**: 여러 AI의 동의를 받은 신뢰도 높은 리뷰 생성
- **객관성 확보**: 단일 관점이 아닌 다중 검증

## 사용 방법

### 방법 1: 리뷰 내용을 직접 제공

```
다음 코드 리뷰를 검증해주세요:

## Critical Issues
1. SQL Injection 취약점 - auth.py:45
   ...
```

### 방법 2: 리뷰 파일 경로 제공

```
reviews/my_review.md 파일의 리뷰를 검증해주세요.
```

### 방법 3: Git 브랜치와 함께 리뷰 제공

```
main 브랜치 대비 변경사항에 대한 다음 리뷰를 검증해주세요:
[리뷰 내용...]
```

## 리뷰 검증 프로세스

- **Phase 1**: 준비된 리뷰 확인 — 입력 수신, 파일 저장, 메타데이터 확인
- **Phase 2**: 검증자 확인 — 현재 런타임을 제외한 Claude/Codex/agy peer 및 선택 검증자 동작 테스트
- **Phase 3**: Round 1 blind 초기 검토 — 준비된 리뷰 없이 아티팩트+계약만 전송, 적대적 프롬프트, 세션 저장
- **Phase 4**: 피드백 분석 — blind 피드백을 준비된 리뷰와 대조해 동의/수정/반대/추가 분류, 합의율 계산
- **Phase 5**: Round 2~N 재검증 — Resume로 token 절약하며 반복
- **Phase 6**: 최종 검증 리포트 생성

상세 프로세스 (bash 코드, 프롬프트 템플릿, 출력 예시 포함): [references/validation-process.md](references/validation-process.md)

## 주요 특징

- **리뷰 생성 안 함**: 사용자가 준비한 리뷰만 검증, 현재 세션은 검증 프로세스만 진행
- **다중 AI 검증**: 현재 실행 주체를 제외한 Claude/Codex/agy peer와 선택 검증자(Grok, Ollama Cloud GLM-5.2, GPT OSS 120B) 활용
- **구조화된 피드백**: 동의/수정/반대/추가로 분류, 정량적 합의율 계산
- **반복적 개선**: 피드백 기반 수정 후 재검증, 합의 도달까지 최대 3라운드
- **Token 효율성**: Resume/Continue + Delta Updates로 평균 45~60% 절감

## 종료 조건과 Red Flags

- 최대 3라운드. 3라운드 후에도 합의 미달이면 **혼자 반복하지 않는다** — 미합의 이슈를 정리해 사용자에게 에스컬레이션한다 (리뷰 대상 아티팩트가 합의 가능한 상태가 아니라는 신호).
- **검증 연극 감지**: 라운드마다 검증자가 이슈를 내는데 리뷰에 반영(수정/제거/추가)된 항목이 0건이면 합의 절차가 형식화된 것 — 즉시 중단하고 사용자 판단을 구한다.
- Round 1에 준비된 리뷰(결론)를 전달하는 것은 red flag다 (blind 원칙 위반).

## 제한사항

- **검증자 필수**: 최소 1개 이상의 peer 검증자 필요. Codex에서 실행 중이면 Codex subagent나 `codex exec`를 검증자로 쓰지 않고 Claude/agy에 협조 요청
- **리뷰 사전 준비**: 스킬은 리뷰를 생성하지 않음
- **agy 세션 제약**: `agy --print`는 매 호출 새 세션이므로 재검토 시 이전 라운드 요약과 변경사항을 prompt에 직접 포함
- **Cloud reviewer 세션 제약**: Ollama Cloud 호출은 stateless이므로 Round 2부터 이전 피드백 요약과 변경사항을 prompt에 직접 포함
- **Token 제한**: 매우 긴 리뷰는 일부만 검증 가능

## 참고

이 Skill은 다음 프로젝트의 "Consensus" 개념을 기반으로 합니다:
- **프로젝트**: https://github.com/hansonkim/consensus-code-review
- **컨셉**: Multi-AI Consensus Validation
- **차이점**: 리뷰 생성 없이 검증만 수행
- **개선점**: Resume 기능으로 token 효율성 최대화

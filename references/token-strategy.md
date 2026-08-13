# Token 절약 전략

이 스킬은 다음 방법으로 token을 최소화합니다:

## 1. 세션 Resume 기능 활용

각 AI CLI의 컨텍스트 유지 기능으로 매번 전체 리뷰를 재전송하지 않습니다:

- **Codex peer**: 현재 runtime이 Codex가 아닐 때만 `codex exec` 또는 `codex resume SESSION_ID` 사용
- **Peer 모델 고정**: Claude는 `fable` + `medium`, 실패 시 동일 prompt로 `opus` + `high`; Codex는 `gpt-5.6-sol` + `high`
- **agy peer**: `agy --print`는 매 호출 새 세션이므로 이전 라운드 요약 + 변경사항을 prompt에 직접 포함
- **Grok**: headless `--prompt-file`에 이전 피드백 요약 + 변경사항만 전달한다. 임의의 최근 대화를 이어받는 `--continue`는 review context 혼선을 만들 수 있어 사용하지 않는다.
- **Ollama Cloud GLM-5.2**: stateless API이므로 이전 피드백 요약 + 변경사항만 전달한다.

## 2. 파일 참조 방식

긴 리뷰 내용을 매번 보내지 않고 파일로 저장 후 참조:

```bash
# Round 1: 전체 리뷰 전송. CURRENT_RUNTIME=codex이면 실행하지 않는다.
codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --ephemeral "@reviews/initial_review.md 이 리뷰를 검증해주세요"

# Round 2: 파일 참조 + 변경사항만 전송
codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --ephemeral "이전 Codex peer 검토 요약: ... 변경사항: Issue #3의 심각도를 Major로 상향했습니다. 다시 검토해주세요."
```

## 3. 변경사항만 전달 (Delta Updates)

Round 2부터는 전체 리뷰가 아닌 수정된 부분만 전달:

```bash
# ❌ 비효율: 전체 리뷰 재전송 (10KB)
codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --ephemeral "@reviews/revised_review_round2.md 재검토해주세요"

# ✅ 효율: 변경사항만 전달 (200 bytes)
codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --ephemeral "
수정 사항:
- Issue #3: Minor → Major (심각도 상향)
- Issue #5: 제거 (False Positive)
- Issue #8: Type safety 이슈 추가

이 변경사항으로 재검토해주세요.
"
```

## 4. 요약 컨텍스트

상세 피드백은 파일로 저장, AI에게는 핵심 요약만 전달:

```bash
# 상세 피드백은 파일에 저장
echo "$detailed_feedback" > reviews/feedback_codex_round1.md

# AI에게는 요약만 제공
codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --ephemeral "
Codex 피드백 요약:
✅ 동의: 7개 (70%)
⚠️  수정 제안: 2개 (Issue #3 심각도, Issue #7 설명 명확화)
❌ 반대: 1개 (Issue #5 False Positive)

이 피드백을 반영했습니다. 재검토해주세요.
"
```

## 5. agy 컨텍스트 재구성

`agy --print`는 비대화형 호출마다 새 세션을 만들기 때문에 resume에 의존하지 않습니다. 재검토 시 직전 피드백 요약과 변경사항만 전달합니다:

```bash
{
  printf '%s\n' "이전 agy 피드백 요약: 동의 7개, 수정 제안 2개, 반대 1개"
  printf '%s\n' "반영 변경사항: Issue #3 심각도 상향, Issue #5 제거"
  printf '%s\n' "이 변경사항만 기준으로 재검토해주세요."
} | agy --print --print-timeout 5m
```

## Token 절감 효과

| Round | 기존 방식 | Token 절약 방식 | 절감율 |
|-------|-----------|----------------|--------|
| Round 1 | 5,000 | 5,000 | 0% (필수) |
| Round 2 | 5,000 | 500 | 90% |
| Round 3 | 5,000 | 300 | 94% |
| **합계** | **15,000** | **5,800** | **61%** |

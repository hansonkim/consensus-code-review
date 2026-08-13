# 리뷰 검증 프로세스 상세

## Phase 2: 검증자 확인

### 실행 표면 결정 (먼저 판별)

peer 매트릭스를 정하기 전에 검증자를 어디에 띄울지 결정한다.

```bash
if [ -n "${ORCA_TERMINAL_HANDLE:-}" ] || [ "${TERM_PROGRAM:-}" = "Orca" ]; then
  SURFACE=orca      # 검증자마다 Orca 터미널 탭, 결과는 파일로 수집
else
  SURFACE=headless  # 아래 Peer 호출 helper 사용
fi
```

`SURFACE=orca`면 기동·프롬프트 전달·완료 대기·정리를 [orca-surface.md](orca-surface.md)에 따른다. 아래 `run_*_peer` helper는 `SURFACE=headless`일 때의 경로다. peer 매트릭스, blind 원칙, 합의율 계산, 종료 조건은 표면과 무관하게 동일하다.

`agy`와 Ollama Cloud는 TUI 에이전트가 아니므로 `SURFACE=orca`에서도 헤드리스 helper를 유지하고, 그 사실을 사용자에게 알린다.

### 런타임별 원칙

- **현재 런타임은 조정자(coordinator)**: 입력 저장, peer 검증자 호출, 피드백 취합, 합의 판단만 담당한다.
- **현재 런타임은 검증자가 아니다**: 자기 자신의 subagent, 동일 CLI 재호출, 동일 runtime resume 결과를 consensus 검증자로 계산하지 않는다.
- **Claude에서 실행 중인 경우**: Codex와 agy에 협조 요청한다. Codex는 가능하면 Codex plugin 또는 `codex exec`를 사용하고, agy(antigravity-cli)는 `agy --print` 비대화형 모드를 사용한다. Claude CLI 결과는 기본 검증자에서 제외한다.
- **Codex에서 실행 중인 경우**: Claude와 agy에 협조 요청한다. `spawn_agent`나 `codex exec`는 자기 검증이므로 기본 검증자에서 제외한다.
- **agy에서 실행 중인 경우**: Claude와 Codex에 협조 요청한다. `agy --print`는 자기 검증이므로 기본 검증자에서 제외한다.
- **Grok/Ollama Cloud/vLLM**: optional peer reviewer로 추가할 수 있다. 핵심 합의는 현재 런타임을 제외한 Claude/Codex/agy peer를 우선한다.

### Peer 매트릭스


| CURRENT_RUNTIME | 기본 peer 검증자                     |
| --------------- | ------------------------------- |
| `claude`        | `codex`, `agy`                  |
| `codex`         | `claude`, `agy`                 |
| `agy`           | `claude`, `codex`               |
| `unknown`       | 현재 주체로 확인되지 않은 Claude/Codex/agy |


### Peer 호출 helper

Claude는 `fable` + `medium`을 우선 사용하고, non-zero exit로 실패하면 동일 prompt를 `opus` + `high`로 한 번 재호출한다. Codex는 `gpt-5.6-sol` + `high`를 명시한다.

```bash
run_claude_peer() {
  local prompt_file status
  prompt_file="$(mktemp)"
  cat > "$prompt_file"

  if claude --model fable --effort medium --permission-mode dontAsk --tools "" -p < "$prompt_file"; then
    status=0
  else
    claude --model opus --effort high --permission-mode dontAsk --tools "" -p < "$prompt_file"
    status=$?
  fi

  rm -f "$prompt_file"
  return "$status"
}

run_codex_peer() {
  codex exec -m gpt-5.6-sol -c model_reasoning_effort=high "$@"
}

run_agy_peer() {
  local prompt_file="$1"
  local timeout="${2:-5m}"
  local prompt
  prompt="$(<"$prompt_file")"
  agy --print "$prompt" --print-timeout "$timeout" --mode plan --sandbox --disable-slash-commands
}

run_grok_peer() {
  local prompt_file="$1"
  grok --model grok-4.5 --reasoning-effort high \
    --permission-mode dontAsk --disable-web-search --no-subagents --no-memory \
    --tools "" --prompt-file "$prompt_file"
}

run_ollama_cloud_peer() {
  local prompt_file="$1"
  python3 "$HOME/ai-agent-config/packages/common/.apm/skills/consensus-code-review/scripts/ollama_cloud_review.py" \
    "$prompt_file" --model glm-5.2:cloud
}
```

1. **사용 가능한 검증자 확인**
  ```bash
   # CURRENT_RUNTIME은 실행 주체를 나타낸다: claude | codex | agy | unknown
   # 알 수 없으면 현재 도구/환경/사용자 컨텍스트로 추론하고, 그래도 불명확하면 unknown으로 둔다.
  
   case "$CURRENT_RUNTIME" in
     claude) PEER_CANDIDATES=("codex" "agy") ;;
     codex) PEER_CANDIDATES=("claude" "agy") ;;
     agy) PEER_CANDIDATES=("claude" "codex") ;;
     *) PEER_CANDIDATES=("claude" "codex" "agy") ;;
   esac
  
   # Claude 확인 (설치 여부 + 동작 테스트)
   if printf '%s\n' "${PEER_CANDIDATES[@]}" | grep -qx "claude" && command -v claude &> /dev/null; then
       if printf '%s' "Reply with just 'OK'" | run_claude_peer 2>&1 | grep -qi "ok"; then
           echo "✅ Claude 사용 가능 및 동작 확인"
           VALIDATORS+=("claude")
       else
           echo "⚠️  Claude 설치되었으나 동작하지 않음 (인증 또는 설정 확인 필요) - 스킵"
       fi
   else
       echo "⚠️  Claude 설치 안됨 - 스킵"
   fi
  
   # Codex 확인 (설치 여부 + 동작 테스트)
   if printf '%s\n' "${PEER_CANDIDATES[@]}" | grep -qx "codex" && command -v codex &> /dev/null; then
       if run_codex_peer -C "$PWD" -s read-only --ephemeral --color never "Reply with exactly OK." 2>&1 | grep -qi "ok"; then
           echo "✅ Codex 사용 가능 및 동작 확인"
           VALIDATORS+=("codex")
       else
           echo "⚠️  Codex 설치되었으나 동작하지 않음 (인증 또는 설정 확인 필요) - 스킵"
       fi
   elif printf '%s\n' "${PEER_CANDIDATES[@]}" | grep -qx "codex"; then
       echo "⚠️  Codex 설치 안됨 - 스킵"
   fi
  
   # agy (antigravity-cli) 확인 — 현재 CLI는 `--print` 바로 다음 인자를
   # prompt로 읽는다. stdin으로 보내거나 `--print-timeout`을 먼저 두면
   # 옵션명이 prompt로 오인될 수 있으므로 prompt를 명시적으로 전달한다.
   if printf '%s\n' "${PEER_CANDIDATES[@]}" | grep -qx "agy" && command -v agy &> /dev/null; then
       if agy --print "Reply with just 'OK'" --print-timeout 30s --mode plan --disable-slash-commands 2>&1 | grep -qi "ok"; then
           echo "✅ agy 사용 가능 및 동작 확인"
           VALIDATORS+=("agy")
       else
           echo "⚠️  agy 설치되었으나 동작하지 않음 (로그인 또는 설정 확인 필요) - 스킵"
       fi
   else
       echo "⚠️  agy 설치 안됨 - 스킵"
   fi
  
   # Grok 확인 (설치 여부 + headless 동작 테스트)
   if command -v grok &> /dev/null; then
       prompt_file="$(mktemp)"
       printf '%s' "Reply with just 'OK'" > "$prompt_file"
       if run_grok_peer "$prompt_file" 2>&1 | grep -qi "ok"; then
           echo "✅ Grok 사용 가능 및 동작 확인"
           VALIDATORS+=("grok")
       else
           echo "⚠️  Grok 설치되었으나 동작하지 않음 (인증 또는 설정 확인 필요) - 스킵"
       fi
       rm -f "$prompt_file"
   else
       echo "⚠️  Grok 설치 안됨 - 스킵"
   fi
  
   # Ollama Cloud GLM-5.2 확인 — helper가 environment 또는 ~/.hermes/.env의
   # OLLAMA_API_KEY를 읽으며 key 값은 argv나 로그에 출력하지 않는다.
   prompt_file="$(mktemp)"
   printf '%s' "Reply with just 'OK'" > "$prompt_file"
   if run_ollama_cloud_peer "$prompt_file" 2>&1 | grep -qi "ok"; then
       echo "✅ Ollama Cloud GLM-5.2 사용 가능 및 동작 확인"
       VALIDATORS+=("ollama-cloud-glm-5.2")
   else
       echo "⚠️  Ollama Cloud GLM-5.2 호출 실패 - 스킵"
   fi
   rm -f "$prompt_file"
  
   # GPT OSS 120B (DGX Spark vLLM) 확인
   if curl -s --connect-timeout 3 http://<internal-vllm-host>:8000/v1/models | grep -q "gpt-oss-120b"; then
       echo "✅ GPT OSS 120B (DGX Spark) 사용 가능"
       VALIDATORS+=("vllm")
   else
       echo "⚠️  GPT OSS 120B (DGX Spark) 접속 불가 - VPN 연결 확인 필요 - 스킵"
   fi
  ```
2. **검증자 목록 생성**
  - 최소 1개 이상의 peer 검증자 필요
  - 현재 런타임은 검증자 목록에서 제외
  - Claude/Codex/agy peer 중 동작하는 검증자는 모두 포함
  - 설치된 모든 외부 AI CLI/도구 활용

## Phase 3: Round 1 - Blind 초기 검토 (세션 시작)

Round 1은 **blind**로 진행한다: 준비된 리뷰(결론)는 전달하지 않는다. 아티팩트(diff/코드) + 계약만 전달해 독립 검토를 받고, 준비된 리뷰와의 대조는 Phase 4에서 조정자가 수행한다.

`SURFACE=orca`면 아래 헤드리스 호출 대신 [orca-surface.md](orca-surface.md)의 워커 배치와 프롬프트 전달을 쓴다. blind 원칙과 적대적 프롬프트 내용은 그대로다.

1. **아티팩트 준비**
  ```bash
   # diff 확보 (사용자가 코드/diff 파일을 직접 제공했으면 그 파일 사용)
   git diff main...HEAD > reviews/artifact.diff
   ARTIFACT_FILE=reviews/artifact.diff
  
   # 계약(이 변경이 지켜야 할 요구사항·제약)을 2~5줄로 요약해 CONTRACT_SUMMARY에 담는다.
   # 준비된 리뷰의 결론·심각도 판정은 계약 요약에 포함하지 않는다.
  
   # 아티팩트 확보 불가 시(diff 없음, 코드 미제공):
   #   blind round를 생략하고 기존 방식(리뷰 전달 + 검증 프롬프트 템플릿)으로 Round 1을 진행하되,
   #   "blind round 생략: 아티팩트 확보 불가"를 사용자에게 보고한다.
  ```
2. **Codex peer 검토 요청**
  ```
   # CURRENT_RUNTIME=codex이면 실행하지 않는다.
   # codex exec를 read-only/ephemeral로 직접 호출한다 (plugin codex:codex-rescue는 stale 버그로 미사용).
  
   CODE_REVIEW_PROMPT="Review and respond only — do not edit any files.
  
   저자가 과신하고 있다고 가정하세요. 아래 코드 변경(diff)을 독립적으로 검토해
   이슈를 찾아주세요. 검증(확인)하지 말고 문제를 찾으세요. 없다면 없다고 명시하세요.
  
   계약(이 변경이 지켜야 할 요구사항·제약):
   ${CONTRACT_SUMMARY}
  
   찾을 것:
  ```
  1. 명시되지 않은 가정
  2. 처리되지 않은 엣지 케이스
  3. 숨은 결합, 계약 위반
  4. 예상 밖 입력에서의 실패 모드
  5. 보안/성능 문제
  
    형식:
     발견 이슈
  6. [파일:라인] [심각도: Critical/Major/Minor] [설명과 근거]
   이슈 없음 확인 영역
  [검토했지만 이슈가 없다고 판단한 영역과 근거]"
  
    printf '%s\n\n' "$CODE_REVIEW_PROMPT"; cat "$ARTIFACT_FILE"; }   
    | run_codex_peer -C "$PWD" -s read-only --ephemeral --color never - \
    > reviews/feedback_codex_round1.md
    > `
3. **Claude peer 검토 요청 (`claude` CLI)**
  ```bash
   # CURRENT_RUNTIME=claude이면 실행하지 않는다.
   {
     printf '%s\n\n' "$CODE_REVIEW_PROMPT"
     cat "$ARTIFACT_FILE"
   } | run_claude_peer > reviews/feedback_claude_round1.md
  ```
4. **agy peer 검토 요청**
  ```bash
   # CURRENT_RUNTIME=agy이면 실행하지 않는다.
   # agy는 `--print` 바로 다음 인자를 prompt로 읽으므로 prompt file 내용을
   # 하나의 인자로 전달한다. --mode plan/--sandbox로 파일 수정은 금지한다.
   AGY_PROMPT_FILE="$(mktemp)"
   { printf '%s\n\n' "$CODE_REVIEW_PROMPT"; cat "$ARTIFACT_FILE"; } > "$AGY_PROMPT_FILE"
   run_agy_peer "$AGY_PROMPT_FILE" 5m > reviews/feedback_agy_round1.md
   rm -f "$AGY_PROMPT_FILE"
  
   # agy --print는 매 호출이 새 세션이므로 세션 저장 개념이 없다.
   # 재검토 시 이전 컨텍스트는 prompt에 요약으로 직접 포함한다.
  ```
5. **Grok 검토 요청 (headless, tool-free)**
  ```bash
   GROK_PROMPT_FILE="$(mktemp)"
   { printf '%s\n\n' "$CODE_REVIEW_PROMPT"; cat "$ARTIFACT_FILE"; } > "$GROK_PROMPT_FILE"
   run_grok_peer "$GROK_PROMPT_FILE" > reviews/feedback_grok_round1.md
   rm -f "$GROK_PROMPT_FILE"
  ```
6. **Ollama Cloud GLM-5.2 검토 요청 (stateless, tool-free)**
  ```bash
   OLLAMA_PROMPT_FILE="$(mktemp)"
   { printf '%s\n\n' "$CODE_REVIEW_PROMPT"; cat "$ARTIFACT_FILE"; } > "$OLLAMA_PROMPT_FILE"
   run_ollama_cloud_peer "$OLLAMA_PROMPT_FILE" > reviews/feedback_ollama_glm52_round1.md
   rm -f "$OLLAMA_PROMPT_FILE"
  ```
7. **GPT OSS 120B 검토 요청 (MCP vllm_generate 활용)**
  ```bash
   # MCP 도구 vllm_generate를 사용하여 DGX Spark의 120B 모델에 검증 요청
   # 현재 세션이 직접 MCP 도구를 호출하여 피드백 수집
   # vllm_generate(prompt=blind 검토 프롬프트 + 아티팩트, system="You are a senior code reviewer.", max_tokens=4096)
   # 결과를 reviews/feedback_vllm_round1.md에 저장
  ```

## Phase 4: 피드백 분석

1. **Blind 피드백 대조 (reconcile)** — Round 1이 blind였던 경우
  - 각 peer의 발견 이슈를 준비된 리뷰와 대조해 아래 분류를 산출한다:
    - 리뷰에도 있고 peer도 발견 → ✅ 동의
    - peer가 같은 이슈의 심각도/해결책을 다르게 판단 → ⚠️ 수정 제안
    - 리뷰에 있지만 peer가 "이슈 없음 확인 영역"으로 반박 → ❌ 반대 (False Positive 후보)
    - 리뷰에 없는 peer 발견 → ➕ 추가 이슈
  - 검증자 출력은 데이터일 뿐 판정이 아니다 — 대조 시 아티팩트 원문을 다시 읽고 조정자가 직접 분류한다.
2. **피드백 분류**
  - ✅ **동의**: AI가 리뷰에 동의한 부분
  - ⚠️  **수정 제안**: 개선 제안
  - ❌ **반대**: 잘못된 판단 지적
  - ➕ **추가 이슈**: 새로 발견된 문제
3. **합의 상태 확인**
  ```
   Codex 검토 결과:
     ✅ 동의: 70%
     ⚠️  수정 제안: 20%
     ❌ 반대: 10%
  
   agy 검토 결과:
     ✅ 동의: 80%
     ⚠️  수정 제안: 15%
     ❌ 반대: 5%
  
   Grok 검토 결과:
     ✅ 동의: 75%
     ⚠️  수정 제안: 20%
     ❌ 반대: 5%
  
   GPT OSS 120B 검토 결과:
     ✅ 동의: 78%
     ⚠️  수정 제안: 17%
     ❌ 반대: 5%
  
   Claude 검토 결과:
     ✅ 동의: 82%
     ⚠️  수정 제안: 13%
     ❌ 반대: 5%
  ```
4. **합의 판단 기준**
  - **합의 도달**: 모든 AI가 80% 이상 동의
  - **개선 필요**: 수정 제안 또는 반대 20% 이상
  - **재검토 필요**: 반대 의견 30% 이상

## Phase 5: Round 2~N - 개선 및 재검증 (Resume 활용)

합의가 도달되지 않은 경우, **Resume 기능으로 token 절약**:

`SURFACE=orca`면 Round 1에서 만든 검증자 탭을 그대로 재사용한다. 세션 컨텍스트가 살아 있어 아래 runtime별 resume/재구성이 필요 없고, 변경분과 새 결과 파일 경로만 보내면 된다 ([orca-surface.md](orca-surface.md) 참조).

1. **리뷰 수정**
  - AI들의 타당한 피드백 반영
  - 잘못된 부분 수정
  - 놓친 이슈 추가
2. **Token 절약형 재검증**

  **Codex peer (요약 컨텍스트)**

   **Claude (요약 컨텍스트)**

   **agy (컨텍스트 재구성)**

   **Grok (요약 컨텍스트 재구성)**

   **Ollama Cloud GLM-5.2 (요약 컨텍스트 재구성)**

   **GPT OSS 120B (MCP vllm_generate 재검증)**
3. **최대 라운드 제한 및 에스컬레이션**
  - 기본값: 최대 3라운드
  - 합의 도달 시 종료
  - 3라운드 초과 시 혼자 반복하지 않는다: 미합의 이슈를 정리해 사용자에게 에스컬레이션한다 (아티팩트가 합의 가능한 상태가 아니라는 신호)
  - **검증 연극 감지**: 라운드마다 이슈가 나오는데 리뷰에 반영(수정/제거/추가)된 항목이 0건이면 즉시 중단하고 사용자 판단을 요청한다

## Phase 6: 최종 검증 리포트 생성

1. **합의 결과 정리**
  ```markdown
   # Code Review - Multi-AI Consensus Validation
  
   ## Validation Metadata
   - Initial Review: reviews/initial_review_20251104_153045.md
   - Validation Date: 2025-11-04 15:30:45
   - Coordinator: {CURRENT_RUNTIME}
   - Validators: peer runtimes only (example: Codex, agy, Grok, Ollama Cloud GLM-5.2, GPT OSS 120B)
   - Rounds: 2
   - Consensus: ✅ Reached
   - Token Usage: 5,800 tokens (61% saved via resume)
  
   ---
  
   ## Token Efficiency Report
  
   ### Session Management
   - **Codex**: Context reconstruction with `codex exec` unless current runtime is Codex
   - **Claude**: Context reconstruction with `claude -p` unless current runtime is Claude
   - **agy**: Context reconstruction (no built-in session) unless current runtime is agy
   - **Grok**: Context reconstruction with headless tool-free invocation
   - **Ollama Cloud GLM-5.2**: Context reconstruction (stateless API)
   - **GPT OSS 120B**: MCP tool based (no session, Claude manages context)
  
   ### Token Savings
   | Round | Traditional | Resume-based | Saved |
   |-------|-------------|--------------|-------|
   | Round 1 | 5,000 | 5,000 | 0% |
   | Round 2 | 5,000 | 500 | 90% |
   | **Total** | **10,000** | **5,500** | **45%** |
  
   ---
  
   ## Consensus Summary
  
   ### Overall Agreement
   - Codex: 90% agreement (↑ from 70%)
   - Claude: 93% agreement (↑ from 82%)
   - agy: 95% agreement (↑ from 80%)
   - Grok: 92% agreement (↑ from 75%)
   - GPT OSS 120B: 91% agreement (↑ from 78%)
   - Combined: 92.0% agreement
  
   ### Validation Status
   ✅ **Consensus Reached** - All validators agree on final review
  
   ---
  
   ## Original Review
  
   {original_review_content}
  
   ---
  
   ## AI Feedback Summary
  
   ### ✅ Agreed Points (by all validators)
  ```
  1. SQL Injection vulnerability in auth.py:45 - Critical severity confirmed
  2. Missing authentication check in api.py:23 - Major severity confirmed
    # ⚠️  Modifications Suggested
  3. **Codex peer**: Issue #3 severity should be Major, not Minor
    - Reason: Database connection pooling affects performance significantly
    - Status: ✅ Accepted and updated
  4. **agy**: Add type safety issue in models.py:67
    - Reason: Missing type hints can lead to runtime errors
    - Status: ✅ Accepted and added to review
  5. **Grok**: Issue #5 appears to be False Positive
    - Reason: Code pattern is actually safe in this context
    - Status: ✅ Accepted and removed
    # ➕ Additional Issues Found
  6. **Codex**: Memory leak in cache.py:123
    - Severity: Major
    - Description: Cache entries never expire
    - Status: ✅ Added to final review
    - 
  
     Final Validated Review
  
    inal_review_with_all_updates}
    - 
  
     Validation History
    # Round 1
  
    Codex peer: 70% agreement, 3 suggestions
    Claude: 82% agreement, 1 suggestion
    agy: 80% agreement, 2 suggestions
    Grok: 75% agreement, 2 suggestions
    GPT OSS 120B: 78% agreement, 2 suggestions
    Action: Updated review based on feedback
    Method: Full review transmission (5,000 tokens)
    # Round 2 (Final)
  
    Codex peer: 90% agreement ✅ (summary context: -90% tokens)
    Claude: 93% agreement ✅ (context summary: -80% tokens)
    agy: 95% agreement ✅ (context summary: -80% tokens)
    Grok: 92% agreement ✅ (auto-continue: -92% tokens)
    GPT OSS 120B: 91% agreement ✅ (MCP tool: context summary)
    Consensus: ✅ Reached
    Method: Delta updates only (500 tokens avg)
    - 
  
     Next Steps
  7. Review all Critical issues before merge
  8. Address Major issues with team
  9. Consider Minor improvements in follow-up
  10. All changes validated by all available validators with 92% consensus
  `
2. **파일 저장**
  ```bash
   # 최종 검증 리포트
   cat > reviews/validated_review_${TIMESTAMP}_final.md
  ```

---

## 출력 예시

```
🤖 AI Code Review - Multi-AI Consensus Validation
======================================================================

📄 준비된 리뷰 확인
  ✅ 리뷰 내용: 사용자 제공
  ✅ 길이: 1,245자
  ✅ 구조: Critical(2), Major(3), Minor(5)

💾 리뷰 파일 저장
  📁 reviews/initial_review_20251104_153045.md

======================================================================
🔍 AI 검증자 확인
======================================================================

  Coordinator: {CURRENT_RUNTIME}
  ✅ Codex peer - CURRENT_RUNTIME=codex이면 제외
  ✅ Claude peer - CURRENT_RUNTIME=claude이면 제외
  ✅ agy peer - CURRENT_RUNTIME=agy이면 제외
  ✅ Grok (검증자) - Auto-continue
  ✅ GPT OSS 120B (검증자) - MCP vllm_generate

  → 현재 실행 주체를 제외한 peer 검증자로 검증을 진행합니다.
  → Token 절약 모드: 활성화

======================================================================
📝 Round 1: 초기 검토
======================================================================

[Codex] 🔍 리뷰 검토 중...
  분석 항목: 10개 이슈
  ✅ 동의: 7개 (70%)
  ⚠️  수정 제안: 2개 (20%)
  ❌ 반대: 1개 (10%)

[Claude] 🔍 리뷰 검토 중...
  분석 항목: 10개 이슈
  ✅ 동의: 8.2개 (82%)
  ⚠️  수정 제안: 1개 (10%)
  ❌ 반대: 0.8개 (8%)

[agy] 🔍 리뷰 검토 중...
  분석 항목: 10개 이슈
  ✅ 동의: 8개 (80%)
  ⚠️  수정 제안: 1개 (10%)
  ➕ 추가 이슈: 1개

[Grok] 🔍 리뷰 검토 중...
  분석 항목: 10개 이슈
  ✅ 동의: 7.5개 (75%)
  ⚠️  수정 제안: 2개 (20%)
  ❌ 반대: 0.5개 (5%)

[GPT OSS 120B] 🔍 리뷰 검토 중 (MCP vllm_generate)...
  분석 항목: 10개 이슈
  ✅ 동의: 7.8개 (78%)
  ⚠️  수정 제안: 1.7개 (17%)
  ❌ 반대: 0.5개 (5%)

💾 피드백 저장
  📁 reviews/feedback_codex_round1.md
  📁 reviews/feedback_claude_round1.md
  📁 reviews/feedback_agy_round1.md
  📁 reviews/feedback_grok_round1.md
  📁 reviews/feedback_vllm_round1.md

📊 합의 상태 확인
  평균 동의율: 77%
  → ⚠️  합의 미달 (목표: 80%)
  → 피드백 반영 후 Round 2 진행

🎯 Token 사용: Round 1 = 5,000 tokens

======================================================================
🔄 Round 2: 개선 및 재검증 (Token 절약 모드)
======================================================================

피드백 반영:
  ⚠️  Codex peer 제안 #1: Issue #3 심각도 상향 (Minor → Major) ✅
  ⚠️  Claude 제안 #1: 재현 조건 명확화 ✅
  ❌ Grok 반대 #1: Issue #5는 False Positive → 제거 ✅
  ➕ agy 추가: Type safety 이슈 추가 ✅

수정된 리뷰로 재검증 (변경사항만 전달)...

[Codex] 🔍 재검토 중 (summary context)...
  ✅ 동의: 9개 (90%)
  ⚠️  수정 제안: 1개 (10%)
  📉 Token 절감: 4,500 (90%)

[Claude] 🔍 재검토 중 (요약 컨텍스트)...
  ✅ 동의: 9.3개 (93%)
  📉 Token 절감: 4,000 (80%)

[agy] 🔍 재검토 중 (요약 컨텍스트)...
  ✅ 동의: 9.5개 (95%)
  📉 Token 절감: 4,000 (80%)

[Grok] 🔍 재검토 중 (Continue)...
  ✅ 동의: 9.2개 (92%)
  📉 Token 절감: 4,600 (92%)

[GPT OSS 120B] 🔍 재검토 중 (MCP vllm_generate)...
  ✅ 동의: 9.1개 (91%)
  📉 Token 절감: Context summary 방식

📊 합의 상태 확인
  평균 동의율: 92.0%
  → ✅ 합의 도달!

🎯 Token 사용: Round 2 = 500 tokens (평균)
💡 Token 절감: 4,500 tokens (90%)

======================================================================
✅ 검증 완료
======================================================================

📄 최종 검증 리포트: reviews/validated_review_20251104_153045_final.md

📊 검증 결과:
  ✅ Consensus Reached
  🔄 Validation Rounds: 2
  👥 Validators: peer runtimes only (Codex/Claude/agy 중 현재 주체 제외) + optional Grok/GPT OSS 120B
  📈 Agreement: 92.0%
  💰 Total Token Usage: 5,500 tokens
  💡 Token Savings: 4,500 tokens (45%)

📝 변경 사항:
  ✅ 1개 이슈 심각도 상향 (Minor → Major)
  ✅ 1개 False Positive 제거
  ✅ 1개 추가 이슈 발견 (Type safety)
  ✅ 2개 설명 명확화

🎯 최종 이슈 목록:
  🔴 Critical: 2개
  🟡 Major: 4개 (1개 상향)
  🟢 Minor: 4개 (1개 제거, 1개 추가)

✅ 모든 AI가 최종 리뷰에 동의했습니다.
```

---

## 파일 구조

```
reviews/
├── initial_review_20251104_153045.md           # 사용자가 제공한 원본 리뷰
├── feedback_codex_round1.md                    # Codex Round 1 피드백
├── feedback_claude_round1.md                   # Claude Round 1 피드백
├── feedback_agy_round1.md                   # agy Round 1 피드백
├── feedback_grok_round1.md                     # Grok Round 1 피드백
├── feedback_vllm_round1.md                     # GPT OSS 120B Round 1 피드백
├── feedback_codex_round2.md                    # Codex Round 2 피드백 (요약)
├── feedback_claude_round2.md                   # Claude Round 2 피드백 (요약)
├── feedback_agy_round2.md                   # agy Round 2 피드백 (요약)
├── feedback_grok_round2.md                     # Grok Round 2 피드백 (요약)
├── feedback_vllm_round2.md                     # GPT OSS 120B Round 2 피드백 (요약)
├── .codex_session_id                           # Codex peer CLI/plugin 세션 ID(있는 경우, CURRENT_RUNTIME=codex이면 없음)
└── validated_review_20251104_153045_final.md   # 최종 검증 리포트
```

---

## 검증 프롬프트 템플릿 (Round 2+ 재검증용)

Round 1은 blind 프롬프트(Phase 3 참조)를 사용한다. 아래 템플릿은 Round 2 이후 수정된 리뷰를 재검증할 때, 또는 아티팩트 확보 불가로 blind round를 생략한 경우에만 사용한다:

```
다음 코드 리뷰를 검증해주세요:

=== CODE REVIEW ===
{review_content}
===================

검증 항목:

1. **정확성**
   - 지적한 이슈가 실제 문제인가요?
   - False Positive가 있나요?

2. **완전성**
   - 놓친 중요한 이슈가 있나요?
   - 추가로 검토해야 할 부분이 있나요?

3. **심각도**
   - Critical/Major/Minor 분류가 적절한가요?
   - 재분류가 필요한 이슈가 있나요?

4. **해결 방법**
   - 제안된 해결 방법이 적절한가요?
   - 더 나은 대안이 있나요?

5. **명확성**
   - 설명이 명확한가요?
   - 개발자가 이해하기 쉬운가요?

응답 형식:

## ✅ 동의하는 부분
1. [이슈 번호]: [동의 이유]

## ⚠️  수정 제안
1. [이슈 번호]: [수정 내용과 이유]

## ❌ 반대하는 부분
1. [이슈 번호]: [반대 이유와 대안]

## ➕ 추가 이슈
1. [새 이슈 설명]: [심각도와 해결 방법]

## 📊 전체 평가
- 동의율: [%]
- 전반적 품질: [상/중/하]
- 종합 의견: [한 줄 평가]
```

---

## 문제 해결

### 검증자가 없는 경우

```
⚠️  사용 가능한 검증자가 없습니다.

다음 중 하나를 설치해주세요:

# Codex (OpenAI)
# CURRENT_RUNTIME=codex이면 자기 검증이므로 설치 여부와 무관하게 검증자에서 제외
# Claude Code에서는 Codex 플러그인 또는 codex exec 사용 가능
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex

# Claude
# https://docs.anthropic.com/claude-code 또는 사내 설치 절차에 따라 claude CLI 설치

# agy (Google Antigravity CLI)
# 공식 설치 가이드: https://antigravity.google/get-started
# 설치 후 `agy install`로 PATH/alias 설정

# Grok (xAI) — 설치된 CLI의 setup/login/model 상태 확인
grok setup
grok login
grok models

# Ollama Cloud GLM-5.2 — OLLAMA_API_KEY 설정 후 helper smoke test
python3 ~/ai-agent-config/packages/common/.apm/skills/consensus-code-review/scripts/ollama_cloud_review.py \
  /path/to/prompt.txt --model glm-5.2:cloud
```

### Resume 기능이 작동하지 않는 경우

**Codex peer:**

```
# CURRENT_RUNTIME=codex이면 실행하지 않는다.
printf '%s\n' "Review only. Previous summary: ... Changes: ..." \
  | run_codex_peer -C "$PWD" -s read-only --ephemeral --color never -

# 이전 세션 이어가기 (codex CLI 직접 — plugin codex:codex-rescue는 stale 버그로 미사용)
printf '%s\n' "--resume 이전 작업 계속" \
  | codex exec resume --last -m gpt-5.6-sol -c model_reasoning_effort=high -C "$PWD" -s read-only --color never -
```

**Claude:**

```bash
printf '%s' "Review and respond only — do not edit any files. 이전 검토 요약: ... 변경사항: ..." | run_claude_peer
```

**agy:**

```bash
# agy --print는 매 호출 새 세션이므로 resume 개념이 없다.
# 인터랙티브 세션을 이어가려면 아래를 사용한다.
agy --continue               # 가장 최근 대화 이어가기
agy --conversation [[ORCA_RICH_MD:<conversation-id>:inline-html:%3Cid%3E]]      # 특정 대화 ID로 재개
```

**Grok:**

```bash
# review context가 섞이지 않도록 최근 대화를 resume하지 않는다.
# 이전 피드백 요약 + 변경사항을 새 prompt file에 담아 headless로 재호출한다.
run_grok_peer /path/to/recheck-prompt.txt
```

**Ollama Cloud GLM-5.2:**

```bash
# stateless API: 이전 피드백 요약 + 변경사항을 prompt file에 포함한다.
run_ollama_cloud_peer /path/to/recheck-prompt.txt
```

### 리뷰 형식이 불명확한 경우

권장 리뷰 형식:

```markdown
## Critical Issues
1. [이슈 제목] - [파일:라인]
   [설명]

## Major Issues
2. [이슈 제목] - [파일:라인]
   [설명]

## Minor Issues
3. [이슈 제목] - [파일:라인]
   [설명]
```

---

## Resume 기능 제공 현황


| 검증자                      | Resume 지원 | 방법                                                                                                              | 자동 저장 |
| ------------------------ | --------- | --------------------------------------------------------------------------------------------------------------- | ----- |
| **Codex peer**           | ⚠️ 제한적    | `codex exec`에 이전 피드백 요약 + 변경사항 전달. CURRENT_RUNTIME=codex이면 제외                                                   | ❌ 수동  |
| **Claude peer**          | ⚠️ 제한적    | `claude -p`에 이전 피드백 요약 + 변경사항 전달. CURRENT_RUNTIME=claude이면 제외                                                   | ❌ 수동  |
| **agy peer**             | ⚠️ 제한적    | `agy --print`는 매 호출 새 세션. resume은 인터랙티브 `agy --continue` 또는 `agy --conversation <id>`. CURRENT_RUNTIME=agy이면 제외 | ❌ 수동  |
| **Grok**                 | ⚠️ 제한적    | headless `--prompt-file`에 이전 피드백 요약 + 변경사항 전달                                                                   | ❌ 수동  |
| **Ollama Cloud GLM-5.2** | ⚠️ 제한적    | stateless API에 이전 피드백 요약 + 변경사항 전달                                                                              | ❌ 수동  |
| **GPT OSS 120B**         | ⚠️ 불필요    | MCP `vllm_generate` 도구 (Claude가 컨텍스트 관리)                                                                        | N/A   |



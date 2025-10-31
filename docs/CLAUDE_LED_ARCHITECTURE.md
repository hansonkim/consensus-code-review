# CLAUDE-Led Iterative Review Architecture

## 핵심 개념

CLAUDE MCP 환경에서 CLAUDE가 주도적으로 리포트를 작성하고, 다른 AI들이 검토하는 iterative refinement 방식입니다.

## 기존 vs 신규 아키텍처

### 기존 (Parallel Independent Review)

```
Round 1: 모든 AI가 독립적으로 리뷰 (병렬)
  AI1 → Review1
  AI2 → Review2
  AI3 → Review3

Round 2: 모든 AI가 서로 비평 (병렬)
  AI1 reads Review2, Review3 → Critique1
  AI2 reads Review1, Review3 → Critique2
  AI3 reads Review1, Review2 → Critique3

Final: Python이 consensus 계산 후 최종 리포트
  Python: 모든 리뷰에서 issue 추출 → 일치율 계산
  AI1: Python 계산 결과로 리포트 작성
```

**문제점**:
- CLAUDE MCP 환경인데 CLAUDE가 특별한 역할이 없음
- 병렬 독립 리뷰는 중복과 불일치 발생
- 최종 통합이 기계적 (Python 계산 기반)

### 신규 (CLAUDE-Led Iterative Refinement)

```
Round N (반복):
  1. CLAUDE가 REPORT 작성 (첫 번째 라운드) 또는 수정 (이후 라운드)
     └─ Python이 큐레이션한 변경사항 기반

  2. 다른 AI들이 REPORT 검토 (병렬)
     AI2 → Review of CLAUDE's REPORT
     AI3 → Review of CLAUDE's REPORT
     AI4 → Review of CLAUDE's REPORT

  3. CLAUDE가 검토들을 읽고 판단:
     ├─ 수정 필요? → REPORT 수정 → 다음 Round
     └─ 수정 불필요? → Consensus 체크

  4. Consensus 체크:
     CLAUDE: "더 이상 수정할 내용이 없음" ✓
     Others: "REPORT에 동의함" ✓
     → 모두 동의하면 DONE

최종 결과: CLAUDE의 refined REPORT
```

**장점**:
- CLAUDE MCP 환경에 자연스러움
- Iterative refinement로 품질 향상
- 일관성 있는 단일 리포트
- 자연스러운 consensus (수렴)

## 상세 Flow

### Phase 1: CLAUDE 초기 REPORT 작성

```python
# Round 1
curated_data = python_curator.curate(base_branch, target_branch)

claude_prompt = f"""
큐레이션된 변경사항을 분석하여 종합적인 코드 리뷰 REPORT를 작성하세요.

{curated_data}

REPORT 형식:
- Critical Issues
- Major Issues
- Minor Issues
- Positive Observations
"""

claude_report_v1 = claude.execute(claude_prompt)
```

### Phase 2: 다른 AI들의 검토 (병렬)

```python
# Round 1 (계속)
def review_claude_report(ai, claude_report):
    prompt = f"""
    CLAUDE가 작성한 코드 리뷰 REPORT를 검토하세요.

    {claude_report}

    각 issue에 대해:
    - ✅ AGREE: 동의
    - ⚠️ NEEDS_CHANGE: 수정 필요
    - ❌ DISAGREE: 동의하지 않음
    - 💡 MISSING: 놓친 issue
    """
    return ai.execute(prompt)

# 병렬 실행
reviews = ThreadPoolExecutor.map(
    review_claude_report,
    other_ais,
    [claude_report_v1] * len(other_ais)
)
```

### Phase 3: CLAUDE의 반영 판단

```python
# Round 2
claude_refinement_prompt = f"""
당신이 작성한 REPORT에 대한 다른 AI들의 검토입니다:

{reviews}

검토 내용을 비판적으로 평가하여:
1. 수정이 필요한가?
   - YES → REPORT를 수정하세요
   - NO → "NO_CHANGES_NEEDED"라고 명시하세요

2. 수정이 필요하다면:
   - 어떤 검토 의견을 수용할 것인가?
   - 어떤 의견은 거부할 것인가? (이유 설명)
   - 수정된 REPORT 작성
"""

claude_decision = claude.execute(claude_refinement_prompt)

if "NO_CHANGES_NEEDED" in claude_decision:
    # Consensus 체크로 진행
else:
    claude_report_v2 = extract_report(claude_decision)
    # 다음 Round로 (Phase 2로 돌아감)
```

### Phase 4: Consensus 확인

```python
# CLAUDE가 "NO_CHANGES_NEEDED"라고 했을 때만 실행

def check_agreement(ai, claude_report):
    prompt = f"""
    CLAUDE의 최종 REPORT입니다:

    {claude_report}

    이 REPORT에 동의하십니까?
    - YES: 동의함 (추가 수정 불필요)
    - NO: 동의하지 않음 (이유 설명)
    """
    return ai.execute(prompt)

agreements = ThreadPoolExecutor.map(
    check_agreement,
    other_ais,
    [claude_report_final] * len(other_ais)
)

if all("YES" in agreement for agreement in agreements):
    # 합의 완료! ✅
    return claude_report_final
else:
    # 합의 실패 → 다음 Round
    # 동의하지 않는 AI의 이유를 CLAUDE에게 전달
```

## Round 개념

하나의 **Round**는:

1. CLAUDE REPORT 작성/수정
2. 다른 AI들 검토 (병렬)
3. CLAUDE 반영 판단
4. Consensus 체크 (if needed)

**예시**:
- **Round 1**: CLAUDE 초기 REPORT → 검토 → CLAUDE "수정 필요" → 수정
- **Round 2**: CLAUDE 수정 REPORT → 검토 → CLAUDE "수정 필요" → 수정
- **Round 3**: CLAUDE 최종 REPORT → 검토 → CLAUDE "수정 불필요" → Consensus ✅

## 합의 (Consensus) 조건

두 가지 모두 만족해야 합의 완료:

1. **CLAUDE**: "NO_CHANGES_NEEDED" (더 이상 수정할 내용이 없음)
2. **다른 AI들**: 모두 "YES" (REPORT에 동의함)

합의 실패 시:
- `round_num < max_rounds` → 다음 Round 계속
- `round_num >= max_rounds` → 최신 CLAUDE REPORT를 최종 결과로 반환 (경고 포함)

## 구현 변경사항

### 1. `phase1_reviewer_mcp_orchestrated.py`

```python
class MCPOrchestratedReviewer:
    def execute(self, available_ais, ...):
        # CLAUDE는 필수
        if "claude" not in available_ais:
            raise ValueError("CLAUDE is required in MCP environment")

        claude = available_ais["claude"]
        other_ais = {k: v for k, v in available_ais.items() if k != "claude"}

        # Round 1: CLAUDE 초기 REPORT
        claude_report = self._claude_initial_report(claude, curated_data)

        # Iteration
        for round_num in range(2, max_rounds + 1):
            # 다른 AI들 검토
            reviews = self._parallel_reviews(other_ais, claude_report)

            # CLAUDE 반영 판단
            decision = self._claude_refine(claude, claude_report, reviews)

            if decision["no_changes_needed"]:
                # Consensus 체크
                if self._check_consensus(other_ais, claude_report):
                    return claude_report  # ✅ 합의 완료
                else:
                    # 동의하지 않는 이유 수집 → 다음 Round
                    continue
            else:
                # REPORT 수정 → 다음 Round
                claude_report = decision["refined_report"]

        # Max rounds 도달 → 최신 REPORT 반환
        return claude_report
```

### 2. `minimal_prompt.py`

4개의 새로운 프롬프트:

```python
def generate_claude_initial_report_prompt(session_id, curated_data):
    """CLAUDE 초기 REPORT 작성"""

def generate_reviewer_critique_prompt(ai_name, claude_report):
    """다른 AI들이 CLAUDE REPORT 검토"""

def generate_claude_refinement_prompt(claude_report, reviews):
    """CLAUDE가 검토를 반영하여 REPORT 수정 판단"""

def generate_consensus_check_prompt(ai_name, claude_report):
    """다른 AI들이 최종 REPORT 동의 여부 확인"""
```

### 3. `review_orchestrator.py`

MCP 도구는 거의 그대로 유지. 단지:
- Round 1에서 CLAUDE만 submit
- Round 2+에서 다른 AI들이 critique submit
- CLAUDE의 refinement 저장
- Consensus 상태 추적

## 장점

1. **CLAUDE MCP 환경에 자연스러움**: CLAUDE가 주도
2. **품질 향상**: Iterative refinement
3. **일관성**: 단일 통합 리포트
4. **효율성**: 중복 리뷰 없음
5. **투명성**: 각 Round의 변경 이력 추적 가능
6. **자연스러운 합의**: 수렴 기반

## 사용자 경험

```bash
python review.py --base develop

🤖 AI Code Review System - CLAUDE-Led Iterative Review
======================================================================

🔍 AI CLI 자동 감지 중...
  ✅ CLAUDE: claude-sonnet-4.5 (Lead Reviewer)
  ✅ GPT4: gpt-4-turbo (Reviewer)
  ✅ GEMINI: gemini-1.5-pro (Reviewer)

======================================================================
Round 1: Initial Report by CLAUDE
======================================================================

[CLAUDE] 📝 코드 변경사항 분석 중...
[CLAUDE] ✅ 초기 REPORT 작성 완료 (3,245자)
   → Critical: 2개
   → Major: 4개
   → Minor: 7개

[GPT4] 🔍 CLAUDE REPORT 검토 중...
[GEMINI] 🔍 CLAUDE REPORT 검토 중...

[GPT4] ✅ 검토 완료: 3개 수정 제안
[GEMINI] ✅ 검토 완료: 2개 수정 제안

[CLAUDE] 🤔 검토 내용 반영 판단 중...
[CLAUDE] ✏️ REPORT 수정 필요 → Round 2로 진행

======================================================================
Round 2: CLAUDE Refines Report
======================================================================

[CLAUDE] ✏️ REPORT 수정 중...
[CLAUDE] ✅ 수정 완료 (3,510자)
   → Critical: 3개 (+1)
   → Major: 4개
   → Minor: 6개 (-1)

[GPT4] 🔍 수정된 REPORT 검토 중...
[GEMINI] 🔍 수정된 REPORT 검토 중...

[GPT4] ✅ 검토 완료: 동의
[GEMINI] ✅ 검토 완료: 1개 수정 제안

[CLAUDE] 🤔 검토 내용 반영 판단 중...
[CLAUDE] ✏️ REPORT 수정 필요 → Round 3로 진행

======================================================================
Round 3: Final Consensus
======================================================================

[CLAUDE] ✏️ REPORT 최종 수정 중...
[CLAUDE] ✅ 수정 완료 (3,580자)
[CLAUDE] ✓ 더 이상 수정할 내용 없음

[GPT4] 🔍 최종 REPORT 확인 중...
[GEMINI] 🔍 최종 REPORT 확인 중...

[GPT4] ✅ 최종 REPORT에 동의
[GEMINI] ✅ 최종 REPORT에 동의

✅ 합의 완료! (Round 3)

======================================================================
📄 최종 리포트: reviews/review_20251031_153045_final.md
======================================================================
```

## 다음 단계

1. ✅ 아키텍처 설계 완료
2. ⏳ `minimal_prompt.py` 수정 (4개 프롬프트)
3. ⏳ `phase1_reviewer_mcp_orchestrated.py` 재작성
4. ⏳ 테스트 업데이트
5. ⏳ 문서 업데이트

---

**설계**: 2025-10-31
**상태**: 설계 완료, 구현 대기중

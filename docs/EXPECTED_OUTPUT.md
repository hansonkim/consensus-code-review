# Expected Output - Multi-Round AI Code Review

이 문서는 Multi-Round AI Code Review 실행 시 예상되는 출력을 보여줍니다.

## 전체 진행 과정

```
======================================================================
MCP-Orchestrated Multi-Round Code Review
======================================================================
참여 AI: 3개 (Claude, GPT-4, Gemini)
Base: develop → Target: HEAD
최대 라운드: 3

✅ 세션 생성: review_1730356789
```

---

## Round 1: Independent Review

### Step 1: Python Data Curation

```
======================================================================
Step 1: Python Data Curation
======================================================================

📊 Python이 변경사항 큐레이션 중...
   Base: develop → Target: HEAD
   ✓ 총 76개 파일 변경 감지
   ✓ 우선순위 계산 완료
   ✓ 큐레이션 완료: 20개 선택, 56개 생략
   ✓ 토큰 사용량: 18,432 / 20,000

✅ 큐레이션 완료:
   - 전체 파일: 76
   - 선택된 파일: 20
   - 토큰 사용: 18,432 / 20,000
```

**설명**:
- Python이 Git 조회 수행 (AI는 관여 안 함)
- 규칙 기반 우선순위: auth/database/api = Priority 1
- 토큰 예산(20K) 내에서 최적 파일 선택
- 56개 파일은 낮은 우선순위로 스킵

### Step 2: AI Independent Reviews (Parallel)

```
======================================================================
Step 2: AI Independent Reviews (Parallel)
======================================================================

[Claude] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중
   → 프롬프트: 23,456 문자

[GPT-4] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중
   → 프롬프트: 23,456 문자

[Gemini] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중
   → 프롬프트: 23,456 문자

[Claude] ✓ 리뷰 완료
   → Critical: 3개
   → Major: 5개
   → Minor: 8개
   → 총 3,245 자

[GPT-4] ✓ 리뷰 완료
   → Critical: 2개
   → Major: 6개
   → Minor: 7개
   → 총 2,987 자

[Gemini] ✓ 리뷰 완료
   → Critical: 3개
   → Major: 4개
   → Minor: 9개
   → 총 3,102 자
```

**설명**:
- 모든 AI가 **동일한 큐레이션 데이터** 받음 (공정성)
- **병렬 실행** (3개 AI 동시 작업)
- AI는 탐색 없이 **리뷰만 작성** (Pure Task Delegation)
- 각 AI가 독립적으로 이슈 발견

### Round 1 Summary

```
======================================================================
Round 1 Summary
======================================================================

각 AI가 발견한 이슈:
  [Claude] Critical: 3개 | Major: 5개 | Minor: 8개
  [GPT-4] Critical: 2개 | Major: 6개 | Minor: 7개
  [Gemini] Critical: 3개 | Major: 4개 | Minor: 9개

총 발견된 이슈 (중복 포함):
  Critical: 8개
  Major: 15개
  Minor: 24개

→ 다음 단계: AI들이 서로의 리뷰를 검토하고 합의 구축
```

**설명**:
- 중복 포함 개수 (같은 이슈를 여러 AI가 발견했을 수 있음)
- 다음 라운드에서 중복 제거 및 합의 구축

---

## Round 2: Peer Review & Consensus Building

```
======================================================================
Round 2: Peer Review & Consensus Building
======================================================================

각 AI가 다른 AI들의 리뷰를 비판적으로 검토합니다...

[Claude] 비판적 검토 시작
   → 검토 대상: GPT-4, Gemini

[GPT-4] 비판적 검토 시작
   → 검토 대상: Claude, Gemini

[Gemini] 비판적 검토 시작
   → 검토 대상: Claude, GPT-4

[Claude] ✓ 검토 완료
   → 동의: 8개 이슈
   → 부분 동의: 3개 이슈
   → 반대: 2개 이슈
   → 새로 발견: 1개 이슈

[GPT-4] ✓ 검토 완료
   → 동의: 9개 이슈
   → 부분 동의: 2개 이슈
   → 반대: 1개 이슈
   → 새로 발견: 0개 이슈

[Gemini] ✓ 검토 완료
   → 동의: 7개 이슈
   → 부분 동의: 4개 이슈
   → 반대: 3개 이슈
   → 새로 발견: 2개 이슈
```

**설명**:
- 각 AI가 다른 AI들의 리뷰를 받아서 비판적 검토
- ✅ 동의, ⚠️ 부분 동의, ❌ 반대로 입장 표명
- 새로운 이슈 추가 발견 가능
- 합의 형성 과정

### Round 2 Summary: Consensus Building

```
======================================================================
Round 2 Summary: Consensus Building
======================================================================

각 AI의 동의/반대 분포:
  [Claude] 동의 62% | 부분동의 3개 | 반대 2개
  [GPT-4] 동의 75% | 부분동의 2개 | 반대 1개
  [Gemini] 동의 50% | 부분동의 4개 | 반대 3개

→ 다음 단계: Python이 자동으로 consensus 계산 후 최종 리포트 생성
```

**설명**:
- 각 AI의 동의 성향 확인
- GPT-4가 가장 협조적 (75% 동의)
- Gemini가 가장 비판적 (50% 동의)
- Python이 객관적으로 합의 수준 계산

---

## Final Round: Consensus Report

### Step 3: Python Consensus Calculation

```
======================================================================
Step 3: Python Consensus Calculation (3 AIs)
======================================================================

📊 모든 AI 리뷰를 분석하여 합의 수준을 자동 계산 중...

✅ Consensus 계산 완료!

합의 수준별 이슈 분류:

  🚨 Critical Issues: 2개 (100% 동의 - 반드시 수정)
     - SQL Injection Vulnerability (auth/login.py:42)
       동의: Claude, GPT-4, Gemini
     - Hardcoded API Key (config/settings.py:15)
       동의: Claude, GPT-4, Gemini

  ⚠️  Major Issues: 5개 (≥66% 동의 - 수정 권장)
     - Memory Leak in File Handler (processor/handler.py:156)
       동의: Claude, GPT-4 (67%)
     - Missing Input Validation (api/endpoints.py:89)
       동의: Claude, Gemini (67%)
     - Race Condition Possible (database/transaction.py:234)
       동의: GPT-4, Gemini (67%)
     ... 외 2개

  📝 Minor Issues: 8개 (≥33% 동의 - 검토 권장)
     - 3개 이슈: 2/3 AI 동의
     - 5개 이슈: 1/3 AI 동의

  🤔 Disputed Issues: 1개 (의견 불일치 - 팀 판단 필요)
     - Performance Optimization Needed (utils/helper.py:78)
       찬성: Claude, GPT-4 | 반대: Gemini

총 16개 unique 이슈 발견 (중복 제거 완료)
```

**설명**:
- **Python이 수학적으로 정확하게 계산** (AI 실수 없음)
- **중복 제거 완료**: 8+15+24 → 16개 unique issues
- **합의 수준 자동 분류**:
  - 100% 동의 (3/3) → Critical
  - ≥66% 동의 (2/3) → Major
  - ≥33% 동의 (1/3) → Minor
  - 반대 있음 → Disputed
- **투명성**: 누가 무엇에 동의했는지 명확

### Step 4: Final Report Writing

```
======================================================================
Step 4: Final Report Writing
======================================================================

[Claude]를 최종 리포트 작성자로 선정

Python이 계산한 consensus를 바탕으로 전문적인 최종 리포트 작성 중...
   → Critical 이슈: 반드시 수정 필요
   → Major 이슈: 수정 권장
   → Minor 이슈: 검토 권장
   → Disputed 이슈: 팀 판단 필요

✅ 최종 리포트 완료!
   → 길이: 4,567 자
   → 작성자: Claude
   → 기반: 3개 AI의 consensus
```

**설명**:
- Claude가 최종 리포트 작성 (순서상 첫 번째)
- **AI는 consensus 계산 안 함** - Python이 이미 했음
- **AI는 리포트 작성만** - 개발팀이 실행할 수 있도록
- 각 이슈별 구체적인 수정 방법 제안

---

## 최종 완료 메시지

```
✅ 최종 합의 완료

======================================================================
Review Complete
======================================================================

Session ID: review_1730356789

Round 1: 3/3 AI completed (독립적 리뷰)
Round 2: 3/3 AI completed (상호 검토)
Final Round: Consensus report generated

발견된 이슈:
  - Critical: 2개 (100% 동의)
  - Major: 5개 (≥66% 동의)
  - Minor: 8개 (≥33% 동의)
  - Disputed: 1개 (의견 불일치)

Total: 16 unique issues

최종 리포트는 세션에 저장되었습니다.
```

---

## 주요 특징

### 1. 진행 상황 투명성 ✅

모든 단계에서 무슨 일이 일어나는지 명확히 출력:
- Python 큐레이션 진행 상황
- 각 AI의 리뷰 완료 시 통계
- Round별 요약
- Consensus 계산 상세 결과

### 2. 합의 과정 가시화 ✅

```
Round 1: AI들이 독립적으로 이슈 발견
   [Claude] 3 critical, 5 major, 8 minor
   [GPT-4] 2 critical, 6 major, 7 minor
   [Gemini] 3 critical, 4 major, 9 minor

Round 2: AI들이 서로 검토
   [Claude] 62% 동의, 3 부분동의, 2 반대
   [GPT-4] 75% 동의, 2 부분동의, 1 반대
   [Gemini] 50% 동의, 4 부분동의, 3 반대

Final: Python이 합의 계산
   100% 동의 (3/3) → 2 critical issues
   ≥66% 동의 (2/3) → 5 major issues
   ≥33% 동의 (1/3) → 8 minor issues
   논쟁 중 → 1 disputed issue
```

### 3. 실시간 피드백 ✅

```
[Claude] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중

[Claude] ✓ 리뷰 완료
   → Critical: 3개
   → Major: 5개
   → Minor: 8개
```

사용자는 각 AI가 **무엇을 하고 있는지** 실시간으로 확인 가능

### 4. 라운드별 요약 ✅

각 라운드 끝에 요약 제공:
- Round 1: 각 AI가 발견한 이슈 통계
- Round 2: 동의/반대 분포
- Final: Consensus 계산 결과

### 5. Python vs AI 역할 명확화 ✅

```
Step 1: Python Data Curation
   → Python이 Git 조회, 파일 선택, 토큰 관리

Step 2: AI Independent Reviews
   → AI가 큐레이션된 데이터 분석

Step 3: Python Consensus Calculation
   → Python이 합의 수준 계산

Step 4: Final Report Writing
   → AI가 리포트 작성
```

---

## 실행 예시

```bash
$ python src/phase1_reviewer_mcp_orchestrated.py \
    --base develop \
    --target HEAD \
    --ais "Claude,GPT-4,Gemini" \
    --max-rounds 3

# 위의 모든 출력이 순차적으로 나타남
```

---

## 사용자 경험

### 명확한 진행 상황 확인

✅ "지금 뭐 하고 있나?" → 출력 보면 명확히 알 수 있음
✅ "어떤 AI가 뭘 발견했나?" → Round 1 Summary 확인
✅ "합의는 어떻게 됐나?" → Consensus Calculation 확인
✅ "얼마나 걸리나?" → 각 단계별 완료 메시지 확인

### 투명한 의사결정

✅ "왜 이게 Critical인가?" → 3/3 AI 모두 동의했기 때문
✅ "누가 반대했나?" → 각 이슈별 동의/반대 AI 명시
✅ "중복은?" → Python이 자동 제거, unique 개수 표시

---

**구현 완료**: 2025-10-31
**Status**: 🟢 Production Ready

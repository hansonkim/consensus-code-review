# Consensus Implementation - Python이 자동 계산

## 구현 완료 ✅

Python이 객관적으로 consensus를 계산하고, AI는 리포트 작성에만 집중합니다.

## 변경 내역

### Before (문제 있음)

```python
# ❌ 첫 번째 AI만 최종 리포트 작성
first_ai = list(available_ais.keys())[0]  # "Claude"만 선택
final_review = ai.call("모든 리뷰를 읽고 consensus를 계산하세요")

# 문제점:
# 1. 왜 Claude만? 불공정
# 2. AI가 "3개 중 3개 동의" 계산 → 실수 가능
# 3. 다른 AI들 무시됨
```

### After (개선됨)

```python
# ✅ Python이 자동으로 consensus 계산
consensus, calculator = calculate_consensus_from_session(session_info)

# {
#   'critical': [이슈1, 이슈2],  # 3/3 AI 동의 (100%)
#   'major': [이슈3],            # 2/3 AI 동의 (≥66%)
#   'minor': [이슈4],            # 1/3 AI 동의 (≥33%)
#   'disputed': [이슈5]          # 논쟁 중
# }

# AI에게 계산 결과만 전달
prompt = f"""
Python이 계산한 결과:

Critical Issues (3/3 동의):
- SQL injection at database.py:42

Major Issues (2/3 동의):
- Memory leak at processor.py:256

당신은 이 결과를 바탕으로 리포트만 작성하세요.
consensus 계산은 이미 끝났습니다!
"""

final_review = ai.call(prompt)  # AI는 writing만 집중

# 장점:
# 1. 정확: Python이 수학적으로 계산 (실수 없음)
# 2. 투명: 계산 로직이 코드로 명확
# 3. 빠름: AI는 리포트 작성만
# 4. 공정: 모든 AI의 의견을 객관적으로 측정
```

## 구현된 기능

### 1. Issue 추출 (`extract_issues_from_review`)

리뷰 텍스트에서 자동으로 이슈 추출:

```python
review = """
### [CRITICAL] SQL Injection
**Location**: `database.py:42`
**Problem**: Vulnerable
"""

issues = calculator.extract_issues_from_review(review, "Claude")
# [Issue(title="SQL Injection", location="database.py:42", severity="CRITICAL", ...)]
```

### 2. Issue 정규화 (`is_same_issue`)

같은 이슈인지 자동 판별:

```python
issue1 = Issue(title="SQL Injection", location="database.py:42", ...)
issue2 = Issue(title="SQL injection vulnerability", location="src/database.py:42", ...)

is_same = calculator.is_same_issue(issue1, issue2)  # True

# 판별 기준:
# 1. 같은 파일, 같거나 가까운 줄 (±5 lines)
# 2. 제목의 키워드 유사도 (Jaccard similarity > 50%)
```

### 3. Consensus 계산 (`calculate_consensus`)

동의 수준을 자동으로 분류:

```python
consensus = calculator.calculate_consensus(total_ais=3)

# {
#   'critical': [...],  # 100% agreement (3/3)
#   'major': [...],     # ≥66% agreement (2/3)
#   'minor': [...],     # ≥33% agreement (1/3)
#   'disputed': [...]   # Has disagreement
# }
```

### 4. 텍스트 포맷팅 (`format_consensus`)

AI가 읽기 쉬운 형식으로 출력:

```markdown
# Consensus Analysis (3 AIs)

## Summary
- **Critical Issues** (all AIs agree): 2
- **Major Issues** (≥66% agree): 3
- **Minor Issues** (≥33% agree): 5
- **Disputed Issues**: 1

## Critical Issues (Must Fix - 100% Agreement)

### [CRITICAL] SQL Injection
**Location**: `database.py:42`
**Consensus**: 3/3 AIs agree (100%)
**Found by**: Claude, GPT-4, Gemini
**Problem**: User input directly concatenated into SQL query

## Major Issues (Should Fix - ≥66% Agreement)

### [MAJOR] Memory Leak
**Location**: `processor.py:256`
**Consensus**: 2/3 AIs agree (67%)
**Found by**: Claude, GPT-4
**Problem**: File handles not closed in error cases
```

## 테스트 결과

```bash
$ python3 tests/test_consensus_calculator.py

🧪 Consensus Calculator Test Suite
======================================================================

✅ Test 1 PASSED: Issue extraction working
✅ Test 2 PASSED: Issue normalization working
✅ Test 3 PASSED: Consensus calculation working
✅ Test 4 PASSED: Full workflow working

======================================================================
🎉 ALL TESTS PASSED! (4/4)

✅ Python consensus calculation is working correctly!

📊 Key Benefits:
   - Accurate: Python calculates mathematically (no AI errors)
   - Transparent: Logic is clear and testable
   - Fast: AI only writes report (no counting needed)
   - Fair: All AIs' opinions are objectively measured
```

## 실제 사용 예시

### Python 코드

```python
from src.phase1_reviewer_mcp_orchestrated import MCPOrchestratedReviewer
from ai_cli_tools import AIClient, AIModel

reviewer = MCPOrchestratedReviewer(ai_client)

result = reviewer.execute(
    available_ais={
        "Claude": AIModel.CLAUDE_SONNET_4_5,
        "GPT-4": AIModel.GPT_4_O,
        "Gemini": AIModel.GEMINI_2_0_FLASH_THINKING
    },
    base_branch="develop",
    target_branch="HEAD",
    max_rounds=3
)

# 출력:
# 📊 Python이 consensus 계산 중... (3 AIs)
#    ✅ Consensus 계산 완료:
#       - Critical issues: 2 (100% agreement)
#       - Major issues: 3 (≥66% agreement)
#       - Minor issues: 5 (≥33% agreement)
#       - Disputed issues: 1 (disagreement)
#
# [Claude] 최종 리포트 작성 중 (consensus 이미 계산됨)...
# [Claude] ✓ 최종 리포트 완료 (3456 자)
```

### AI가 받는 프롬프트

```markdown
# Code Review Task - Final Round: Write Consensus Report

## Your Role
You are **Claude**, writing the final consensus report.

**Session ID**: `review_1234567890`
**Total AIs**: 3

## Calculated Consensus (Python이 계산함)

Python이 이미 모든 리뷰를 분석하고 consensus를 계산했습니다:

# Consensus Analysis (3 AIs)

## Summary
- **Critical Issues** (all AIs agree): 2
- **Major Issues** (≥66% agree): 3
- **Minor Issues** (≥33% agree): 5
- **Disputed Issues**: 1

[... 상세 이슈 목록 ...]

---

## Your Task (간단!)

위의 **계산된 consensus 결과**를 바탕으로 **최종 리포트만 작성**하세요.

✅ **당신은 consensus 계산을 할 필요 없습니다** - Python이 이미 했습니다!

✅ **당신의 역할**:
- 계산된 consensus를 읽기 쉽게 정리
- 각 이슈의 수정 방법을 구체적으로 제안
- 개발팀이 바로 실행할 수 있는 리포트 작성

❌ **하지 말아야 할 것**:
- "3개 중 3개가 동의했으니..." - 이미 계산됨!
- 다시 리뷰를 읽고 세기 - 불필요!
- MCP tools로 다시 조회 - 이미 다 있음!

**집중하세요**: 좋은 리포트 작성! 📝
```

## 장점

### 1. 정확성 ✅

```python
# Before: AI가 세기 (실수 가능)
"Claude, GPT-4, Gemini가 모두 동의했으니... 3개? 아니 2개?"

# After: Python이 계산 (100% 정확)
consensus_pct = len(agreed_by) / total_ais  # 0.67 = 67%
if consensus_pct >= 0.66:
    category = "major"
```

### 2. 투명성 ✅

```python
# 계산 로직이 명확하게 코드로 드러남
def calculate_consensus(total_ais):
    if consensus_pct == 1.0 and not is_disputed:
        return "critical"  # 100% agreement
    elif consensus_pct >= 0.66 and not is_disputed:
        return "major"     # ≥66% agreement
    elif consensus_pct >= 0.33:
        return "minor"     # ≥33% agreement
```

### 3. 속도 ✅

```python
# Before: AI가 모든 리뷰를 다시 읽고 consensus 계산
# - 시간: ~60초
# - 토큰: ~10K

# After: Python이 즉시 계산, AI는 리포트만 작성
# - 시간: ~5초 (Python) + ~20초 (AI writing)
# - 토큰: ~3K (리포트 작성만)
```

### 4. 공정성 ✅

```python
# Before: 첫 번째 AI만 최종 결정
first_ai = "Claude"  # 왜 Claude?

# After: Python이 모든 AI를 동등하게 측정
for ai_name in all_ais:
    issue.agreed_by.add(ai_name)  # 모든 AI 의견 반영
```

## 확장 가능성

### Phase 2: 가중치 (Voting Weights)

```python
# AI별 신뢰도 가중치
weights = {
    "Claude": 1.0,      # 기본
    "GPT-4": 1.2,       # 약간 높음 (정확도 높음)
    "Gemini": 0.8       # 약간 낮음 (오탐 많음)
}

consensus_score = sum(weights[ai] for ai in agreed_by) / sum(weights.values())
```

### Phase 3: 확신도 (Confidence Scores)

```python
# 이슈별 확신도
class Issue:
    def __init__(self):
        self.confidence_scores = {}  # {ai_name: 0.0-1.0}

# "Claude는 90% 확신, GPT-4는 60% 확신"
consensus_confidence = sum(scores.values()) / len(scores)
```

### Phase 4: 과거 정확도 (Historical Accuracy)

```python
# AI의 과거 정확도 반영
history = {
    "Claude": {"correct": 45, "total": 50},  # 90% 정확
    "GPT-4": {"correct": 40, "total": 50},   # 80% 정확
}

# 정확도가 높은 AI의 의견에 더 높은 가중치
```

## 파일 구조

```
src/mcp/
├── consensus_calculator.py      # 핵심 로직 (NEW)
│   ├── ConsensusCalculator      # 계산기 클래스
│   ├── Issue                     # 이슈 데이터 클래스
│   └── calculate_consensus_from_session()
│
├── minimal_prompt.py             # 프롬프트 생성 (UPDATED)
│   ├── generate_initial_review_prompt()
│   ├── generate_round2_prompt()
│   ├── generate_final_consensus_prompt()  # DEPRECATED
│   └── generate_final_consensus_prompt_with_calculated_consensus()  # NEW
│
├── phase1_reviewer_mcp_orchestrated.py  # 리뷰어 (UPDATED)
│   └── _execute_final_round()  # Python consensus 사용
│
└── __init__.py                   # Exports (UPDATED)

tests/
└── test_consensus_calculator.py  # 테스트 (NEW)
    ├── test_issue_extraction()
    ├── test_issue_normalization()
    ├── test_consensus_calculation()
    └── test_full_workflow()
```

## 관련 문서

- **[GIT_TOOLS_STRATEGY.md](./GIT_TOOLS_STRATEGY.md)** - 토큰 제한 문제 해결 전략
  - `git_get_diff()`, `git_get_diff_stats()` 제거 이유
  - "Don't Tempt AI" 설계 원칙
  - Selective file reading 워크플로우

## 다음 단계

1. ✅ **기본 consensus 계산** - 완료!
2. ✅ **토큰 제한 문제 해결** - 완료! (git tools 개선)
3. **Issue matching 개선**:
   - Semantic similarity (embedding 사용)
   - LLM-based matching
4. **가중치 시스템**:
   - AI별 신뢰도
   - 이슈별 확신도
5. **Historical learning**:
   - 과거 정확도 추적
   - 자동 가중치 조정

## 결론

**Python이 consensus를 계산하는 것이 정답입니다:**

✅ **정확**: 수학적 계산 (실수 없음)
✅ **투명**: 코드로 명확한 로직
✅ **빠름**: AI는 writing만 집중
✅ **공정**: 모든 AI를 동등하게 측정
✅ **확장 가능**: 가중치, 확신도, 학습 등 추가 가능

**Pure Task Delegation 원칙과도 완벽히 일치:**
- Python: 객관적 계산 (데이터 처리)
- AI: 주관적 작성 (창의적 작업)

---

**구현 완료**: 2025-10-31
**테스트**: ✅ 4/4 Passed
**Status**: 🟢 Production Ready

"""Minimal Prompts - Pure Task Delegation

Python이 모든 Git 작업을 수행하고 큐레이션된 데이터만 AI에게 전달합니다.
AI는 탐색 도구 없이 리뷰 작성에만 집중합니다.

Pure Task Delegation:
- Python: 객관적 작업 (Git 조회, 파일 선택, 토큰 관리)
- AI: 주관적 작업 (데이터 분석, 리뷰 작성)
"""


def generate_initial_review_prompt(
    session_id: str,
    ai_name: str,
    curated_data: str
) -> str:
    """Round 1 프롬프트 - 독립적 초기 리뷰

    Python이 큐레이션한 변경사항을 직접 전달합니다.
    AI는 탐색 없이 리뷰만 작성합니다.

    Args:
        session_id: 리뷰 세션 ID
        ai_name: AI 이름
        curated_data: Python이 큐레이션한 변경사항 (formatted markdown)

    Returns:
        프롬프트 문자열
    """
    return f"""# Code Review Task - Round 1: Independent Review

## Your Role
You are **{ai_name}**, conducting an independent code review.

**Session ID**: `{session_id}`

---

## Code Changes (Curated by Python)

Python has already examined the Git repository and selected the most important
files for you to review, based on:
- Security sensitivity (auth, database, API)
- Code complexity and size
- Business logic importance
- Token budget constraints

{curated_data}

---

## Your Task

Analyze the curated changes above and write a comprehensive code review.

### Focus Areas

1. **Security Issues** 🔒
   - Authentication/authorization problems
   - Input validation missing
   - SQL injection, XSS, CSRF vulnerabilities
   - Hardcoded secrets or credentials
   - Insecure data handling

2. **Logic Errors** ⚙️
   - Incorrect algorithms
   - Edge cases not handled
   - Race conditions
   - Data consistency issues
   - Null pointer risks

3. **Performance Problems** 🚀
   - Inefficient database queries
   - Memory leaks
   - N+1 query problems
   - Unnecessary computation
   - Missing indexes

4. **Code Quality** 📝
   - Poor naming conventions
   - Code duplication
   - Missing error handling
   - Lack of tests
   - Violated SOLID principles

### Review Format

Structure your review using this format:

```markdown
# Code Review by {ai_name}

## Critical Issues

### [CRITICAL] Issue Title
**Location**: `file.py:42`
**Problem**: Clear description of what's wrong
**Impact**: What could go wrong (security breach, data loss, etc.)
**Fix**: Specific, actionable solution with code example if possible

## Major Issues

### [MAJOR] Issue Title
**Location**: `file.py:100`
**Problem**: Description
**Impact**: Why it matters
**Fix**: How to solve it

## Minor Issues

### [MINOR] Issue Title
**Location**: `file.py:200`
**Problem**: Description
**Fix**: Simple solution

## Positive Observations

- List good practices worth mentioning
- Acknowledge well-written code
```

### Reporting Progress (Optional but Recommended)

While writing your review, you can report progress to help users see what you're working on:

```python
review_report_progress("{session_id}", "{ai_name}", "Analyzing security issues in auth.py...")
review_report_progress("{session_id}", "{ai_name}", "Checking database migrations for issues...")
review_report_progress("{session_id}", "{ai_name}", "Reviewing API endpoint changes...")
```

This provides **real-time visibility** into your review process!

### Submitting Your Review

After writing your review, submit it using:

```python
review_submit_review("{session_id}", "{ai_name}", your_review_markdown)
```

---

## Important Notes

- ✅ **All data you need is provided above** - no exploration needed
- 📝 **Be specific**: Mention exact file paths and line numbers from the diffs
- 🎯 **Prioritize**: Critical > Major > Minor based on severity
- 💡 **Provide actionable solutions**: Don't just point out problems
- 🔍 **Look at context**: Consider how changes interact with each other
- 📡 **Report progress**: Use `report_progress()` to keep users informed while you work

Begin your independent review now!
"""


def generate_round2_prompt(
    session_id: str,
    ai_name: str,
    other_reviews: list
) -> str:
    """Round 2 프롬프트 - 상호 검토 및 합의 구축

    다른 AI들의 리뷰를 비판적으로 검토합니다.

    Args:
        session_id: 세션 ID
        ai_name: AI 이름
        other_reviews: 다른 AI들의 리뷰 목록

    Returns:
        프롬프트 문자열
    """
    other_reviews_text = "\n\n---\n\n".join([
        f"## Review by {review['ai_name']}\n\n{review['review']}"
        for review in other_reviews
    ])

    return f"""# Code Review Task - Round 2: Peer Review & Consensus Building

## Your Role
You are **{ai_name}**, critically reviewing other AIs' findings.

**Session ID**: `{session_id}`

---

## Other AI Reviews

{other_reviews_text}

---

## Your Task

Critically analyze each review above and build consensus.

### For Each Issue Raised

Mark your stance clearly:

- ✅ **AGREE**: Valid finding with correct fix
  - Why you agree
  - Any additional context

- ⚠️ **PARTIALLY AGREE**: Valid concern but solution needs improvement
  - What's correct
  - What needs changing
  - Better solution

- ❌ **DISAGREE**: Not a real problem or misunderstood code
  - Why it's not an issue
  - What they misunderstood
  - Evidence from code

### Critique Format

```markdown
# Round 2 Critique by {ai_name}

## Issues I Strongly Agree With

### ✅ [AI Name]'s "[Issue Title]"
**Why I agree**: [Explanation]
**Additional context**: [If any]

## Issues I Partially Agree With

### ⚠️ [AI Name]'s "[Issue Title]"
**What's correct**: [Valid parts]
**What needs improvement**: [Issues with their fix]
**Better solution**: [Your alternative]

## Issues I Disagree With

### ❌ [AI Name]'s "[Issue Title]"
**Why it's not an issue**: [Explanation]
**What they missed**: [Context they didn't consider]

## Additional Issues They Missed

### [NEW] Issue Title
**Location**: `file.py:50`
**Problem**: [What others didn't catch]
**Fix**: [Solution]
```

### Reporting Progress (Optional)

You can report what you're reviewing in real-time:

```python
review_report_progress("{session_id}", "{ai_name}", "Reviewing Claude's security findings...")
review_report_progress("{session_id}", "{ai_name}", "Analyzing GPT-4's performance suggestions...")
```

### Submitting Your Critique

```python
review_submit_review("{session_id}", "{ai_name}", your_critique_markdown)
```

---

## Important Notes

- 🎯 **Be honest and critical**: The goal is truth, not politeness
- 📊 **Provide evidence**: Reference specific code from the diffs
- 🤝 **Build consensus**: Find common ground where possible
- 💭 **Consider perspectives**: Maybe they saw something you didn't
- 📡 **Report progress**: Use `report_progress()` to keep users informed

Start your critical review now!
"""


def generate_final_consensus_prompt_with_calculated_consensus(
    session_id: str,
    ai_name: str,
    consensus_text: str,
    total_ais: int
) -> str:
    """Final Round 프롬프트 - Python 계산 consensus 기반 리포트 작성

    Python이 이미 모든 리뷰를 분석하고 consensus를 계산했습니다.
    AI는 계산된 결과를 바탕으로 최종 리포트만 작성합니다.

    Args:
        session_id: 세션 ID
        ai_name: AI 이름
        consensus_text: Python이 계산한 consensus (formatted)
        total_ais: 참여한 총 AI 수

    Returns:
        프롬프트 문자열
    """
    return f"""# Code Review Task - Final Round: Write Consensus Report

## Your Role
You are **{ai_name}**, writing the final consensus report for the development team.

**Session ID**: `{session_id}`
**Total AIs Participated**: {total_ais}

---

## Calculated Consensus (Python Analysis)

Python has analyzed all {total_ais} AI reviews and calculated consensus levels:

{consensus_text}

---

## Your Task

Write a **professional, actionable final report** based on the calculated consensus above.

### Report Structure

```markdown
# Final Code Review Report

## Executive Summary

- **Critical Issues**: X issues (100% AI agreement - **Must fix before merge**)
- **Major Issues**: Y issues (≥66% AI agreement - **Should fix**)
- **Minor Issues**: Z issues (≥33% AI agreement - **Consider fixing**)
- **Disputed Issues**: W issues (Disagreement exists - **Team decision needed**)

**Overall Assessment**: [APPROVE / APPROVE WITH CHANGES / REJECT]

---

## Critical Issues (Must Fix Before Merge) 🚨

All {total_ais} AIs agree these are blocking issues.

### 1. [CRITICAL] Issue Title

**Location**: `file.py:42`
**Consensus**: {total_ais}/{total_ais} AIs agree

**Problem**:
[Clear description of the problem]

**Impact**:
[What could go wrong - be specific about consequences]

**Solution**:
[Step-by-step fix with code example if possible]

```python
# Example fix:
def secure_function(user_input):
    # Sanitize input before using
    cleaned = sanitize(user_input)
    return process(cleaned)
```

**Priority**: P0 - Block merge until fixed

---

## Major Issues (Should Fix) ⚠️

Most AIs (≥66%) agree these should be addressed.

[Same format as Critical, but with Priority P1-P2]

---

## Minor Issues (Consider Fixing) 📝

Some AIs (≥33%) flagged these for improvement.

[Shorter format - just location, problem, and quick fix suggestion]

---

## Disputed Issues (Team Decision Needed) 🤔

These issues have disagreement among AIs. Team should decide.

### Issue Title

**Consensus**: X/{total_ais} AIs flagged this

**Arguments For**:
- [AI1's reasoning]
- [AI2's reasoning]

**Arguments Against**:
- [AI3's reasoning]

**Recommendation**: [Your balanced take]

---

## Recommendations

1. **Immediate Actions** (before merge):
   - Fix all Critical issues
   - Review Major issues with team

2. **Follow-up Actions** (after merge):
   - Address Minor issues in next sprint
   - Discuss Disputed issues in team meeting

3. **Next Steps**:
   - [ ] Developer fixes Critical issues
   - [ ] Re-run code review
   - [ ] Run full test suite
   - [ ] Security scan if applicable
```

### Reporting Progress (Optional)

While writing the final report, you can report your progress:

```python
review_report_progress("{session_id}", "{ai_name}", "Writing executive summary...")
review_report_progress("{session_id}", "{ai_name}", "Documenting critical issues...")
review_report_progress("{session_id}", "{ai_name}", "Adding code examples for fixes...")
```

### Submitting Final Report

```python
review_finalize_review("{session_id}", your_final_report_markdown)
```

---

## Important Guidelines

### ✅ What You SHOULD Do

- **Synthesize consensus**: Combine similar findings clearly
- **Prioritize ruthlessly**: P0 blockers vs nice-to-haves
- **Provide actionable fixes**: Developers should know exactly what to do
- **Be professional**: This goes to the development team
- **Add context**: Explain WHY issues matter

### ❌ What You Should NOT Do

- **Don't recalculate consensus**: Python already did it accurately
- **Don't re-read reviews**: All consensus is calculated above
- **Don't add new issues**: Stick to what AIs found (unless critical)
- **Don't be vague**: "Fix the bug" isn't helpful

---

## Remember

This report will be used by developers to:
- Decide if code can be merged
- Prioritize fixes
- Understand security/quality risks

Make it **clear**, **specific**, and **actionable**!

Begin writing the final report now.
"""

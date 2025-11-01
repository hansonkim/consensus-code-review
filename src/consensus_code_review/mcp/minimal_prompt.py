"""Minimal Prompts - CLAUDE-Led Iterative Review

CLAUDE가 주도적으로 REPORT를 작성하고, 다른 AI들이 검토하는
iterative refinement 방식입니다.

CLAUDE-Led Architecture:
- CLAUDE: REPORT 작성자이자 통합자
- 다른 AI들: REPORT 검토자
- Consensus: 자연스러운 수렴 (수정 없음 + 동의)
"""


def generate_claude_initial_report_prompt(
    session_id: str,
    curated_data: str
) -> str:
    """CLAUDE 초기 REPORT 작성 프롬프트 (Round 1)

    Python이 큐레이션한 변경사항을 분석하여
    종합적인 코드 리뷰 REPORT를 작성합니다.

    Args:
        session_id: 리뷰 세션 ID
        curated_data: Python이 큐레이션한 변경사항 (formatted markdown)

    Returns:
        프롬프트 문자열
    """
    return f"""# Code Review Task - Round 1: Initial Report by CLAUDE

## ⚠️ IMPORTANT: All Data Provided - No Tools Needed

**❌ DO NOT use any MCP tools** (no create_review_session, no git commands)
**❌ DO NOT run git diff or any bash commands**
**✅ ALL data you need is provided below - just analyze it and write your report**

---

## Your Role
You are **CLAUDE**, the **Lead Reviewer** in this MCP environment.

Your responsibility is to write a comprehensive code review REPORT that will be
reviewed and refined through multiple rounds with other AI reviewers.

**Session ID**: `{session_id}`

---

## Code Changes (Already Curated by Python)

**Python has already completed all Git operations for you.**

All changes have been:
- ✅ Retrieved from Git repository
- ✅ Filtered by importance (security, complexity, business impact)
- ✅ Formatted for your review
- ✅ Provided in full below

**Your job: Analyze the data below and write your REPORT. Nothing else.**

---

{curated_data}

---

## Your Task

Write a comprehensive code review REPORT analyzing **ONLY** the changes above.

**Do NOT:**
- ❌ Use any MCP tools to "explore" or "get" data
- ❌ Run git diff or any git commands
- ❌ Try to read additional files
- ❌ Search for more information

**Do:**
- ✅ Analyze the provided code changes
- ✅ Identify issues (Critical, Major, Minor)
- ✅ Write your REPORT in markdown
- ✅ (Optional) Report progress to keep users informed

### Report Structure

```markdown
# Code Review Report by CLAUDE

## Executive Summary

- **Total Files Changed**: X files
- **Critical Issues Found**: Y issues (🚨 must fix)
- **Major Issues Found**: Z issues (⚠️ should fix)
- **Minor Issues Found**: W issues (📝 consider fixing)
- **Overall Assessment**: [APPROVE / APPROVE WITH CHANGES / REJECT]

---

## Critical Issues (Must Fix Before Merge) 🚨

### 1. [CRITICAL] Issue Title

**Location**: `file.py:42-45`

**Problem**:
Clear description of what's wrong. Be specific about:
- What code pattern is problematic
- Why it's critical (security risk, data loss potential, etc.)

**Impact**:
Concrete consequences if not fixed:
- Security: SQL injection allows database access
- Data: User data could be exposed
- System: Application could crash

**Evidence**:
```python
# Current problematic code:
def unsafe_query(user_input):
    query = f"SELECT * FROM users WHERE id = {{user_input}}"
    return db.execute(query)  # ❌ SQL injection vulnerability
```

**Solution**:
Step-by-step fix with code example:

```python
# Fixed code:
def safe_query(user_input):
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, [user_input])  # ✅ Parameterized query
```

**Priority**: P0 - Block merge

---

## Major Issues (Should Fix) ⚠️

[Same detailed format as Critical, but with Priority P1-P2]

---

## Minor Issues (Consider Fixing) 📝

[Shorter format - location, problem, quick fix]

### [MINOR] Issue Title
**Location**: `file.py:200`
**Problem**: Brief description
**Fix**: Quick solution

---

## Positive Observations ✅

List good practices worth mentioning:
- Well-structured error handling in auth module
- Comprehensive test coverage for new features
- Clear documentation and comments
```

### Important Guidelines

#### ✅ What You SHOULD Do

- **Be specific**: Cite exact file paths and line numbers
- **Prioritize ruthlessly**: P0 (blocker) vs P1 (important) vs P2 (nice-to-have)
- **Provide evidence**: Show the problematic code
- **Give actionable fixes**: Include code examples
- **Consider security first**: Auth, validation, injection risks
- **Think about edge cases**: Null checks, error handling
- **Check performance**: N+1 queries, memory leaks

#### ❌ What You Should NOT Do

- **Don't be vague**: "Fix the bug" isn't helpful
- **Don't just list files**: Explain what's wrong
- **Don't skip evidence**: Always show code snippets
- **Don't forget impacts**: Explain consequences
- **Don't ignore good code**: Acknowledge what's well done

### Reporting Progress (Optional)

You may optionally report progress while writing (this helps users see what you're doing):

```python
review_report_progress("{session_id}", "CLAUDE", "Analyzing security patterns...")
```

But this is **completely optional**. Your main job is to write the REPORT.

---

## How to Submit Your Report

**You don't need to do anything special!**

Just write your REPORT in markdown format as your response. Python will automatically:
- ✅ Capture your REPORT
- ✅ Save it to the MCP session
- ✅ Pass it to other AI reviewers in the next round

---

## Remember

This is your **initial REPORT**. Other AI reviewers will critique it, and you'll
have opportunities to refine it in subsequent rounds.

Focus on:
- **Accuracy**: Get the facts right
- **Clarity**: Make issues easy to understand
- **Actionability**: Provide concrete solutions
- **Use ONLY the data provided above**: Don't explore or search for more

---

**Now write your comprehensive code review REPORT based on the data provided above.**
"""


def generate_reviewer_critique_prompt(
    session_id: str,
    ai_name: str,
    claude_report: str,
    curated_data: str
) -> str:
    """다른 AI들이 CLAUDE REPORT를 검토하는 프롬프트

    Args:
        session_id: 세션 ID
        ai_name: 검토자 AI 이름
        claude_report: CLAUDE가 작성한 REPORT
        curated_data: 원본 큐레이션 데이터 (필요시 참조)

    Returns:
        프롬프트 문자열
    """
    return f"""# Code Review Task - Critique CLAUDE's Report

## Your Role
You are **{ai_name}**, reviewing CLAUDE's code review REPORT.

**Session ID**: `{session_id}`

---

## CLAUDE's Report

{claude_report}

---

## Your Task

Critically review CLAUDE's report and provide feedback.

### For Each Issue CLAUDE Raised

Mark your stance clearly:

#### ✅ AGREE: Valid issue with correct analysis

```markdown
### ✅ AGREE: "[Issue Title from CLAUDE]"

**Why I agree**:
- The problem is correctly identified
- Impact assessment is accurate
- Proposed fix is appropriate

**Additional context** (if any):
- Edge case to consider: ...
- Alternative solution: ...
```

#### ⚠️ NEEDS_CHANGE: Valid concern but needs improvement

```markdown
### ⚠️ NEEDS_CHANGE: "[Issue Title]"

**What's correct**:
- Core problem is real

**What needs improvement**:
- Priority should be P0 not P1 because...
- Impact is more severe: ...
- Better fix would be: ...

**Suggested changes**:
[More accurate description or better solution]
```

#### ❌ DISAGREE: Not a real problem

```markdown
### ❌ DISAGREE: "[Issue Title]"

**Why it's not an issue**:
- Code is actually correct because...
- Context CLAUDE missed: ...

**Evidence**:
```python
# The code is safe because:
# [Explanation]
```
```

#### 💡 MISSING: Issues CLAUDE didn't catch

```markdown
### 💡 MISSING: New Issue Title

**Location**: `file.py:80`
**Problem**: CLAUDE missed this issue...
**Severity**: [Critical/Major/Minor]
**Fix**: How to solve it
```

### Your Critique Format

Structure your review like this:

```markdown
# Critique of CLAUDE's Report by {ai_name}

## Summary
- Issues I agree with: X
- Issues needing changes: Y
- Issues I disagree with: Z
- Missing issues I found: W

## Detailed Feedback

### ✅ Issues I Agree With

[List with brief confirmation]

### ⚠️ Issues Needing Changes

[Detailed feedback with improvements]

### ❌ Issues I Disagree With

[Clear reasoning with evidence]

### 💡 Missing Issues

[New issues CLAUDE didn't catch]

## Overall Assessment

- CLAUDE's report quality: [Excellent/Good/Needs Improvement]
- Key strengths: ...
- Key areas for improvement: ...
```

### Reference Data (For Context)

The original code changes are provided below for your reference:

<details>
<summary>Original Curated Changes (Click to expand)</summary>

{curated_data}

</details>

**Note**: You don't need to re-analyze all the code. Focus on reviewing CLAUDE's REPORT.

### Reporting Progress (Optional)

```python
review_report_progress("{session_id}", "{ai_name}", "Reviewing CLAUDE's security findings...")
```

This is **completely optional**.

---

## How to Submit Your Critique

**You don't need to do anything special!**

Just write your critique in markdown format as your response. Python will automatically:
- ✅ Capture your critique
- ✅ Save it to the MCP session
- ✅ Pass it to CLAUDE for refinement

---

## Important Notes

- 🎯 **Be honest and critical**: Truth over politeness
- 📊 **Provide evidence**: Reference specific code from CLAUDE's report
- 🤝 **Be constructive**: Help improve the report
- 🔍 **Look for gaps**: What did CLAUDE miss?
- 💭 **Consider context**: Maybe CLAUDE saw something you didn't
- ❌ **Don't use MCP tools or run git commands**: All data is already provided

---

**Now write your critical review of CLAUDE's REPORT.**
"""


def generate_claude_refinement_prompt(
    session_id: str,
    current_report: str,
    reviews: list,
    round_num: int
) -> str:
    """CLAUDE가 검토를 반영하여 REPORT 수정 판단 프롬프트

    Args:
        session_id: 세션 ID
        current_report: 현재 CLAUDE REPORT
        reviews: 다른 AI들의 검토 목록
        round_num: 현재 라운드 번호

    Returns:
        프롬프트 문자열
    """
    reviews_text = "\n\n---\n\n".join([
        f"## Review by {review['ai_name']}\n\n{review['review']}"
        for review in reviews
    ])

    return f"""# Code Review Task - Round {round_num}: Refine Your Report

## Your Role
You are **CLAUDE**, the Lead Reviewer, reviewing feedback on your REPORT.

**Session ID**: `{session_id}`

---

## Your Current Report

{current_report}

---

## Feedback from Other AI Reviewers

{reviews_text}

---

## Your Task

Critically evaluate the feedback and decide whether to refine your REPORT.

### Step 1: Evaluate Each Feedback

For each piece of feedback, decide:

#### ✅ ACCEPT: Valid improvement

- **Feedback**: [What they said]
- **Decision**: ACCEPT
- **Reason**: They caught a real issue / Their fix is better / I missed important context
- **Action**: Update REPORT accordingly

#### 🤔 PARTIALLY ACCEPT: Some merit

- **Feedback**: [What they said]
- **Decision**: PARTIALLY ACCEPT
- **Reason**: Core concern is valid, but their solution has issues
- **Action**: Modify REPORT with better solution

#### ❌ REJECT: Not convincing

- **Feedback**: [What they said]
- **Decision**: REJECT
- **Reason**: They misunderstood the code / Their concern isn't valid / Evidence contradicts
- **Action**: Keep REPORT as is (maybe add clarification)

### Step 2: Make Your Decision

After evaluating all feedback, choose ONE:

#### Option A: NO_CHANGES_NEEDED

If you believe your current REPORT is accurate and complete:

```markdown
# DECISION: NO_CHANGES_NEEDED

## Evaluation Summary
- Accepted: X feedbacks
- Partially accepted: Y feedbacks
- Rejected: Z feedbacks

## Why No Changes Needed

The current REPORT is accurate and comprehensive because:
1. All valid feedback has already been addressed in current version
2. Rejected feedback was based on misunderstandings
3. No critical issues were missed

## Final Report Confirmation

[Confirm that current report is final]
```

**Important**: If you choose this, other AIs will be asked for final agreement.
If they don't agree, we'll proceed to another round.

#### Option B: REPORT_NEEDS_REFINEMENT

If feedback reveals issues that need addressing:

```markdown
# DECISION: REPORT_NEEDS_REFINEMENT

## Evaluation Summary
- Accepted: X feedbacks
- Partially accepted: Y feedbacks
- Rejected: Z feedbacks

## Changes Being Made

### 1. [Change Description]
**Based on**: {ai_name}'s feedback
**What's changing**: ...
**Why**: ...

### 2. [Change Description]
...

## Refined Report

[Write your updated, improved REPORT here]

Include all previous content plus refinements based on accepted feedback.
```

### Reporting Progress (Optional)

```python
review_report_progress("{session_id}", "CLAUDE", "Evaluating feedback...")
```

This is **completely optional**.

---

## How to Submit Your Decision

**You don't need to do anything special!**

Just write your decision (NO_CHANGES_NEEDED or REPORT_NEEDS_REFINEMENT with refined report) as your response. Python will automatically process it.

---

## Important Guidelines

### Critical Thinking Required

- **Don't blindly accept**: Other AIs can be wrong
- **Don't stubbornly reject**: They might see what you missed
- **Evaluate evidence**: Who has stronger reasoning?
- **Consider severity**: Missing a critical issue is worse than false positive

### Quality Standards

Your REPORT should be:
- ✅ **Accurate**: No false positives or missed criticals
- ✅ **Complete**: All important issues covered
- ✅ **Actionable**: Clear fixes provided
- ✅ **Prioritized**: P0 vs P1 vs P2 correctly assigned

### When to Stop Refining

Choose NO_CHANGES_NEEDED when:
- All critical issues are accurately reported
- All major issues are covered
- Fixes are clear and actionable
- No significant gaps remain

It's better to do one more round than to finalize an incomplete report.

---

Begin evaluating the feedback and making your decision now!
"""


def generate_consensus_check_prompt(
    session_id: str,
    ai_name: str,
    claude_final_report: str
) -> str:
    """다른 AI들이 CLAUDE의 최종 REPORT에 동의하는지 확인

    Args:
        session_id: 세션 ID
        ai_name: AI 이름
        claude_final_report: CLAUDE의 최종 REPORT

    Returns:
        프롬프트 문자열
    """
    return f"""# Code Review Task - Final Consensus Check

## Your Role
You are **{ai_name}**, making a final decision on CLAUDE's REPORT.

**Session ID**: `{session_id}`

---

## CLAUDE's Final Report

CLAUDE has indicated that no further changes are needed.

{claude_final_report}

---

## Your Task

Make a simple YES/NO decision: Do you agree with this REPORT as the final output?

### Option A: YES - I Agree

If you believe the REPORT is accurate and ready to be delivered:

```markdown
# DECISION: YES

## I Agree With This Report

This report is comprehensive and accurate because:
- All critical issues are correctly identified
- Priorities are appropriately assigned
- Solutions are actionable and correct
- No significant issues are missing

**Final confirmation**: This report is ready for delivery to the development team.
```

### Option B: NO - I Disagree

If you still have concerns that need addressing:

```markdown
# DECISION: NO

## I Disagree - Issues Remain

I cannot agree with this report because:

### Critical Concerns Still Unaddressed

1. **[Issue Title]**
   - **Problem**: CLAUDE's report still has...
   - **Why it matters**: This could cause...
   - **Must fix**: ...

### Missing Critical Issues

2. **[New Issue]**
   - **Location**: `file.py:X`
   - **Problem**: This wasn't caught...
   - **Severity**: Critical/Major

---

**Bottom line**: Report needs one more round to address these concerns.
```

---

## Important Notes

- ⚖️ **Be fair**: Has CLAUDE addressed your previous feedback?
- 🎯 **Focus on blockers**: Don't reject over minor disagreements
- 📊 **Consider evidence**: Is your concern valid or preference?
- 🤝 **Build consensus**: Agreement is the goal, but not at the cost of quality

### Reporting Progress (Optional)

```python
review_report_progress("{session_id}", "{ai_name}", "Making final decision...")
```

This is **completely optional**.

---

## How to Submit Your Decision

**You don't need to do anything special!**

Just write your decision (YES or NO with reasons) as your response. Python will automatically process it.

---

## Decision Criteria

### Say YES if:
- All P0 issues are correctly identified
- All P1 issues are covered
- Fixes are clear and correct
- Your previous feedback was addressed

### Say NO only if:
- Critical issue missed (security, data loss, crash)
- Major issue misclassified as minor
- Proposed fix is incorrect/dangerous
- Your valid feedback was ignored without reason

---

Make your decision now: YES or NO?
"""

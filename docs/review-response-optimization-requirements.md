# Code Review Response Optimization Requirements

## 📋 문제 정의

### 현재 문제
- **`review_run_code_review`** 및 **`review_audit_code_review`** MCP 도구의 응답 크기가 **34,780 토큰**으로 MCP 제한(25,000 토큰) 초과
- 응답에는 3개 AI × 3 라운드 × 각 리뷰 내용 = **전체 협업 대화 트랜스크립트** 포함
- Claude Code가 응답을 받을 수 없어 후속 작업 불가능

### 영향받는 MCP 도구
1. **`review_run_code_review`**: Claude Code가 초기 리뷰 작성 → 다른 AI들이 검토 → 반복 개선
2. **`review_audit_code_review`**: 사용자가 작성한 리뷰 → 다른 AI들이 검토 → 반복 개선

**두 도구 모두 동일한 문제 발생 → 동일한 해결책 적용**

### 목표
1. MCP 응답 크기를 25,000 토큰 이하로 제한
2. Claude가 최종 리뷰 결과를 컨텍스트로 활용 가능
3. 전체 상세 내용은 파일로 보존
4. 사용자가 필요시 상세 내용 접근 가능
5. **두 도구가 동일한 응답 구조 사용** (코드 재사용)

---

## 🎯 해결 방안: 하이브리드 응답 구조

### 핵심 설계 원칙
1. **인라인 요약**: Claude가 즉시 분석할 수 있는 최종 리뷰 (< 5,000 토큰)
2. **파일 저장**: 전체 트랜스크립트 및 라운드별 상세 내용
3. **메타데이터**: 통계 및 파일 경로 정보

---

## 📐 API 스펙

### 1. `review_run_code_review` 수정

#### 기존 시그니처
```python
async def review_run_code_review(
    base: str,
    target: str,
    max_rounds: int = 3,
    ais: str = "gpt4,gemini"
) -> str  # 전체 텍스트 (문제 발생)
```

#### 새로운 시그니처
```python
async def review_run_code_review(
    base: str,
    target: str,
    max_rounds: int = 3,
    ais: str = "gpt4,gemini",
    verbosity: str = "summary"  # "summary" | "detailed" | "full"
) -> ReviewResponse
```

### 2. `review_audit_code_review` 수정

#### 기존 시그니처
```python
async def review_audit_code_review(
    base: str,
    target: str,
    initial_review: str,  # 사용자가 작성한 초기 리뷰
    max_rounds: int = 3,
    ais: str = "gpt4,gemini"
) -> str  # 전체 텍스트 (문제 발생)
```

#### 새로운 시그니처
```python
async def review_audit_code_review(
    base: str,
    target: str,
    initial_review: str,  # 사용자가 작성한 초기 리뷰
    max_rounds: int = 3,
    ais: str = "gpt4,gemini",
    verbosity: str = "summary"  # "summary" | "detailed" | "full"
) -> ReviewResponse  # run_code_review와 동일한 구조
```

**중요**: 두 도구 모두 동일한 `ReviewResponse` 타입을 반환합니다.

### 3. ReviewResponse 구조 (공통)

#### ReviewResponse
```python
class ReviewResponse(TypedDict):
    session_id: str
    status: str  # "COMPLETED" | "IN_PROGRESS" | "FAILED"
    consensus: ConsensusResult
    summary: ReviewSummary
    final_review_text: str  # 최종 합의 리뷰 (< 5000 토큰)
    artifacts: ArtifactPaths
```

#### ConsensusResult
```python
class ConsensusResult(TypedDict):
    result: str  # "APPROVED" | "APPROVE_WITH_CHANGES" | "REJECTED" | "NO_CONSENSUS"
    confidence: float  # 0.0 ~ 1.0
    participating_ais: list[str]  # ["claude-sonnet-4", "gpt-4", "gemini-pro"]
    rounds_completed: int
```

#### ReviewSummary
```python
class ReviewSummary(TypedDict):
    critical_issues: int
    high_priority: int
    medium_priority: int
    low_priority: int
    suggestions: int
    key_findings: list[str]  # 최대 10개
    files_reviewed: int
    total_changes: int
```

#### ArtifactPaths
```python
class ArtifactPaths(TypedDict):
    summary_file: str  # "/docs/reviews/{target}-{timestamp}/summary.md"
    full_transcript: str  # "/docs/reviews/{target}-{timestamp}/full-transcript.md"
    rounds_dir: str  # "/docs/reviews/{target}-{timestamp}/rounds/"
    consensus_log: str  # "/docs/reviews/{target}-{timestamp}/consensus.json"
```

---

## 📂 파일 구조

### run_code_review (Claude가 초기 리뷰 작성)
```
/docs/reviews/{target-branch}-{timestamp}/
├── summary.md                    # 최종 합의 리뷰 (Claude 읽기 가능)
├── full-transcript.md            # 전체 대화 트랜스크립트
├── consensus.json                # 합의 메타데이터
├── statistics.json               # 통계 정보
├── review-type.txt               # "run_code_review"
└── rounds/
    ├── round-1-claude-initial.md
    ├── round-1-gpt4-feedback.md
    ├── round-1-gemini-feedback.md
    ├── round-2-claude-revised.md
    ├── round-2-gpt4-feedback.md
    ├── round-2-gemini-feedback.md
    ├── round-3-claude-final.md
    ├── round-3-gpt4-final.md
    └── round-3-gemini-final.md
```

### audit_code_review (사용자가 초기 리뷰 작성)
```
/docs/reviews/{target-branch}-{timestamp}/
├── summary.md                    # 최종 합의 리뷰 (Claude 읽기 가능)
├── full-transcript.md            # 전체 대화 트랜스크립트
├── consensus.json                # 합의 메타데이터
├── statistics.json               # 통계 정보
├── review-type.txt               # "audit_code_review"
├── initial-review.md             # 사용자가 작성한 초기 리뷰
└── rounds/
    ├── round-1-gpt4-feedback.md
    ├── round-1-gemini-feedback.md
    ├── round-2-user-revised.md    # 사용자가 개선한 리뷰
    ├── round-2-gpt4-feedback.md
    ├── round-2-gemini-feedback.md
    ├── round-3-user-final.md
    ├── round-3-gpt4-final.md
    └── round-3-gemini-final.md
```

**차이점**:
- `run_code_review`: Claude가 라운드마다 리뷰 작성
- `audit_code_review`: 사용자 리뷰를 AI들이 검토만 수행
- 두 경우 모두 **동일한 파일 구조 및 응답 형식** 사용

---

## 📝 파일 포맷

### summary.md (run_code_review)
```markdown
# Code Review Summary: {target-branch}

**Branch**: `{base}...{target}`
**Date**: {timestamp}
**Review Type**: Initial review by Claude Code
**Consensus**: {result}
**Confidence**: {confidence}%
**Reviewed by**: Claude Sonnet 4 (primary), GPT-4, Gemini Pro

## Critical Issues (3)

### 🔴 SQL Injection Vulnerability in Authentication
**File**: `src/auth.py:45`
**Severity**: CRITICAL
**Description**: User input directly concatenated into SQL query...
**Recommendation**: Use parameterized queries...

## High Priority (12)

### 🟠 Type Safety Issues
**Files**: `src/models/*.py`
**Description**: Missing type annotations...

## Key Findings

1. **Security**: SQL injection vulnerability requires immediate attention
2. **Type Safety**: 23 type errors across 8 files
3. **Testing**: Coverage dropped from 87% to 62%
4. **Performance**: N+1 query issue in user listing endpoint

## Recommendations

1. [ ] Fix SQL injection in `src/auth.py:45`
2. [ ] Add type annotations to models
3. [ ] Restore test coverage to >80%
4. [ ] Optimize database queries

---

*Full transcript available at: `{full-transcript-path}`*
```

### summary.md (audit_code_review)
```markdown
# Code Review Audit Summary: {target-branch}

**Branch**: `{base}...{target}`
**Date**: {timestamp}
**Review Type**: User review audit
**Initial Review**: Provided by user
**Consensus**: {result}
**Confidence**: {confidence}%
**Audited by**: GPT-4, Gemini Pro

## Initial Review Assessment

**Original Quality Score**: 7.5/10
**Improved to**: 9.2/10
**Key Improvements Made**:
- Added security considerations
- Enhanced type safety recommendations
- Included performance metrics

## Critical Issues (3)

### 🔴 SQL Injection Vulnerability in Authentication
**File**: `src/auth.py:45`
**Severity**: CRITICAL
**Original Review**: ❌ Not mentioned
**Auditors Found**: ✅ Identified by GPT-4 and Gemini
**Description**: User input directly concatenated into SQL query...
**Recommendation**: Use parameterized queries...

## Audit Findings

### Issues Added by Auditors
1. **Security gaps**: 3 critical issues not in original review
2. **Type safety**: Additional 5 type errors identified
3. **Performance**: N+1 query issue missed

### Original Review Strengths
1. Good coverage of code style issues
2. Clear explanation of refactoring needs
3. Well-structured recommendations

---

*Original review available at: `{initial-review-path}`*
*Full audit transcript at: `{full-transcript-path}`*
```

### consensus.json
```json
{
  "session_id": "review-abc123",
  "timestamp": "2025-01-01T14:30:00Z",
  "review_type": "run_code_review",
  "branches": {
    "base": "develop",
    "target": "refactor/remove-unused-phase2"
  },
  "consensus": {
    "result": "APPROVE_WITH_CHANGES",
    "confidence": 0.95,
    "rounds": 3
  },
  "ais": [
    {
      "name": "claude-sonnet-4",
      "role": "primary_reviewer",
      "rounds_participated": 3
    },
    {
      "name": "gpt-4",
      "role": "validator",
      "rounds_participated": 3
    },
    {
      "name": "gemini-pro",
      "role": "validator",
      "rounds_participated": 3
    }
  ],
  "issues": {
    "critical": 3,
    "high": 12,
    "medium": 25,
    "low": 7,
    "suggestions": 8
  },
  "files_changed": 23,
  "total_changes": 456
}
```

---

## 🔧 구현 요구사항

### Phase 1: Core Response Structure (우선순위: 높음)

#### 1.1 ReviewResponse 클래스 구현
**파일**: `src/mcp/types.py`
```python
from typing import TypedDict, Literal

class ConsensusResult(TypedDict):
    result: Literal["APPROVED", "APPROVE_WITH_CHANGES", "REJECTED", "NO_CONSENSUS"]
    confidence: float
    participating_ais: list[str]
    rounds_completed: int

class ReviewSummary(TypedDict):
    critical_issues: int
    high_priority: int
    medium_priority: int
    low_priority: int
    suggestions: int
    key_findings: list[str]
    files_reviewed: int
    total_changes: int

class ArtifactPaths(TypedDict):
    summary_file: str
    full_transcript: str
    rounds_dir: str
    consensus_log: str

class ReviewResponse(TypedDict):
    session_id: str
    status: Literal["COMPLETED", "IN_PROGRESS", "FAILED"]
    consensus: ConsensusResult
    summary: ReviewSummary
    final_review_text: str
    artifacts: ArtifactPaths
```

#### 1.2 응답 생성 로직 (공통)
**파일**: `src/mcp/handlers/review_handler.py`
```python
async def create_review_response(
    session: ReviewSession,
    verbosity: str = "summary"
) -> ReviewResponse:
    """
    전체 리뷰 세션 결과를 하이브리드 응답으로 변환

    ✅ run_code_review와 audit_code_review 모두 사용

    Args:
        session: 완료된 리뷰 세션
        verbosity: "summary" | "detailed" | "full"

    Returns:
        ReviewResponse with inline summary + file artifacts
    """
    # 1. 파일 저장
    artifact_paths = await save_review_artifacts(session)

    # 2. 요약 추출
    summary = extract_summary(session)
    consensus = extract_consensus(session)
    final_review = extract_final_review(session, max_tokens=5000)

    # 3. 응답 구성
    return ReviewResponse(
        session_id=session.id,
        status="COMPLETED",
        consensus=consensus,
        summary=summary,
        final_review_text=final_review,
        artifacts=artifact_paths
    )
```

#### 1.3 MCP 핸들러 통합
**파일**: `src/mcp/server.py`
```python
@server.call_tool()
async def review_run_code_review(
    base: str,
    target: str,
    max_rounds: int = 3,
    ais: str = "gpt4,gemini",
    verbosity: str = "summary"
) -> ReviewResponse:
    """Claude Code가 초기 리뷰 작성 → 다른 AI 검토"""
    session = await execute_full_review(
        base=base,
        target=target,
        initial_reviewer="claude",  # Claude가 작성
        max_rounds=max_rounds,
        validators=ais.split(",")
    )
    return await create_review_response(session, verbosity)

@server.call_tool()
async def review_audit_code_review(
    base: str,
    target: str,
    initial_review: str,
    max_rounds: int = 3,
    ais: str = "gpt4,gemini",
    verbosity: str = "summary"
) -> ReviewResponse:
    """사용자가 작성한 리뷰 → 다른 AI 검토"""
    session = await execute_audit_review(
        base=base,
        target=target,
        initial_review=initial_review,  # 사용자가 작성
        max_rounds=max_rounds,
        validators=ais.split(",")
    )
    return await create_review_response(session, verbosity)  # 동일한 함수 사용
```

### Phase 2: File Artifact Generation (우선순위: 높음)

#### 2.1 Artifact 저장 함수 (공통)
**파일**: `src/mcp/utils/artifact_writer.py`
```python
async def save_review_artifacts(
    session: ReviewSession
) -> ArtifactPaths:
    """
    리뷰 세션 결과를 파일로 저장

    ✅ run_code_review와 audit_code_review 모두 사용

    Directory structure:
    /docs/reviews/{target}-{timestamp}/
        ├── summary.md
        ├── full-transcript.md
        ├── consensus.json
        ├── statistics.json
        ├── review-type.txt           # "run" or "audit"
        ├── initial-review.md          # audit만 해당
        └── rounds/
            ├── round-1-claude-initial.md
            ├── round-1-gpt4-feedback.md
            └── ...
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_dir = f"/docs/reviews/{session.target_branch}-{timestamp}"

    # 1. 디렉토리 생성
    os.makedirs(f"{base_dir}/rounds", exist_ok=True)

    # 2. Review type 기록
    await write_review_type(session, base_dir)

    # 3. Initial review 저장 (audit_code_review만 해당)
    if session.review_type == "audit" and session.initial_review:
        await write_initial_review(session, base_dir)

    # 4. Summary 작성
    summary_path = await write_summary_md(session, base_dir)

    # 5. Full transcript 작성
    transcript_path = await write_full_transcript(session, base_dir)

    # 6. Rounds 작성
    rounds_dir = await write_round_files(session, base_dir)

    # 7. Consensus JSON 작성
    consensus_path = await write_consensus_json(session, base_dir)

    return ArtifactPaths(
        summary_file=summary_path,
        full_transcript=transcript_path,
        rounds_dir=rounds_dir,
        consensus_log=consensus_path
    )
```

#### 2.2 Summary 생성 (공통)
**파일**: `src/mcp/utils/summary_generator.py`
```python
async def write_summary_md(
    session: ReviewSession,
    base_dir: str
) -> str:
    """
    최종 합의 리뷰를 summary.md로 작성

    ✅ run_code_review와 audit_code_review 모두 사용

    목표: < 5000 토큰, Claude가 읽기 좋은 형식
    """
    # 1. 이슈 분류 및 정렬
    issues = classify_issues(session.final_review)

    # 2. Markdown 생성 (review type에 따라 템플릿 선택)
    if session.review_type == "run":
        md_content = generate_run_summary_markdown(
            session=session,
            issues=issues,
            max_length=5000
        )
    else:  # audit
        md_content = generate_audit_summary_markdown(
            session=session,
            issues=issues,
            original_review=session.initial_review,
            max_length=5000
        )

    # 3. 파일 작성
    path = f"{base_dir}/summary.md"
    async with aiofiles.open(path, "w") as f:
        await f.write(md_content)

    return path
```

### Phase 3: Verbosity Modes (우선순위: 중간)

#### 3.1 Verbosity 처리
```python
if verbosity == "summary":
    # 최소 응답: 요약 + 파일 경로만
    final_review_text = extract_final_review(session, max_tokens=5000)

elif verbosity == "detailed":
    # 중간 응답: 요약 + 라운드별 요약
    final_review_text = extract_detailed_review(session, max_tokens=15000)

elif verbosity == "full":
    # 전체 응답: 모든 내용 (토큰 제한 초과 가능성 경고)
    final_review_text = session.full_transcript
```

### Phase 4: Token Counting & Validation (우선순위: 높음)

#### 4.1 토큰 카운터
**파일**: `src/mcp/utils/token_counter.py`
```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """텍스트의 토큰 수 계산"""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def truncate_to_tokens(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    """텍스트를 지정 토큰 수로 자르기"""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return text

    # 토큰 잘라내기
    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens) + "\n\n...(truncated)"
```

#### 4.2 응답 검증
```python
def validate_response_size(response: ReviewResponse) -> None:
    """
    응답 크기가 MCP 제한을 초과하지 않는지 검증

    Raises:
        ValueError: 25,000 토큰 초과시
    """
    # JSON 직렬화 후 토큰 카운트
    response_json = json.dumps(response)
    token_count = count_tokens(response_json)

    if token_count > 25000:
        raise ValueError(
            f"Response size ({token_count} tokens) exceeds MCP limit (25000). "
            f"Consider using verbosity='summary' or reducing content."
        )
```

---

## 🧪 테스트 시나리오

### Test 1: Summary Response (run_code_review)
```python
async def test_run_code_review_summary_response():
    """run_code_review summary 모드가 5000 토큰 이하인지 확인"""
    response = await review_run_code_review(
        base="develop",
        target="feature/large-change",
        max_rounds=3,
        verbosity="summary"
    )

    token_count = count_tokens(response["final_review_text"])
    assert token_count <= 5000
    assert response["artifacts"]["summary_file"].endswith(".md")
    assert os.path.exists(response["artifacts"]["summary_file"])
```

### Test 1-2: Summary Response (audit_code_review)
```python
async def test_audit_code_review_summary_response():
    """audit_code_review summary 모드가 5000 토큰 이하인지 확인"""
    initial_review = """
    # My Review
    - Good code structure
    - Need more tests
    """

    response = await review_audit_code_review(
        base="develop",
        target="feature/auth",
        initial_review=initial_review,
        max_rounds=3,
        verbosity="summary"
    )

    token_count = count_tokens(response["final_review_text"])
    assert token_count <= 5000
    assert response["artifacts"]["summary_file"].endswith(".md")
    assert os.path.exists(response["artifacts"]["summary_file"])

    # audit만 해당: initial_review.md 파일 확인
    initial_review_path = os.path.join(
        os.path.dirname(response["artifacts"]["summary_file"]),
        "initial-review.md"
    )
    assert os.path.exists(initial_review_path)
```

### Test 2: File Artifacts
```python
async def test_artifact_generation():
    """모든 아티팩트가 올바르게 생성되는지 확인"""
    response = await review_run_code_review(
        base="develop",
        target="refactor/cleanup",
        max_rounds=2
    )

    artifacts = response["artifacts"]

    # 파일 존재 확인
    assert os.path.exists(artifacts["summary_file"])
    assert os.path.exists(artifacts["full_transcript"])
    assert os.path.exists(artifacts["consensus_log"])
    assert os.path.isdir(artifacts["rounds_dir"])

    # 라운드 파일 확인
    round_files = os.listdir(artifacts["rounds_dir"])
    assert len(round_files) >= 6  # 2 rounds × 3 AIs
```

### Test 3: Token Limit Compliance
```python
async def test_mcp_token_limit():
    """전체 응답이 MCP 제한을 초과하지 않는지 확인"""
    response = await review_run_code_review(
        base="develop",
        target="feature/very-large",
        max_rounds=3,
        verbosity="summary"
    )

    response_json = json.dumps(response)
    token_count = count_tokens(response_json)

    assert token_count <= 25000, f"Response {token_count} tokens exceeds limit"
```

### Test 4: Claude Context Usability (run_code_review)
```python
async def test_claude_can_use_context_run():
    """Claude가 run_code_review 응답을 컨텍스트로 활용 가능한지 확인"""
    response = await review_run_code_review(
        base="develop",
        target="feature/auth",
        max_rounds=2
    )

    # 최종 리뷰 텍스트가 구조화되어 있는지
    assert "Critical Issues" in response["final_review_text"]
    assert "Recommendations" in response["final_review_text"]

    # 핵심 정보가 포함되어 있는지
    assert response["summary"]["critical_issues"] >= 0
    assert len(response["summary"]["key_findings"]) > 0
```

### Test 4-2: Claude Context Usability (audit_code_review)
```python
async def test_claude_can_use_context_audit():
    """Claude가 audit_code_review 응답을 컨텍스트로 활용 가능한지 확인"""
    initial_review = "Basic review without security analysis"

    response = await review_audit_code_review(
        base="develop",
        target="feature/payment",
        initial_review=initial_review,
        max_rounds=2
    )

    # audit 특화 내용 확인
    assert "Audit Findings" in response["final_review_text"] or \
           "Initial Review Assessment" in response["final_review_text"]
    assert "Issues Added by Auditors" in response["final_review_text"] or \
           response["summary"]["critical_issues"] >= 0

    # 핵심 정보가 포함되어 있는지
    assert len(response["summary"]["key_findings"]) > 0
```

### Test 5: Response Structure Consistency
```python
async def test_response_structure_consistency():
    """두 도구가 동일한 응답 구조를 사용하는지 확인"""

    # run_code_review 응답
    run_response = await review_run_code_review(
        base="develop",
        target="feature/test",
        max_rounds=2
    )

    # audit_code_review 응답
    audit_response = await review_audit_code_review(
        base="develop",
        target="feature/test",
        initial_review="Test review",
        max_rounds=2
    )

    # 두 응답의 구조가 동일한지 확인
    assert set(run_response.keys()) == set(audit_response.keys())
    assert set(run_response["consensus"].keys()) == set(audit_response["consensus"].keys())
    assert set(run_response["summary"].keys()) == set(audit_response["summary"].keys())
    assert set(run_response["artifacts"].keys()) == set(audit_response["artifacts"].keys())
```

---

## 📊 성공 기준

### 필수 (Must Have)
- [ ] `review_run_code_review` 응답이 25,000 토큰 이하
- [ ] `review_audit_code_review` 응답이 25,000 토큰 이하
- [ ] **두 도구가 동일한 `ReviewResponse` 구조 사용**
- [ ] Claude가 최종 리뷰를 컨텍스트로 활용 가능 (두 도구 모두)
- [ ] 전체 트랜스크립트가 파일로 보존 (두 도구 모두)
- [ ] 모든 테스트 통과 (두 도구 모두)

### 권장 (Should Have)
- [ ] `summary.md`가 5,000 토큰 이하
- [ ] 파일 구조가 직관적
- [ ] 메타데이터(JSON)가 정확
- [ ] 토큰 카운팅 정확도 95% 이상

### 선택 (Nice to Have)
- [ ] `verbosity` 파라미터로 응답 크기 조절
- [ ] 라운드별 diff 하이라이팅
- [ ] HTML 리포트 생성
- [ ] 리뷰 히스토리 관리

---

## 🚀 구현 순서

1. **Phase 1**: Response structure (1-2시간)
   - ReviewResponse 타입 정의
   - 기본 응답 생성 로직 (두 도구 공통)
   - ReviewSession에 `review_type` 필드 추가

2. **Phase 2**: File artifacts (2-3시간)
   - 디렉토리 생성
   - summary.md 작성 (run/audit 템플릿 분리)
   - full-transcript.md 작성
   - rounds/ 파일 작성
   - initial-review.md 작성 (audit만 해당)
   - review-type.txt 작성

3. **Phase 3**: Token management (1시간)
   - tiktoken 통합
   - 토큰 카운팅
   - Truncation 로직

4. **Phase 4**: MCP Handler Integration (1시간)
   - `review_run_code_review` 수정
   - `review_audit_code_review` 수정
   - 두 핸들러가 `create_review_response()` 공유 확인

5. **Phase 5**: Testing (2-3시간)
   - 단위 테스트 (공통 로직)
   - run_code_review 통합 테스트
   - audit_code_review 통합 테스트
   - 응답 구조 일관성 테스트
   - 실제 리뷰 시나리오 테스트

**예상 총 소요 시간**: 7-10시간

---

## 📚 참고 자료

- [MCP 프로토콜 스펙](https://modelcontextprotocol.io/docs)
- [tiktoken 문서](https://github.com/openai/tiktoken)
- [AsyncIO 파일 I/O](https://github.com/Tinche/aiofiles)

---

**작성일**: 2025-01-01
**버전**: 2.0
**작성자**: Development Team

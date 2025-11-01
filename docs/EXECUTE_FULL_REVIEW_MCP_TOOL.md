# execute_full_review MCP Tool

## 개요

`execute_full_review`는 Claude Code MCP 환경에서 **전체 Multi-AI 코드 리뷰**를 **단일 도구 호출**로 실행할 수 있게 해주는 새로운 MCP 도구입니다.

이전에는 `python review.py`로만 가능했던 Multi-AI 협업 리뷰를 이제 MCP에서 직접 실행할 수 있습니다.

## 핵심 기능

### 🚀 원클릭 Multi-AI 리뷰

하나의 MCP 도구 호출로:
1. ✅ 사용 가능한 AI CLI 자동 감지 (CLAUDE, GPT-4, Gemini)
2. ✅ CLAUDE-Led Iterative Review 전체 프로세스 실행
3. ✅ 최종 합의된 REPORT 반환

### 🤖 CLAUDE-Led Iterative Review

```
Round 1: CLAUDE 초기 REPORT 작성
  ↓
Round 2~N (반복):
  1. 다른 AI들이 CLAUDE REPORT 검토 (병렬)
  2. CLAUDE가 검토 반영하여 REPORT 수정
  3. 합의 확인
  ↓
최종 REPORT (모든 AI 동의)
```

## 사용법

### Claude Code MCP에서 사용

```python
# 기본 사용 (자동으로 모든 AI 감지)
result = execute_full_review(
    base="develop",
    target="HEAD"
)

# 최대 라운드 지정
result = execute_full_review(
    base="main",
    target="feature/new-feature",
    max_rounds=5
)

# 특정 AI만 사용
result = execute_full_review(
    base="develop",
    target="HEAD",
    ais="claude,gpt4"
)
```

### MCP Server API (JSON-RPC)

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "review_execute_full_review",
    "arguments": {
      "base": "develop",
      "target": "HEAD",
      "max_rounds": 5
    }
  },
  "id": 1
}
```

## 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `base` | str | (필수) | 기준 브랜치 (예: "develop", "main") |
| `target` | str | "HEAD" | 비교 대상 브랜치 |
| `max_rounds` | int | 5 | 최대 반복 라운드 수 |
| `ais` | str | None | 사용할 AI 지정 (쉼표 구분, None=자동 감지) |

## 반환값

### 성공 시

```python
{
    "status": "success",
    "session_id": "review_20251031_153045",
    "final_review": "# Code Review Report\n...",
    "participating_ais": ["claude", "gpt4", "gemini"],
    "rounds_completed": 3,
    "final_review_file": "reviews/review_20251031_153045_final.md"
}
```

### 실패 시

```python
{
    "status": "error",
    "error": "CLAUDE is required for MCP environment. CLAUDE CLI not found.",
    "available_ais": ["gpt4"]
}
```

## 내부 동작

### 1. AI CLI 자동 감지

```python
# ai_cli_tools 모듈 사용
ai_client = AIClient()
available_ais = ai_client.detect_available_ais()
# → {"claude": AIModel(...), "gpt4": AIModel(...), ...}
```

### 2. CLAUDE 필수 검증

```python
if "claude" not in available_ais:
    return {"status": "error", "error": "CLAUDE is required..."}
```

CLAUDE는 MCP 환경의 Lead Reviewer이므로 필수입니다.

### 3. MCPOrchestratedReviewer 실행

```python
reviewer = MCPOrchestratedReviewer(ai_client, verbose=True)
result = reviewer.execute(
    available_ais=available_ais,
    base_branch=base,
    target_branch=target,
    max_rounds=max_rounds
)
```

### 4. 결과 보강 및 반환

```python
result["participating_ais"] = list(available_ais.keys())
result["rounds_completed"] = result.get("rounds_completed", 1)
return result
```

## 아키텍처

### 기존 방식 (CLI)

```bash
python review.py --base develop --target HEAD
```

- ✅ Multi-AI 리뷰 가능
- ❌ MCP 외부에서만 실행
- ❌ Claude Code에서 직접 호출 불가

### 신규 방식 (MCP)

```python
# Claude Code MCP 내부에서
use ai-code-review mcp
execute_full_review(base="develop")
```

- ✅ Multi-AI 리뷰 가능
- ✅ MCP 내부에서 실행
- ✅ Claude Code에서 직접 호출 가능
- ✅ 단일 도구 호출로 전체 프로세스

## 예시 실행

### Claude Code에서 사용

```
> use ai-code-review mcp

[MCP Server Connected: ai-code-review]

> execute_full_review(base="develop", target="HEAD", max_rounds=5)

======================================================================
CLAUDE-Led Iterative Code Review
======================================================================

👑 Lead Reviewer: CLAUDE (claude-sonnet-4.5)
🔍 Reviewers: 2개 AI
   • GPT4: gpt-4-turbo
   • GEMINI: gemini-1.5-pro
🔄 Max Rounds: 5

✅ 세션 생성: review_20251031_153045

📊 Python이 변경사항을 큐레이션하는 중...
   ✅ 15개 파일 선택 완료
   → 총 변경사항: 42개 파일

======================================================================
Round 1: Initial Report by CLAUDE
======================================================================

[CLAUDE] 📝 코드 변경사항 분석 중...
[CLAUDE] ✅ 초기 REPORT 작성 완료 (3,245자)
   → Critical: 2개
   → Major: 4개
   → Minor: 7개

======================================================================
Round 2: Review and Refine
======================================================================

🔍 2개 AI가 CLAUDE REPORT를 검토합니다:
   • GPT4
   • GEMINI

[GPT4] 🔍 검토 시작...
[GEMINI] 🔍 검토 시작...

[GPT4] ✅ 검토 완료
[GEMINI] ✅ 검토 완료

[CLAUDE] 🤔 검토 내용 반영 판단 중...
[CLAUDE] ✏️ REPORT 수정 완료 → Round 3로 진행

======================================================================
Round 3: Review and Refine
======================================================================

🔍 2개 AI가 CLAUDE REPORT를 검토합니다:
   • GPT4
   • GEMINI

[GPT4] ✅ 검토 완료
[GEMINI] ✅ 검토 완료

[CLAUDE] 🤔 검토 내용 반영 판단 중...
[CLAUDE] ✓ 더 이상 수정할 내용 없음

🤝 최종 합의 확인 중...

[GPT4] ✅ 최종 REPORT에 동의
[GEMINI] ✅ 최종 REPORT에 동의

✅ 합의 완료! 모든 AI가 최종 REPORT에 동의했습니다.

======================================================================
✅ 리뷰 완료!
======================================================================

📄 최종 리포트: reviews/review_20251031_153045_final.md

Result:
{
  "status": "success",
  "session_id": "review_20251031_153045",
  "participating_ais": ["claude", "gpt4", "gemini"],
  "rounds_completed": 3,
  "final_review_file": "reviews/review_20251031_153045_final.md"
}
```

## 에러 처리

### CLAUDE 없음

```python
{
  "status": "error",
  "error": "CLAUDE is required for MCP environment. CLAUDE CLI not found.",
  "available_ais": ["gpt4", "gemini"]
}
```

**해결**: Claude CLI 설치 필요

### Git 저장소 없음

```python
{
  "status": "error",
  "error": "Not a git repository",
  "available_ais": ["claude", "gpt4"]
}
```

**해결**: Git 저장소에서 실행 필요

### AI CLI 없음

```python
{
  "status": "error",
  "error": "No AI CLIs detected. Install at least Claude CLI.",
  "available_ais": []
}
```

**해결**: AI CLI 설치 필요 (Claude 필수)

## 기존 도구와의 관계

### execute_full_review (신규)

- **목적**: 전체 Multi-AI 리뷰 자동 실행
- **사용 시점**: Claude Code MCP에서 리뷰를 바로 시작하고 싶을 때
- **특징**:
  - 단일 호출로 전체 프로세스 실행
  - AI CLI 자동 감지
  - CLAUDE-Led 전체 워크플로우
  - 최종 REPORT까지 자동 생성

### create_review_session (기존)

- **목적**: 수동 리뷰 세션 생성
- **사용 시점**: 단계별로 직접 제어하고 싶을 때
- **특징**:
  - 세션만 생성 (다른 도구들과 조합 필요)
  - 수동으로 submit_review, advance_round 등 호출
  - 세밀한 제어 가능

### 선택 가이드

| 상황 | 권장 도구 | 이유 |
|-----|---------|------|
| 빠르게 Multi-AI 리뷰 받고 싶음 | `execute_full_review` | 자동화된 전체 프로세스 |
| 각 단계를 직접 제어하고 싶음 | `create_review_session` + 기타 도구들 | 세밀한 제어 |
| CLAUDE 단독 리뷰만 원함 | `execute_full_review` | 다른 AI 없어도 동작 |
| 특정 AI만 사용하고 싶음 | `execute_full_review(ais="claude,gpt4")` | AI 선택 가능 |

## 구현 세부사항

### 파일 위치

- **Method**: `src/mcp/review_orchestrator.py:335-428`
- **Tool Registration**: `src/mcp/review_orchestrator.py:430-438`
- **Tests**: `tests/test_execute_full_review.py`
- **Documentation**: `docs/EXECUTE_FULL_REVIEW_MCP_TOOL.md`

### 의존성

```python
from ai_cli_tools import AIClient  # AI CLI 자동 감지
from src.phase1_reviewer_mcp_orchestrated import MCPOrchestratedReviewer  # 리뷰 실행
```

### 테스트

```bash
# 단위 테스트
pytest tests/test_execute_full_review.py -v

# 통합 테스트 (Git repo 필요)
pytest tests/test_execute_full_review.py::TestExecuteFullReview::test_integration_with_git_repo -v
```

## 성능

- **토큰 사용량**: 기존 CLI와 동일 (98.4% 감소 후)
- **실행 시간**: 기존 CLI와 동일 (병렬 검토로 최적화)
- **AI 감지**: < 1초 (캐싱)
- **REPORT 생성**: AI 응답 시간에 의존

## 향후 개선

1. **스트리밍 진행 상황**: 실시간 진행 상황을 MCP를 통해 스트리밍
2. **캐싱**: 반복 실행 시 AI 감지 결과 캐싱
3. **비동기 실행**: asyncio로 병렬 처리 최적화
4. **중단/재개**: 장시간 리뷰 중단 후 재개 기능

## FAQ

### Q: CLAUDE 없이 실행 가능한가요?

**A**: 아니요. CLAUDE는 MCP 환경의 Lead Reviewer이므로 필수입니다.

### Q: 다른 AI가 없어도 실행되나요?

**A**: 네. CLAUDE만 있어도 실행되며, 이 경우 CLAUDE 단독 리뷰가 진행됩니다.

### Q: 기존 `python review.py`와 차이는?

**A**: 기능은 동일하지만, MCP 내부에서 실행 가능하다는 점이 다릅니다. Claude Code에서 직접 호출할 수 있습니다.

### Q: 실행 결과를 파일로 받을 수 있나요?

**A**: 네. 결과에 `final_review_file` 경로가 포함되어 있으며, `reviews/` 디렉토리에 저장됩니다.

### Q: 다른 MCP 도구들과 함께 사용 가능한가요?

**A**: 네. 필요하다면 `execute_full_review` 후에 `get_session_info` 등으로 세부 정보를 조회할 수 있습니다.

## 관련 문서

- [CLAUDE-Led Architecture](./CLAUDE_LED_ARCHITECTURE.md)
- [MCP Setup](./MCP_SETUP.md)
- [CLI Usage](./CLI_USAGE.md)
- [Quick Reference](./QUICK_REFERENCE.md)

---

**작성일**: 2025-11-01
**버전**: 1.0.0
**상태**: 완료 ✅

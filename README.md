# AI Code Review System - CLAUDE-Led Iterative Review

**MCP 기반 Multi-AI 코드 리뷰 시스템 (CLAUDE-Led Iterative Review)**

## 🎯 핵심 개념

이 시스템은 **CLAUDE-Led Iterative Review** 아키텍처를 사용합니다:

- **CLAUDE**: 주도적 작성자 및 통합자 (Lead Reviewer)
  - 초기 REPORT 작성
  - 검토 의견 반영 판단
  - REPORT 지속적 개선

- **다른 AI들**: 검토자 (Reviewers)
  - CLAUDE REPORT 비판적 검토
  - 놓친 이슈 발견
  - 개선 의견 제시

- **Python**: 객관적 작업 처리
  - Git 변경사항 조회
  - 파일 선택 및 큐레이션
  - 토큰 예산 관리

- **Consensus**: 자연스러운 수렴
  - CLAUDE: "더 이상 수정 없음"
  - 다른 AI들: "REPORT에 동의"
  - 모두 동의하면 합의 완료

## ✨ 주요 특징

### 1. CLAUDE 중심 리뷰
- **CLAUDE MCP 환경에 최적화**: CLAUDE가 Lead Reviewer로 활약
- **일관성 있는 REPORT**: 단일 통합 리포트 (CLAUDE 작성)
- **CLAUDE는 필수**: MCP 환경이므로 CLAUDE는 반드시 사용

### 2. Iterative Refinement Process
- **Round 1**: CLAUDE가 초기 REPORT 작성
- **Round 2~N** (반복):
  1. 다른 AI들이 CLAUDE REPORT 검토 (병렬)
  2. CLAUDE가 검토 읽고 판단:
     - 수정 필요 → REPORT 수정 후 다음 Round
     - 수정 불필요 → Consensus 체크
  3. Consensus 체크:
     - 모두 동의 → 완료 ✅
     - 일부 반대 → 다음 Round
- **최종 결과**: CLAUDE의 refined REPORT

### 3. 자동 AI 리뷰어 구성
- 시스템에 설치된 AI CLI 자동 감지 (Claude, GPT-4, Gemini)
- CLAUDE는 Lead Reviewer (필수)
- 다른 AI들은 Reviewers (선택)
- 다른 AI가 없어도 CLAUDE 단독 리뷰 가능

### 4. 실시간 Progress 보고
- AI가 작업 중인 내용을 실시간으로 사용자에게 보고
- MCP를 통한 progress tracking
- 투명한 리뷰 프로세스

## 🚀 빠른 시작

### 설치

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. AI CLI 설치
# CLAUDE는 필수 (MCP 환경)
# 다른 AI는 선택 (더 많을수록 좋은 리뷰)
```

### 사용법

```bash
# Git diff 리뷰 (자동으로 모든 AI 감지)
python review.py --base develop

# 특정 브랜치와 비교
python review.py --base main --target feature/new-feature

# 특정 AI만 사용 (CLAUDE는 자동 포함)
python review.py --base develop --ais claude,gpt4

# 최대 라운드 수 지정
python review.py --base develop --max-rounds 5

# 상세 출력 모드
python review.py --base develop --verbose
```

### 출력 예시

```
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
```

## 📋 MCP Tools (9개)

AI에게 제공되는 도구는 **Review session 관리만**:

1. `create_review_session` - 리뷰 세션 생성
2. `submit_review` - 리뷰 제출
3. `get_other_reviews` - 다른 AI 리뷰 읽기
4. `check_consensus` - 합의 상태 확인
5. `advance_round` - 라운드 진행
6. `finalize_review` - 최종 확정
7. `get_session_info` - 세션 정보 조회
8. `report_progress` - 실시간 진행 보고
9. `get_progress` - 진행 상황 조회

**Git/Filesystem 도구는 제거됨** (Python이 내부 처리)

## 📚 문서

- [**CLAUDE-Led 아키텍처**](docs/CLAUDE_LED_ARCHITECTURE.md) ⭐ **NEW**
- [Pure Task Delegation 아키텍처](docs/PURE_TASK_DELEGATION_ARCHITECTURE.md)
- [CLI 사용법](docs/CLI_USAGE.md)
- [MCP 설정](docs/MCP_SETUP.md)
- [빠른 참조](docs/QUICK_REFERENCE.md)
- [테스트 가이드](docs/TESTING_GUIDE.md)
- [Consensus 구현](docs/CONSENSUS_IMPLEMENTATION.md)
- [실시간 Progress](docs/REALTIME_PROGRESS.md)
- [트러블슈팅](docs/TROUBLESHOOTING_LARGE_REVIEWS.md)

## 🏗️ 프로젝트 구조

```
src/
├── phase1_reviewer_mcp_orchestrated.py  ← CLAUDE-Led 리뷰어
├── data_curator.py                       ← Python 큐레이터
└── mcp/                                  ← MCP 서버 모듈
    ├── review_orchestrator.py            ← 리뷰 세션 관리
    ├── minimal_prompt.py                 ← 4개 프롬프트
    │                                       • CLAUDE 초기 REPORT
    │                                       • 검토자 REPORT 리뷰
    │                                       • CLAUDE 수정 판단
    │                                       • 최종 합의 확인
    ├── consensus_calculator.py           ← Consensus 계산 (예비)
    ├── manager.py                        ← MCP 매니저
    └── server.py                         ← MCP 서버
```

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest tests/ -v

# MCP 서버 테스트
pytest tests/test_mcp_servers.py -v

# Consensus 테스트
pytest tests/test_consensus_calculator.py -v
```

## 📊 아키텍처 비교

### 기존 (Parallel Independent Review)
```
Round 1: 모든 AI가 독립 리뷰 (병렬) → 중복/불일치 발생
Round 2: 서로 비평 (병렬) → 복잡한 조율
Final: Python 계산 기반 통합 → 기계적
```

### 신규 (CLAUDE-Led Iterative Review)
```
Round 1: CLAUDE 초기 REPORT 작성
Round N: CLAUDE REPORT → 검토 → 수정 → 합의 확인 (반복)
Result: CLAUDE의 refined REPORT (일관성, 품질 향상)
```

**장점**:
- ✅ CLAUDE MCP 환경에 자연스러움
- ✅ Iterative refinement로 품질 향상
- ✅ 일관성 있는 단일 REPORT
- ✅ 자연스러운 consensus (수렴 기반)
- ✅ 중복 리뷰 없음

## 📊 성과

- **토큰 사용량**: 98.4% 감소 (275K → 4.5K tokens)
- **코드베이스**: 57% 감소 (불필요한 코드 제거)
- **MCP Tools**: 50% 감소 (18 → 9 tools)
- **프롬프트**: 4개로 간소화 (명확한 역할 분리)

## 🔧 개발

이 프로젝트는 검증된 `ai_cli_tools` 모듈을 사용합니다:
- AI CLI 자동 감지 및 관리
- 에러 처리 및 재시도 로직
- 캐싱 시스템

## 📄 라이선스

MIT License

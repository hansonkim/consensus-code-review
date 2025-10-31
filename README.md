# AI Code Review System - Pure Task Delegation

**MCP 기반 Multi-AI 코드 리뷰 시스템 (Pure Task Delegation Architecture)**

## 🎯 핵심 개념

이 시스템은 **Pure Task Delegation** 아키텍처를 사용합니다:

- **Python**: 모든 객관적 작업 처리
  - Git 변경사항 조회
  - 파일 선택 및 우선순위 결정
  - 토큰 예산 관리
  - Consensus 계산

- **AI**: 주관적 작업만 수행
  - 큐레이션된 변경사항 분석
  - 코드 리뷰 작성
  - 다른 AI 리뷰 검증

## ✨ 주요 특징

### 1. 자동 AI 리뷰어 구성
- 시스템에 설치된 AI CLI 자동 감지 (Claude, GPT-4, Gemini)
- 각 AI가 독립적인 리뷰어로 참여
- 최소 2개의 AI 필요

### 2. Multi-Round Review Process
- **Round 1**: 각 AI가 독립적으로 리뷰 작성
- **Round 2**: 서로의 리뷰를 비판적으로 검증
- **Final Round**: Python이 계산한 consensus 기반 최종 리포트

### 3. 실시간 Progress 보고
- AI가 작업 중인 내용을 실시간으로 사용자에게 보고
- MCP를 통한 progress tracking
- 투명한 리뷰 프로세스

## 🚀 빠른 시작

### 설치

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. AI CLI 설치 (최소 2개)
# Claude CLI, OpenAI CLI, Google AI CLI 등
```

### 사용법

```bash
# Git diff 리뷰
python src/phase1_reviewer_mcp_orchestrated.py --base develop

# 특정 브랜치와 비교
python src/phase1_reviewer_mcp_orchestrated.py --base main --target feature/new-feature

# AI 선택 (선택사항)
python src/phase1_reviewer_mcp_orchestrated.py --base develop --ais claude,gpt4
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
├── phase1_reviewer_mcp_orchestrated.py  ← 메인 리뷰어
├── data_curator.py                       ← Python 큐레이터
└── mcp/                                  ← MCP 서버 모듈
    ├── review_orchestrator.py            ← 리뷰 세션 관리
    ├── minimal_prompt.py                 ← 프롬프트 생성
    ├── consensus_calculator.py           ← Consensus 계산
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

## 📊 성과

- **토큰 사용량**: 98.4% 감소 (275K → 4.5K tokens)
- **코드베이스**: 57% 감소 (불필요한 코드 제거)
- **MCP Tools**: 50% 감소 (18 → 9 tools)
- **테스트**: 100% 통과율

## 🔧 개발

이 프로젝트는 검증된 `ai_cli_tools` 모듈을 사용합니다:
- AI CLI 자동 감지 및 관리
- 에러 처리 및 재시도 로직
- 캐싱 시스템

## 📄 라이선스

MIT License

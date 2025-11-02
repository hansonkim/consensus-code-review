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

#### PyPI에서 설치 (권장)

```bash
# uv 사용 (권장)
uv pip install ai-code-review

# 또는 pip 사용
pip install ai-code-review
```

#### 소스에서 설치 (개발자용)

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/ai-code-review.git
cd ai-code-review

# 2. uv로 의존성 설치
uv sync

# 또는 pip 사용
pip install -e ".[dev]"

# 3. MCP 설정 (선택사항)
# config/claude_mcp_config.json.template을 복사하여 설정
cp config/claude_mcp_config.json.template config/claude_mcp_config.json
# ${PROJECT_ROOT}를 실제 경로로 수정

# 4. AI CLI 설치
# CLAUDE는 필수 (MCP 환경)
# 다른 AI는 선택 (GPT-4, Gemini 등)
```

#### 의존성

핵심 의존성:
- `tiktoken>=0.5.0` - 토큰 계산
- `aiofiles>=23.2.0` - 비동기 파일 I/O

개발 의존성:
- `pytest>=8.3.5` - 테스트 프레임워크
- `pytest-asyncio>=0.21.0` - 비동기 테스트 지원
- `mypy>=1.5.0` - 타입 체킹
- `black>=23.7.0` - 코드 포매팅
- `ruff>=0.1.0` - 린팅

### ⚠️ 보안 및 로컬 개발 주의사항

#### 소스 체크아웃 개발자용

**로컬에서 소스를 체크아웃하여 개발하는 경우:**

1. **MCP 설정 템플릿 사용**:
   ```bash
   # 템플릿 복사
   cp config/claude_mcp_config.json.template config/claude_mcp_config.json

   # ${PROJECT_ROOT}를 실제 프로젝트 절대 경로로 수정
   # 예: /Users/yourname/projects/ai-code-review
   ```

2. **Setup 스크립트 제한**:
   - `scripts/setup_mcp_config.sh`는 **소스 체크아웃 전용**
   - PyPI 설치에는 사용하지 마세요
   - 절대 경로를 하드코딩하므로 배포 불가

3. **제외된 민감한 파일들** (`.gitignore`로 보호):
   - `*_cache*.json` - AI 응답 캐시 (개인 데이터)
   - `reviews/` - 리뷰 결과물 (실행 산출물)
   - `logs/` - 실행 로그 (디버그 정보)
   - `.mcp.json`, `.claude/`, `.grok/` - 개인 AI 설정
   - `config/claude_mcp_config.json` - 로컬 절대 경로 포함

4. **Git History 정리** (민감한 파일이 실수로 커밋된 경우):
   ```bash
   # 백업 브랜치 생성
   git branch backup-before-cleanup-$(date +%Y%m%d-%H%M%S)

   # 민감한 파일 제거
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch [파일명]' \
     --prune-empty --tag-name-filter cat -- --all

   # Repository 최적화
   rm -rf .git/refs/original/
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

#### PyPI 사용자용

**PyPI에서 설치한 경우:**
- 위 민감한 파일들은 배포 패키지에 포함되지 않습니다
- `pyproject.toml`의 `[tool.hatch.build.targets.sdist]` 참조
- 설정 템플릿만 포함됩니다

### 사용법

#### 방법 1: MCP에서 직접 실행 (Claude Code) ⭐ **신규**

```python
# Claude Code MCP 환경에서
use consensus-code-review mcp

# Claude Code가 초기 리뷰 작성 후 다른 AI 검토
run_code_review(base="develop", target="HEAD")

# 최대 라운드 수 지정
run_code_review(base="develop", max_rounds=5)

# 이미 작성된 리뷰를 다른 AI에게 검토 요청
audit_code_review(base="develop", initial_review="[your review here]")

# 특정 AI만 사용
audit_code_review(base="develop", initial_review="...", ais="gpt4,gemini")
```

#### 방법 2: CLI에서 실행 (기존)

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

## 📋 MCP Tools

### 사용자용 도구 (2개)

**대부분의 경우 이것만 사용하면 됩니다:**

1. `run_code_review` - 🚀 **Claude Code가 초기 리뷰 작성 후 다른 AI 검토**
   - AI CLI 자동 감지 (GPT-4, Gemini)
   - Claude Code가 현재 컨텍스트에서 초기 리뷰 작성
   - 다른 AI들이 검토 및 iterative refinement
   - 최종 합의된 REPORT 자동 생성

2. `audit_code_review` - 🔍 **이미 작성된 리뷰를 다른 AI에게 검토 요청**
   - 사용자가 준비한 리뷰를 다른 AI들이 검토
   - Claude Code 초기 리뷰 단계 건너뜀
   - 빠른 peer validation

### 내부용 도구 (9개)

**run_code_review와 audit_code_review가 내부적으로 사용합니다. 직접 사용하지 마세요:**

3. `create_review_session` - 🔧 [내부용] 리뷰 세션 생성
4. `submit_review` - 🔧 [내부용] 리뷰 제출
5. `get_other_reviews` - 🔧 [내부용] 다른 AI 리뷰 읽기
6. `check_consensus` - 🔧 [내부용] 합의 상태 확인
7. `advance_round` - 🔧 [내부용] 라운드 진행
8. `finalize_review` - 🔧 [내부용] 최종 확정
9. `get_session_info` - 🔧 [내부용] 세션 정보 조회
10. `report_progress` - 🔧 [내부용] 진행 상황 보고
11. `get_progress` - 🔧 [내부용] 진행 상황 조회

**Git/Filesystem 도구는 제거됨** (Python이 내부 처리)

## 📚 문서

- [**Consensus Code Review MCP Tools**](docs/CONSENSUS_CODE_REVIEW_MCP_TOOLS.md) ⭐ **NEW**
- [**CLAUDE-Led 아키텍처**](docs/CLAUDE_LED_ARCHITECTURE.md)
- [Pure Task Delegation 아키텍처](docs/PURE_TASK_DELEGATION_ARCHITECTURE.md)
- [CLI 사용법](docs/CLI_USAGE.md)
- [MCP 설정](docs/MCP_SETUP.md)
- [빠른 참조](docs/QUICK_REFERENCE.md)
- [테스트 가이드](docs/TESTING_GUIDE.md)
- [실시간 Progress](docs/REALTIME_PROGRESS.md)
- [트러블슈팅](docs/TROUBLESHOOTING_LARGE_REVIEWS.md)

## 🏗️ 프로젝트 구조

```
server.py                                    ← MCP 서버 진입점 (stdio)
src/consensus_code_review/                   ← 메인 패키지
├── __init__.py                              ← 패키지 초기화
├── __main__.py                              ← CLI 진입점
├── cli.py                                   ← 명령줄 인터페이스
├── data_curator.py                          ← Git diff 큐레이터 (토큰 제한)
├── stdio_server.py                          ← stdio MCP 서버
└── mcp/                                     ← MCP 서버 모듈
    ├── __init__.py
    ├── manager.py                           ← MCP 서버 매니저
    ├── review_orchestrator.py               ← 리뷰 도구 제공자 (11개)
    ├── minimal_prompt.py                    ← 4개 프롬프트 생성기
    │                                          • CLAUDE 초기 REPORT
    │                                          • 검토자 REPORT 리뷰
    │                                          • CLAUDE 수정 판단
    │                                          • 최종 합의 확인
    ├── types.py                             ← 타입 정의
    ├── handlers/                            ← 핸들러 모듈
    │   ├── __init__.py
    │   └── review_handler.py                ← 리뷰 핸들러
    └── utils/                               ← 유틸리티 모듈
        ├── __init__.py
        ├── artifact_manager.py              ← 아티팩트 관리
        ├── artifact_writer.py               ← 아티팩트 작성
        ├── summary_generator.py             ← 요약 생성
        └── token_counter.py                 ← 토큰 계산

config/
├── claude_mcp_config.json.template          ← MCP 설정 템플릿
└── claude_mcp_config.json                   ← 로컬 설정 (gitignore)

tests/                                       ← 테스트 디렉토리
├── conftest.py                              ← pytest 설정
├── test_*.py                                ← 단위 테스트
└── mcp/utils/                               ← MCP 유틸 테스트
    ├── test_artifact_manager.py
    ├── test_artifact_writer.py
    ├── test_summary_generator.py
    └── test_token_counter.py

docs/                                        ← 문서
scripts/                                     ← 유틸리티 스크립트
```

## 🧪 테스트

### 테스트 실행

```bash
# uv 사용 (권장)
uv run pytest

# 또는 직접 pytest 실행
pytest tests/ -v

# 특정 테스트만 실행
uv run pytest tests/test_mcp_servers.py -v

# 비동기 테스트 실행
uv run pytest tests/mcp/utils/ -v

# 커버리지와 함께 실행
uv run pytest --cov=src/consensus_code_review --cov-report=html

# 실패시 즉시 중단 (빠른 피드백)
uv run pytest -xvs
```

### 테스트 요구사항

- `pytest>=8.3.5` - 테스트 프레임워크
- `pytest-asyncio>=0.21.0` - 비동기 테스트 지원
  - `asyncio` 마커 자동 처리
  - `@pytest.mark.asyncio` 데코레이터 지원

### 알려진 이슈

- `test_artifact_manager.py`: 7개 테스트 스킵
  - 이유: API 리팩토링 필요 (dict vs ReviewSession)
  - 상태: 향후 버전에서 수정 예정

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

### 기술 스택

이 프로젝트는 검증된 `ai_cli_tools` 모듈을 사용합니다:
- AI CLI 자동 감지 및 관리
- 에러 처리 및 재시도 로직
- 응답 캐싱 시스템

### 빌드 시스템

- **패키지 매니저**: `uv` (Python 3.8+ 필수)
- **빌드 백엔드**: `hatchling`
- **타입 체킹**: `mypy`
- **코드 포매팅**: `black`
- **린팅**: `ruff`

### 개발 워크플로우

```bash
# 의존성 동기화
uv sync

# 타입 체크
uv run mypy src/

# 코드 포매팅
uv run black src/ tests/

# 린팅
uv run ruff check src/ tests/

# 테스트
uv run pytest

# 패키지 빌드
uv build
```

### 기여하기

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest`
5. Submit a pull request

⚠️ **주의**: PR 제출 전 민감한 파일이 포함되지 않았는지 확인하세요.

## 📄 라이선스

MIT License

## 🔗 관련 링크

- **GitHub**: https://github.com/yourusername/ai-code-review
- **Issues**: https://github.com/yourusername/ai-code-review/issues
- **Documentation**: https://github.com/yourusername/ai-code-review/blob/main/docs/

# AI Code Review System

설치된 모든 AI CLI 도구를 자동으로 감지하여 각각이 독립적인 리뷰어로 참여하고, 서로의 리뷰를 비판적으로 검증하여 최종 합의된 코드 리뷰 문서를 생성하는 완전 자동화 시스템입니다.

## 🎯 프로젝트 개요

시스템에 설치된 AI CLI(Claude, Gemini, Grok, OpenAI 등)를 자동 감지하여 **각 AI가 독립적인 리뷰어**로 동작합니다. 각 리뷰어는 내장된 Agent들과 MCP 서버를 활용하여 코드를 다각도로 분석하고, 서로의 리뷰를 검증하며 합의에 도달합니다.

### 핵심 차별점

- **완전 자동화**: 사용자 입력 없이 비대화형으로 실행
- **자동 리뷰어 구성**: 사용 가능한 모든 AI CLI = 리뷰어 (수동 선택 불필요)
- **비판적 검증**: 각 AI가 다른 AI의 리뷰를 면밀히 검토하고 오류나 과장을 지적
- **Agent 기반 분석**: 각 AI가 전문 Agent(코드 분석, 보안 검사, 성능 분석 등) 활용
- **MCP 통합**: Bitbucket, Jira, Confluence, Slack 등 MCP 서버 적극 활용
- **증거 기반**: 구체적인 코드 라인과 예시를 기반으로 한 리뷰
- **실행 가능성**: 추상적 제안이 아닌 구체적이고 실행 가능한 개선안
- **모듈화**: 검증된 `ai_cli_tools` 모듈 사용 (ai-discussion 프로젝트에서 추출)

## ✨ 주요 기능

### 1. 자동 AI 리뷰어 구성
- **완전 자동 감지**: 시스템에 설치된 모든 AI CLI 자동 탐지
- **1 CLI = 1 리뷰어**: 각 사용 가능한 AI CLI가 독립적인 리뷰어로 참여
- **캐싱 시스템**: AI CLI 가용성을 캐시하여 빠른 재실행
- **최소 요구사항**: 최소 2개의 AI CLI 필요 (더 많을수록 다양한 관점)

### 2. Agent 기반 분석 시스템
각 AI 리뷰어가 내장 Agent들을 자동으로 활용:
- **Explore Agent**: 코드베이스 구조 탐색 및 파일 관계 분석
- **Orient Agent**: 코드 패턴 식별 및 컨텍스트 이해
- **Observe Agent**: 세부 코드 검사 및 이슈 발견
- **Code Review Agent**: 전문적인 코드 리뷰 수행
- **Security Agent**: 보안 취약점 자동 스캔
- **Performance Agent**: 성능 병목 지점 분석

### 3. MCP 서버 통합
사용 가능한 MCP 서버를 적극 활용:
- **Bitbucket MCP**: PR 정보, diff, 코드 히스토리 분석
- **Jira MCP**: 관련 이슈 및 요구사항 확인
- **Confluence MCP**: 프로젝트 문서 및 아키텍처 문서 참조
- **Slack MCP**: 리뷰 결과 알림 전송 (선택적)
- **Context7 MCP**: 라이브러리/프레임워크 문서 자동 참조

### 4. 다양한 리뷰 모드

#### 파일/디렉토리 리뷰
```bash
python ai_code_review.py ./src/main.py
python ai_code_review.py ./src/
```

#### PR 생성 전 리뷰 (Staged Changes)
```bash
python ai_code_review.py --staged
```
Git staged 변경사항을 자동으로 리뷰

#### 특정 커밋 범위 리뷰
```bash
python ai_code_review.py --commits HEAD~3..HEAD
```

### 6. 3단계 리뷰 프로세스

#### Phase 1: 독립적 초기 리뷰
- 각 AI 리뷰어가 Agent들을 활용하여 독립적으로 코드 분석
- MCP를 통해 관련 컨텍스트(PR 정보, 이슈, 문서) 자동 수집
- 보안, 성능, 가독성, 아키텍처 등 다각도 분석
- 각자의 발견사항을 구체적 코드 라인과 함께 기록

#### Phase 2: 비판적 검증 (1-N 라운드)
- 각 AI가 다른 AI의 리뷰를 면밀히 검증
- 논리적 오류, 과장, 근거 부족, 잘못된 가정 지적
- Agent를 활용하여 반박 근거 탐색
- 대안 제시 및 반론
- **조기 종료**: 모든 AI가 합의 준비되면 최종 라운드로 이동

#### Phase 3: 최종 합의
- 각 AI가 토론을 바탕으로 최종 검증된 리뷰 제출
- 시스템이 모든 리뷰를 통합하여 단일 문서 생성
- 합의된 이슈만 최종 리뷰에 포함 (우선순위 자동 분류)

### 7. 상세한 리뷰 문서 생성
- **실시간 기록**: 리뷰 과정을 실시간으로 마크다운 파일에 저장
- **통합 리뷰**: 모든 AI의 합의를 반영한 최종 리뷰 문서
- **구조화된 형식**: Critical/Major/Minor/Suggestion 자동 분류
- **코드 스니펫**: 문제 코드와 개선안을 함께 제시
- **실행 가능성**: 즉시 적용 가능한 구체적 개선안

## 📋 사용 요구사항

### 필수 설치

최소 2개 이상의 AI CLI가 설치되어 있어야 합니다:

- **Claude CLI**: [설치 방법](https://github.com/anthropics/claude-cli)
- **OpenAI Codex CLI**: [설치 방법](https://github.com/openai/codex-cli)
- **Gemini CLI**: [설치 방법](https://github.com/google/gemini-cli)
- **Grok CLI**: [설치 방법](https://github.com/xai-org/grok-cli)

프로그램 시작 시 자동으로 사용 가능한 CLI를 감지하고, 없으면 설치 안내를 표시합니다.

### Python 요구사항
- Python 3.8 이상
- [uv](https://github.com/astral-sh/uv) - 빠른 Python 패키지 및 프로젝트 관리자
- 표준 라이브러리만 사용 (추가 패키지 불필요)

### 환경 설정

#### 1. uv 설치

**macOS/Linux**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**패키지 매니저로 설치**:
```bash
# Homebrew (macOS)
brew install uv

# pipx
pipx install uv
```

#### 2. 프로젝트 초기화

```bash
# 프로젝트 클론
git clone https://github.com/yourusername/ai-code-review.git
cd ai-code-review

# uv로 가상환경 생성 및 활성화
uv venv
source .venv/bin/activate  # macOS/Linux
# 또는
.venv\Scripts\activate     # Windows

# 의존성 설치 (현재는 표준 라이브러리만 사용)
# 향후 추가 패키지가 필요할 경우:
# uv pip install -r requirements.txt
```

#### 3. uv를 사용한 실행

```bash
# 가상환경 활성화 후 실행
python ai_code_review.py ./src/main.py

# 또는 uv run으로 직접 실행 (가상환경 자동 관리)
uv run python ai_code_review.py ./src/main.py
```

### 프로젝트 구조

```
ai-code-review/
├── ai_cli_tools/              # AI CLI 호출 모듈 (ai-discussion에서 추출)
│   ├── models.py              # AIModel 데이터 클래스
│   ├── client.py              # AI CLI 호출 클라이언트
│   ├── manager.py             # AI 자동 감지 및 관리
│   ├── cache.py               # 가용성 캐싱
│   ├── constants.py           # AI 모델 정의
│   └── exceptions.py          # 커스텀 예외
├── ai_code_review.py          # 메인 시스템
└── .ai_code_review_cache.json # AI CLI 캐시 (자동 생성)
```

`ai_cli_tools` 모듈은 [ai-discussion](https://github.com/yourusername/ai-discussion) 프로젝트에서 검증된 AI CLI 호출 메커니즘을 모듈화하여 재사용합니다.

## 🚀 사용 방법

### 기본 사용법

**완전 비대화형** - 사용자 입력 없이 자동으로 실행됩니다.

#### 1. 파일 리뷰
```bash
# uv 환경에서 실행 (권장)
uv run python ai_code_review.py ./src/main.py

# 또는 가상환경 활성화 후
source .venv/bin/activate
python ai_code_review.py ./src/main.py
```

#### 2. 디렉토리 리뷰
```bash
uv run python ai_code_review.py ./src/
```

#### 3. Staged Changes 리뷰 (PR 생성 전)
```bash
uv run python ai_code_review.py --staged
```

#### 4. 특정 커밋 범위 리뷰
```bash
uv run python ai_code_review.py --commits HEAD~5..HEAD
```

#### 5. 현재 브랜치의 모든 변경사항
```bash
uv run python ai_code_review.py --branch
```

### 고급 옵션

```bash
# 최대 검증 라운드 수 지정 (기본: 3)
uv run python ai_code_review.py ./src/main.py --max-rounds 5

# 최대 파일 수 제한 (대규모 리뷰 시 권장)
uv run python ai_code_review.py --branch develop --max-files 20

# 특정 AI만 사용 (기본: 모든 사용 가능한 AI)
uv run python ai_code_review.py ./src/main.py --only claude,gemini

# MCP 비활성화 (기본: 활성화)
uv run python ai_code_review.py ./src/main.py --no-mcp

# 특정 파일 확장자만 리뷰
uv run python ai_code_review.py ./src/ --extensions .py,.js

# 조기 종료 비활성화 (모든 라운드 강제 실행)
uv run python ai_code_review.py ./src/main.py --no-early-exit

# AI CLI 캐시 강제 갱신
uv run python ai_code_review.py ./src/main.py --force-refresh
```

#### 💡 대규모 리뷰 팁

파일이 많을 때는 AI 모델의 컨텍스트 제한으로 실패할 수 있습니다:

```bash
# 1. 파일 수 제한 (권장: 20-30개)
ai-review --branch develop --max-files 20

# 2. 특정 확장자만 필터링
ai-review --branch develop --extensions .py

# 3. 특정 디렉토리만 리뷰
ai-review ./src/core/ --max-files 30

# 4. 조합 사용
ai-review --branch develop --extensions .py,.js --max-files 25
```

**경고 메시지:**
- 30개 이상 파일: 자동 경고 및 권장사항 표시
- 100,000 토큰 초과: 프롬프트 크기 경고
- 빈 파일: 자동 필터링 및 스킵 알림

### 실행 예시

```bash
$ uv run python ai_code_review.py ./src/authentication.py

🔍 AI Code Review System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📂 리뷰 대상: ./src/authentication.py
🤖 사용 가능한 AI 리뷰어: 3명
   • Claude (Anthropic)
   • Gemini (Google)
   • Grok (xAI)

🔌 활성화된 MCP 서버:
   • Bitbucket MCP
   • Context7 MCP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Phase 1] 초기 리뷰 진행 중...
  ✓ Claude: 보안 및 인증 로직 분석 완료
  ✓ Gemini: 성능 및 알고리즘 분석 완료
  ✓ Grok: 코드 구조 및 패턴 분석 완료

[Phase 2] 비판적 검증 - Round 1...
  ✓ Claude: Gemini의 리뷰 검증 완료
  ✓ Gemini: Grok의 리뷰 검증 완료
  ✓ Grok: Claude의 리뷰 검증 완료

[Phase 2] 비판적 검증 - Round 2...
  ✓ 모든 리뷰어가 합의 준비 완료

[Phase 3] 최종 합의 생성 중...
  ✓ 통합 리뷰 문서 생성 완료

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 리뷰 완료!

📄 생성된 파일:
   • authentication-review-20240129-143022.md
   • authentication-final-review-20240129-143022.md

📊 발견된 이슈:
   • Critical: 2
   • Major: 5
   • Minor: 3
   • Suggestions: 7
```

## 📄 출력 파일

### 1. 전체 리뷰 기록 (`{filename}-review-{timestamp}.md`)

```markdown
# 코드 리뷰 기록

**생성 일시**: 2024-01-29 14:30:22
**리뷰 대상**: authentication.py
**리뷰 모드**: File Review

## 🤖 AI 리뷰어 구성

### 🔵 Claude (Anthropic)
> 사용된 Agent: Explore, Security, Code Review
> MCP 활용: Context7 (라이브러리 문서 참조)

### 🟢 Gemini (Google)
> 사용된 Agent: Observe, Performance, Code Review
> MCP 활용: Context7

### 🟡 Grok (xAI)
> 사용된 Agent: Orient, Code Review
> MCP 활용: -

---

## 📝 Phase 1: 독립적 초기 리뷰

### 🔵 Claude
#### 발견 이슈 (5개)

**[CRITICAL] SQL Injection 취약점**
- 위치: `authentication.py:45-47`
- 분석 경로: Security Agent → 취약점 패턴 매칭
```python
# 문제 코드
query = f"SELECT * FROM users WHERE username = '{username}'"
```

**[MAJOR] 비밀번호 해싱 알고리즘 미흡**
- 위치: `authentication.py:89`
- 분석 경로: Security Agent → Context7 MCP (bcrypt 문서 참조)
...

### 🟢 Gemini
#### 발견 이슈 (4개)
...

---

## 💬 Phase 2: 비판적 검증

### Round 1

#### 🔵 Claude → Gemini 리뷰 검증
**Gemini의 "N+1 쿼리 문제" 지적에 대한 검증**
- 동의: 맞습니다. `get_user_permissions()` 호출이 반복됩니다.
- 추가 발견: Explore Agent로 확인 결과, 실제로는 캐싱이 적용되어 있음
- 결론: 문제의 심각도를 Major → Minor로 하향 조정 제안

#### 🟢 Gemini → Grok 리뷰 검증
...

### Round 2
...

---

## 🎯 Phase 3: 최종 합의

### 🔵 Claude 최종 리뷰
[검증을 거친 최종 이슈 목록]

### 🟢 Gemini 최종 리뷰
...
```

### 2. 최종 통합 리뷰 (`{filename}-final-review-{timestamp}.md`)

```markdown
# 최종 코드 리뷰

**생성 일시**: 2024-01-29 14:30:22
**리뷰 대상**: authentication.py

---

## 🎯 통합 리뷰 요약

[AI가 자동 생성한 통합 요약]

---

## 🔴 Critical Issues (즉시 수정 필요)

### Issue 1: SQL Injection 취약점
**위치**: `authentication.py:45-47`
**발견자**: 보안 전문가, 아키텍처 전문가 (합의)

**문제**:
```python
query = f"SELECT * FROM users WHERE username = '{username}'"
```

**개선안**:
```python
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))
```

**합의 근거**:
- 보안 전문가: SQL Injection 공격 가능
- 아키텍처 전문가: ORM 사용 권장

---

## 🟡 Major Issues (우선 개선 권장)

## 🟢 Minor Issues (개선 고려)

## 💡 Suggestions (선택적 개선)

---

## 📊 리뷰 통계

- Total Issues: 12
- Critical: 2
- Major: 5
- Minor: 3
- Suggestions: 2
```

## 🔧 고급 기능

### 1. 캐시 시스템
AI CLI 가용성을 캐시하여 빠른 시작 (`ai_cli_tools` 모듈 활용):
```bash
# 캐시 파일 확인
cat .ai_code_review_cache.json

# 캐시 초기화 (새 AI CLI 설치 후)
rm .ai_code_review_cache.json

# 또는 프로그램 실행 시 강제 갱신 (권장)
uv run python ai_code_review.py --force-refresh
```

### 2. 리뷰 범위 제어
- **단일 파일**: 심층 분석
- **디렉토리**: 구조적 분석, 파일 간 의존성
- **필터링**: 특정 확장자만 리뷰 (예: `*.py`, `*.js`)

### 3. 리뷰 관점 커스터마이징
기본 제공 관점 외에도 사용자 정의 가능:
- "API 설계 전문가"
- "데이터베이스 최적화 전문가"
- "프론트엔드 접근성 전문가"
- "DevOps 전문가"

## 📊 작동 원리

```
1. 시스템 초기화
   ├─ AI CLI 가용성 자동 감지 (캐시 활용)
   ├─ 각 AI CLI = 1 리뷰어로 등록
   ├─ MCP 서버 연결 확인
   └─ Agent 시스템 초기화

2. 리뷰 대상 분석
   ├─ 파일/디렉토리/Git 변경사항 식별
   ├─ 관련 컨텍스트 수집 (MCP 활용)
   │   ├─ Bitbucket: PR 정보, diff, 커밋 히스토리
   │   ├─ Jira: 관련 이슈, 요구사항
   │   └─ Confluence: 프로젝트 문서, 아키텍처
   └─ 코드 파싱 및 구조 분석

3. Phase 1: 독립적 초기 리뷰 (병렬 실행)
   각 AI 리뷰어가 독립적으로:
   ├─ Explore Agent: 코드베이스 구조 파악
   ├─ Observe Agent: 세부 코드 검사
   ├─ Orient Agent: 패턴 및 컨텍스트 이해
   ├─ 전문 Agent: 보안/성능/테스트 분석
   ├─ Context7 MCP: 사용된 라이브러리 문서 참조
   └─ 발견 이슈 기록 (코드 라인 + 근거)

4. Phase 2: 비판적 검증 (순차 라운드)
   Round 1~N:
   ├─ 각 AI가 다른 AI의 리뷰 검증
   │   ├─ Agent로 반박 근거 탐색
   │   ├─ 논리적 오류, 과장, 잘못된 가정 지적
   │   └─ 대안 제시 및 심각도 재평가
   ├─ [매 라운드 후] 합의 준비 확인
   │   └─ 모두 준비 완료 → Phase 3로 조기 이동
   └─ [최대 라운드] 도달 시 Phase 3로 이동

5. Phase 3: 최종 합의
   ├─ 각 AI가 검증된 최종 리뷰 제출
   ├─ 시스템이 모든 리뷰 통합
   │   ├─ 합의된 이슈만 포함
   │   ├─ 우선순위 자동 분류 (Critical/Major/Minor/Suggestion)
   │   └─ 코드 스니펫 + 개선안 정리
   └─ 통합 문서 생성

6. 결과 저장
   ├─ 전체 리뷰 과정 기록 (.md)
   ├─ 최종 통합 리뷰 문서 (.md)
   └─ [선택] Slack 알림 전송 (MCP)
```

## 🎓 활용 사례

### 1. 오픈소스 프로젝트
- Pull Request 리뷰 자동화
- 코드 품질 게이트로 활용
- 기여자 가이드라인 준수 확인

### 2. 팀 코드 리뷰
- 리뷰어 부담 감소
- 놓치기 쉬운 이슈 발견
- 리뷰 품질 표준화

### 3. 레거시 코드 분석
- 기술 부채 파악
- 리팩토링 우선순위 결정
- 보안 취약점 스캔

### 4. 교육 목적
- 코드 품질 학습
- 베스트 프랙티스 이해
- 다양한 관점 습득

## 🔒 보안 및 프라이버시

- **로컬 실행**: 모든 처리는 로컬 환경에서 실행
- **API 호출**: 각 AI CLI를 통해 API 호출 (각 서비스의 약관 준수)
- **데이터 보관**: 리뷰 결과는 로컬 파일로만 저장
- **민감 정보**: 민감한 코드는 리뷰 전 마스킹 권장

## ⚠️ 제약사항

1. **AI CLI 의존성**: 최소 2개의 AI CLI 설치 필요
2. **API 비용**: AI 호출마다 비용 발생 가능
3. **처리 시간**: 코드 크기와 리뷰어 수에 비례하여 시간 소요
4. **완벽성 보장 불가**: AI 리뷰는 참고용이며, 최종 판단은 개발자 몫

## 🤝 기여하기

이슈 제보, 기능 제안, PR은 언제나 환영합니다!

## 📜 라이센스

MIT License

## 🔗 관련 프로젝트

- [ai-discussion](https://github.com/yourusername/ai-discussion) - AI 토론 시스템 (본 프로젝트의 기반)

---

**Made with ❤️ by AI Collaboration**

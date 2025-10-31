# Product Requirements Document (PRD)
# AI Code Review System

**버전**: 1.0
**작성일**: 2025-10-31
**작성자**: AI Code Review Team

---

## 1. 개요 (Executive Summary)

### 1.1 제품 비전

AI Code Review System은 여러 AI CLI 도구를 자동으로 감지하고 각 AI가 독립적인 코드 리뷰어로 동작하여, 서로의 리뷰를 비판적으로 검증하고 최종 합의된 코드 리뷰 문서를 생성하는 완전 자동화 시스템입니다.

### 1.2 문제 정의

**현재 코드 리뷰의 문제점**:
- 단일 AI 리뷰어는 편향적이고 불완전할 수 있음
- 인간 리뷰어는 시간 제약과 일관성 문제가 있음
- 보안, 성능, 아키텍처 등 다양한 관점의 동시 검토가 어려움
- AI의 과장되거나 잘못된 지적을 검증하기 어려움

**해결 방법**:
- 여러 AI가 독립적으로 리뷰하고 서로를 검증
- Agent 시스템을 활용한 심층 분석
- MCP를 통한 프로젝트 컨텍스트 자동 수집
- 비판적 검증을 통한 합의 기반 최종 리뷰

### 1.3 핵심 가치 제안

1. **다중 관점**: 여러 AI가 독립적으로 분석하여 다각도 검토
2. **자동 검증**: AI들이 서로의 리뷰를 비판적으로 검증
3. **완전 자동화**: 사용자 입력 없이 비대화형 실행
4. **증거 기반**: 구체적인 코드 라인과 예시 제공
5. **모듈화**: 검증된 `ai_cli_tools` 모듈 재사용

---

## 2. 목표 및 목적

### 2.1 비즈니스 목표

- **품질 향상**: 코드 품질을 자동으로 높은 수준으로 유지
- **시간 절약**: 인간 리뷰어의 부담을 줄이고 효율성 증대
- **일관성 확보**: 일관된 기준으로 코드 리뷰 수행
- **지식 공유**: 다양한 관점의 리뷰를 통한 팀 학습

### 2.2 사용자 목표

- **개발자**: 빠르고 정확한 코드 리뷰 피드백 획득
- **팀 리드**: 코드 품질 게이트 자동화
- **오픈소스 메인테이너**: PR 리뷰 자동화로 부담 감소

### 2.3 성공 지표 (KPI)

| 지표 | 목표값 | 측정 방법 |
|------|--------|-----------|
| AI 감지 성공률 | 95% 이상 | 설치된 AI CLI 중 감지된 비율 |
| 리뷰 완료 시간 | 10분 이내 | 파일 당 평균 리뷰 시간 |
| 이슈 합의율 | 80% 이상 | 검증을 통과한 이슈 비율 |
| False Positive 감소 | 50% 이상 | 단일 AI 대비 잘못된 지적 감소 |
| 사용자 만족도 | 4.0/5.0 이상 | 사용자 피드백 평균 점수 |

---

## 3. 이해관계자 (Stakeholders)

### 3.1 주요 사용자

| 사용자 그룹 | 역할 | 주요 니즈 |
|-------------|------|-----------|
| **개발자** | 코드 작성자 | 빠른 피드백, 구체적인 개선안 |
| **시니어 개발자** | 리뷰어 | 리뷰 부담 감소, 놓치기 쉬운 이슈 발견 |
| **팀 리드** | 품질 관리자 | 코드 품질 표준화, 통계 및 트렌드 |
| **DevOps 엔지니어** | CI/CD 관리자 | 파이프라인 통합, 자동화 |

### 3.2 기술 이해관계자

- **AI 서비스 제공자**: Anthropic (Claude), Google (Gemini), xAI (Grok), OpenAI
- **MCP 제공자**: Bitbucket, Jira, Confluence, Slack, Context7
- **오픈소스 커뮤니티**: ai-discussion 프로젝트

---

## 4. 주요 기능 (Core Features)

### 4.1 필수 기능 (MVP)

#### F1: AI CLI 자동 감지 (`ai_cli_tools` 모듈)

**설명**: 시스템에 설치된 모든 AI CLI를 자동으로 감지하고 리뷰어로 구성

**기능 상세**:
- 병렬 AI CLI 감지 (2-10초 이내)
- 2단계 감지 알고리즘 (CLI 설치 확인 + API 호출 테스트)
- 캐싱을 통한 빠른 재시작
- 최소 2개의 AI CLI 필요

**사용자 스토리**:
```
AS a developer
I WANT the system to automatically detect available AI CLIs
SO THAT I don't have to manually configure reviewers
```

**인수 조건** (Acceptance Criteria):
- [ ] Claude, Gemini, Grok, OpenAI CLI 자동 감지
- [ ] 10초 이내 모든 AI CLI 확인
- [ ] 캐시 파일 자동 생성 (.ai_code_review_cache.json)
- [ ] 최소 2개 미만 시 에러 메시지와 설치 안내

**우선순위**: P0 (Critical)

---

#### F2: 3단계 리뷰 프로세스

**Phase 1: 독립적 초기 리뷰**
- 각 AI가 병렬로 독립적 분석
- Agent 시스템 활용 (Explore, Observe, Orient, Security, Performance)
- MCP 통해 컨텍스트 수집 (PR 정보, 이슈, 문서)

**Phase 2: 비판적 검증 (1-N 라운드)**
- 각 AI가 다른 AI의 리뷰 검증
- 논리적 오류, 과장, 근거 부족 지적
- Agent로 반박 근거 탐색
- 조기 종료 가능 (모두 합의 시)

**Phase 3: 최종 합의**
- 검증된 이슈만 포함
- 우선순위 자동 분류 (CRITICAL/MAJOR/MINOR/SUGGESTION)
- 중복 제거 및 통합

**사용자 스토리**:
```
AS a developer
I WANT multiple AIs to verify each other's reviews
SO THAT I get more accurate and trustworthy feedback
```

**인수 조건**:
- [ ] Phase 1 병렬 실행으로 시간 단축
- [ ] Phase 2 최대 3라운드 (설정 가능)
- [ ] 조기 종료로 불필요한 라운드 스킵
- [ ] Phase 3에서 합의된 이슈만 포함

**우선순위**: P0 (Critical)

---

#### F3: 다양한 리뷰 모드

**지원 모드**:
1. **파일 리뷰**: 단일 파일 심층 분석
2. **디렉토리 리뷰**: 여러 파일 구조적 분석
3. **Staged Changes 리뷰**: PR 생성 전 커밋 예정 코드 리뷰
4. **커밋 범위 리뷰**: 특정 커밋 범위 분석
5. **브랜치 리뷰**: 현재 브랜치의 모든 변경사항

**사용자 스토리**:
```
AS a developer
I WANT to review code at different stages (file, staged, PR)
SO THAT I can catch issues early in the development process
```

**인수 조건**:
- [ ] 5가지 리뷰 모드 모두 지원
- [ ] Git 통합으로 자동 변경사항 감지
- [ ] 파일 확장자 필터링 지원

**우선순위**: P0 (Critical)

---

#### F4: Agent 기반 분석

**사용 가능한 Agent**:
- **Explore Agent**: 코드베이스 구조 탐색
- **Observe Agent**: 세부 코드 검사
- **Orient Agent**: 패턴 및 컨텍스트 이해
- **Security Agent**: 보안 취약점 스캔
- **Performance Agent**: 성능 병목 분석
- **Code Review Agent**: 종합적 리뷰

**사용자 스토리**:
```
AS a developer
I WANT AIs to use specialized agents
SO THAT I get deep analysis from multiple perspectives
```

**인수 조건**:
- [ ] AI CLI에 Agent 사용 지시 전달
- [ ] Phase별로 적절한 Agent 선택
- [ ] Agent 사용 여부를 리뷰 문서에 기록

**우선순위**: P1 (High)

---

#### F5: MCP 통합

**지원 MCP 서버**:
- **Bitbucket MCP**: PR 정보, diff, 커밋 히스토리
- **Jira MCP**: 관련 이슈 및 요구사항
- **Confluence MCP**: 프로젝트 문서, 아키텍처
- **Context7 MCP**: 라이브러리 문서 자동 참조
- **Slack MCP**: 리뷰 완료 알림 (선택적)

**사용자 스토리**:
```
AS a developer
I WANT the system to automatically gather project context
SO THAT AIs can provide more informed reviews
```

**인수 조건**:
- [ ] MCP 서버 자동 감지
- [ ] MCP 없이도 동작 (graceful degradation)
- [ ] MCP 정보를 AI 프롬프트에 포함

**우선순위**: P1 (High)

---

#### F6: 상세한 리뷰 문서 생성

**생성 파일**:
1. **전체 리뷰 기록**: `{name}-review-{timestamp}.md`
   - Phase 1, 2, 3 전체 과정 기록
   - 각 AI의 발견사항 및 검증 과정

2. **최종 통합 리뷰**: `{name}-final-review-{timestamp}.md`
   - 합의된 이슈만 포함
   - 심각도별 분류 및 우선순위
   - 통계 및 요약

**문서 형식**:
- Markdown 형식
- 코드 스니펫 포함
- 파일:라인 참조
- 개선안 코드 포함

**사용자 스토리**:
```
AS a developer
I WANT detailed review documents with code examples
SO THAT I can easily understand and fix issues
```

**인수 조건**:
- [ ] 2개의 마크다운 파일 생성
- [ ] 코드 스니펫 및 위치 정보 포함
- [ ] 구체적이고 실행 가능한 개선안
- [ ] 통계 및 요약 제공

**우선순위**: P0 (Critical)

---

### 4.2 고급 기능 (v1.1+)

#### F7: 캐시 시스템
- AI CLI 가용성 캐싱
- MCP 서버 상태 캐싱
- 빠른 재시작 (2-3초)

#### F8: 커스터마이징
- 리뷰 관점 커스터마이징
- 검증 라운드 수 조정
- 조기 종료 on/off
- 특정 AI만 사용

#### F9: 통합
- Git hooks (pre-commit, pre-push)
- CI/CD 파이프라인 통합
- IDE 플러그인

---

## 5. 기술 요구사항 (Technical Requirements)

### 5.1 시스템 아키텍처

```
ai-code-review/
├── ai_cli_tools/                   # AI CLI 호출 모듈 (모듈화, 재사용 가능)
│   ├── models.py                   # AIModel 데이터 클래스
│   ├── client.py                   # AIClient (AI CLI 호출 + 재시도)
│   ├── manager.py                  # ModelManager (자동 감지 + 병렬 처리)
│   ├── cache.py                    # CacheManager (가용성 캐싱)
│   ├── constants.py                # AI 모델 정의 및 설정
│   └── exceptions.py               # 커스텀 예외 계층
└── ai_code_review.py               # 메인 시스템 (의존성 주입)
```

### 5.2 기술 스택

| 컴포넌트 | 기술 |
|----------|------|
| **언어** | Python 3.7+ |
| **의존성** | 표준 라이브러리만 (subprocess, json, dataclasses, concurrent.futures) |
| **AI CLI** | Claude, Gemini, Grok, OpenAI Codex |
| **MCP** | Bitbucket, Jira, Confluence, Slack, Context7 |
| **출력 형식** | Markdown (GitHub-flavored) |

### 5.3 데이터 모델

#### AIModel (from `ai_cli_tools`)
```python
@dataclass
class AIModel:
    name: str                         # 예: "Claude"
    command: List[str]                # 예: ["claude", "-p"]
    display_name: str                 # 예: "Claude (Anthropic)"
    test_command: Optional[List[str]] # 예: ["claude", "--version"]
```

#### ReviewIssue
```python
@dataclass
class ReviewIssue:
    severity: str                     # CRITICAL/MAJOR/MINOR/SUGGESTION
    title: str
    location: str                     # 파일:라인
    description: str
    code_snippet: str
    suggestion: str
    reviewer: str                     # AI 이름
    verified: bool                    # 검증 통과 여부
    verification_notes: List[str]     # 검증 과정 기록
```

#### ReviewContext
```python
@dataclass
class ReviewContext:
    target_path: str
    review_mode: str                  # file/directory/staged/commits/branch
    files: List[str]
    mcp_context: Dict[str, Any]
    git_info: Dict[str, Any]
    max_rounds: int = 3
    allow_early_exit: bool = True
    use_mcp: bool = True
```

### 5.4 핵심 알고리즘

#### AI CLI 감지 알고리즘 (from `ai_cli_tools`)

**2단계 감지**:
1. **Phase 1** (빠른 체크): CLI 설치 확인 (--version, 2초 타임아웃)
2. **Phase 2** (API 체크): 실제 API 호출 테스트 (10초 타임아웃)

**병렬 처리**:
- ThreadPoolExecutor 사용
- 4개 AI CLI를 2-10초 내 확인

#### 이슈 통합 알고리즘

**중복 제거**:
- 같은 파일, 근접한 라인 (±5줄)
- 제목 유사도 70% 이상
- 여러 AI가 발견한 유사 이슈 통합

**우선순위 결정**:
- 심각도: CRITICAL > MAJOR > MINOR > SUGGESTION
- 합의 수: 더 많은 AI가 동의한 이슈 우선
- 검증 통과 여부: verified=True 이슈만 포함

---

## 6. 비기능적 요구사항 (Non-Functional Requirements)

### 6.1 성능 (Performance)

| 요구사항 | 목표 | 측정 |
|----------|------|------|
| AI 감지 시간 | 10초 이내 | 4개 AI CLI 병렬 확인 |
| 파일 리뷰 시간 | 5분 이내 | 1000줄 이하 단일 파일 |
| 캐시 재시작 | 3초 이내 | 캐시 사용 시 |
| 병렬 처리 | Phase 1 병렬 | AI 수만큼 동시 실행 |

### 6.2 확장성 (Scalability)

- 새로운 AI CLI 추가: 설정 파일만 수정
- 파일 수: 1-1000개 처리 가능
- AI 리뷰어 수: 2-10명 지원

### 6.3 안정성 (Reliability)

- AI 호출 실패 시 재시도 (최대 3회)
- AI 타임아웃 처리 (10분)
- MCP 실패 시 graceful degradation
- 캐시 오류 시 자동 재감지

### 6.4 사용성 (Usability)

- 사용자 입력 없이 완전 자동 실행
- 명확한 에러 메시지 및 설치 안내
- 상세한 진행 상황 표시
- 읽기 쉬운 마크다운 출력

### 6.5 보안 (Security)

- 로컬 실행 (외부 서버로 코드 전송 안 함)
- AI CLI의 API 키 관리는 각 CLI가 담당
- 민감 정보 마스킹 권장 (사용자 책임)

### 6.6 유지보수성 (Maintainability)

- 모듈화: `ai_cli_tools` 독립 모듈
- 타입 힌트: 모든 공개 API
- Docstring: Google 스타일
- 의존성 주입: 테스트 용이성

---

## 7. 제약사항 (Constraints)

### 7.1 기술적 제약

| 제약사항 | 설명 | 완화 방법 |
|----------|------|-----------|
| **AI CLI 의존** | 최소 2개의 AI CLI 필요 | 명확한 설치 안내 제공 |
| **API 비용** | AI 호출마다 비용 발생 | 캐싱으로 불필요한 호출 최소화 |
| **처리 시간** | 대용량 코드는 시간 소요 | 병렬 처리 + 조기 종료 |
| **표준 라이브러리만** | 외부 패키지 사용 불가 | subprocess로 AI CLI 호출 |

### 7.2 비즈니스 제약

- **오픈소스**: MIT 라이센스
- **무료 도구**: 추가 유료 서비스 없음
- **로컬 실행**: 클라우드 의존성 없음

---

## 8. 로드맵 (Roadmap)

### Phase 1: MVP (v1.0) - 완료 목표 Q1 2025

- [x] `ai_cli_tools` 모듈 추출 및 모듈화 (ai-discussion에서)
- [ ] AI CLI 자동 감지 시스템
- [ ] 3단계 리뷰 프로세스 (Phase 1-3)
- [ ] 5가지 리뷰 모드
- [ ] 마크다운 문서 생성
- [ ] 캐시 시스템
- [ ] Agent 기본 통합

### Phase 2: Enhancement (v1.1) - 목표 Q2 2025

- [ ] MCP 서버 통합 (Bitbucket, Jira, Confluence)
- [ ] Context7 MCP (라이브러리 문서 자동 참조)
- [ ] 고급 Agent 활용 (Security, Performance)
- [ ] 커스터마이징 옵션 확장
- [ ] 웹 UI (Flask/FastAPI)
- [ ] JSON 출력 지원

### Phase 3: Integration (v1.5) - 목표 Q3 2025

- [ ] Git hooks 통합 (pre-commit, pre-push)
- [ ] CI/CD 파이프라인 통합
- [ ] VSCode 플러그인
- [ ] 리뷰 히스토리 DB (SQLite)
- [ ] 통계 및 트렌드 분석

### Phase 4: Advanced (v2.0) - 목표 Q4 2025

- [ ] 자체 Agent 시스템 구현
- [ ] 리뷰 학습 시스템 (과거 리뷰로부터 학습)
- [ ] 다국어 지원
- [ ] 클라우드 버전 (SaaS)

---

## 9. 의존성 및 통합 (Dependencies & Integrations)

### 9.1 외부 의존성

#### AI CLI 도구
| AI | CLI 명령 | 설치 방법 | 필수 여부 |
|----|----------|-----------|-----------|
| Claude | `claude -p` | npm install -g @anthropic-ai/claude-cli | 최소 2개 필요 |
| Gemini | `gemini -p` | pip install google-generativeai | 최소 2개 필요 |
| Grok | `grok -p` | pip install grok-cli | 최소 2개 필요 |
| OpenAI | `codex exec` | npm install -g @openai/codex-cli | 최소 2개 필요 |

#### MCP 서버 (선택)
- Bitbucket MCP
- Jira MCP
- Confluence MCP
- Context7 MCP
- Slack MCP

### 9.2 내부 모듈

**`ai_cli_tools` 모듈** (from ai-discussion):
- 출처: [ai-discussion](https://github.com/yourusername/ai-discussion) 프로젝트
- 버전: 1.0.0
- 라이센스: MIT
- 기능: AI CLI 자동 감지, 호출, 캐싱, 에러 처리

---

## 10. 위험 및 완화 전략 (Risks & Mitigation)

| 위험 | 영향 | 확률 | 완화 전략 |
|------|------|------|-----------|
| **AI CLI 설치 실패** | Critical | 중간 | 명확한 설치 가이드 + 자동 감지 + 에러 메시지 |
| **AI API 비용 초과** | High | 높음 | 캐싱 + 조기 종료 + 타임아웃 설정 |
| **AI 응답 타임아웃** | Medium | 높음 | 재시도 로직 + 10분 타임아웃 + 병렬 처리 |
| **MCP 서버 연결 실패** | Low | 중간 | Graceful degradation + MCP 없이도 동작 |
| **대용량 코드 처리** | Medium | 중간 | 파일 필터링 + 병렬 처리 + 진행 상황 표시 |
| **False Positive** | Medium | 높음 | 비판적 검증 (Phase 2) + 합의 기반 |

---

## 11. 품질 보증 (Quality Assurance)

### 11.1 테스트 전략

#### 단위 테스트
- `ai_cli_tools` 모듈의 각 컴포넌트
- AI 감지 로직
- 리뷰 통합 알고리즘
- 캐시 관리

#### 통합 테스트
- 전체 리뷰 프로세스 (Phase 1-3)
- MCP 통합
- 파일 생성 및 저장

#### 시스템 테스트
- 다양한 리뷰 모드
- 여러 AI CLI 조합
- 대용량 코드베이스

### 11.2 품질 기준

- **코드 커버리지**: 80% 이상
- **타입 안전성**: 100% 타입 힌트
- **문서화**: 모든 공개 API Docstring
- **코드 스타일**: PEP 8 준수

---

## 12. 문서 (Documentation)

### 12.1 사용자 문서
- [x] **README.md**: 사용자 가이드 및 빠른 시작
- [x] **CLAUDE.md**: 기술 문서 (개발자용)
- [x] **PRD.md**: 제품 요구사항 문서 (본 문서)
- [ ] **CONTRIBUTING.md**: 기여 가이드
- [ ] **CHANGELOG.md**: 버전별 변경사항

### 12.2 기술 문서
- [x] **ai_cli_tools/__init__.py**: 모듈 API 문서
- [ ] **Architecture.md**: 시스템 아키텍처 상세
- [ ] **API.md**: 공개 API 레퍼런스

---

## 13. 릴리스 기준 (Release Criteria)

### v1.0 릴리스 조건

**필수 기능**:
- [x] `ai_cli_tools` 모듈 완성 및 통합
- [ ] AI CLI 자동 감지 (4개 AI 지원)
- [ ] 3단계 리뷰 프로세스 완전 구현
- [ ] 5가지 리뷰 모드 지원
- [ ] 마크다운 문서 생성
- [ ] 캐시 시스템 동작
- [ ] 에러 처리 및 재시도 로직

**품질 기준**:
- [ ] 모든 필수 테스트 통과
- [ ] 문서 작성 완료 (README, CLAUDE, PRD)
- [ ] 최소 3명의 내부 사용자 테스트 완료
- [ ] 성능 기준 충족 (10초 AI 감지, 5분 파일 리뷰)

**운영 준비**:
- [ ] GitHub 리포지토리 공개
- [ ] 이슈 트래커 설정
- [ ] CI/CD 파이프라인 (테스트 자동화)

---

## 14. 부록 (Appendix)

### 14.1 용어 정의

| 용어 | 정의 |
|------|------|
| **AI CLI** | 터미널에서 실행 가능한 AI 명령줄 도구 |
| **Agent** | 특정 작업을 수행하는 전문화된 AI 컴포넌트 |
| **MCP** | Model Context Protocol - AI가 외부 데이터를 참조하는 프로토콜 |
| **Phase 1-3** | 3단계 리뷰 프로세스 (초기 리뷰 → 검증 → 합의) |
| **Verified Issue** | 여러 AI의 검증을 통과한 이슈 |

### 14.2 참고 자료

- [ai-discussion 프로젝트](https://github.com/yourusername/ai-discussion): `ai_cli_tools` 원본 소스
- [Multi-Agent Debate 논문](https://arxiv.org/abs/2305.14325): 다중 AI 검증 이론
- [MCP Specification](https://modelcontextprotocol.io/): MCP 프로토콜 명세
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code): Claude CLI 문서

### 14.3 변경 이력

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 1.0 | 2025-10-31 | 초기 PRD 작성 | AI Code Review Team |

---

## 승인 (Approvals)

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| Product Owner | | | |
| Tech Lead | | | |
| Stakeholder | | | |

---

**문서 상태**: Draft
**다음 리뷰 날짜**: 2025-11-07
**문의**: [프로젝트 이슈 트래커](https://github.com/yourusername/ai-code-review/issues)

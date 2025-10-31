# AI Code Review System - 개발 실행 계획

## 📋 개요

이 문서는 AI Code Review System의 Phase 1 (MVP v1.0) 개발을 위한 상세 실행 계획입니다.
Claude-flow를 통해 단계적으로 구현하며, 각 Feature마다 테스트 우선 개발(TDD)을 수행합니다.

### 참고 문서
- **README.md**: 사용자 가이드 및 기능 개요
- **CLAUDE.md**: 기술 아키텍처 및 구현 상세
- **PRD.md**: 제품 요구사항 및 기능 명세

### 개발 원칙
1. ✅ **테스트 우선**: 각 기능 구현 전 pytest 테스트 작성
2. 🔄 **점진적 구현**: Feature 단위로 개발 및 검증
3. 📝 **문서 동기화**: 구현 완료 시 PRD.md 체크박스 업데이트 후 커밋
4. 👤 **사용자 확인**: 각 Feature 완료 시 사용자 확인 필수
5. 🤖 **Agent 활용**: 적절한 Agent를 병렬로 활용하여 효율성 극대화

---

## 🎯 Phase 1: MVP (v1.0) 개발 계획

### 현재 상태
- [x] `ai_cli_tools` 모듈 완성 (ai-discussion에서 추출 및 조정)
- [x] 프로젝트 구조 설정 (.gitignore, pyproject.toml, requirements-dev.txt)
- [x] 문서 작성 완료 (README.md, CLAUDE.md, PRD.md)

### 구현 대상 Features

```
Phase 1 MVP
├── F1: AI CLI 자동 감지 시스템 ✅ (ai_cli_tools 모듈로 완료)
├── F2: 데이터 모델 구현 (ReviewIssue, ReviewContext)
├── F3: 리뷰 프로세스 엔진 (AICodeReviewSystem)
│   ├── F3-1: Phase 1 - 독립적 초기 리뷰
│   ├── F3-2: Phase 2 - 비판적 검증
│   └── F3-3: Phase 3 - 최종 합의
├── F4: 5가지 리뷰 모드 구현
├── F5: 프롬프트 생성 시스템
├── F6: 마크다운 문서 생성
└── F7: CLI 인터페이스 및 통합
```

---

## 📦 Feature 2: 데이터 모델 구현

### 목표
ReviewIssue와 ReviewContext 데이터 클래스를 구현하여 리뷰 시스템의 핵심 데이터 구조를 정의합니다.

### 구현 사항

#### 파일: `ai_code_review/models.py`

```python
"""리뷰 시스템 데이터 모델"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class Severity(Enum):
    """이슈 심각도"""
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    SUGGESTION = "SUGGESTION"


class ReviewMode(Enum):
    """리뷰 모드"""
    FILE = "file"
    DIRECTORY = "directory"
    STAGED = "staged"
    COMMITS = "commits"
    BRANCH = "branch"


@dataclass
class ReviewIssue:
    """코드 리뷰 이슈

    Attributes:
        severity: 심각도 (CRITICAL/MAJOR/MINOR/SUGGESTION)
        title: 이슈 제목
        location: 파일:라인 형식 (예: "main.py:45-47")
        description: 상세 설명
        code_snippet: 문제가 되는 코드
        suggestion: 개선 제안 (코드 포함)
        reviewer: 발견한 리뷰어 이름 (AI 이름)
        verified: 다른 리뷰어들이 검증했는지 여부
        verification_notes: 검증 과정 기록
    """
    severity: str
    title: str
    location: str
    description: str
    code_snippet: str
    suggestion: str
    reviewer: str
    verified: bool = False
    verification_notes: List[str] = field(default_factory=list)

    def __post_init__(self):
        """데이터 검증"""
        valid_severities = [s.value for s in Severity]
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}. Must be one of {valid_severities}")


@dataclass
class ReviewContext:
    """리뷰 실행 컨텍스트

    Attributes:
        target_path: 리뷰 대상 경로
        review_mode: 리뷰 모드 (file/directory/staged/commits/branch)
        files: 리뷰할 파일 목록
        mcp_context: MCP로부터 수집한 정보
        git_info: Git 관련 정보
        max_rounds: 최대 검증 라운드
        allow_early_exit: 조기 종료 허용 여부
        use_mcp: MCP 사용 여부
        file_extensions: 필터링할 확장자
    """
    target_path: str
    review_mode: str
    files: List[str]
    mcp_context: Dict[str, Any] = field(default_factory=dict)
    git_info: Dict[str, Any] = field(default_factory=dict)
    max_rounds: int = 3
    allow_early_exit: bool = True
    use_mcp: bool = True
    file_extensions: Optional[List[str]] = None

    def __post_init__(self):
        """데이터 검증"""
        valid_modes = [m.value for m in ReviewMode]
        if self.review_mode not in valid_modes:
            raise ValueError(f"Invalid review_mode: {self.review_mode}. Must be one of {valid_modes}")

        if self.max_rounds < 1:
            raise ValueError("max_rounds must be at least 1")
```

### 테스트 구현

#### 파일: `tests/test_models.py`

```python
"""데이터 모델 테스트"""

import pytest
from ai_code_review.models import ReviewIssue, ReviewContext, Severity, ReviewMode


class TestReviewIssue:
    """ReviewIssue 테스트"""

    def test_create_valid_issue(self):
        """정상적인 이슈 생성"""
        issue = ReviewIssue(
            severity="CRITICAL",
            title="SQL Injection",
            location="main.py:45",
            description="SQL 인젝션 취약점",
            code_snippet="query = f'SELECT * FROM users WHERE id={user_id}'",
            suggestion="parameterized query 사용",
            reviewer="claude"
        )

        assert issue.severity == "CRITICAL"
        assert issue.verified is False
        assert len(issue.verification_notes) == 0

    def test_invalid_severity(self):
        """잘못된 심각도 시 에러"""
        with pytest.raises(ValueError, match="Invalid severity"):
            ReviewIssue(
                severity="INVALID",
                title="Test",
                location="test.py:1",
                description="Test",
                code_snippet="test",
                suggestion="test",
                reviewer="test"
            )

    def test_verification_notes(self):
        """검증 노트 추가"""
        issue = ReviewIssue(
            severity="MAJOR",
            title="Test",
            location="test.py:1",
            description="Test",
            code_snippet="test",
            suggestion="test",
            reviewer="claude",
            verification_notes=["검증 1", "검증 2"]
        )

        assert len(issue.verification_notes) == 2


class TestReviewContext:
    """ReviewContext 테스트"""

    def test_create_valid_context(self):
        """정상적인 컨텍스트 생성"""
        context = ReviewContext(
            target_path="./src/main.py",
            review_mode="file",
            files=["./src/main.py"]
        )

        assert context.target_path == "./src/main.py"
        assert context.max_rounds == 3
        assert context.allow_early_exit is True

    def test_invalid_review_mode(self):
        """잘못된 리뷰 모드 시 에러"""
        with pytest.raises(ValueError, match="Invalid review_mode"):
            ReviewContext(
                target_path="./src",
                review_mode="invalid",
                files=[]
            )

    def test_invalid_max_rounds(self):
        """잘못된 max_rounds 시 에러"""
        with pytest.raises(ValueError, match="max_rounds must be at least 1"):
            ReviewContext(
                target_path="./src",
                review_mode="file",
                files=[],
                max_rounds=0
            )

    def test_custom_settings(self):
        """커스텀 설정"""
        context = ReviewContext(
            target_path="./src",
            review_mode="directory",
            files=["./src/a.py", "./src/b.py"],
            max_rounds=5,
            allow_early_exit=False,
            use_mcp=False,
            file_extensions=[".py", ".js"]
        )

        assert context.max_rounds == 5
        assert context.allow_early_exit is False
        assert context.use_mcp is False
        assert ".py" in context.file_extensions
```

### 검증 기준
- [ ] 모든 테스트 통과 (`uv run pytest tests/test_models.py`)
- [ ] 타입 체크 통과 (`uv run mypy ai_code_review/models.py`)
- [ ] Enum 사용으로 타입 안전성 확보
- [ ] 데이터 검증 로직 동작 확인

### Agent 활용
- **Orient Agent**: 데이터 모델 설계 검토
- **Code Review Agent**: 코드 품질 검증

---

## 📦 Feature 3-1: Phase 1 - 독립적 초기 리뷰

### 목표
모든 AI 리뷰어가 병렬로 독립적인 코드 분석을 수행하는 Phase 1을 구현합니다.

### 구현 사항

#### 파일: `ai_code_review/review_engine.py`

```python
"""리뷰 엔진 - Phase 1 구현"""

from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from ai_cli_tools import AIClient, AIModel
from ai_code_review.models import ReviewIssue, ReviewContext
from ai_code_review.prompt_generator import PromptGenerator


class ReviewEngine:
    """코드 리뷰 엔진"""

    def __init__(
        self,
        ai_client: AIClient,
        prompt_generator: PromptGenerator
    ):
        self.ai_client = ai_client
        self.prompt_generator = prompt_generator

    def phase1_initial_review(
        self,
        context: ReviewContext,
        available_ais: Dict[str, AIModel]
    ) -> Dict[str, List[ReviewIssue]]:
        """Phase 1: 독립적 초기 리뷰 (병렬 실행)

        Args:
            context: 리뷰 컨텍스트
            available_ais: 사용 가능한 AI 모델들

        Returns:
            {ai_name: [issues]} 형태의 딕셔너리
        """
        print("\n[Phase 1] 독립적 초기 리뷰 시작...")
        reviews = {}

        # 코드 읽기
        code_content = self._read_files(context.files)

        # 병렬 실행
        with ThreadPoolExecutor(max_workers=len(available_ais)) as executor:
            futures = {}

            for ai_name, ai_model in available_ais.items():
                # 프롬프트 생성
                prompt = self.prompt_generator.generate_initial_review_prompt(
                    context=context,
                    code_content=code_content,
                    ai_name=ai_name
                )

                # Agent 지정
                agents = ["Explore", "Observe", "Orient", "Security", "Performance"]

                # 비동기 실행
                future = executor.submit(
                    self.ai_client.call_ai_with_retry,
                    prompt,
                    ai_model,
                    agents
                )
                futures[future] = ai_name

            # 결과 수집
            for future in as_completed(futures):
                ai_name = futures[future]
                try:
                    response = future.result(timeout=600)
                    issues = self._parse_review_response(response, ai_name)
                    reviews[ai_name] = issues
                    print(f"  ✓ {ai_name}: {len(issues)}개 이슈 발견")
                except Exception as e:
                    print(f"  ✗ {ai_name}: 리뷰 실패 - {e}")
                    reviews[ai_name] = []

        return reviews

    def _read_files(self, files: List[str]) -> Dict[str, str]:
        """파일들 읽기"""
        content = {}
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content[file_path] = f.read()
            except Exception as e:
                print(f"⚠️  파일 읽기 실패 {file_path}: {e}")
                content[file_path] = ""
        return content

    def _parse_review_response(
        self,
        response: str,
        reviewer: str
    ) -> List[ReviewIssue]:
        """AI 응답을 ReviewIssue 리스트로 파싱

        응답 형식:
        [SEVERITY] 이슈 제목
        - 위치: 파일:라인
        - 설명: ...
        - 코드: ...
        - 제안: ...
        """
        issues = []
        # TODO: 파싱 로직 구현
        # 정규식이나 구조화된 파싱 필요
        return issues
```

### 테스트 구현

#### 파일: `tests/test_review_engine_phase1.py`

```python
"""ReviewEngine Phase 1 테스트"""

import pytest
from unittest.mock import Mock, patch
from ai_code_review.review_engine import ReviewEngine
from ai_code_review.models import ReviewContext
from ai_cli_tools import AIClient, AIModel


@pytest.fixture
def mock_ai_client():
    """Mock AI 클라이언트"""
    client = Mock(spec=AIClient)
    client.call_ai_with_retry.return_value = """
[CRITICAL] SQL Injection
- 위치: test.py:10
- 설명: SQL 인젝션 취약점
- 코드: query = f"SELECT * FROM users WHERE id={user_id}"
- 제안: parameterized query 사용
"""
    return client


@pytest.fixture
def mock_prompt_generator():
    """Mock 프롬프트 생성기"""
    generator = Mock()
    generator.generate_initial_review_prompt.return_value = "Review this code..."
    return generator


@pytest.fixture
def review_engine(mock_ai_client, mock_prompt_generator):
    """ReviewEngine 인스턴스"""
    return ReviewEngine(mock_ai_client, mock_prompt_generator)


def test_phase1_initial_review_parallel_execution(review_engine):
    """Phase 1 병렬 실행 테스트"""
    context = ReviewContext(
        target_path="./test.py",
        review_mode="file",
        files=["./tests/fixtures/sample.py"]
    )

    available_ais = {
        "claude": AIModel("Claude", ["claude", "-p"], "Claude (Anthropic)"),
        "gemini": AIModel("Gemini", ["gemini", "-p"], "Gemini (Google)")
    }

    # 파일 읽기 Mock
    with patch.object(review_engine, '_read_files') as mock_read:
        mock_read.return_value = {"./tests/fixtures/sample.py": "def hello(): pass"}

        reviews = review_engine.phase1_initial_review(context, available_ais)

    # 모든 AI가 호출되었는지 확인
    assert len(reviews) == 2
    assert "claude" in reviews
    assert "gemini" in reviews


def test_phase1_handles_ai_failure(review_engine, mock_ai_client):
    """AI 실패 시 처리 테스트"""
    # 하나의 AI는 실패
    mock_ai_client.call_ai_with_retry.side_effect = [
        "Valid response",
        Exception("API Error")
    ]

    context = ReviewContext(
        target_path="./test.py",
        review_mode="file",
        files=["./tests/fixtures/sample.py"]
    )

    available_ais = {
        "claude": AIModel("Claude", ["claude", "-p"], "Claude"),
        "gemini": AIModel("Gemini", ["gemini", "-p"], "Gemini")
    }

    with patch.object(review_engine, '_read_files') as mock_read:
        mock_read.return_value = {"test.py": "code"}

        reviews = review_engine.phase1_initial_review(context, available_ais)

    # 성공한 AI의 리뷰만 포함
    assert len(reviews) == 2
    assert reviews["gemini"] == []  # 실패한 경우 빈 리스트
```

### 검증 기준
- [ ] 병렬 실행 동작 확인
- [ ] AI 호출 실패 시 graceful degradation
- [ ] 프롬프트 생성 및 Agent 지정 확인
- [ ] 모든 테스트 통과

### Agent 활용
- **Backend Developer Agent**: 리뷰 엔진 구현
- **Test Engineer**: 테스트 코드 작성

---

## 📦 Feature 3-2: Phase 2 - 비판적 검증

### 목표
각 AI가 다른 AI의 리뷰를 비판적으로 검증하는 Phase 2를 구현합니다.

### 구현 사항

#### 파일: `ai_code_review/review_engine.py` (추가)

```python
def phase2_critical_verification(
    self,
    context: ReviewContext,
    initial_reviews: Dict[str, List[ReviewIssue]],
    available_ais: Dict[str, AIModel]
) -> List[Dict]:
    """Phase 2: 비판적 검증 (순차 라운드)

    Args:
        context: 리뷰 컨텍스트
        initial_reviews: Phase 1 결과
        available_ais: 사용 가능한 AI 모델들

    Returns:
        라운드별 검증 기록
    """
    print("\n[Phase 2] 비판적 검증 시작...")
    verification_history = []

    for round_num in range(1, context.max_rounds + 1):
        print(f"\n  Round {round_num}/{context.max_rounds}")
        round_verifications = {}

        for ai_name, ai_model in available_ais.items():
            # 자신을 제외한 다른 AI들의 리뷰
            other_reviews = {
                name: issues
                for name, issues in initial_reviews.items()
                if name != ai_name
            }

            # 검증 프롬프트 생성
            prompt = self.prompt_generator.generate_verification_prompt(
                ai_name=ai_name,
                own_reviews=initial_reviews.get(ai_name, []),
                other_reviews=other_reviews,
                round_num=round_num
            )

            # Agent 지정
            agents = ["Explore", "Observe", "Orient"]

            # AI 호출
            try:
                response = self.ai_client.call_ai_with_retry(
                    prompt,
                    ai_model,
                    agents
                )

                verification = self._parse_verification_response(response)
                round_verifications[ai_name] = verification

                # 검증 결과를 원본 이슈에 반영
                self._apply_verification_results(initial_reviews, verification)

                print(f"    ✓ {ai_name}: 검증 완료")
            except Exception as e:
                print(f"    ✗ {ai_name}: 검증 실패 - {e}")

        verification_history.append({
            "round": round_num,
            "verifications": round_verifications
        })

        # 조기 종료 체크 (최소 2라운드 후)
        if round_num >= 2 and context.allow_early_exit:
            if self._check_all_consensus_ready(available_ais, verification_history):
                print(f"\n  ✓ 모든 리뷰어가 합의 준비 완료 (Round {round_num})")
                break

    return verification_history

def _parse_verification_response(self, response: str) -> Dict:
    """검증 응답 파싱"""
    # TODO: 구현
    return {
        "agreed": [],
        "disagreed": [],
        "severity_adjustments": []
    }

def _apply_verification_results(
    self,
    reviews: Dict[str, List[ReviewIssue]],
    verification: Dict
) -> None:
    """검증 결과를 이슈에 반영"""
    # TODO: 구현
    pass

def _check_all_consensus_ready(
    self,
    available_ais: Dict[str, AIModel],
    history: List[Dict]
) -> bool:
    """모든 AI가 합의 준비되었는지 확인"""
    # TODO: 각 AI에게 YES/NO 질문
    return False
```

### 테스트 구현

#### 파일: `tests/test_review_engine_phase2.py`

```python
"""ReviewEngine Phase 2 테스트"""

import pytest
from ai_code_review.review_engine import ReviewEngine
from ai_code_review.models import ReviewIssue, ReviewContext


def test_phase2_verification_rounds():
    """검증 라운드 실행 테스트"""
    # TODO: 구현
    pass


def test_phase2_early_exit():
    """조기 종료 테스트"""
    # TODO: 구현
    pass


def test_phase2_verification_application():
    """검증 결과 반영 테스트"""
    # TODO: 구현
    pass
```

### 검증 기준
- [ ] 순차 라운드 실행 확인
- [ ] 검증 결과 파싱 및 반영
- [ ] 조기 종료 로직 동작
- [ ] 모든 테스트 통과

---

## 📦 Feature 3-3: Phase 3 - 최종 합의

### 목표
검증된 이슈들을 통합하여 최종 합의 리뷰를 생성하는 Phase 3를 구현합니다.

### 구현 사항

#### 파일: `ai_code_review/review_engine.py` (추가)

```python
def phase3_final_consensus(
    self,
    context: ReviewContext,
    initial_reviews: Dict[str, List[ReviewIssue]],
    verification_history: List[Dict],
    available_ais: Dict[str, AIModel]
) -> Dict[str, Any]:
    """Phase 3: 최종 합의 생성

    Args:
        context: 리뷰 컨텍스트
        initial_reviews: Phase 1 결과
        verification_history: Phase 2 검증 기록
        available_ais: 사용 가능한 AI 모델들

    Returns:
        통합된 최종 리뷰
    """
    print("\n[Phase 3] 최종 합의 생성 중...")

    # 1. 검증된 이슈만 필터링
    verified_issues = self._filter_verified_issues(initial_reviews)

    # 2. 유사 이슈 통합
    merged_issues = self._merge_similar_issues(verified_issues)

    # 3. 우선순위 정렬
    sorted_issues = self._sort_by_priority(merged_issues)

    # 4. 통합 요약 생성 (AI 활용)
    summary = self._generate_summary(sorted_issues, available_ais)

    # 5. 통계 생성
    statistics = self._calculate_statistics(sorted_issues)

    final_review = {
        "summary": summary,
        "issues": sorted_issues,
        "statistics": statistics,
        "context": context,
        "verification_history": verification_history
    }

    print("  ✓ 통합 리뷰 문서 생성 완료")

    return final_review
```

### 검증 기준
- [ ] 검증된 이슈만 포함
- [ ] 유사 이슈 통합 로직 동작
- [ ] 우선순위 정렬 정확성
- [ ] 통합 요약 생성
- [ ] 모든 테스트 통과

---

## 📦 Feature 4: 5가지 리뷰 모드

### 목표
파일, 디렉토리, staged, commits, branch 5가지 리뷰 모드를 구현합니다.

### 구현 사항

#### 파일: `ai_code_review/file_analyzer.py`

```python
"""파일 분석 및 Git 통합"""

from typing import List, Dict, Any
from pathlib import Path
import subprocess
from ai_code_review.models import ReviewContext, ReviewMode


class FileAnalyzer:
    """파일 및 Git 분석"""

    def analyze_target(self, context: ReviewContext) -> None:
        """리뷰 대상 분석 및 파일 목록 수집"""
        if context.review_mode == ReviewMode.FILE.value:
            self._analyze_file(context)
        elif context.review_mode == ReviewMode.DIRECTORY.value:
            self._analyze_directory(context)
        elif context.review_mode == ReviewMode.STAGED.value:
            self._analyze_staged(context)
        elif context.review_mode == ReviewMode.COMMITS.value:
            self._analyze_commits(context)
        elif context.review_mode == ReviewMode.BRANCH.value:
            self._analyze_branch(context)

    def _analyze_file(self, context: ReviewContext) -> None:
        """단일 파일 분석"""
        if Path(context.target_path).is_file():
            context.files = [context.target_path]
        else:
            raise FileNotFoundError(f"File not found: {context.target_path}")

    def _analyze_directory(self, context: ReviewContext) -> None:
        """디렉토리 분석"""
        path = Path(context.target_path)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {context.target_path}")

        # 파일 수집 (확장자 필터링)
        files = []
        for file_path in path.rglob("*"):
            if file_path.is_file():
                if self._should_include_file(file_path, context.file_extensions):
                    files.append(str(file_path))

        context.files = files

    def _analyze_staged(self, context: ReviewContext) -> None:
        """Staged 변경사항 분석"""
        try:
            # git diff --cached --name-only
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )

            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            context.files = files
            context.git_info["mode"] = "staged"
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git staged 분석 실패: {e}")

    def _analyze_commits(self, context: ReviewContext) -> None:
        """커밋 범위 분석"""
        # TODO: git diff <range> --name-only
        pass

    def _analyze_branch(self, context: ReviewContext) -> None:
        """브랜치 변경사항 분석"""
        # TODO: git diff <base>...<current> --name-only
        pass

    def _should_include_file(
        self,
        file_path: Path,
        extensions: List[str] = None
    ) -> bool:
        """파일 포함 여부 확인"""
        if extensions is None:
            return True
        return file_path.suffix in extensions
```

### 테스트 구현

테스트는 각 리뷰 모드별로 작성합니다.

### 검증 기준
- [ ] 5가지 리뷰 모드 모두 동작
- [ ] Git 명령 정확성
- [ ] 파일 필터링 정확성
- [ ] 모든 테스트 통과

---

## 📦 Feature 5: 프롬프트 생성 시스템

### 목표
각 Phase별로 AI에게 전달할 프롬프트를 생성하는 시스템을 구현합니다.

### 구현 사항

#### 파일: `ai_code_review/prompt_generator.py`

```python
"""프롬프트 생성 시스템"""

from typing import Dict, List, Any
from ai_code_review.models import ReviewIssue, ReviewContext


class PromptGenerator:
    """AI 프롬프트 생성기"""

    def generate_initial_review_prompt(
        self,
        context: ReviewContext,
        code_content: Dict[str, str],
        ai_name: str
    ) -> str:
        """Phase 1 초기 리뷰 프롬프트"""
        # TODO: CLAUDE.md의 프롬프트 템플릿 구현
        pass

    def generate_verification_prompt(
        self,
        ai_name: str,
        own_reviews: List[ReviewIssue],
        other_reviews: Dict[str, List[ReviewIssue]],
        round_num: int
    ) -> str:
        """Phase 2 검증 프롬프트"""
        # TODO: CLAUDE.md의 검증 프롬프트 구현
        pass

    def generate_consensus_prompt(
        self,
        all_reviews: Dict[str, List[ReviewIssue]],
        verification_history: List[Dict]
    ) -> str:
        """Phase 3 합의 프롬프트"""
        # TODO: CLAUDE.md의 합의 프롬프트 구현
        pass
```

### 검증 기준
- [ ] 프롬프트에 Agent 사용 지시 포함
- [ ] MCP 컨텍스트 포함
- [ ] 명확한 출력 형식 지시
- [ ] 모든 테스트 통과

---

## 📦 Feature 6: 마크다운 문서 생성

### 목표
리뷰 결과를 마크다운 형식으로 저장하는 시스템을 구현합니다.

### 구현 사항

#### 파일: `ai_code_review/markdown_generator.py`

```python
"""마크다운 문서 생성"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from ai_code_review.models import ReviewIssue, ReviewContext


class MarkdownGenerator:
    """마크다운 문서 생성기"""

    def save_review_files(
        self,
        context: ReviewContext,
        initial_reviews: Dict[str, List[ReviewIssue]],
        verification_history: List[Dict],
        final_review: Dict[str, Any]
    ) -> tuple[str, str]:
        """리뷰 문서 저장

        Returns:
            (전체 리뷰 경로, 최종 리뷰 경로)
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_name = self._get_base_filename(context.target_path)

        # 1. 전체 리뷰 기록
        full_path = f"{base_name}-review-{timestamp}.md"
        with open(full_path, 'w', encoding='utf-8') as f:
            content = self._format_full_review(
                context,
                initial_reviews,
                verification_history,
                final_review,
                timestamp
            )
            f.write(content)

        # 2. 최종 통합 리뷰
        final_path = f"{base_name}-final-review-{timestamp}.md"
        with open(final_path, 'w', encoding='utf-8') as f:
            content = self._format_final_review(
                context,
                final_review,
                timestamp
            )
            f.write(content)

        return (full_path, final_path)

    def _format_full_review(self, ...) -> str:
        """전체 리뷰 마크다운 생성"""
        # TODO: README.md의 예시 참조
        pass

    def _format_final_review(self, ...) -> str:
        """최종 리뷰 마크다운 생성"""
        # TODO: README.md의 예시 참조
        pass
```

### 검증 기준
- [ ] 2개 파일 정상 생성
- [ ] 마크다운 형식 정확성
- [ ] 코드 스니펫 포함
- [ ] 모든 테스트 통과

---

## 📦 Feature 7: CLI 인터페이스 및 통합

### 목표
argparse를 사용한 CLI 인터페이스를 구현하고 모든 컴포넌트를 통합합니다.

### 구현 사항

#### 파일: `ai_code_review.py`

```python
"""AI Code Review System - 메인 진입점"""

import argparse
import sys
from pathlib import Path
from ai_cli_tools import AIClient, ModelManager, CacheManager
from ai_cli_tools.constants import CACHE_FILE
from ai_code_review.models import ReviewContext
from ai_code_review.review_engine import ReviewEngine
from ai_code_review.file_analyzer import FileAnalyzer
from ai_code_review.prompt_generator import PromptGenerator
from ai_code_review.markdown_generator import MarkdownGenerator


def parse_arguments() -> argparse.Namespace:
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="AI Code Review System - 다중 AI 코드 리뷰",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # 리뷰 대상
    parser.add_argument(
        "target",
        nargs="?",
        help="리뷰할 파일 또는 디렉토리 경로"
    )

    # 리뷰 모드
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--staged", action="store_true")
    mode_group.add_argument("--commits", metavar="RANGE")
    mode_group.add_argument("--branch", action="store_true")

    # 옵션
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--only", metavar="AI_LIST")
    parser.add_argument("--no-mcp", action="store_true")
    parser.add_argument("--extensions", metavar="EXT_LIST")
    parser.add_argument("--no-early-exit", action="store_true")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--verbose", action="store_true")

    return parser.parse_args()


def main():
    """메인 함수"""
    args = parse_arguments()

    # 배너 출력
    print_banner()

    try:
        # 1. AI CLI 초기화
        cache_manager = CacheManager(CACHE_FILE)
        model_manager = ModelManager(cache_manager)
        model_manager.initialize_models(force_refresh=args.force_refresh)
        available_ais = model_manager.get_available_models()

        # 2. AI 필터링 (--only 옵션)
        if args.only:
            specified = set(args.only.split(","))
            available_ais = {k: v for k, v in available_ais.items() if k in specified}

        # 3. 컨텍스트 생성
        context = create_review_context(args)

        # 4. 파일 분석
        file_analyzer = FileAnalyzer()
        file_analyzer.analyze_target(context)

        # 5. 리뷰 실행
        ai_client = AIClient()
        prompt_generator = PromptGenerator()
        review_engine = ReviewEngine(ai_client, prompt_generator)

        initial_reviews = review_engine.phase1_initial_review(context, available_ais)
        verification_history = review_engine.phase2_critical_verification(
            context,
            initial_reviews,
            available_ais
        )
        final_review = review_engine.phase3_final_consensus(
            context,
            initial_reviews,
            verification_history,
            available_ais
        )

        # 6. 문서 저장
        markdown_gen = MarkdownGenerator()
        full_path, final_path = markdown_gen.save_review_files(
            context,
            initial_reviews,
            verification_history,
            final_review
        )

        # 7. 성공 메시지
        print_success(full_path, final_path, final_review)

    except KeyboardInterrupt:
        print("\n\n리뷰가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 검증 기준
- [ ] 모든 명령줄 옵션 동작
- [ ] 에러 처리 정상 동작
- [ ] 전체 플로우 통합 테스트 통과
- [ ] 실제 AI CLI로 E2E 테스트 성공

---

## 🔄 개발 워크플로우

### 각 Feature 개발 순서

1. **테스트 작성** (TDD)
   ```bash
   # 테스트 파일 생성
   vi tests/test_<feature>.py

   # 실패 확인
   uv run pytest tests/test_<feature>.py
   ```

2. **구현**
   ```bash
   # 코드 작성
   vi ai_code_review/<module>.py

   # 테스트 통과 확인
   uv run pytest tests/test_<feature>.py
   ```

3. **품질 검증**
   ```bash
   # 타입 체크
   uv run mypy ai_code_review/<module>.py

   # 포맷 체크
   uv run black --check ai_code_review/<module>.py

   # Lint
   uv run ruff check ai_code_review/<module>.py
   ```

4. **PRD 업데이트 및 커밋**
   ```bash
   # PRD.md에서 체크박스 업데이트
   vi PRD.md  # - [x] Feature X 완료

   # 커밋
   git add .
   git commit -m "feat: Feature X 구현 완료

   - 테스트 통과: test_<feature>.py
   - 타입 체크 통과
   - PRD.md 업데이트

   Closes #<issue_number>"
   ```

5. **사용자 확인 대기**

---

## 📋 체크리스트

### Phase 1 MVP 완료 조건

#### 기능 구현
- [x] F1: AI CLI 자동 감지 (`ai_cli_tools` 완료)
- [ ] F2: 데이터 모델 (ReviewIssue, ReviewContext)
- [ ] F3-1: Phase 1 - 독립적 초기 리뷰
- [ ] F3-2: Phase 2 - 비판적 검증
- [ ] F3-3: Phase 3 - 최종 합의
- [ ] F4: 5가지 리뷰 모드
- [ ] F5: 프롬프트 생성 시스템
- [ ] F6: 마크다운 문서 생성
- [ ] F7: CLI 인터페이스 및 통합

#### 테스트
- [ ] 모든 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] E2E 테스트 통과 (실제 AI CLI 사용)
- [ ] 테스트 커버리지 80% 이상

#### 품질
- [ ] 타입 힌트 100%
- [ ] Docstring 모든 공개 API
- [ ] 코드 포맷 (black) 통과
- [ ] Lint (ruff) 통과

#### 문서
- [x] README.md 작성 완료
- [x] CLAUDE.md 작성 완료
- [x] PRD.md 작성 완료
- [ ] 모든 체크박스 업데이트

---

## 🤖 Agent 활용 전략

### Feature별 Agent 매핑

| Feature | 주 Agent | 보조 Agent |
|---------|----------|-----------|
| F2: 데이터 모델 | Orient Agent | Code Review Agent |
| F3-1: Phase 1 | Backend Developer | Test Engineer |
| F3-2: Phase 2 | Backend Developer | Security Agent |
| F3-3: Phase 3 | Backend Developer | Orient Agent |
| F4: 리뷰 모드 | Backend Developer | - |
| F5: 프롬프트 | Technical Writer | Orient Agent |
| F6: 마크다운 | Frontend Developer | Technical Writer |
| F7: CLI 통합 | Fullstack Developer | - |

### 병렬 실행 가능 작업

- F2와 F4는 독립적이므로 병렬 가능
- F5와 F6는 독립적이므로 병렬 가능
- 테스트 작성과 문서 작성은 병렬 가능

---

## 📝 커밋 메시지 규칙

```
<type>: <subject>

<body>

<footer>
```

### Type
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `test`: 테스트 추가/수정
- `docs`: 문서 수정
- `refactor`: 리팩토링
- `style`: 코드 포맷 변경

### 예시
```
feat: ReviewIssue 및 ReviewContext 데이터 모델 구현

- Enum을 사용한 타입 안전성 확보
- 데이터 검증 로직 추가
- 테스트 전체 통과 (tests/test_models.py)
- 타입 체크 통과

Closes #2
```

---

## 🚀 시작하기

```bash
# 1. 개발 환경 설정
uv venv
source .venv/bin/activate
uv pip install -r requirements-dev.txt

# 2. 첫 번째 Feature 시작
# Feature 2: 데이터 모델 구현
vi tests/test_models.py  # 테스트 먼저 작성
uv run pytest tests/test_models.py  # 실패 확인

mkdir -p ai_code_review
vi ai_code_review/models.py  # 구현
uv run pytest tests/test_models.py  # 통과 확인

# 3. PRD 업데이트 및 커밋
vi PRD.md  # Feature 2 체크
git add .
git commit -m "feat: ReviewIssue 및 ReviewContext 구현"

# 4. 사용자에게 확인 요청
```

---

**다음 단계**: Feature 2 (데이터 모델) 구현부터 시작합니다.

# CLI Usage Guide

## Overview

`ai_review.py`는 AI Code Review System의 메인 CLI 진입점입니다. 이 문서는 CLI의 모든 기능과 사용 방법을 설명합니다.

## 기본 사용법

```bash
python ai_review.py <대상> [옵션]
```

## 리뷰 모드

### 1. 파일 리뷰

단일 파일을 리뷰합니다.

```bash
python ai_review.py ./src/main.py
```

**특징**:
- 파일 전체를 상세히 분석
- 모든 AI가 독립적으로 리뷰 수행
- 가장 깊이 있는 분석 가능

### 2. 디렉토리 리뷰

디렉토리 내 모든 파일을 리뷰합니다.

```bash
python ai_review.py ./src/
```

**옵션**:
- `--extensions`: 특정 확장자만 리뷰

```bash
# Python 파일만 리뷰
python ai_review.py ./src/ --extensions .py

# Python과 JavaScript 파일 리뷰
python ai_review.py ./src/ --extensions .py,.js
```

### 3. Staged 변경사항 리뷰

Git staged된 파일들을 리뷰합니다 (PR 생성 전 리뷰에 유용).

```bash
python ai_review.py --staged
```

**사용 시나리오**:
```bash
# 1. 코드 작성 및 staged
git add src/main.py src/helper.py

# 2. 커밋 전 리뷰
python ai_review.py --staged

# 3. 리뷰 결과 확인 후 커밋
git commit -m "Add feature X"
```

### 4. 커밋 범위 리뷰

특정 커밋 범위의 변경사항을 리뷰합니다.

```bash
# 최근 3개 커밋 리뷰
python ai_review.py --commits HEAD~3..HEAD

# 특정 커밋 범위
python ai_review.py --commits abc123..def456
```

### 5. 브랜치 리뷰

현재 브랜치의 모든 변경사항을 리뷰합니다 (main 브랜치 기준).

```bash
python ai_review.py --branch
```

## 주요 옵션

### AI 관련 옵션

#### `--only AI_LIST`

특정 AI만 사용하여 리뷰를 수행합니다.

```bash
# Claude와 Gemini만 사용
python ai_review.py ./src/main.py --only claude,gemini

# Claude만 사용 (테스트용)
python ai_review.py ./src/main.py --only claude
```

**주의**: 최소 2개의 AI가 필요합니다.

#### `--force-refresh`

AI CLI 캐시를 무시하고 재감지합니다.

```bash
python ai_review.py ./src/main.py --force-refresh
```

**사용 시나리오**:
- 새로운 AI CLI를 설치한 후
- 캐시 오류가 의심될 때

### 리뷰 프로세스 옵션

#### `--max-rounds N`

Phase 2 검증 라운드의 최대 횟수를 지정합니다 (기본값: 3).

```bash
# 더 철저한 검증을 위해 5라운드
python ai_review.py ./src/main.py --max-rounds 5

# 빠른 리뷰를 위해 1라운드
python ai_review.py ./src/main.py --max-rounds 1
```

**권장 값**:
- 간단한 리뷰: 1-2 라운드
- 일반 리뷰: 3 라운드 (기본값)
- 중요한 리뷰: 5 라운드

#### `--no-early-exit`

조기 종료를 비활성화하고 모든 라운드를 실행합니다.

```bash
python ai_review.py ./src/main.py --no-early-exit
```

**사용 시나리오**:
- 최대한 많은 검증이 필요할 때
- Phase 2 과정을 완전히 관찰하고 싶을 때

### 통합 옵션

#### `--no-mcp`

MCP 서버 사용을 비활성화합니다.

```bash
python ai_review.py ./src/main.py --no-mcp
```

**사용 시나리오**:
- MCP 서버가 설정되지 않았을 때
- MCP 없이 빠른 리뷰를 원할 때

#### `--extensions EXT_LIST`

특정 파일 확장자만 리뷰합니다.

```bash
# Python 파일만
python ai_review.py ./src/ --extensions .py

# Python, JavaScript, TypeScript 파일
python ai_review.py ./src/ --extensions .py,.js,.ts
```

### 기타 옵션

#### `-v, --verbose`

상세 출력 모드를 활성화합니다.

```bash
python ai_review.py ./src/main.py -v
```

**출력 내용**:
- AI 호출 세부 정보
- 파일 읽기 상세 로그
- 에러 스택트레이스

## 실전 예시

### 예시 1: PR 생성 전 리뷰

```bash
# 1. 변경사항 staged
git add .

# 2. staged 변경사항 리뷰
python ai_review.py --staged

# 3. 리뷰 결과 확인
cat *-final-review-*.md

# 4. 문제 수정 후 다시 리뷰
python ai_review.py --staged

# 5. 문제가 없으면 커밋
git commit -m "Feature: Add user authentication"
```

### 예시 2: 특정 모듈 집중 리뷰

```bash
# 보안 모듈만 Python 파일 리뷰
python ai_review.py ./src/security/ --extensions .py --max-rounds 5

# Claude와 Gemini만 사용 (보안 전문)
python ai_review.py ./src/security/ --only claude,gemini --max-rounds 5
```

### 예시 3: 브랜치 전체 리뷰

```bash
# feature 브랜치의 모든 변경사항 리뷰
git checkout feature/user-auth
python ai_review.py --branch

# main과의 차이 리뷰
python ai_review.py --commits main..HEAD
```

### 예시 4: 빠른 리뷰 (개발 중)

```bash
# 조기 종료 활성화, 1라운드만
python ai_review.py ./src/main.py --max-rounds 1

# MCP 없이 빠르게
python ai_review.py ./src/main.py --no-mcp --max-rounds 1
```

### 예시 5: 철저한 리뷰 (릴리스 전)

```bash
# 모든 라운드 실행, 조기 종료 없음
python ai_review.py ./src/ --max-rounds 5 --no-early-exit --extensions .py

# 상세 로그와 함께
python ai_review.py ./src/ --max-rounds 5 --no-early-exit -v
```

## 출력 파일

리뷰 완료 후 2개의 마크다운 파일이 생성됩니다:

### 1. 전체 리뷰 기록 (`<파일명>-review-<타임스탬프>.md`)

Phase 1-3 전체 과정이 기록된 파일입니다.

**내용**:
- Phase 1: 각 AI의 독립적 리뷰
- Phase 2: 라운드별 검증 과정
- Phase 3: 최종 합의

**용도**:
- 리뷰 과정 전체를 이해하고 싶을 때
- AI들의 논의 과정을 확인하고 싶을 때

### 2. 최종 합의 리뷰 (`<파일명>-final-review-<타임스탬프>.md`)

Phase 3 최종 합의만 포함된 파일입니다.

**내용**:
- 리뷰 요약 (통계)
- 합의된 이슈들 (Critical → Suggestion 순)
- 각 이슈의 상세 정보

**용도**:
- 바로 수정할 이슈 확인
- 팀과 공유할 리뷰 결과
- PR 코멘트 작성 참고

## 에러 처리

### AI CLI가 없을 때

```
❌ 오류 발생: 사용 가능한 AI CLI가 없습니다. 최소 2개 이상의 AI CLI를 설치해주세요.
설치 방법: https://github.com/yourusername/ai-code-review#requirements
```

**해결 방법**: AI CLI 설치

### 파일이 없을 때

```
❌ 오류 발생: 대상을 찾을 수 없습니다: ./nonexistent.py
```

**해결 방법**: 경로 확인

### Git 명령 실패

```
❌ 오류 발생: Git staged 분석 실패: ...
```

**해결 방법**:
- Git 저장소인지 확인
- staged된 파일이 있는지 확인

## 성능 최적화

### 빠른 리뷰를 위한 팁

1. **파일 수 제한**: `--extensions`로 필요한 파일만
2. **라운드 수 감소**: `--max-rounds 1`
3. **MCP 비활성화**: `--no-mcp`
4. **특정 AI만 사용**: `--only claude,gemini`

```bash
# 최고 속도 설정
python ai_review.py ./src/main.py --no-mcp --max-rounds 1 --only claude
```

### 철저한 리뷰를 위한 팁

1. **라운드 수 증가**: `--max-rounds 5`
2. **조기 종료 비활성화**: `--no-early-exit`
3. **모든 AI 사용**: `--only` 옵션 제거
4. **상세 로그**: `-v`

```bash
# 최고 품질 설정
python ai_review.py ./src/ --max-rounds 5 --no-early-exit -v
```

## 워크플로우 통합

### Pre-commit Hook

`.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Running AI Code Review..."
python ai_review.py --staged --max-rounds 1 --no-mcp

# 리뷰 결과 확인 (사용자 선택)
read -p "Continue with commit? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi
```

### CI/CD 통합

`.github/workflows/code-review.yml`:

```yaml
name: AI Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: AI Code Review
        run: |
          python ai_review.py --branch
      - name: Upload Review
        uses: actions/upload-artifact@v2
        with:
          name: code-review
          path: "*-final-review-*.md"
```

## 자주 묻는 질문

### Q: 리뷰 시간이 얼마나 걸리나요?

**A**: 파일 크기와 AI 수에 따라 다릅니다:
- 단일 파일 (100-500줄): 3-5분
- 디렉토리 (10개 파일): 10-15분
- 대규모 프로젝트: 30분 이상

### Q: 어떤 AI를 사용해야 하나요?

**A**: 사용 가능한 모든 AI를 사용하는 것이 좋습니다. 더 많은 관점을 얻을 수 있습니다.

### Q: 리뷰 결과가 정확한가요?

**A**: Phase 2 검증을 통해 정확도를 높이지만, 최종 판단은 개발자가 해야 합니다.

### Q: 리뷰 비용이 얼마나 드나요?

**A**: AI CLI의 API 비용이 발생합니다. 캐싱과 조기 종료로 비용을 최소화할 수 있습니다.

## 문제 해결

### 캐시 초기화

```bash
rm .ai_code_review_cache.json
python ai_review.py --force-refresh
```

### 상세 로그 확인

```bash
python ai_review.py ./src/main.py -v
```

### 특정 Phase만 테스트

현재는 전체 프로세스만 지원됩니다. 향후 버전에서 개별 Phase 실행을 지원할 예정입니다.

## 피드백 및 지원

- GitHub Issues: https://github.com/yourusername/ai-code-review/issues
- 문서: https://github.com/yourusername/ai-code-review/blob/main/README.md

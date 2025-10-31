# Quick Start Guide

## 5분 만에 시작하기

### 1. 설치 확인

```bash
cd /Users/hanson/PycharmProjects/ai-code-review
ls ai_review.py  # CLI 진입점 확인
```

### 2. 샘플 코드 리뷰

```bash
# 샘플 코드 리뷰 (데모)
python ai_review.py ./examples/sample_code.py
```

**주의**: 실제 AI CLI가 설치되어 있어야 합니다.

### 3. 결과 확인

리뷰 완료 후 생성된 파일 확인:

```bash
ls *-final-review-*.md
cat sample_code-final-review-*.md
```

## 일반적인 사용 패턴

### 패턴 1: PR 생성 전 리뷰

```bash
# 1. 변경사항 staged
git add .

# 2. 리뷰 실행
python ai_review.py --staged

# 3. 결과 확인
cat *-final-review-*.md

# 4. 문제 수정 후 커밋
git commit -m "Feature: Add authentication"
```

### 패턴 2: 특정 파일 집중 리뷰

```bash
# 보안이 중요한 파일 리뷰
python ai_review.py ./src/auth.py --max-rounds 5
```

### 패턴 3: 디렉토리 전체 리뷰

```bash
# Python 파일만 리뷰
python ai_review.py ./src/ --extensions .py
```

## 자주 사용하는 옵션

```bash
# 빠른 리뷰 (1라운드)
python ai_review.py ./file.py --max-rounds 1

# 철저한 리뷰 (5라운드, 조기 종료 없음)
python ai_review.py ./file.py --max-rounds 5 --no-early-exit

# 특정 AI만 사용
python ai_review.py ./file.py --only claude,gemini

# 상세 로그
python ai_review.py ./file.py -v
```

## 출력 파일

### 1. 전체 리뷰 기록 (`*-review-*.md`)
- Phase 1-3 전체 과정
- AI들의 논의 내용
- 검증 과정 상세

### 2. 최종 합의 리뷰 (`*-final-review-*.md`)
- **이 파일을 먼저 확인하세요!**
- 합의된 이슈만 포함
- Critical → Suggestion 순 정렬
- 바로 적용 가능

## 도움말

```bash
# 전체 옵션 보기
python ai_review.py --help

# 상세 사용법
cat docs/CLI_USAGE.md
```

## 문제 해결

### AI CLI가 없다고 나올 때

```bash
# AI CLI 설치 필요 (최소 2개)
# - Claude CLI
# - Gemini CLI
# - Grok CLI
# - OpenAI Codex CLI
```

### 파일을 찾을 수 없을 때

```bash
# 경로 확인
ls ./src/main.py

# 절대 경로 사용
python ai_review.py /full/path/to/file.py
```

### Git 명령 실패 시

```bash
# Git 저장소 확인
git status

# staged 파일 확인
git diff --cached --name-only
```

## 다음 단계

1. ✅ 샘플 코드로 테스트
2. 📖 [CLI Usage Guide](./CLI_USAGE.md) 읽기
3. 🚀 실제 프로젝트에 적용
4. 📝 피드백 제공

---

**즐거운 코드 리뷰 되세요!** 🎉

# 대규모 리뷰 문제 해결 가이드

## 🐛 문제 상황

### 증상
```bash
$ ai-review --branch develop

⚠️  Gemini 오류 발생, 재시도 중... (1/3)
⚠️  Gemini 오류 발생, 재시도 중... (2/3)
⚠️  OpenAI 오류 발생, 재시도 중... (1/3)
⚠️  Claude 오류 발생, 재시도 중... (1/3)
```

모든 AI가 동시에 실패하고 재시도를 반복합니다.

### 근본 원인

1. **프롬프트 크기 초과**
   - 76개 파일을 한 번에 리뷰 시도
   - 전체 코드를 프롬프트에 포함 → 수십만 토큰 생성
   - AI 모델의 컨텍스트 제한 초과:
     - Claude: 200K 토큰
     - GPT-4: 128K 토큰
     - Gemini: 1M 토큰 (하지만 레이트 제한 존재)

2. **빈 파일 포함**
   - 삭제된 26개 파일이 프롬프트에 포함됨
   - 파일 목록에는 있지만 내용은 비어있음
   - 불필요한 프롬프트 크기 증가

3. **에러 메시지 부족**
   - 실제 오류 내용이 숨겨짐
   - "⚠️ 오류 발생" 만 표시
   - 디버깅 불가능

---

## ✅ 해결 방법

### v1.1.0 업데이트 적용 사항

#### 1. 에러 로깅 개선
```bash
# 이전 (v1.0.0)
⚠️  Gemini 오류 발생, 재시도 중... (1/3)

# 개선 (v1.1.0)
⚠️  Gemini 오류 발생, 재시도 중... (1/3)
    오류 내용: Request payload too large: 245,823 tokens exceeds limit of 200,000
    프롬프트 크기: 983,292 문자, 12,456 줄
```

이제 실제 오류 원인을 확인할 수 있습니다!

#### 2. 자동 빈 파일 필터링
```bash
# Phase 1 시작 시
⚠️  26개 파일 스킵 (빈 내용 또는 읽기 실패)
✓ 50개 파일 리뷰 준비 완료
```

삭제되거나 읽을 수 없는 파일이 자동으로 제외됩니다.

#### 3. 프롬프트 크기 경고
```bash
⚠️  경고: 프롬프트 크기가 매우 큽니다 (~123,456 토큰)
    일부 AI 모델은 컨텍스트 제한으로 실패할 수 있습니다
    파일 수: 50개, 총 문자: 493,824개
```

문제가 발생하기 전에 미리 경고합니다.

#### 4. 파일 수 제한 옵션
```bash
# 30개 이상 파일 시 자동 경고
⚠️  주의: 76개 파일을 한 번에 리뷰하면 AI 모델 제한으로 실패할 수 있습니다.
    권장: --max-files=20 옵션으로 제한하거나 --extensions로 파일 필터링
```

---

## 📋 권장 사용법

### 1. 파일 수 제한 (가장 권장)

```bash
# Python 파일 20개로 제한
ai-review --branch develop --extensions .py --max-files 20

# 전체 파일 중 처음 30개만
ai-review --branch develop --max-files 30
```

**권장 파일 수:**
- 일반 리뷰: 20-30개
- 간단한 파일: 40-50개
- 복잡한 파일: 10-15개

### 2. 파일 확장자 필터링

```bash
# Python만
ai-review --branch develop --extensions .py

# Python과 JavaScript만
ai-review --branch develop --extensions .py,.js

# 설정 파일 제외하고 코드만
ai-review --branch develop --extensions .py,.js,.ts,.tsx
```

### 3. 특정 디렉토리만 리뷰

```bash
# src/core 디렉토리만
ai-review ./src/core/ --max-files 25

# 여러 디렉토리를 순차적으로
ai-review ./src/auth/
ai-review ./src/api/
ai-review ./src/db/
```

### 4. 조합 사용

```bash
# 가장 안전한 방법
ai-review --branch develop \
  --extensions .py \
  --max-files 20 \
  --only claude,openai

# 빠른 리뷰 (1개 AI만)
ai-review ./src/main.py --only claude
```

---

## 🔧 트러블슈팅

### Q1: 여전히 오류가 발생합니다

**A:** 파일 수를 더 줄이세요:
```bash
# 10개로 시작
ai-review --branch develop --max-files 10

# 단일 파일로 테스트
ai-review ./src/main.py
```

### Q2: 어떤 파일이 스킵되었는지 알고 싶습니다

**A:** verbose 모드 사용:
```bash
ai-review --branch develop -v
```

### Q3: 특정 AI만 실패합니다

**A:** 다른 AI만 사용:
```bash
# Gemini 제외
ai-review --branch develop --only claude,openai

# Claude만 사용
ai-review --branch develop --only claude
```

### Q4: 전체 브랜치를 리뷰해야 합니다

**A:** 여러 번 나눠서 실행:
```bash
# 1. Python 파일
ai-review --branch develop --extensions .py --max-files 20

# 2. JavaScript 파일
ai-review --branch develop --extensions .js --max-files 20

# 3. TypeScript 파일
ai-review --branch develop --extensions .ts,.tsx --max-files 20

# 또는 스크립트로 자동화
for dir in src/auth src/api src/core src/utils; do
  ai-review ./$dir/ --max-files 15
done
```

---

## 📊 성능 가이드

### 예상 처리 시간 (AI 3개 기준)

| 파일 수 | 평균 크기 | 예상 시간 | 성공률 |
|---------|-----------|-----------|--------|
| 5-10개  | 200줄     | 3-5분     | 99%    |
| 10-20개 | 200줄     | 5-10분    | 95%    |
| 20-30개 | 200줄     | 10-15분   | 85%    |
| 30-50개 | 200줄     | 15-25분   | 60%    |
| 50개+   | 200줄     | 실패 가능성 높음 | 30%    |

### 토큰 추정

```
총 토큰 ≈ (파일 수 × 평균 줄 수 × 4) / 3

예시:
- 20개 × 200줄 × 4 / 3 = ~53,000 토큰 (안전)
- 50개 × 200줄 × 4 / 3 = ~133,000 토큰 (Claude만 가능)
- 100개 × 200줄 × 4 / 3 = ~266,000 토큰 (모두 실패)
```

---

## 🎯 베스트 프랙티스

### ✅ DO
- ✅ 20-30개 파일로 제한
- ✅ 확장자 필터링 사용
- ✅ verbose 모드로 디버깅 (`-v`)
- ✅ 작은 리뷰부터 시작
- ✅ 여러 번 나눠서 실행
- ✅ 중요한 파일 우선 리뷰

### ❌ DON'T
- ❌ 50개 이상 파일 한 번에 리뷰
- ❌ 바이너리 파일 포함
- ❌ node_modules, __pycache__ 포함
- ❌ 생성된 코드 포함
- ❌ 삭제된 파일 포함

---

## 📝 요약

### 문제
- 76개 파일 → 프롬프트 너무 큼 → AI 실패

### 해결책
1. **--max-files=20**: 파일 수 제한
2. **--extensions .py**: 확장자 필터링
3. **자동 경고**: 문제 사전 감지
4. **에러 로깅**: 실제 오류 내용 표시

### 권장 명령어
```bash
ai-review --branch develop --extensions .py --max-files 20
```

---

## 🆘 추가 도움

문제가 계속되면:
1. GitHub Issues에 리포트
2. verbose 로그 첨부 (`-v`)
3. 파일 수와 프롬프트 크기 정보 포함

**Happy Reviewing! 🚀**

# Git Tools Strategy - 토큰 제한 문제 해결

## 문제 상황

### 발생한 에러
```
git_get_diff response (145276 tokens) exceeds maximum allowed tokens (25000)
```

### 원인 분석
```
User: develop 브랜치랑 비교해서 코드 리뷰

AI 내부 사고:
1. "먼저 얼마나 많이 변경되었는지 확인해야지"
2. git_get_diff_stats() 호출
3. 결과: "76 files changed, 5653 insertions(+), 2301 deletions(-)"
4. "오! 꽤 많이 변경되었네. 전체 diff를 봐야겠다!"
5. git_get_diff() 호출
6. ❌ 145K 토큰 - 25K 제한 초과!
```

### 근본 원인 (User의 통찰)

**User's Question**: "git_get_diff_stats tool 을 제공하기 때문에 발생하는 거 아닌가?"

**정확한 진단**:
- `git_get_diff_stats()`는 AI에게 "미끼"가 됨
- "76개 파일, 5653줄 변경"을 보면 자연스럽게 전체를 보고 싶어짐
- AI는 호기심이 많음: 통계를 보면 → 전체를 보고 싶어함
- 이는 AI의 문제가 아니라 **툴 설계의 문제**

## 해결 방법

### ❌ 잘못된 접근 (Before)

```python
# 제공된 도구들:
- git_get_diff()          # ❌ 거의 항상 토큰 초과
- git_get_diff_stats()    # ⚠️  "미끼" - AI를 git_get_diff()로 유도
- git_get_changed_files() # ✅ 필요
- git_get_file_diff()     # ✅ 핵심 도구

# AI의 자연스러운 워크플로우:
1. git_get_diff_stats() - "얼마나 변경되었나?"
2. git_get_diff() - "전체를 봐야겠다!" ← 💥 여기서 실패
```

### ✅ 올바른 접근 (After)

```python
# 제공된 도구들 (엄선됨):
- git_get_changed_files() # ✅ 첫 단계: 어떤 파일이?
- git_get_file_diff()     # ✅ 두 번째: 각 파일 개별 조회
- git_get_blame()         # ✅ 컨텍스트: 누가 작성?
- git_get_commit_info()   # ✅ 컨텍스트: 커밋 정보
- git_get_current_branch()# ✅ 컨텍스트: 현재 브랜치

# 제거된 도구들 (의도적):
- git_get_diff()          # ❌ 제거: 항상 토큰 초과
- git_get_diff_stats()    # ❌ 제거: AI를 잘못된 방향으로 유도

# AI의 새로운 워크플로우:
1. git_get_changed_files() - "76개 파일이 변경됨"
2. AI 전략적 판단: "중요한 파일만 선택하자"
3. git_get_file_diff("중요파일1.py")
4. git_get_file_diff("중요파일2.py")
5. ...
```

## 구현 상세

### src/mcp/git.py

#### 1. `get_diff()` - 항상 에러 발생

```python
def get_diff(self, base: str, head: str = "HEAD") -> str:
    """⚠️ DEPRECATED: 이 도구는 거의 항상 토큰 제한을 초과합니다!

    ❌ 이 도구를 사용하지 마세요! ❌
    """
    # 통계만 계산해서 얼마나 큰지 보여주기
    stats_result = subprocess.run(...)

    # 항상 에러 발생 (실제 diff 반환 안 함)
    raise RuntimeError(
        f"❌ git_get_diff() is DEPRECATED - DO NOT USE!\n"
        f"📊 This change is too large:\n"
        f"   - Files changed: {len(changed_files)}\n"
        f"   - Estimated tokens: {total_changes * 2:,}\n\n"
        f"✅ CORRECT APPROACH:\n"
        f"1️⃣ files = git_get_changed_files('{base}', '{head}')\n"
        f"2️⃣ for file in important_files:\n"
        f"       git_get_file_diff(file, '{base}', '{head}')\n"
    )
```

**이유**: 만약 AI가 (다른 방법으로) 이 함수를 호출하려 해도, 토큰 낭비 없이 올바른 방법을 안내

#### 2. `get_available_tools()` - 엄선된 도구만 노출

```python
def get_available_tools(self) -> List[Dict[str, str]]:
    """⚠️ 중요: git_get_diff()와 git_get_diff_stats()는 의도적으로 제외됨

    이유:
    - git_get_diff(): 거의 항상 토큰 제한 초과
    - git_get_diff_stats(): AI에게 전체 diff를 보고 싶게 만드는 "미끼"

    올바른 워크플로우:
    1. git_get_changed_files() - 파일 목록 확인
    2. 중요한 파일 전략적 선택
    3. git_get_file_diff() - 각 파일 개별 조회
    """
    return [
        {
            "name": "get_changed_files",
            "description": "변경된 파일 목록 조회 (파일 경로만, diff 내용 없음)",
            "note": "⭐ 첫 단계: 어떤 파일이 변경되었는지 확인"
        },
        {
            "name": "get_file_diff",
            "description": "⭐ 특정 파일의 diff 조회 - 가장 중요한 도구!",
            "note": "한 번에 한 파일씩 조회. 중요한 파일만 전략적으로 선택!"
        },
        # get_blame, get_commit_info, get_current_branch...
    ]
```

**결과**: AI는 `git_get_diff()`와 `git_get_diff_stats()`를 **전혀 볼 수 없음** → 시도조차 할 수 없음

## 효과

### Before (문제 상황)
```
AI: git_get_diff_stats()를 봐야겠다
Result: "76 files, 5653 insertions"

AI: 오! 많이 변경되었네. 전체를 봐야겠다!
AI: git_get_diff() 호출

❌ Error: 145K tokens exceeds 25K limit
```

### After (해결)
```
AI: 사용 가능한 도구를 보니...
     - git_get_changed_files (파일 목록)
     - git_get_file_diff (개별 파일)

AI: git_get_changed_files() 호출
Result: ["auth.py", "database.py", "api.py", ...]

AI: 전략적 판단 - 중요한 파일부터:
     1. auth.py (보안 중요)
     2. database.py (데이터 중요)
     3. api.py (인터페이스 중요)

AI: git_get_file_diff("auth.py")
✅ Success: 342 tokens

AI: git_get_file_diff("database.py")
✅ Success: 589 tokens

AI: git_get_file_diff("api.py")
✅ Success: 421 tokens

✅ Total: 1,352 tokens (25K 제한 안전!)
```

## 설계 원칙

### 1. "Don't Tempt AI" 원칙

❌ **나쁜 설계**:
```python
# 먼저 통계를 보여줌
- git_get_diff_stats() → "5653 lines changed"

# AI 반응: "오! 많이 변경되었네, 전체를 봐야겠다"
- git_get_diff() → 💥 토큰 초과
```

✅ **좋은 설계**:
```python
# 통계를 아예 안 보여줌
# AI는 처음부터 파일별 전략을 짜야 함

1. git_get_changed_files() → 파일 목록만
2. AI 전략적 선택
3. git_get_file_diff() → 개별 조회
```

### 2. "Constraint Drives Strategy" 원칙

**제약이 없을 때**:
- AI는 "모든 것을 보고 싶어함" (human nature)
- 비효율적, 토큰 낭비

**제약이 있을 때**:
- AI는 "무엇이 중요한가?" 고민
- 전략적, 효율적

**Tools as Constraints**:
```python
# ❌ 너무 많은 옵션 = AI 혼란
tools = [get_diff, get_stats, get_files, get_file_diff, ...]

# ✅ 명확한 경로 = AI 집중
tools = [get_changed_files, get_file_diff]
```

### 3. "Paved Path" 원칙

AI에게 "올바른 길"을 자연스럽게 만들기:

```python
# Tool 이름과 설명이 워크플로우를 안내:

{
    "name": "get_changed_files",
    "description": "변경된 파일 목록 조회",
    "note": "⭐ 첫 단계: 어떤 파일이 변경되었는지 확인"
}
↓
{
    "name": "get_file_diff",
    "description": "⭐ 특정 파일의 diff 조회 - 가장 중요한 도구!",
    "note": "한 번에 한 파일씩 조회. 중요한 파일만 전략적으로 선택!"
}
```

AI는 자연스럽게 1 → 2 순서로 실행

## 추가 개선 가능성

### 1. 파일 우선순위 자동 제안

```python
def get_changed_files_with_priority(self, base: str, head: str = "HEAD") -> List[Dict]:
    """변경된 파일 목록 + 우선순위"""
    files = self.get_changed_files(base, head)

    prioritized = []
    for file in files:
        priority = calculate_priority(file)
        # 우선순위 계산:
        # - 보안 관련: 높음 (auth, database, api)
        # - 핵심 로직: 높음 (main, core, processor)
        # - 설정 파일: 중간 (config, settings)
        # - 테스트: 낮음 (test_, _test)
        # - 문서: 매우 낮음 (README, docs)

        prioritized.append({
            "path": file,
            "priority": priority,
            "reason": explain_priority(file)
        })

    return sorted(prioritized, key=lambda x: x["priority"], reverse=True)
```

### 2. 토큰 예산 제공

```python
{
    "name": "get_file_diff",
    "description": "특정 파일의 diff 조회",
    "note": "⚠️ 토큰 예산: 25,000 / 현재 사용: {current_tokens} / 남음: {remaining}"
}
```

AI가 자신의 토큰 사용량을 의식하도록

### 3. 스마트 배치 읽기

```python
def get_files_diff_batch(self, files: List[str], base: str, head: str = "HEAD", max_tokens: int = 20000) -> Dict:
    """여러 파일을 토큰 제한 내에서 배치 조회"""
    result = {}
    total_tokens = 0

    for file in files:
        diff = self.get_file_diff(file, base, head)
        estimated_tokens = len(diff) * 0.3  # rough estimate

        if total_tokens + estimated_tokens > max_tokens:
            result["warning"] = f"Token budget reached. {len(files) - len(result)} files skipped."
            break

        result[file] = diff
        total_tokens += estimated_tokens

    return result
```

## 결론

**문제**: AI가 `git_get_diff_stats()`를 보고 자연스럽게 `git_get_diff()`를 호출 → 토큰 초과

**해결**:
1. ❌ `git_get_diff()` - 완전 제거 (available tools에서)
2. ❌ `git_get_diff_stats()` - 완전 제거 ("미끼" 제거)
3. ✅ `git_get_changed_files()` - 유지 (필수)
4. ✅ `git_get_file_diff()` - 강조 (핵심 도구)

**결과**:
- AI는 처음부터 전략적으로 접근
- 토큰 제한 문제 원천 차단
- 더 나은 리뷰 품질 (선택적 집중)

**교훈**:
- "Don't tempt AI" - 잘못된 길을 아예 보이지 않게
- "Constraint drives strategy" - 제약이 더 나은 전략을 만듦
- "Paved path" - 올바른 길을 자연스럽게

---

**구현 완료**: 2025-10-31
**근본 원인 제공**: User의 통찰
**Status**: 🟢 Production Ready

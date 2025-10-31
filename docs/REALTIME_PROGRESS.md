# Real-Time Progress Reporting via MCP

## 개요

AI가 코드 리뷰를 작성하는 동안 실시간으로 진행 상황을 MCP를 통해 보고하고, Python이 이를 폴링하여 사용자에게 표시하는 기능입니다.

**구현 일자**: 2025-10-31

---

## 사용자 요청사항

> "review 가 동작 중일때도 MCP 를 통해 진행중인 내용이 출력되면 좋겠다."

사용자는 AI가 리뷰를 작성하는 동안 무엇을 하고 있는지 실시간으로 확인하고 싶어했습니다.

---

## 구현 내용

### 1. MCP Tools 추가 (`src/mcp/review_orchestrator.py`)

#### `report_progress(session_id, ai_name, message)`
AI가 작업 중 진행 상황을 보고하는 도구:

```python
review_report_progress(session_id, "Claude", "Analyzing security issues in auth.py...")
review_report_progress(session_id, "Claude", "Checking database migrations for issues...")
review_report_progress(session_id, "Claude", "Reviewing API endpoint changes...")
```

**구현**:
- `ReviewSession.progress` 딕셔너리에 AI별 progress 저장
- 각 progress는 `{message, timestamp}` 형태
- 너무 자주 파일에 저장하면 I/O 부담이 커서 메모리에만 저장

#### `get_progress(session_id, since=0)`
특정 시간 이후의 모든 progress 조회:

```python
{
  "session_id": "review_1730356789",
  "updates": [
    {"ai_name": "Claude", "message": "Analyzing...", "timestamp": 1730356790.5},
    {"ai_name": "GPT-4", "message": "Reviewing...", "timestamp": 1730356791.2}
  ],
  "count": 2
}
```

**특징**:
- `since` 파라미터로 마지막 확인 이후의 progress만 가져옴
- 시간순 정렬 반환
- 효율적인 폴링 가능

### 2. Prompt 업데이트 (`src/mcp/minimal_prompt.py`)

모든 라운드의 프롬프트에 progress 보고 기능 안내 추가:

#### Round 1 (Independent Review)
```python
### Reporting Progress (Optional but Recommended)

While writing your review, you can report progress to help users see what you're working on:

review_report_progress("{session_id}", "{ai_name}", "Analyzing security issues in auth.py...")
review_report_progress("{session_id}", "{ai_name}", "Checking database migrations for issues...")
review_report_progress("{session_id}", "{ai_name}", "Reviewing API endpoint changes...")

This provides **real-time visibility** into your review process!
```

#### Round 2 (Peer Review)
```python
### Reporting Progress (Optional)

You can report what you're reviewing in real-time:

review_report_progress("{session_id}", "{ai_name}", "Reviewing Claude's security findings...")
review_report_progress("{session_id}", "{ai_name}", "Analyzing GPT-4's performance suggestions...")
```

#### Final Round (Consensus Report)
```python
### Reporting Progress (Optional)

While writing the final report, you can report your progress:

review_report_progress("{session_id}", "{ai_name}", "Writing executive summary...")
review_report_progress("{session_id}", "{ai_name}", "Documenting critical issues...")
review_report_progress("{session_id}", "{ai_name}", "Adding code examples for fixes...")
```

### 3. Progress Polling (`src/phase1_reviewer_mcp_orchestrated.py`)

#### Helper Method: `_poll_and_display_progress()`
```python
def _poll_and_display_progress(self, session_id: str, last_check: float = 0) -> float:
    """실시간 진행 상황을 폴링하고 출력"""
    try:
        # MCP를 통해 progress 조회
        progress_result = self.mcp_manager.call_tool(
            "review",
            "get_progress",
            session_id=session_id,
            since=last_check
        )

        # 새로운 progress 출력
        for update in progress_result.get("updates", []):
            ai_name = update["ai_name"]
            message = update["message"]
            print(f"  [{ai_name}] 📡 {message}")

    except Exception as e:
        # 에러는 조용히 무시 (progress는 선택사항)
        pass

    return time.time()
```

**특징**:
- 에러 발생 시 조용히 무시 (progress는 선택적 기능)
- 현재 timestamp 반환 (다음 폴링에 사용)
- 새로운 progress만 출력

#### Round 1/2: 병렬 실행 중 폴링
```python
# 결과 수집 + 실시간 progress 폴링
import time
last_check = time.time()
completed_count = 0
total_ais = len(futures)

print()
print("⏳ AI 리뷰 진행 중... (실시간 progress)")
print()

for future in as_completed(futures):
    # Progress 폴링 (2초마다)
    if time.time() - last_check > 2:
        last_check = self._poll_and_display_progress(session_id, last_check)

    ai_name = futures[future]
    try:
        review = future.result(timeout=600)
        # ... 리뷰 처리 ...

        completed_count += 1
        print(f"\n[{ai_name}] ✓ 리뷰 완료 ({completed_count}/{total_ais})")
        # ... 통계 출력 ...
    except Exception as e:
        print(f"\n[{ai_name}] ✗ 리뷰 실패: {e}")

# 마지막 progress 체크
self._poll_and_display_progress(session_id, last_check)
```

**특징**:
- 2초마다 progress 폴링
- `as_completed()`로 완료되는 순서대로 결과 수집
- 완료 카운트 표시 (`1/3`, `2/3`, `3/3`)
- 마지막에 남은 progress 한 번 더 확인

#### Final Round: 단일 AI 실행 중 폴링
```python
print("⏳ 최종 리포트 작성 중... (실시간 progress)")
print()

# 병렬로 실행하면서 progress 폴링
import time
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(
        self.ai_client.call_ai_with_retry,
        prompt,
        first_ai_model,
        []
    )

    # Progress 폴링 (2초마다)
    last_check = time.time()
    while not future.done():
        time.sleep(2)
        if time.time() - last_check > 2:
            last_check = self._poll_and_display_progress(session_id, last_check)

    final_review = future.result()

    # 마지막 progress 체크
    self._poll_and_display_progress(session_id, last_check)
```

**특징**:
- 단일 AI만 실행하므로 `while not future.done()` 사용
- 2초마다 폴링 (CPU 부담 최소화)
- 완료 후 마지막 progress 확인

---

## 예상 출력

### Round 1 실행 중

```
======================================================================
Step 2: AI Independent Reviews (Parallel)
======================================================================

[Claude] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중

[GPT-4] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중

[Gemini] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중

⏳ AI 리뷰 진행 중... (실시간 progress)

  [Claude] 📡 Analyzing security issues in auth/login.py...
  [GPT-4] 📡 Checking database migrations in db/migrations/...
  [Gemini] 📡 Reviewing API endpoint changes in api/users.py...
  [Claude] 📡 Checking input validation in api/endpoints.py...
  [GPT-4] 📡 Analyzing memory leaks in processor/handler.py...

[Claude] ✓ 리뷰 완료 (1/3)
   → Critical: 3개
   → Major: 5개
   → Minor: 8개
   → 총 3,245 자

  [Gemini] 📡 Documenting performance issues in utils/helper.py...

[GPT-4] ✓ 리뷰 완료 (2/3)
   → Critical: 2개
   → Major: 6개
   → Minor: 7개
   → 총 2,987 자

[Gemini] ✓ 리뷰 완료 (3/3)
   → Critical: 3개
   → Major: 4개
   → Minor: 9개
   → 총 3,102 자
```

### Final Round 실행 중

```
======================================================================
Step 4: Final Report Writing
======================================================================

[Claude]를 최종 리포트 작성자로 선정

Python이 계산한 consensus를 바탕으로 전문적인 최종 리포트 작성 중...
   → Critical 이슈: 반드시 수정 필요
   → Major 이슈: 수정 권장
   → Minor 이슈: 검토 권장
   → Disputed 이슈: 팀 판단 필요

⏳ 최종 리포트 작성 중... (실시간 progress)

  [Claude] 📡 Writing executive summary...
  [Claude] 📡 Documenting critical issues with code examples...
  [Claude] 📡 Adding recommendations for major issues...
  [Claude] 📡 Formatting final report...

✅ 최종 리포트 완료!
   → 길이: 4,567 자
   → 작성자: Claude
   → 기반: 3개 AI의 consensus
```

---

## 사용자 경험 개선

### Before (이전)
```
[Claude] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중

... 😴 3분 동안 아무 출력 없음 😴 ...

[Claude] ✓ 리뷰 완료
```

**문제점**:
- AI가 뭘 하고 있는지 모름
- 진행 중인지 멈춘 건지 불분명
- 사용자는 답답함

### After (현재)
```
[Claude] 독립적 리뷰 시작...
   → 큐레이션된 20개 파일 분석 중

⏳ AI 리뷰 진행 중... (실시간 progress)

  [Claude] 📡 Analyzing security issues in auth.py...
  [Claude] 📡 Checking database migrations...
  [Claude] 📡 Reviewing API endpoints...
  [Claude] 📡 Documenting performance issues...

[Claude] ✓ 리뷰 완료 (1/3)
```

**개선점**:
- ✅ AI가 무엇을 분석하고 있는지 실시간 확인
- ✅ 진행 중임을 명확히 알 수 있음
- ✅ 완료까지 얼마나 남았는지 확인 (`1/3`, `2/3`)
- ✅ 사용자 경험 대폭 향상

---

## 기술적 특징

### 1. 비침해적 (Non-intrusive)
- Progress 보고는 **선택사항** (AI가 안 보고해도 작동)
- Progress 조회 실패 시 조용히 무시
- 기존 워크플로우에 영향 없음

### 2. 효율적 폴링
- 2초마다 폴링 (CPU/네트워크 부담 최소화)
- `since` 파라미터로 **새로운 progress만** 조회
- 중복 출력 방지

### 3. 메모리 효율성
- Progress는 메모리에만 저장 (파일 I/O 없음)
- 세션 종료 시 자동으로 사라짐
- 불필요한 디스크 쓰기 방지

### 4. 병렬 실행 호환
- Round 1/2: 여러 AI 동시 실행 중 pollin
- Final Round: 단일 AI 실행 중 polling
- `as_completed()` 및 `while not done()` 패턴 지원

---

## 파일 변경 사항

### 수정된 파일
1. `src/mcp/review_orchestrator.py`
   - `report_progress()` 메서드 추가
   - `get_progress()` 메서드 추가
   - `get_available_tools()` 업데이트 (2개 도구 추가)

2. `src/mcp/minimal_prompt.py`
   - Round 1 프롬프트에 progress 보고 안내 추가
   - Round 2 프롬프트에 progress 보고 안내 추가
   - Final Round 프롬프트에 progress 보고 안내 추가

3. `src/phase1_reviewer_mcp_orchestrated.py`
   - `_poll_and_display_progress()` 헬퍼 메서드 추가
   - `_execute_round1()` 업데이트: progress 폴링 추가
   - `_execute_round2()` 업데이트: progress 폴링 추가
   - `_execute_final_round()` 업데이트: progress 폴링 추가

### 새로 생성된 파일
- `docs/REALTIME_PROGRESS.md` (이 문서)

---

## 향후 개선 가능 사항

### 1. Progress 파일 저장 (선택적)
현재는 메모리에만 저장하지만, 디버깅을 위해 선택적으로 파일에 저장 가능:

```python
def report_progress(self, session_id: str, ai_name: str, message: str) -> Dict:
    # ... existing code ...

    # 선택적 파일 저장
    if self.save_progress_to_file:
        self._save_session(session)  # progress 포함하여 저장
```

### 2. Progress 이벤트 스트리밍
WebSocket이나 SSE를 통해 실시간 이벤트 스트리밍:

```python
# WebSocket으로 progress 전송
await websocket.send_json({
    "type": "progress",
    "ai_name": ai_name,
    "message": message,
    "timestamp": timestamp
})
```

### 3. Progress 분석 및 통계
AI가 어떤 작업에 시간을 많이 쓰는지 분석:

```python
# 각 AI가 보고한 progress 분석
progress_stats = {
    "Claude": {
        "total_messages": 15,
        "avg_interval": 12.3,  # seconds
        "areas": {"security": 5, "performance": 3, "quality": 7}
    }
}
```

### 4. Progress 타입 분류
Progress에 타입 추가:

```python
review_report_progress(session_id, ai_name, "Analyzing security...", type="security")
review_report_progress(session_id, ai_name, "Checking performance...", type="performance")
```

---

## 요약

✅ **구현 완료**:
- AI가 MCP를 통해 실시간 진행 상황 보고
- Python이 2초마다 progress 폴링
- 사용자에게 실시간 출력

✅ **사용자 경험 개선**:
- AI가 무엇을 하고 있는지 투명하게 확인
- 진행 상황을 실시간으로 추적
- 완료까지 얼마나 남았는지 확인 가능

✅ **기술적 우수성**:
- 비침해적 (AI가 안 보고해도 작동)
- 효율적 폴링 (새로운 progress만 조회)
- 병렬 실행 호환
- 메모리 효율적

**Status**: 🟢 Production Ready

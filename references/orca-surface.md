# Orca orchestration 실행 표면

현재 세션이 Orca 관리 터미널에서 돌고 있으면 peer 검증자를 헤드리스 subprocess가 아니라 **`orca orchestration` task/dispatch로 추적되는 Orca 터미널 워커**로 띄운다. 사용자가 각 검증자의 진행을 앱에서 그대로 본다.

판별과 기본 원칙은 `phase-harness`의 [adapter-orca.md](../../phase-harness/references/adapter-orca.md)와 동일하다. 이 문서는 consensus 흐름에 맞춘 차이만 적는다.

## 활성 조건

```bash
[ -n "${ORCA_TERMINAL_HANDLE:-}" ] || [ "${TERM_PROGRAM:-}" = "Orca" ]
```

- 참이고 `orca status --json`의 `result.runtime.state`가 `ready`면 이 표면을 쓴다.
- 거짓이면 `validation-process.md`의 기존 헤드리스 peer helper(`run_claude_peer` 등)를 그대로 쓴다.
- 사용자가 orca를 명시적으로 언급한 경우에도 이 표면을 쓴다.

`ORCA_TERMINAL_HANDLE`은 coordinator 자신의 pane handle이다. peer에게 결과를 되돌려 받을 주소로 쓸 수 있다.

## 무엇이 달라지나

| 항목 | 헤드리스(기본) | Orca 표면 |
|---|---|---|
| peer 기동 | `claude -p`, `codex exec`, `agy --print` | `orca terminal create --command <agent>` + `orca orchestration dispatch --inject` |
| 프롬프트 전달 | stdin / `--prompt-file` | `orca orchestration task-create` + `dispatch --inject` |
| 결과 수집 | stdout 파싱 | **peer가 지정된 파일에 쓴다** |
| Round 2+ | `--resume` / stateless 재구성 | 같은 터미널에 추가 프롬프트 → 세션 컨텍스트 유지 |
| 관측 | 없음 | 앱에 검증자별 탭 |

**stdout을 파싱하지 않는다.** TUI 렌더링 문자가 섞여 신뢰할 수 없다. 모든 peer 프롬프트 끝에 결과 파일 경로를 명시한다.

```
검토 결과를 .consensus/round-1/feedback-<peer>.md 에 작성해라.
첫 줄은 "Verdict: AGREE|MODIFY|DISAGREE"로 시작하고, 그 아래 동의/수정/반대/추가를 나눠 적는다.
파일을 쓴 뒤 "<PEER> DONE"만 출력한다.
```

## peer orchestration 배치

검증자마다 탭 하나를 만든다. coordinator 자신은 검증자가 아니므로 탭을 만들지 않는다.

```bash
for peer in "${VALIDATORS[@]}"; do
  HANDLE="$(orca terminal create --worktree active --title "REVIEW-${peer}" --command "$peer" --json | jq -r '.result.handle')"
done
```

- known agent id: `claude`, `codex`, `omp`, `pi`, `grok`. `agy`와 Ollama Cloud helper는 TUI 에이전트가 아니므로 기존 헤드리스 경로를 유지하고, 그 사실을 사용자에게 알린다.
- `--worktree active`를 쓴다. consensus는 현재 checkout을 검토하므로 별도 checkout lifecycle을 만들지 않는다. 작업 lifecycle은 `orca orchestration`에 남긴다.
- 응답의 handle을 peer 이름에 매핑해 보관한다. 에이전트가 탭 제목을 덮어쓰므로 식별 기준은 handle이다.
- 모델·추론 강도 지정이 필요하면 `--command "claude --model fable --effort medium"`처럼 argv에 실어 띄운다. SKILL.md의 Peer 모델 표를 그대로 따른다.
- 이 단계에서는 실행 표면만 준비한다. `tui-idle` 확인 후 Round 1에서 각 handle에 `task-create` + `dispatch --inject`를 실행한다.

## 라운드 진행

Round 1(blind)은 준비된 리뷰를 전달하지 않는다는 원칙이 그대로 적용된다. 아티팩트 + 계약 + 적대적 프롬프트만 보낸다.

```bash
TASK=$(orca orchestration task-create --spec "$(cat "$PROMPT_FILE")" --json | jq -r '.result.task.id')
orca orchestration dispatch --task "$TASK" --to "$HANDLE" --inject --json
```

프롬프트를 보내기 전에 기동을 확인한다. **이 대기만 `tui-idle`을 쓴다.**

```bash
orca terminal wait --terminal "$HANDLE" --for tui-idle --timeout-ms 90000 --json
```

완료 판정은 **결과 파일 존재**로 한다. `tui-idle`은 검증자가 작업 중에도 satisfied를 반환하므로 완료 신호가 아니다.

`orca orchestration dispatch --inject`로 보냈다면 `orca orchestration check --wait --types worker_done,escalation --timeout-ms <n> --json`으로 기다린다. timeout과 `{count:0}`은 실패가 아니라 checkpoint다.

Round 2+는 같은 터미널을 재사용한다. 세션 컨텍스트가 살아 있어 이전 라운드를 다시 설명할 필요가 없다 — 헤드리스 경로의 resume/재구성보다 토큰이 덜 든다. 변경분과 새 결과 파일 경로만 보낸다.

```bash
TASK=$(orca orchestration task-create --spec "리뷰가 아래처럼 수정됐다. 재검토 결과를 .consensus/round-2/feedback-${peer}.md 에 써라. ..." --json | jq -r '.result.task.id')
orca orchestration dispatch --task "$TASK" --to "$HANDLE" --inject --json
```

## 관측과 정리

- 라운드 전환마다 어떤 검증자가 어느 탭에서 무엇을 하는지 한두 줄로 보고한다. 완료 알림만 남기지 않는다.
- 중간 확인은 `orca terminal read --terminal <handle> --limit 200 --json`. `--limit`을 반드시 준다.
- 합의 종료 후 검증자 탭을 닫는다.

```bash
orca terminal close --terminal "$HANDLE" --tab --json
```

## 금지 사항

1. 검증자 여러 개를 한 탭이나 한 드라이버 스크립트에 묶는 것.
2. peer 출력을 `>/dev/null` 하거나 파일로만 남겨 탭에서 안 보이게 하는 것.
3. TUI stdout을 파싱해 합의율을 계산하는 것 — 결과는 파일로 받는다.
4. `tui-idle`을 완료 신호로 쓰는 것.
5. coordinator 자신의 탭을 검증자로 쓰는 것 — 런타임 주체 원칙 위반이다.

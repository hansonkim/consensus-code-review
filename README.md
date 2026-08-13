# consensus-code-review

**Multi-AI Consensus Code Review** — 이미 작성된 코드 리뷰를 여러 peer AI 런타임(Claude, Codex, agy, 선택적으로 Grok / Ollama Cloud / vLLM)에게 검증받고 합의(consensus)를 도출하는 스킬입니다.

> 이 스킬은 **리뷰를 생성하지 않습니다.** 사용자가 준비한 리뷰를 받아서 다중 AI 합의 검증만 수행합니다. (초기 리뷰 작성이 필요한 경우 repo의 `run_code_review` 개념과 함께 사용)

## 핵심 개념

1. 사용자가 준비한 리뷰를 수신
2. 현재 실행 런타임을 제외한 peer 검증자(Claude, Codex, agy, 필요 시 Grok/vLLM)에게 검토 요청
3. 피드백 수집·분석
4. 합의 프로세스 진행 (최대 3라운드)
5. 최종 검증된 리뷰 생성

## 주요 특징

- **Blind 1차 검토**: Round 1에서는 peer 검증자에게 준비된 리뷰(결론)를 전달하지 않아 앵커링을 방지
- **다중 AI 검증**: 현재 실행 주체를 제외한 peer + 선택 검증자 활용
- **구조화된 피드백**: `AGREE / NEEDS_CHANGE / DISAGREE / MISSING`(동의/수정/반대/추가) 분류와 정량적 합의율 계산
- **Token 효율성**: Resume/Continue + Delta Updates로 평균 45~61% 절감
- **Orca 실행 표면**: Orca 관리 터미널에서는 `orca orchestration` task/dispatch로 검증자를 배치

## 파일 구조

```
consensus-code-review/
├── SKILL.md                              # 스킬 본문 (사용 가이드)
├── README.md                             # 저장소 소개
├── references/
│   ├── orca-surface.md                   # Orca 실행 표면 상세
│   ├── token-strategy.md                 # Token 절약 전략
│   └── validation-process.md             # 리뷰 검증 프로세스 상세
└── scripts/
    └── ollama_cloud_review.py            # Ollama Cloud 검증자 helper (API 키 비노출)
```

## 사용 방법

스킬로 배포된 환경에서는 `~/.agents/skills/consensus-code-review/SKILL.md`를 읽고 프로세스에 따라 실행합니다.

- 방법 1: 리뷰 내용을 직접 제공
- 방법 2: 리뷰 파일 경로 제공
- 방법 3: Git 브랜치와 함께 리뷰 제공

## 실행 주체 원칙

현재 이 스킬을 실행하는 runtime은 **조정자(coordinator)**이며 검증자가 아닙니다. 자기 자신에게 다시 검토를 맡겨 합의율에 포함하지 않습니다.

| 실행 주체 | 기본 협조 요청 대상 |
|---|---|
| Claude | Codex, agy |
| Codex | Claude, agy |
| agy | Claude, Codex |
| pi | Claude, Codex |
| 기타/불명확 | 사용 가능한 Claude, Codex, agy 중 현재 주체로 확인되지 않은 runtime |

## 라이선스

MIT License

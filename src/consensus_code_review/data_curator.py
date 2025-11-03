"""Data Curator - Python이 Git 데이터를 큐레이션

AI에게 탐색 도구를 주는 대신, Python이 모든 Git 작업을 수행하고
큐레이션된 데이터만 AI에게 전달합니다.

Pure Task Delegation:
- Python: 객관적 작업 (Git 조회, 파일 선택, 토큰 관리)
- AI: 주관적 작업 (큐레이션된 데이터 분석, 리뷰 작성)
"""

import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class FileChange:
    """파일 변경 정보"""

    path: str
    priority: int  # 1 (highest) to 5 (lowest)
    reason: str
    insertions: int
    deletions: int
    diff: Optional[str] = None


class DataCurator:
    """Git 데이터 큐레이션 - Python이 모든 결정을 내림"""

    def __init__(self, token_budget: int = 20000, cwd: Optional[str] = None):
        """초기화

        Args:
            token_budget: AI에게 전달할 최대 토큰 수
            cwd: Git 명령어를 실행할 작업 디렉토리
        """
        self.token_budget = token_budget
        self.timeout = 30
        self.cwd = cwd

    def curate_changes(self, base_branch: str, target_branch: str = "HEAD") -> Dict:
        """변경사항 큐레이션 - Python이 모든 Git 작업 수행

        Args:
            base_branch: 기준 브랜치
            target_branch: 비교 대상 브랜치

        Returns:
            큐레이션된 데이터:
            {
                'summary': {...},
                'curated_files': [FileChange, ...],
                'skipped_files': [...],
                'token_usage': int
            }
        """
        print("\n📊 Python이 변경사항 큐레이션 중...")
        print(f"   Base: {base_branch} → Target: {target_branch}")

        # 1. 모든 변경 파일 가져오기
        all_files = self._get_all_changed_files(base_branch, target_branch)
        print(f"   ✓ 총 {len(all_files)}개 파일 변경 감지")

        # 2. 파일별 우선순위 계산 (Python의 규칙 기반 판단)
        prioritized_files = self._prioritize_files(all_files, base_branch, target_branch)
        print("   ✓ 우선순위 계산 완료")

        # 3. 토큰 예산 내에서 중요한 파일만 선택
        curated_files, skipped_files = self._select_within_budget(
            prioritized_files, base_branch, target_branch
        )
        print(f"   ✓ 큐레이션 완료: {len(curated_files)}개 선택, {len(skipped_files)}개 생략")

        # 4. 통계 생성
        total_insertions = sum(f.insertions for f in curated_files)
        total_deletions = sum(f.deletions for f in curated_files)
        token_usage = sum(self._estimate_tokens(f.diff or "") for f in curated_files)

        print(f"   ✓ 토큰 사용량: {token_usage:,} / {self.token_budget:,}")

        return {
            "summary": {
                "total_files": len(all_files),
                "curated_files": len(curated_files),
                "skipped_files": len(skipped_files),
                "insertions": total_insertions,
                "deletions": total_deletions,
                "token_usage": token_usage,
            },
            "curated_files": curated_files,
            "skipped_files": skipped_files,
            "base_branch": base_branch,
            "target_branch": target_branch,
        }

    def _get_all_changed_files(self, base: str, head: str) -> List[str]:
        """모든 변경된 파일 목록 가져오기"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{base}...{head}"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True,
                cwd=self.cwd,
            )
            files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
            return files
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git failed: {e.stderr}")

    def _prioritize_files(self, files: List[str], base: str, head: str) -> List[FileChange]:
        """파일별 우선순위 계산 (Python의 규칙 기반)"""
        prioritized = []

        for file_path in files:
            # 각 파일의 변경 통계 가져오기
            insertions, deletions = self._get_file_stats(file_path, base, head)

            # 우선순위 계산 (Python의 명확한 규칙)
            priority, reason = self._calculate_priority(file_path, insertions, deletions)

            prioritized.append(
                FileChange(
                    path=file_path,
                    priority=priority,
                    reason=reason,
                    insertions=insertions,
                    deletions=deletions,
                )
            )

        # 우선순위 순으로 정렬 (1 = highest)
        return sorted(prioritized, key=lambda x: (x.priority, -x.insertions - x.deletions))

    def _calculate_priority(
        self, file_path: str, insertions: int, deletions: int
    ) -> Tuple[int, str]:
        """파일 우선순위 계산 (명확한 규칙)

        Returns:
            (priority, reason)
            priority: 1 (highest) to 5 (lowest)
        """
        path_lower = file_path.lower()
        total_changes = insertions + deletions

        # Priority 1: 보안 관련 (최우선)
        security_keywords = [
            "auth",
            "password",
            "token",
            "secret",
            "crypto",
            "security",
            "permission",
        ]
        if any(keyword in path_lower for keyword in security_keywords):
            return (1, "🔒 Security-sensitive")

        # Priority 1: 데이터베이스 관련
        if any(
            keyword in path_lower for keyword in ["database", "db", "migration", "schema", "sql"]
        ):
            return (1, "💾 Database-related")

        # Priority 1: API 관련
        if any(keyword in path_lower for keyword in ["api", "endpoint", "route", "controller"]):
            return (1, "🌐 API endpoint")

        # Priority 2: 핵심 비즈니스 로직
        if any(
            keyword in path_lower
            for keyword in ["core", "main", "processor", "service", "business"]
        ):
            return (2, "⚙️ Core logic")

        # Priority 2: 대규모 변경 (>100 lines)
        if total_changes > 100:
            return (2, f"📊 Large change ({total_changes} lines)")

        # Priority 3: 설정 파일
        if any(
            keyword in path_lower for keyword in ["config", "setting", ".env", ".yaml", ".json"]
        ):
            return (3, "⚙️ Configuration")

        # Priority 4: 테스트 파일
        if (
            "test" in path_lower
            or path_lower.endswith("_test.py")
            or path_lower.endswith(".test.js")
        ):
            return (4, "🧪 Test file")

        # Priority 5: 문서/기타
        if any(
            ext in path_lower for ext in [".md", ".txt", ".rst", "readme", "changelog", "license"]
        ):
            return (5, "📄 Documentation")

        # Default: Priority 3
        return (3, "📝 Standard file")

    def _get_file_stats(self, file_path: str, base: str, head: str) -> Tuple[int, int]:
        """파일의 변경 통계 (insertions, deletions)"""
        try:
            result = subprocess.run(
                ["git", "diff", "--numstat", f"{base}...{head}", "--", file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True,
                cwd=self.cwd,
            )
            # Output: "5\t3\tpath/to/file.py" (insertions, deletions, path)
            if result.stdout.strip():
                parts = result.stdout.strip().split("\t")
                if len(parts) >= 2:
                    insertions = int(parts[0]) if parts[0] != "-" else 0
                    deletions = int(parts[1]) if parts[1] != "-" else 0
                    return insertions, deletions
        except (subprocess.CalledProcessError, ValueError):
            pass

        return 0, 0

    def _select_within_budget(
        self, prioritized_files: List[FileChange], base: str, head: str
    ) -> Tuple[List[FileChange], List[FileChange]]:
        """토큰 예산 내에서 파일 선택"""
        curated = []
        skipped = []
        current_tokens = 0

        for file_change in prioritized_files:
            # 파일의 실제 diff 가져오기
            diff = self._get_file_diff(file_change.path, base, head)
            estimated_tokens = self._estimate_tokens(diff)

            # 예산 내에 들어가는지 확인
            if current_tokens + estimated_tokens <= self.token_budget:
                file_change.diff = diff
                curated.append(file_change)
                current_tokens += estimated_tokens
            else:
                # 예산 초과 - 스킵
                skipped.append(file_change)

                # Priority 1 파일이 스킵되면 경고
                if file_change.priority == 1:
                    print(f"   ⚠️  Priority 1 파일 스킵됨 (예산 부족): {file_change.path}")

        return curated, skipped

    def _get_file_diff(self, file_path: str, base: str, head: str) -> str:
        """특정 파일의 diff 가져오기"""
        try:
            result = subprocess.run(
                ["git", "diff", f"{base}...{head}", "--", file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True,
                cwd=self.cwd,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 추정 (rough estimate)"""
        # 대략 1 token ≈ 4 characters (영어 기준)
        # 코드는 좀 더 조밀하므로 3.5 characters per token
        return int(len(text) / 3.5)

    def format_curated_data(self, curated_data: Dict) -> str:
        """큐레이션된 데이터를 AI가 읽기 좋게 포맷

        Args:
            curated_data: curate_changes()의 결과

        Returns:
            Markdown 포맷의 큐레이션 데이터
        """
        summary = curated_data["summary"]
        curated_files = curated_data["curated_files"]
        skipped_files = curated_data["skipped_files"]

        output = f"""# Code Changes Summary

**Base**: `{curated_data["base_branch"]}` → **Target**: `{curated_data["target_branch"]}`

## Overview

- **Total files changed**: {summary["total_files"]}
- **Files included in review**: {summary["curated_files"]} (selected by priority)
- **Files skipped**: {summary["skipped_files"]} (low priority or budget limit)
- **Lines**: +{summary["insertions"]} / -{summary["deletions"]}
- **Token usage**: {summary["token_usage"]:,} / {self.token_budget:,}

---

## Files Included (Priority-Ordered)

"""

        # 포함된 파일들
        for i, file_change in enumerate(curated_files, 1):
            output += f"""### {i}. `{file_change.path}` {file_change.reason}

**Priority**: {file_change.priority} | **Changes**: +{file_change.insertions} / -{file_change.deletions}

```diff
{file_change.diff}
```

---

"""

        # 스킵된 파일들 (요약만)
        if skipped_files:
            output += f"\n## Files Skipped ({len(skipped_files)} files)\n\n"
            output += (
                "These files were skipped due to low priority or token budget constraints:\n\n"
            )
            for file_change in skipped_files[:20]:  # 최대 20개만
                output += f"- `{file_change.path}` {file_change.reason} "
                output += f"(+{file_change.insertions} / -{file_change.deletions})\n"

            if len(skipped_files) > 20:
                output += f"\n... and {len(skipped_files) - 20} more files\n"

        return output

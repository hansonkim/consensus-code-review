"""Git MCP Server

AI가 Git 리포지토리를 조회하고 분석할 수 있도록 하는 MCP 도구들을 제공합니다.
"""

import subprocess
from typing import List, Dict, Optional


class GitMCP:
    """Git 작업을 위한 MCP 서버"""

    def __init__(self):
        """초기화"""
        self.timeout = 30  # 30초 타임아웃

    def get_diff(self, base: str, head: str = "HEAD") -> str:
        """두 커밋/브랜치 간의 diff 조회

        Args:
            base: 기준 커밋/브랜치
            head: 비교 대상 커밋/브랜치 (기본: HEAD)

        Returns:
            Git diff 출력

        Raises:
            RuntimeError: Git 명령 실패 시
        """
        try:
            result = subprocess.run(
                ["git", "diff", f"{base}...{head}"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git diff 실패: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git diff 타임아웃")

    def get_changed_files(self, base: str, head: str = "HEAD") -> List[str]:
        """변경된 파일 목록 조회

        Args:
            base: 기준 커밋/브랜치
            head: 비교 대상 커밋/브랜치

        Returns:
            변경된 파일 경로 리스트
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{base}...{head}"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )
            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return files
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git changed files 실패: {e.stderr}")

    def get_file_diff(self, path: str, base: str, head: str = "HEAD") -> str:
        """특정 파일의 diff 조회

        Args:
            path: 파일 경로
            base: 기준 커밋/브랜치
            head: 비교 대상 커밋/브랜치

        Returns:
            파일 diff
        """
        try:
            result = subprocess.run(
                ["git", "diff", f"{base}...{head}", "--", path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git file diff 실패: {e.stderr}")

    def get_blame(self, path: str, line_start: int, line_end: Optional[int] = None) -> str:
        """파일의 blame 정보 조회

        Args:
            path: 파일 경로
            line_start: 시작 라인
            line_end: 종료 라인 (None이면 한 줄만)

        Returns:
            Git blame 출력
        """
        try:
            if line_end is None:
                line_end = line_start

            result = subprocess.run(
                ["git", "blame", "-L", f"{line_start},{line_end}", path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git blame 실패: {e.stderr}")

    def get_commit_info(self, commit_hash: str) -> Dict[str, str]:
        """커밋 정보 조회

        Args:
            commit_hash: 커밋 해시

        Returns:
            커밋 정보 딕셔너리
        """
        try:
            # 커밋 메시지
            message_result = subprocess.run(
                ["git", "log", "-1", "--format=%s", commit_hash],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )

            # 작성자
            author_result = subprocess.run(
                ["git", "log", "-1", "--format=%an <%ae>", commit_hash],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )

            # 날짜
            date_result = subprocess.run(
                ["git", "log", "-1", "--format=%ai", commit_hash],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )

            return {
                "hash": commit_hash,
                "message": message_result.stdout.strip(),
                "author": author_result.stdout.strip(),
                "date": date_result.stdout.strip()
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git commit info 실패: {e.stderr}")

    def get_current_branch(self) -> str:
        """현재 브랜치 이름 조회

        Returns:
            브랜치 이름
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git current branch 실패: {e.stderr}")

    def get_diff_stats(self, base: str, head: str = "HEAD") -> Dict[str, int]:
        """Diff 통계 조회

        Args:
            base: 기준 커밋/브랜치
            head: 비교 대상 커밋/브랜치

        Returns:
            통계 딕셔너리 (files_changed, insertions, deletions)
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--shortstat", f"{base}...{head}"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )

            # Parse: "3 files changed, 45 insertions(+), 12 deletions(-)"
            output = result.stdout.strip()

            stats = {
                "files_changed": 0,
                "insertions": 0,
                "deletions": 0
            }

            if not output:
                return stats

            parts = output.split(',')
            for part in parts:
                part = part.strip()
                if 'file' in part:
                    stats["files_changed"] = int(part.split()[0])
                elif 'insertion' in part:
                    stats["insertions"] = int(part.split()[0])
                elif 'deletion' in part:
                    stats["deletions"] = int(part.split()[0])

            return stats
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git diff stats 실패: {e.stderr}")

    def get_available_tools(self) -> List[Dict[str, str]]:
        """사용 가능한 MCP 도구 목록 반환

        Returns:
            도구 목록
        """
        return [
            {
                "name": "get_diff",
                "description": "두 커밋/브랜치 간의 전체 diff 조회",
                "parameters": "base: str, head: str = 'HEAD'",
                "example": 'get_diff("main", "feature-branch")'
            },
            {
                "name": "get_changed_files",
                "description": "변경된 파일 목록만 조회",
                "parameters": "base: str, head: str = 'HEAD'",
                "example": 'get_changed_files("main")'
            },
            {
                "name": "get_file_diff",
                "description": "특정 파일의 diff만 조회",
                "parameters": "path: str, base: str, head: str = 'HEAD'",
                "example": 'get_file_diff("src/main.py", "main")'
            },
            {
                "name": "get_blame",
                "description": "파일 특정 줄의 작성자/커밋 정보 조회",
                "parameters": "path: str, line_start: int, line_end: int = None",
                "example": 'get_blame("src/main.py", 45, 50)'
            },
            {
                "name": "get_commit_info",
                "description": "커밋 정보 조회 (메시지, 작성자, 날짜)",
                "parameters": "commit_hash: str",
                "example": 'get_commit_info("abc123")'
            },
            {
                "name": "get_current_branch",
                "description": "현재 브랜치 이름 조회",
                "parameters": "없음",
                "example": 'get_current_branch()'
            },
            {
                "name": "get_diff_stats",
                "description": "Diff 통계 조회 (변경 파일 수, 추가/삭제 줄)",
                "parameters": "base: str, head: str = 'HEAD'",
                "example": 'get_diff_stats("main")'
            }
        ]

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
        """⚠️ DEPRECATED: 이 도구는 거의 항상 토큰 제한을 초과합니다!

        ❌ 이 도구를 사용하지 마세요! ❌

        대신 이렇게 하세요:
        1. git_get_diff_stats() - 통계 확인
        2. git_get_changed_files() - 파일 목록
        3. git_get_file_diff() - 각 파일 개별 조회

        Args:
            base: 기준 커밋/브랜치
            head: 비교 대상 커밋/브랜치

        Returns:
            항상 에러 발생 (도구를 사용하지 말 것)

        Raises:
            RuntimeError: 항상 발생 (이 도구를 사용하지 말라는 안내)
        """
        # 통계만 확인해서 얼마나 큰지 보여주기
        try:
            stats_result = subprocess.run(
                ["git", "diff", f"{base}...{head}", "--shortstat"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )

            files_result = subprocess.run(
                ["git", "diff", f"{base}...{head}", "--name-only"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )
            changed_files = [f for f in files_result.stdout.split('\n') if f.strip()]

            stats_line = stats_result.stdout.strip()
            if stats_line:
                import re
                match = re.search(r'(\d+) insertion|(\d+) deletion', stats_line)
                insertions = int(match.group(1)) if match and match.group(1) else 0
                deletions = int(match.group(2)) if match and match.group(2) else 0
                total_changes = insertions + deletions
            else:
                total_changes = 0

        except Exception:
            total_changes = 0
            changed_files = []

        # 항상 에러 (이 도구를 사용하지 말 것!)
        raise RuntimeError(
            f"❌ ❌ ❌ git_get_diff() is DEPRECATED - DO NOT USE! ❌ ❌ ❌\n\n"
            f"📊 This change is too large for a single diff:\n"
            f"   - Files changed: {len(changed_files)}\n"
            f"   - Lines changed: {total_changes:,}\n"
            f"   - Estimated tokens: {total_changes * 2:,} (likely exceeds limit)\n\n"
            f"✅ ✅ ✅ CORRECT APPROACH ✅ ✅ ✅\n\n"
            f"1️⃣ Get overview:\n"
            f"   stats = git_get_diff_stats('{base}', '{head}')\n\n"
            f"2️⃣ Get file list:\n"
            f"   files = git_get_changed_files('{base}', '{head}')\n\n"
            f"3️⃣ Read files ONE BY ONE:\n"
            f"   for file in important_files:  # Select strategically!\n"
            f"       diff = git_get_file_diff(file, '{base}', '{head}')\n"
            f"       # Analyze this file\n\n"
            f"4️⃣ Focus on important files:\n"
            f"   - Security-sensitive (auth, database, API)\n"
            f"   - Large changes (>100 lines)\n"
            f"   - Core logic files\n\n"
            f"📁 Changed files (first 15):\n"
            f"{chr(10).join('   - ' + f for f in changed_files[:15])}\n"
            f"{'   ... and ' + str(len(changed_files) - 15) + ' more files' if len(changed_files) > 15 else ''}\n\n"
            f"🚫 NEVER call git_get_diff() again!\n"
            f"✅ ALWAYS use git_get_file_diff() for selective reading!\n"
        )

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

        ⚠️ 중요: git_get_diff()와 git_get_diff_stats()는 의도적으로 제외됨

        이유:
        - git_get_diff(): 거의 항상 토큰 제한 초과 (100K+ 토큰)
        - git_get_diff_stats(): AI에게 전체 diff를 보고 싶게 만드는 "미끼"

        올바른 워크플로우:
        1. git_get_changed_files() - 파일 목록 확인
        2. 중요한 파일 전략적 선택
        3. git_get_file_diff() - 각 파일 개별 조회

        Returns:
            도구 목록 (git_get_diff, git_get_diff_stats 제외)
        """
        return [
            {
                "name": "get_changed_files",
                "description": "변경된 파일 목록 조회 (파일 경로만, diff 내용 없음)",
                "parameters": "base: str, head: str = 'HEAD'",
                "example": 'get_changed_files("main")',
                "note": "⭐ 첫 단계: 어떤 파일이 변경되었는지 확인"
            },
            {
                "name": "get_file_diff",
                "description": "⭐ 특정 파일의 diff 조회 - 가장 중요한 도구!",
                "parameters": "path: str, base: str, head: str = 'HEAD'",
                "example": 'get_file_diff("src/main.py", "main")',
                "note": "한 번에 한 파일씩 조회. 중요한 파일만 전략적으로 선택!"
            },
            {
                "name": "get_blame",
                "description": "파일 특정 줄의 작성자/커밋 정보 조회",
                "parameters": "path: str, line_start: int, line_end: int = None",
                "example": 'get_blame("src/main.py", 45, 50)',
                "note": "특정 코드를 누가 언제 작성했는지 확인"
            },
            {
                "name": "get_commit_info",
                "description": "커밋 정보 조회 (메시지, 작성자, 날짜)",
                "parameters": "commit_hash: str",
                "example": 'get_commit_info("abc123")',
                "note": "특정 커밋의 상세 정보 확인"
            },
            {
                "name": "get_current_branch",
                "description": "현재 브랜치 이름 조회",
                "parameters": "없음",
                "example": 'get_current_branch()',
                "note": "현재 작업 중인 브랜치 확인"
            }
        ]

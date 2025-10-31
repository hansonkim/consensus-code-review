"""파일 분석 및 Git 통합 모듈

이 모듈은 다양한 리뷰 모드에 맞춰 대상 파일들을 분석하고 수집합니다.
"""

import subprocess
from pathlib import Path
from typing import List, Optional


class FileAnalyzer:
    """파일 및 Git 분석기

    리뷰 모드에 따라 적절한 파일 목록을 수집합니다.
    """

    def analyze_file_mode(self, target_path: str, extensions: Optional[List[str]] = None) -> List[str]:
        """단일 파일 모드 분석

        Args:
            target_path: 파일 경로
            extensions: 확장자 필터 (사용 안 함)

        Returns:
            파일 경로 리스트 (단일 파일)

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
        """
        path = Path(target_path)
        if not path.is_file():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {target_path}")
        return [str(path)]

    def analyze_directory_mode(
        self, target_path: str, extensions: Optional[List[str]] = None
    ) -> List[str]:
        """디렉토리 모드 분석

        Args:
            target_path: 디렉토리 경로
            extensions: 확장자 필터 (예: ['.py', '.js'])

        Returns:
            디렉토리 내 모든 파일 경로 리스트

        Raises:
            NotADirectoryError: 디렉토리가 아닐 때
        """
        path = Path(target_path)
        if not path.is_dir():
            raise NotADirectoryError(f"디렉토리가 아닙니다: {target_path}")

        files = []
        for file_path in path.rglob("*"):
            if file_path.is_file() and self._should_include_file(file_path, extensions):
                files.append(str(file_path))

        return sorted(files)

    def analyze_staged_mode(self, extensions: Optional[List[str]] = None) -> List[str]:
        """Staged 변경사항 모드 분석

        Args:
            extensions: 확장자 필터

        Returns:
            staged된 파일 경로 리스트

        Raises:
            RuntimeError: git 명령 실패 시
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            files = [f.strip() for f in result.stdout.split("\n") if f.strip()]

            # 확장자 필터링
            if extensions:
                files = [
                    f for f in files
                    if Path(f).suffix in extensions
                ]

            return files

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git staged 분석 실패: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git 명령 타임아웃")

    def analyze_commits_mode(
        self, commit_range: str, extensions: Optional[List[str]] = None
    ) -> List[str]:
        """커밋 범위 모드 분석

        Args:
            commit_range: 커밋 범위 (예: HEAD~3..HEAD)
            extensions: 확장자 필터

        Returns:
            변경된 파일 경로 리스트

        Raises:
            RuntimeError: git 명령 실패 시
        """
        try:
            result = subprocess.run(
                ["git", "diff", commit_range, "--name-only"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            files = [f.strip() for f in result.stdout.split("\n") if f.strip()]

            # 확장자 필터링
            if extensions:
                files = [
                    f for f in files
                    if Path(f).suffix in extensions
                ]

            return files

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git commits 분석 실패: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git 명령 타임아웃")

    def analyze_branch_mode(
        self, base_branch: str = "auto", extensions: Optional[List[str]] = None
    ) -> List[str]:
        """브랜치 모드 분석

        Args:
            base_branch: 기준 브랜치 (기본값: auto - 자동 감지)
            extensions: 확장자 필터

        Returns:
            현재 브랜치에서 변경된 파일 경로 리스트

        Raises:
            RuntimeError: git 명령 실패 시
        """
        try:
            # 현재 브랜치 이름 가져오기
            current_branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            current_branch = current_branch_result.stdout.strip()

            # 기본 브랜치 자동 감지
            if base_branch == "auto":
                base_branch = self._detect_base_branch()

            # 변경 파일 목록 가져오기
            result = subprocess.run(
                ["git", "diff", f"{base_branch}...{current_branch}", "--name-only"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            files = [f.strip() for f in result.stdout.split("\n") if f.strip()]

            # 확장자 필터링
            if extensions:
                files = [
                    f for f in files
                    if Path(f).suffix in extensions
                ]

            return files

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git branch 분석 실패: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git 명령 타임아웃")

    def _detect_base_branch(self) -> str:
        """기본 브랜치 자동 감지

        Returns:
            감지된 기본 브랜치 이름

        Raises:
            RuntimeError: 기본 브랜치를 찾을 수 없을 때
        """
        # 일반적인 기본 브랜치 이름들 (우선순위 순)
        common_base_branches = ["main", "master", "develop", "development"]

        # 모든 브랜치 목록 가져오기
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            branches = [
                line.strip().replace("* ", "").replace("remotes/origin/", "")
                for line in result.stdout.split("\n")
                if line.strip()
            ]

            # 우선순위에 따라 기본 브랜치 찾기
            for base in common_base_branches:
                if base in branches:
                    return base

            # 찾지 못한 경우 첫 번째 브랜치 사용
            if branches:
                return branches[0].replace("* ", "")

            raise RuntimeError("기본 브랜치를 찾을 수 없습니다")

        except subprocess.CalledProcessError:
            # Git 명령 실패 시 기본값 사용
            return "main"

    def _should_include_file(
        self, file_path: Path, extensions: Optional[List[str]] = None
    ) -> bool:
        """파일 포함 여부 확인

        Args:
            file_path: 파일 경로
            extensions: 확장자 필터

        Returns:
            포함 여부
        """
        # 숨김 파일/디렉토리 제외
        if any(part.startswith(".") for part in file_path.parts):
            return False

        # __pycache__ 등 제외
        if "__pycache__" in file_path.parts or "node_modules" in file_path.parts:
            return False

        # 확장자 필터링
        if extensions is None:
            return True

        return file_path.suffix in extensions

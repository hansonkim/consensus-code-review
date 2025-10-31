"""MCP 컨텍스트 수집 모듈

Model Context Protocol을 통해 프로젝트 정보를 수집합니다.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List


class MCPCollector:
    """MCP 컨텍스트 수집기"""

    def __init__(self, project_root: str = "."):
        """초기화

        Args:
            project_root: 프로젝트 루트 경로
        """
        self.project_root = Path(project_root).resolve()

    def collect_context(self) -> Dict[str, Any]:
        """프로젝트 컨텍스트 수집

        Returns:
            컨텍스트 딕셔너리
        """
        context = {
            "repository": self._get_repository_info(),
            "git": self._get_git_info(),
            "files": self._get_file_structure(),
            "conventions": self._detect_conventions(),
        }

        return context

    def _get_repository_info(self) -> Dict[str, Any]:
        """저장소 정보 수집"""
        info = {
            "name": self.project_root.name,
            "path": str(self.project_root),
        }

        # Git 저장소 확인
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                info["remote_url"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return info

    def _get_git_info(self) -> Dict[str, Any]:
        """Git 정보 수집"""
        info = {
            "branch": "",
            "commit": "",
            "status": "",
        }

        try:
            # 현재 브랜치
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                info["branch"] = result.stdout.strip()

            # 현재 커밋
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                info["commit"] = result.stdout.strip()

            # Git 상태
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                status_lines = result.stdout.strip().split("\n")
                info["status"] = f"{len(status_lines)} files changed"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return info

    def _get_file_structure(self) -> Dict[str, Any]:
        """파일 구조 정보"""
        structure = {
            "total_files": 0,
            "languages": {},
            "directories": [],
        }

        # 주요 디렉토리만 탐색
        for path in self.project_root.rglob("*"):
            if self._should_ignore(path):
                continue

            if path.is_file():
                structure["total_files"] += 1
                ext = path.suffix
                structure["languages"][ext] = structure["languages"].get(ext, 0) + 1
            elif path.is_dir() and len(list(path.iterdir())) > 0:
                rel_path = path.relative_to(self.project_root)
                if rel_path != Path("."):
                    structure["directories"].append(str(rel_path))

        return structure

    def _detect_conventions(self) -> List[str]:
        """프로젝트 컨벤션 감지"""
        conventions = []

        # pyproject.toml 체크
        if (self.project_root / "pyproject.toml").exists():
            conventions.append("Python 프로젝트 (pyproject.toml)")

        # requirements.txt 체크
        if (self.project_root / "requirements.txt").exists():
            conventions.append("pip requirements 사용")

        # .gitignore 체크
        if (self.project_root / ".gitignore").exists():
            conventions.append("Git 버전 관리")

        # pytest 체크
        if (self.project_root / "pytest.ini").exists() or (
            self.project_root / "pyproject.toml"
        ).exists():
            conventions.append("pytest 테스트 프레임워크")

        # README 체크
        readme_files = ["README.md", "README.rst", "README.txt"]
        if any((self.project_root / f).exists() for f in readme_files):
            conventions.append("README 문서 존재")

        # 타입 체크 도구
        if (self.project_root / "mypy.ini").exists():
            conventions.append("mypy 타입 체크")

        # 코드 포매터
        if (self.project_root / ".black").exists():
            conventions.append("black 코드 포매터")

        return conventions

    def _should_ignore(self, path: Path) -> bool:
        """무시할 경로인지 확인"""
        ignore_patterns = [
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".mypy_cache",
            ".tox",
            "dist",
            "build",
            "*.egg-info",
        ]

        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True

        return False

    def get_related_files(
        self, target_file: str, max_files: int = 5
    ) -> List[str]:
        """관련 파일 찾기

        Args:
            target_file: 대상 파일
            max_files: 최대 파일 수

        Returns:
            관련 파일 경로 리스트
        """
        target_path = Path(target_file)
        related = []

        # 같은 디렉토리 파일
        if target_path.parent.exists():
            for file in target_path.parent.glob("*.py"):
                if file != target_path:
                    related.append(str(file))
                    if len(related) >= max_files:
                        break

        return related

    def collect_for_review(self, target_path: str) -> Dict[str, Any]:
        """리뷰용 컨텍스트 수집

        Args:
            target_path: 리뷰 대상 경로

        Returns:
            리뷰용 컨텍스트
        """
        base_context = self.collect_context()

        # 관련 파일 추가
        if Path(target_path).is_file():
            base_context["related_files"] = self.get_related_files(target_path)

        return base_context

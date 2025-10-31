"""Filesystem MCP Server

AI가 파일 시스템을 읽고 탐색할 수 있도록 하는 MCP 도구들을 제공합니다.
"""

from pathlib import Path
from typing import List, Dict, Optional


class FileSystemMCP:
    """파일 시스템 작업을 위한 MCP 서버"""

    def __init__(self, root_dir: Optional[str] = None):
        """초기화

        Args:
            root_dir: 루트 디렉토리 (None이면 현재 디렉토리)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()

    def read_file(self, path: str) -> str:
        """파일 읽기

        Args:
            path: 파일 경로

        Returns:
            파일 내용

        Raises:
            FileNotFoundError: 파일이 없을 때
            UnicodeDecodeError: 바이너리 파일일 때
        """
        file_path = self.root_dir / path

        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return "[Binary file - cannot display]"

    def list_files(self, pattern: str = "**/*") -> List[str]:
        """패턴에 맞는 파일 목록 조회

        Args:
            pattern: Glob 패턴 (예: "**/*.py")

        Returns:
            파일 경로 리스트
        """
        files = []
        for path in self.root_dir.glob(pattern):
            if path.is_file():
                # 상대 경로로 변환
                rel_path = path.relative_to(self.root_dir)
                files.append(str(rel_path))
        return sorted(files)

    def get_file_info(self, path: str) -> Dict[str, any]:
        """파일 메타데이터 조회

        Args:
            path: 파일 경로

        Returns:
            파일 정보 딕셔너리
        """
        file_path = self.root_dir / path

        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

        stat = file_path.stat()

        # 줄 수 계산
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f)
        except (UnicodeDecodeError, PermissionError):
            lines = 0

        return {
            "path": str(path),
            "size_bytes": stat.st_size,
            "modified_timestamp": stat.st_mtime,
            "lines": lines,
            "is_binary": lines == 0,
        }

    def file_exists(self, path: str) -> bool:
        """파일 존재 여부 확인

        Args:
            path: 파일 경로

        Returns:
            존재 여부
        """
        file_path = self.root_dir / path
        return file_path.exists() and file_path.is_file()

    def get_available_tools(self) -> List[Dict[str, str]]:
        """사용 가능한 MCP 도구 목록 반환

        Returns:
            도구 목록
        """
        return [
            {
                "name": "read_file",
                "description": "파일 내용 읽기",
                "parameters": "path: str",
                "example": 'read_file("src/main.py")'
            },
            {
                "name": "list_files",
                "description": "패턴에 맞는 파일 목록 조회",
                "parameters": "pattern: str",
                "example": 'list_files("**/*.py")'
            },
            {
                "name": "get_file_info",
                "description": "파일 메타데이터 조회 (크기, 수정 시간, 줄 수 등)",
                "parameters": "path: str",
                "example": 'get_file_info("src/main.py")'
            },
            {
                "name": "file_exists",
                "description": "파일 존재 여부 확인",
                "parameters": "path: str",
                "example": 'file_exists("src/main.py")'
            }
        ]

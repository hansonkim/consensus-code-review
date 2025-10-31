"""MCP 서버 테스트

FileSystemMCP와 GitMCP의 기본 기능을 테스트합니다.
"""

import unittest
import tempfile
import os
from pathlib import Path
from src.mcp import FileSystemMCP, GitMCP, MCPManager


class TestFileSystemMCP(unittest.TestCase):
    """FileSystemMCP 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.mcp = FileSystemMCP(self.temp_dir)

        # 테스트 파일 생성
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('Hello, World!')\n")

        test_dir = Path(self.temp_dir) / "subdir"
        test_dir.mkdir()
        (test_dir / "another.py").write_text("x = 42\n")

    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_read_file(self):
        """파일 읽기 테스트"""
        content = self.mcp.read_file("test.py")
        self.assertEqual(content, "print('Hello, World!')\n")

    def test_read_file_not_found(self):
        """존재하지 않는 파일 읽기 테스트"""
        with self.assertRaises(FileNotFoundError):
            self.mcp.read_file("nonexistent.py")

    def test_list_files(self):
        """파일 목록 조회 테스트"""
        files = self.mcp.list_files("**/*.py")
        self.assertEqual(len(files), 2)
        self.assertIn("test.py", files)
        self.assertIn("subdir/another.py", files)

    def test_get_file_info(self):
        """파일 정보 조회 테스트"""
        info = self.mcp.get_file_info("test.py")
        self.assertIn("path", info)
        self.assertIn("size_bytes", info)
        self.assertIn("lines", info)
        self.assertEqual(info["lines"], 1)

    def test_file_exists(self):
        """파일 존재 여부 확인 테스트"""
        self.assertTrue(self.mcp.file_exists("test.py"))
        self.assertFalse(self.mcp.file_exists("missing.py"))

    def test_get_available_tools(self):
        """사용 가능한 도구 목록 테스트"""
        tools = self.mcp.get_available_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

        # 도구 구조 확인
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("parameters", tool)
            self.assertIn("example", tool)


class TestGitMCP(unittest.TestCase):
    """GitMCP 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.mcp = GitMCP()

    def test_get_current_branch(self):
        """현재 브랜치 조회 테스트"""
        try:
            branch = self.mcp.get_current_branch()
            self.assertIsInstance(branch, str)
            self.assertGreater(len(branch), 0)
        except RuntimeError:
            # Git 리포지토리가 아닐 수 있음
            self.skipTest("Not a git repository")

    def test_get_available_tools(self):
        """사용 가능한 도구 목록 테스트"""
        tools = self.mcp.get_available_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

        # 기대하는 도구들이 있는지 확인
        tool_names = [t["name"] for t in tools]
        self.assertIn("get_diff", tool_names)
        self.assertIn("get_changed_files", tool_names)
        self.assertIn("get_blame", tool_names)


class TestMCPManager(unittest.TestCase):
    """MCPManager 테스트"""

    def setUp(self):
        """테스트 환경 설정"""
        self.manager = MCPManager()

    def test_get_all_tools(self):
        """모든 도구 목록 조회 테스트"""
        tools = self.manager.get_all_tools()
        self.assertIsInstance(tools, dict)

        # filesystem과 git 서버가 있어야 함
        self.assertIn("filesystem", tools)
        self.assertIn("git", tools)

        # 각 서버에 도구들이 있어야 함
        self.assertGreater(len(tools["filesystem"]), 0)
        self.assertGreater(len(tools["git"]), 0)

    def test_generate_tool_description(self):
        """도구 설명 문서 생성 테스트"""
        doc = self.manager.generate_tool_description()
        self.assertIsInstance(doc, str)
        self.assertGreater(len(doc), 100)

        # 주요 섹션이 포함되어 있는지 확인
        self.assertIn("Available MCP Tools", doc)
        self.assertIn("Filesystem", doc)
        self.assertIn("Git", doc)

    def test_call_tool(self):
        """도구 호출 테스트"""
        # Git current branch 호출
        try:
            result = self.manager.call_tool("git", "get_current_branch")
            self.assertIsInstance(result, str)
        except RuntimeError:
            self.skipTest("Not a git repository")

    def test_call_tool_invalid_server(self):
        """존재하지 않는 서버 호출 테스트"""
        with self.assertRaises(ValueError):
            self.manager.call_tool("invalid_server", "some_tool")

    def test_call_tool_invalid_tool(self):
        """존재하지 않는 도구 호출 테스트"""
        with self.assertRaises(ValueError):
            self.manager.call_tool("git", "nonexistent_tool")


if __name__ == "__main__":
    unittest.main()

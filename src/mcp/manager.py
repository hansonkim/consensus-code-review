"""MCP Manager

MCP 서버들을 관리하고 AI에게 도구 목록을 제공합니다.
"""

from typing import Dict, List, Any
from .filesystem import FileSystemMCP
from .git import GitMCP
from .review_orchestrator import ReviewOrchestrator


class MCPManager:
    """MCP 서버 매니저"""

    def __init__(self, root_dir: str = None):
        """초기화

        Args:
            root_dir: 루트 디렉토리
        """
        self.filesystem = FileSystemMCP(root_dir)
        self.git = GitMCP()
        self.orchestrator = ReviewOrchestrator()
        self.servers = {
            "filesystem": self.filesystem,
            "git": self.git,
            "review": self.orchestrator
        }

    def get_all_tools(self) -> Dict[str, List[Dict[str, str]]]:
        """모든 MCP 도구 목록 조회

        Returns:
            {server_name: [tools]} 형태의 딕셔너리
        """
        tools = {}
        for name, server in self.servers.items():
            if hasattr(server, 'get_available_tools'):
                tools[name] = server.get_available_tools()
        return tools

    def generate_tool_description(self) -> str:
        """AI를 위한 도구 설명 문서 생성

        Returns:
            마크다운 형식의 도구 설명
        """
        tools_by_server = self.get_all_tools()

        doc = "## Available MCP Tools\n\n"
        doc += "You have access to the following tools for code review:\n\n"

        for server_name, tools in tools_by_server.items():
            doc += f"### {server_name.capitalize()} Tools\n\n"

            for tool in tools:
                doc += f"**`{tool['name']}`**\n"
                doc += f"- Description: {tool['description']}\n"
                doc += f"- Parameters: `{tool['parameters']}`\n"
                doc += f"- Example: `{tool['example']}`\n\n"

        return doc

    def call_tool(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """MCP 도구 호출

        Args:
            server_name: 서버 이름 (filesystem, git)
            tool_name: 도구 이름
            **kwargs: 도구 파라미터

        Returns:
            도구 실행 결과

        Raises:
            ValueError: 서버나 도구를 찾을 수 없을 때
        """
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")

        server = self.servers[server_name]

        if not hasattr(server, tool_name):
            raise ValueError(f"Unknown tool: {tool_name} in {server_name}")

        method = getattr(server, tool_name)
        return method(**kwargs)

    def get_context_for_review(self, base_branch: str, head_branch: str = "HEAD") -> Dict[str, Any]:
        """리뷰를 위한 컨텍스트 정보 수집

        Args:
            base_branch: 기준 브랜치
            head_branch: 비교 대상 브랜치

        Returns:
            컨텍스트 정보 딕셔너리
        """
        context = {}

        # Git 정보
        try:
            context["current_branch"] = self.git.get_current_branch()
            context["changed_files"] = self.git.get_changed_files(base_branch, head_branch)
            context["diff_stats"] = self.git.get_diff_stats(base_branch, head_branch)
        except Exception as e:
            context["git_error"] = str(e)

        return context

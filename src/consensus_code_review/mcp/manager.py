"""MCP Manager

MCP 서버들을 관리하고 AI에게 도구 목록을 제공합니다.

Pure Task Delegation Architecture:
- Python이 모든 Git/Filesystem 작업을 내부적으로 처리
- AI는 큐레이션된 데이터만 받아서 리뷰 작성에 집중
- AI에게는 review session 관리 도구만 제공
"""

from typing import Any, Dict, List

from .review_orchestrator import ReviewOrchestrator


class MCPManager:
    """MCP 서버 매니저 (Pure Task Delegation)

    AI에게 Git/Filesystem 탐색 도구를 제공하지 않습니다.
    Python이 모든 객관적 작업을 처리하고,
    AI는 리뷰 작성(주관적 작업)만 수행합니다.
    """

    def __init__(self, root_dir: str = None):
        """초기화

        Args:
            root_dir: 루트 디렉토리 (사용되지 않음, 하위 호환성 유지)
        """
        # Review session 관리 도구만 제공
        self.orchestrator = ReviewOrchestrator()
        self.servers = {"review": self.orchestrator}

    def get_all_tools(self) -> Dict[str, List[Dict[str, str]]]:
        """모든 MCP 도구 목록 조회

        Returns:
            {server_name: [tools]} 형태의 딕셔너리
        """
        tools = {}
        for name, server in self.servers.items():
            if hasattr(server, "get_available_tools"):
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
            server_name: 서버 이름 (review만 허용)
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

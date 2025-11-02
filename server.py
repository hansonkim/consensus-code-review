#!/usr/bin/env python3
"""MCP Server for Consensus Code Review

Claude Code와 통신하기 위한 stdio 기반 MCP 서버입니다.
다른 AI CLI들과의 합의 기반 코드 리뷰를 제공합니다.
"""

import sys
import json
import traceback
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from consensus_code_review.mcp import MCPManager


class MCPServer:
    """MCP 프로토콜 서버"""

    def __init__(self):
        """초기화"""
        self.manager = MCPManager()

        # 디버깅을 위한 로그 파일 (활성화)
        # logs 디렉토리가 없으면 자동 생성
        log_dir = Path("./logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = open(log_dir / "mcp_server.log", "a")
        self.log("=" * 70)
        self.log("MCP Server initialized")

    def log(self, message: str):
        """디버그 로그 (stderr에 출력하지 않음)"""
        if self.log_file:
            self.log_file.write(f"{message}\n")
            self.log_file.flush()

    def handle_request(self, request: dict) -> dict:
        """MCP 요청 처리

        Args:
            request: MCP 요청 딕셔너리

        Returns:
            MCP 응답 딕셔너리
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        self.log(f"Request: method={method}, id={request_id}, params={list(params.keys()) if params else 'none'}")

        try:
            # tools/list - 사용 가능한 도구 목록
            if method == "tools/list":
                tools = []
                all_tools = self.manager.get_all_tools()

                for server_name, server_tools in all_tools.items():
                    for tool in server_tools:
                        tools.append({
                            "name": f"{server_name}_{tool['name']}",
                            "description": tool["description"],
                            "inputSchema": {
                                "type": "object",
                                "properties": self._parse_parameters(tool["parameters"]),
                                "required": []
                            }
                        })

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools}
                }

            # tools/call - 도구 실행
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                # 서버 이름과 도구 이름 분리
                if "_" in tool_name:
                    server_name, method_name = tool_name.split("_", 1)
                else:
                    return self._error_response(request_id, "Invalid tool name format")

                # 도구 실행
                result = self.manager.call_tool(server_name, method_name, **arguments)

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": str(result)
                            }
                        ]
                    }
                }

            # initialize - 서버 초기화
            elif method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {}
                        },
                        "serverInfo": {
                            "name": "consensus-code-review",
                            "version": "2.0.0"
                        }
                    }
                }

            # resources/list - 리소스 목록 (파일 경로들)
            elif method == "resources/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "resources": [
                            {
                                "uri": "file:///",
                                "name": "Project Files",
                                "description": "Access project files through filesystem MCP tools",
                                "mimeType": "text/plain"
                            }
                        ]
                    }
                }

            # resources/read - 리소스 읽기
            elif method == "resources/read":
                uri = params.get("uri")
                if uri and uri.startswith("file://"):
                    path = uri[7:]  # Remove "file://"
                    try:
                        content = self.manager.call_tool("filesystem", "read_file", path=path)
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "contents": [
                                    {
                                        "uri": uri,
                                        "mimeType": "text/plain",
                                        "text": content
                                    }
                                ]
                            }
                        }
                    except Exception as e:
                        return self._error_response(request_id, f"Failed to read resource: {e}")
                else:
                    return self._error_response(request_id, "Invalid resource URI")

            # notifications/initialized - 초기화 완료 알림
            elif method == "notifications/initialized":
                # notification은 응답 불필요
                return None

            else:
                self.log(f"Unknown method: {method}")
                return self._error_response(request_id, f"Unknown method: {method}")

        except Exception as e:
            self.log(f"Error handling request: {e}")
            self.log(traceback.format_exc())
            return self._error_response(request_id, str(e))

    def _parse_parameters(self, params_str: str) -> dict:
        """파라미터 문자열을 JSON Schema로 변환

        Args:
            params_str: "path: str, line: int" 형식

        Returns:
            JSON Schema properties
        """
        properties = {}

        if not params_str or params_str == "없음":
            return properties

        for param in params_str.split(","):
            param = param.strip()
            if ":" in param:
                name, type_str = param.split(":", 1)
                name = name.strip()
                type_str = type_str.strip()

                # Python 타입을 JSON Schema 타입으로 변환
                if "str" in type_str:
                    properties[name] = {"type": "string"}
                elif "int" in type_str:
                    properties[name] = {"type": "integer"}
                elif "bool" in type_str:
                    properties[name] = {"type": "boolean"}
                elif "dict" in type_str or "Dict" in type_str:
                    properties[name] = {"type": "object"}
                elif "list" in type_str or "List" in type_str:
                    properties[name] = {"type": "array"}
                else:
                    properties[name] = {"type": "string"}

        return properties

    def _error_response(self, request_id, message: str) -> dict:
        """에러 응답 생성"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": message
            }
        }

    def run(self):
        """서버 실행 (stdio 루프)"""
        self.log("MCP Server started")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    self.log(f"Request: {request}")

                    response = self.handle_request(request)

                    if response:  # notification은 응답 없음
                        response_str = json.dumps(response)
                        self.log(f"Response: {response_str}")
                        print(response_str, flush=True)

                except json.JSONDecodeError as e:
                    self.log(f"JSON decode error: {e}")
                    continue

        except KeyboardInterrupt:
            self.log("Server interrupted")
        finally:
            if self.log_file:
                self.log_file.close()


if __name__ == "__main__":
    server = MCPServer()
    server.run()

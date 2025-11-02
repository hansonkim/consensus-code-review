#!/usr/bin/env python3
"""Verify MCP server setup"""

import json
import subprocess
import sys
from pathlib import Path


def test_server_starts():
    """Test if server can start"""
    print("1. Testing if MCP server starts...")
    try:
        # Send initialize request
        request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        result = subprocess.run(
            ["python3", "src/mcp/server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=5,
        )
        response = json.loads(result.stdout)
        assert response.get("result", {}).get("serverInfo", {}).get("name") == "ai-code-review-mcp"
        print("   ✅ Server starts successfully")
        return True
    except Exception as e:
        print(f"   ❌ Server failed to start: {e}")
        return False


def test_tools_list():
    """Test if tools can be listed"""
    print("2. Testing tools/list...")
    try:
        request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        result = subprocess.run(
            ["python3", "src/mcp/server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=5,
        )
        response = json.loads(result.stdout)
        tools = response.get("result", {}).get("tools", [])
        assert len(tools) > 0
        print(f"   ✅ Found {len(tools)} tools")
        for tool in tools[:3]:
            print(f"      - {tool['name']}")
        return True
    except Exception as e:
        print(f"   ❌ Tools list failed: {e}")
        return False


def test_filesystem_tool():
    """Test filesystem.read_file"""
    print("3. Testing filesystem_read_file...")
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "filesystem_read_file", "arguments": {"path": "README.md"}},
        }
        result = subprocess.run(
            ["python3", "src/mcp/server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=5,
        )
        response = json.loads(result.stdout)
        content = response.get("result", {}).get("content", [{}])[0].get("text", "")
        assert len(content) > 0
        print(f"   ✅ Read README.md ({len(content)} chars)")
        return True
    except Exception as e:
        print(f"   ❌ Filesystem tool failed: {e}")
        return False


def check_config_file():
    """Check if Claude config exists"""
    print("4. Checking Claude CLI configuration...")
    config_path = Path.home() / ".claude" / "claude_desktop_config.json"
    if config_path.exists():
        print(f"   ✅ Config file exists: {config_path}")
        try:
            with open(config_path) as f:
                config = json.load(f)
            if "ai-code-review" in config.get("mcpServers", {}):
                print("   ✅ ai-code-review server configured")
                return True
            else:
                print("   ⚠️  ai-code-review server not found in config")
                return False
        except Exception as e:
            print(f"   ❌ Failed to read config: {e}")
            return False
    else:
        print(f"   ⚠️  Config file not found: {config_path}")
        print("      Create it with the configuration from docs/MCP_SETUP.md")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("MCP Server Setup Verification")
    print("=" * 70)
    print()

    results = [test_server_starts(), test_tools_list(), test_filesystem_tool(), check_config_file()]

    print()
    print("=" * 70)
    if all(results):
        print("✅ All checks passed! MCP server is ready.")
        print()
        print("Next steps:")
        print("1. Run: ai-review --help")
        print("2. Try: ai-review --branch develop")
        print("3. Check Claude CLI can use MCP tools")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please review the errors above.")
        sys.exit(1)

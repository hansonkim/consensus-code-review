# MCP Server Setup Guide

## Overview

This guide shows how to connect the AI Code Review MCP server to Claude CLI, enabling AI agents to read files and access Git information directly using MCP tools instead of embedding content in prompts.

## Architecture

```
┌─────────────────┐
│   Claude CLI    │
│  (AI Client)    │
└────────┬────────┘
         │ JSON-RPC via stdio
         │ (tools/list, tools/call)
         ▼
┌─────────────────┐
│   MCP Server    │
│  (server.py)    │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌─────────┐
│FileSystem│ │ Git MCP │
│   MCP    │ │         │
└──────────┘ └─────────┘
```

## Configuration for Claude CLI

### 1. Configuration File Location

Claude CLI uses a configuration file to register MCP servers. The location depends on your OS:

- **macOS/Linux**: `~/.claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\.claude\claude_desktop_config.json`

### 2. Configuration JSON

Create or update the configuration file with the following content:

```json
{
  "mcpServers": {
    "ai-code-review": {
      "command": "python3",
      "args": [
        "/absolute/path/to/ai-code-review/src/mcp/server.py"
      ],
      "description": "AI Code Review MCP Server - provides filesystem and git tools for autonomous code review",
      "env": {}
    }
  }
}
```

**Important**: Replace `/absolute/path/to/ai-code-review` with your actual project path.

### 3. Get Your Absolute Path

Run this command in your project directory:

```bash
pwd
```

Example output: `/Users/hanson/PycharmProjects/ai-code-review`

Then update the config to:

```json
{
  "mcpServers": {
    "ai-code-review": {
      "command": "python3",
      "args": [
        "/Users/hanson/PycharmProjects/ai-code-review/src/mcp/server.py"
      ],
      "description": "AI Code Review MCP Server",
      "env": {}
    }
  }
}
```

### 4. Make Server Executable

```bash
chmod +x src/mcp/server.py
```

## Configuration for Your Project (Recommended)

For easier setup, create a configuration file in your project:

**config/claude_mcp_config.json**:

```json
{
  "mcpServers": {
    "ai-code-review": {
      "command": "python3",
      "args": [
        "$(pwd)/src/mcp/server.py"
      ],
      "description": "AI Code Review MCP Server",
      "env": {
        "PYTHONPATH": "$(pwd)"
      }
    }
  }
}
```

Then create a symlink:

```bash
# macOS/Linux
mkdir -p ~/.claude
ln -sf "$(pwd)/config/claude_mcp_config.json" ~/.claude/claude_desktop_config.json

# Or manually copy
cp config/claude_mcp_config.json ~/.claude/claude_desktop_config.json
```

## Available MCP Tools

Once connected, Claude CLI will have access to these tools:

### Filesystem Tools

- `filesystem_read_file` - Read file contents
- `filesystem_list_files` - List files with glob patterns
- `filesystem_get_file_info` - Get file metadata (size, lines, modified time)
- `filesystem_file_exists` - Check if file exists

### Git Tools

- `git_get_current_branch` - Get current branch name
- `git_get_diff` - Get diff between branches/commits
- `git_get_changed_files` - Get list of changed files
- `git_get_diff_stats` - Get diff statistics (files changed, insertions, deletions)
- `git_get_blame` - Get blame info for specific lines
- `git_get_commit_info` - Get commit details by hash
- `git_get_file_history` - Get commit history for a file

## Testing the Connection

### 1. Test MCP Server Standalone

```bash
# Test the server can start
python3 src/mcp/server.py
```

It should wait for input (stdio mode). Press Ctrl+C to exit.

### 2. Test with Manual Input

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 src/mcp/server.py
```

Expected output:
```json
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "ai-code-review-mcp", "version": "1.0.0"}}}
```

### 3. Test Tool List

```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python3 src/mcp/server.py
```

Should return a list of all available tools.

### 4. Test with Claude CLI

Create a test script:

**test_mcp_connection.sh**:

```bash
#!/bin/bash
# Test if Claude CLI can see MCP tools

claude --version
echo ""
echo "Checking MCP tools..."
claude mcp list

echo ""
echo "Testing filesystem.read_file..."
claude "Use the filesystem_read_file tool to read README.md"
```

## Verification Script

Create this verification script:

**scripts/verify_mcp_setup.py**:

```python
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
            timeout=5
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
            timeout=5
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
            "params": {
                "name": "filesystem_read_file",
                "arguments": {"path": "README.md"}
            }
        }
        result = subprocess.run(
            ["python3", "src/mcp/server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=5
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
        print(f"      Create it with the configuration from docs/MCP_SETUP.md")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("MCP Server Setup Verification")
    print("=" * 70)
    print()

    results = [
        test_server_starts(),
        test_tools_list(),
        test_filesystem_tool(),
        check_config_file()
    ]

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
```

Make it executable:

```bash
chmod +x scripts/verify_mcp_setup.py
python3 scripts/verify_mcp_setup.py
```

## Usage Example

Once configured, when you run:

```bash
ai-review --branch develop
```

The AI agents will:

1. **NOT** receive file contents in the prompt (saves tokens!)
2. **USE** MCP tools to:
   - Check git diff: `git_get_diff("main", "develop")`
   - Get changed files: `git_get_changed_files("main", "develop")`
   - Read specific files: `filesystem_read_file("src/analyzer.py")`
   - Check blame: `git_get_blame("src/analyzer.py", 45, 67)`

## Troubleshooting

### Server Not Found

**Error**: `MCP server 'ai-code-review' not found`

**Solution**: Check config file location and content:

```bash
cat ~/.claude/claude_desktop_config.json
```

### Permission Denied

**Error**: `Permission denied: src/mcp/server.py`

**Solution**: Make it executable:

```bash
chmod +x src/mcp/server.py
```

### Python Path Issues

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Add PYTHONPATH to config:

```json
{
  "mcpServers": {
    "ai-code-review": {
      "command": "python3",
      "args": ["/absolute/path/to/src/mcp/server.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/ai-code-review"
      }
    }
  }
}
```

### Server Hangs

**Error**: Server starts but hangs

**Solution**: Server runs in stdio mode - it's waiting for JSON-RPC input. This is normal behavior.

## Configuration for Other AI CLIs

### OpenAI CLI (if MCP support added)

Similar configuration pattern:

```json
{
  "mcpServers": {
    "ai-code-review": {
      "command": "python3",
      "args": ["/absolute/path/to/src/mcp/server.py"],
      "protocol": "stdio"
    }
  }
}
```

### Gemini CLI (if MCP support added)

Check Gemini CLI documentation for MCP server configuration format.

## Benefits

### Before MCP (Embedding Files)

```python
# ❌ Old approach - embed 50 files = 250K tokens
prompt = """
Review these files:

File: src/analyzer.py
```python
[10000 lines of code]
```

File: src/phase1_reviewer.py
```python
[5000 lines of code]
```
... (48 more files)
"""

# Result: Token explosion, API errors, limited to 20-30 files
```

### After MCP (Delegation)

```python
# ✅ New approach - AI reads on demand = 25K tokens
prompt = """
Files to review: 50

Use these tools:
- filesystem_read_file(path)
- git_get_diff("main", "develop")

Review the changes.
"""

# AI internally:
diff = git_get_diff("main", "develop")  # Check what changed
changed_files = git_get_changed_files()  # Get file list
for file in important_files:
    content = filesystem_read_file(file)  # Read only needed files
    analyze(content)

# Result: 10x less tokens, handles 1000+ files
```

## Next Steps

1. ✅ Create configuration file
2. ✅ Run verification script
3. ✅ Test with small repo (5-10 files)
4. ✅ Test with large repo (100+ files)
5. ✅ Compare token usage before/after

## References

- MCP Protocol: https://spec.modelcontextprotocol.io/
- Claude CLI: https://docs.anthropic.com/claude/docs/claude-cli
- Project Architecture: [ARCHITECTURE_REDESIGN.md](ARCHITECTURE_REDESIGN.md)

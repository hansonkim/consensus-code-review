#!/bin/bash
# Diagnose MCP Server Connection Issues

echo "========================================================================"
echo "MCP Server Diagnostics"
echo "========================================================================"
echo ""

# Clear old logs
rm -f /tmp/mcp_server.log

# Test 1: Initialize
echo "1. Testing initialize..."
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}' | python3 src/mcp/server.py > /tmp/init_response.json 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Initialize successful"
    echo "Response:"
    cat /tmp/init_response.json | python3 -m json.tool
else
    echo "❌ Initialize failed"
fi
echo ""

# Test 2: Tools list
echo "2. Testing tools/list..."
(
    echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
    echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
) | python3 src/mcp/server.py > /tmp/tools_response.json 2>&1

echo "Response:"
tail -1 /tmp/tools_response.json | python3 -m json.tool
echo ""

# Test 3: Resources list
echo "3. Testing resources/list..."
(
    echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
    echo '{"jsonrpc":"2.0","id":2,"method":"resources/list","params":{}}'
) | python3 src/mcp/server.py > /tmp/resources_response.json 2>&1

echo "Response:"
tail -1 /tmp/resources_response.json | python3 -m json.tool
echo ""

# Show server logs
echo "4. Server logs:"
echo "========================================================================"
if [ -f /tmp/mcp_server.log ]; then
    cat /tmp/mcp_server.log
else
    echo "No logs found at /tmp/mcp_server.log"
fi
echo "========================================================================"
echo ""

# Check Claude config
echo "5. Claude CLI Configuration:"
CLAUDE_CONFIG="$HOME/.claude/claude_desktop_config.json"
if [ -f "$CLAUDE_CONFIG" ]; then
    echo "✅ Config exists: $CLAUDE_CONFIG"
    echo "Content:"
    cat "$CLAUDE_CONFIG" | python3 -m json.tool
else
    echo "❌ Config not found: $CLAUDE_CONFIG"
    echo "Run: ./scripts/setup_mcp_config.sh"
fi
echo ""

# Summary
echo "========================================================================"
echo "Diagnostic Summary"
echo "========================================================================"
echo ""
echo "To view real-time logs when Claude CLI connects:"
echo "  tail -f /tmp/mcp_server.log"
echo ""
echo "To manually test tools:"
echo "  echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}' | python3 src/mcp/server.py"
echo ""
echo "To check if Claude CLI can see the server:"
echo "  Run Claude CLI and use listMcpResources('ai-code-review')"
echo "  Then check: tail -f /tmp/mcp_server.log"
echo ""

#!/bin/bash
# Setup MCP configuration for Claude CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/config/claude_mcp_config.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "AI Code Review - MCP Configuration Setup"
echo "========================================================================"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Update paths in config
echo "📝 Updating configuration with absolute paths..."
TMP_CONFIG=$(mktemp)
sed "s|/Users/hanson/PycharmProjects/ai-code-review|$PROJECT_DIR|g" "$CONFIG_FILE" > "$TMP_CONFIG"

# Determine Claude config location
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/.claude"
    CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    CLAUDE_CONFIG_DIR="$APPDATA/.claude"
    CLAUDE_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
else
    echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

# Create Claude config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Check if config already exists
if [ -f "$CLAUDE_CONFIG" ]; then
    echo -e "${YELLOW}⚠️  Claude config already exists: $CLAUDE_CONFIG${NC}"
    echo ""
    read -p "Do you want to backup and replace it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BACKUP="${CLAUDE_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CLAUDE_CONFIG" "$BACKUP"
        echo -e "${GREEN}✅ Backed up to: $BACKUP${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping config update${NC}"
        echo ""
        echo "To manually merge the configuration:"
        echo "1. Open: $CLAUDE_CONFIG"
        echo "2. Add the ai-code-review server from: $TMP_CONFIG"
        rm "$TMP_CONFIG"
        exit 0
    fi
fi

# Copy config
cp "$TMP_CONFIG" "$CLAUDE_CONFIG"
rm "$TMP_CONFIG"

echo -e "${GREEN}✅ Configuration installed: $CLAUDE_CONFIG${NC}"
echo ""

# Make server executable
SERVER_SCRIPT="$PROJECT_DIR/src/mcp/server.py"
if [ -f "$SERVER_SCRIPT" ]; then
    chmod +x "$SERVER_SCRIPT"
    echo -e "${GREEN}✅ Server script is executable${NC}"
else
    echo -e "${RED}❌ Server script not found: $SERVER_SCRIPT${NC}"
    exit 1
fi

# Show configuration
echo ""
echo "========================================================================"
echo "Configuration Details"
echo "========================================================================"
echo ""
echo "Config file: $CLAUDE_CONFIG"
echo "Server script: $SERVER_SCRIPT"
echo "Project directory: $PROJECT_DIR"
echo ""

# Run verification
echo "Running verification tests..."
echo ""

if [ -f "$PROJECT_DIR/scripts/verify_mcp_setup.py" ]; then
    python3 "$PROJECT_DIR/scripts/verify_mcp_setup.py"
else
    echo -e "${YELLOW}⚠️  Verification script not found${NC}"
fi

echo ""
echo "========================================================================"
echo -e "${GREEN}✅ MCP Setup Complete!${NC}"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "1. Restart Claude CLI (if running)"
echo "2. Test with: ai-review --help"
echo "3. Try: ai-review --branch develop"
echo ""

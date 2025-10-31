#!/bin/bash

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                   AI Code Review System Uninstaller                      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# ai-review 설치 확인
if ! command -v ai-review &> /dev/null; then
    echo -e "${YELLOW}⚠ ai-review가 설치되어 있지 않습니다${NC}"
    exit 0
fi

# 제거 확인
echo -e "${YELLOW}ai-review를 제거하시겠습니까? (y/n)${NC}"
read -r response

if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${GREEN}제거를 취소했습니다${NC}"
    exit 0
fi

# 제거 실행
echo ""
echo -e "${BLUE}→ ai-review 제거 중...${NC}"
uv tool uninstall ai-review

# 제거 확인
if ! command -v ai-review &> /dev/null; then
    echo ""
    echo -e "${GREEN}✓ ai-review가 성공적으로 제거되었습니다${NC}"
    echo ""
    echo -e "${YELLOW}다시 설치하려면:${NC}"
    echo "  ./install.sh"
    echo ""
else
    echo ""
    echo -e "${RED}✗ 제거 실패${NC}"
    echo ""
    echo "수동으로 제거하려면 다음 명령을 실행하세요:"
    echo "  uv tool uninstall ai-review"
    exit 1
fi

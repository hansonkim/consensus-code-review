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
║                    AI Code Review System Installer                       ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# 1. uv 설치 확인
echo -e "${YELLOW}[1/3] uv 설치 확인 중...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv가 설치되어 있지 않습니다.${NC}"
    echo ""
    echo -e "${YELLOW}uv를 설치하시겠습니까? (y/n)${NC}"
    read -r response

    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${BLUE}→ uv 설치 중...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # PATH에 uv 추가
        export PATH="$HOME/.cargo/bin:$PATH"

        # 설치 확인
        if ! command -v uv &> /dev/null; then
            echo -e "${RED}✗ uv 설치 실패${NC}"
            echo ""
            echo "수동으로 설치하려면 다음 명령을 실행하세요:"
            echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
            exit 1
        fi

        echo -e "${GREEN}✓ uv 설치 완료${NC}"
    else
        echo ""
        echo "uv를 먼저 설치해주세요:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
else
    echo -e "${GREEN}✓ uv가 이미 설치되어 있습니다 ($(uv --version))${NC}"
fi

echo ""

# 2. 프로젝트 경로 확인
echo -e "${YELLOW}[2/3] 프로젝트 확인 중...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$SCRIPT_DIR/pyproject.toml" ]; then
    echo -e "${RED}✗ pyproject.toml을 찾을 수 없습니다${NC}"
    echo "이 스크립트는 프로젝트 루트에서 실행해야 합니다."
    exit 1
fi

echo -e "${GREEN}✓ 프로젝트 경로: $SCRIPT_DIR${NC}"
echo ""

# 3. ai-review 설치
echo -e "${YELLOW}[3/3] ai-review 설치 중...${NC}"

# 기존 설치 확인
if command -v ai-review &> /dev/null; then
    echo -e "${YELLOW}⚠ ai-review가 이미 설치되어 있습니다${NC}"
    echo ""
    echo -e "${YELLOW}재설치하시겠습니까? (y/n)${NC}"
    read -r response

    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${BLUE}→ 재설치 중...${NC}"
        uv tool install --editable "$SCRIPT_DIR" --force
    else
        echo -e "${GREEN}✓ 설치를 건너뛰었습니다${NC}"
    fi
else
    echo -e "${BLUE}→ 설치 중...${NC}"
    uv tool install --editable "$SCRIPT_DIR"
fi

echo ""

# 4. 설치 확인
echo -e "${YELLOW}설치 확인 중...${NC}"
if command -v ai-review &> /dev/null; then
    echo -e "${GREEN}✓ ai-review 설치 완료!${NC}"
    echo ""

    # 성공 메시지
    echo -e "${GREEN}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                    🎉 설치가 완료되었습니다! 🎉                          ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    # 사용법 안내
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}🚀 사용법:${NC}"
    echo ""
    echo -e "  ${GREEN}# PR 전 리뷰 (가장 많이 사용)${NC}"
    echo -e "  ${BLUE}ai-review --staged${NC}"
    echo ""
    echo -e "  ${GREEN}# 브랜치 변경사항 리뷰${NC}"
    echo -e "  ${BLUE}ai-review --branch${NC}"
    echo ""
    echo -e "  ${GREEN}# 특정 파일 리뷰${NC}"
    echo -e "  ${BLUE}ai-review file.py${NC}"
    echo ""
    echo -e "  ${GREEN}# 디렉토리 리뷰${NC}"
    echo -e "  ${BLUE}ai-review ./src/${NC}"
    echo ""
    echo -e "  ${GREEN}# 커밋 범위 리뷰${NC}"
    echo -e "  ${BLUE}ai-review --commits HEAD~5..HEAD${NC}"
    echo ""
    echo -e "  ${GREEN}# 도움말 보기${NC}"
    echo -e "  ${BLUE}ai-review --help${NC}"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}💡 팁:${NC}"
    echo "  • 다른 디렉토리에서도 'ai-review' 명령어를 사용할 수 있습니다"
    echo "  • Pre-commit hook으로 설정하여 자동 리뷰를 받을 수 있습니다"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}📚 문서:${NC}"
    echo "  • README.md - 전체 문서"
    echo "  • docs/QUICK_START.md - 빠른 시작 가이드"
    echo "  • docs/CLI_USAGE.md - 상세 사용법"
    echo ""
    echo -e "${GREEN}지금 바로 사용해보세요! 🚀${NC}"
    echo ""

else
    echo -e "${RED}✗ 설치 확인 실패${NC}"
    echo ""
    echo "문제가 발생했습니다. 다음을 확인해주세요:"
    echo "  1. uv가 올바르게 설치되었는지 확인: uv --version"
    echo "  2. 터미널을 재시작하거나 다음 명령 실행:"
    echo "     export PATH=\"\$HOME/.cargo/bin:\$PATH\""
    echo "  3. 수동 설치 시도:"
    echo "     uv tool install --editable $SCRIPT_DIR"
    exit 1
fi

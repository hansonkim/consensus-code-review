# AI Code Review System - 설치 가이드

## 🚀 빠른 설치 (권장)

### uv tool로 설치 (가장 쉬운 방법)

```bash
# 1. 저장소 클론
git clone <repository-url>
cd ai-code-review

# 2. 설치 스크립트 실행
./install.sh
```

설치가 완료되면 **어느 디렉토리에서든** `ai-review` 명령어를 사용할 수 있습니다!

---

## 📦 설치 방법 상세

### 방법 1: install.sh 스크립트 (권장)

**가장 쉽고 자동화된 방법입니다.**

```bash
# 프로젝트 디렉토리에서
./install.sh
```

**스크립트가 자동으로:**
- ✅ uv 설치 여부 확인 (없으면 설치 안내)
- ✅ ai-review를 uv tool로 설치
- ✅ PATH에 자동 추가
- ✅ 설치 확인 및 사용법 안내

### 방법 2: 수동 uv tool 설치

```bash
# 1. uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. ai-review 설치
cd /path/to/ai-code-review
uv tool install --editable .

# 3. 설치 확인
ai-review --help
```

### 방법 3: pip install (개발 모드)

```bash
# 프로젝트 디렉토리에서
pip install -e .

# 확인
python -m ai_code_review --help
```

---

## ✅ 설치 확인

설치가 완료되었는지 확인:

```bash
# 버전 확인
ai-review --help

# 테스트 실행
cd /path/to/your/project
ai-review --staged
```

---

## 🗑️ 제거

### uninstall.sh 스크립트 사용

```bash
./uninstall.sh
```

### 수동 제거

```bash
# uv tool로 설치한 경우
uv tool uninstall ai-review

# pip로 설치한 경우
pip uninstall ai-code-review
```

---

## 🔄 업데이트

### uv tool로 설치한 경우

```bash
# 프로젝트 디렉토리에서 최신 코드 가져오기
cd /path/to/ai-code-review
git pull

# 재설치 (editable 모드는 자동으로 최신 코드 반영)
uv tool install --editable . --force
```

### pip로 설치한 경우

```bash
cd /path/to/ai-code-review
git pull
pip install -e . --upgrade
```

---

## 🛠️ 트러블슈팅

### "ai-review: command not found"

**원인**: PATH에 추가되지 않았습니다.

**해결책**:

```bash
# uv tool 경로 확인
uv tool list

# PATH에 추가 (Linux/Mac)
export PATH="$HOME/.local/bin:$PATH"

# PATH에 추가 (Mac with Homebrew)
export PATH="$HOME/.cargo/bin:$PATH"

# 영구적으로 추가 (~/.zshrc 또는 ~/.bashrc)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### "uv: command not found"

**원인**: uv가 설치되지 않았습니다.

**해결책**:

```bash
# uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# 터미널 재시작 또는
source ~/.zshrc  # 또는 ~/.bashrc
```

### 설치는 되었는데 실행 안됨

**해결책**:

```bash
# 1. 설치 확인
which ai-review

# 2. Python 경로 확인
python --version

# 3. 재설치
uv tool uninstall ai-review
uv tool install --editable /path/to/ai-code-review

# 4. 터미널 재시작
```

---

## 📚 다음 단계

설치가 완료되었다면:

1. **빠른 시작**: `docs/QUICK_START.md` 읽기
2. **사용법**: `docs/CLI_USAGE.md` 참조
3. **첫 리뷰 실행**:
   ```bash
   cd /path/to/your/project
   ai-review --staged
   ```

---

## 💡 추천 설정

### Pre-commit Hook으로 자동 리뷰

프로젝트의 `.git/hooks/pre-commit` 파일 생성:

```bash
#!/bin/bash

echo "🤖 AI Code Review 실행 중..."
ai-review --staged

if [ $? -ne 0 ]; then
    echo "⚠️  코드 리뷰 실패"
    exit 1
fi

echo "✅ AI 코드 리뷰 완료!"
```

실행 권한 부여:
```bash
chmod +x .git/hooks/pre-commit
```

### Shell 별칭 설정

`~/.zshrc` 또는 `~/.bashrc`에 추가:

```bash
# AI Code Review 별칭
alias review="ai-review --staged"
alias review-all="ai-review --branch"
alias review-verbose="ai-review --staged -v"
```

---

## 🆘 지원

문제가 발생하면:

1. **문서 확인**: `README.md`, `docs/` 디렉토리
2. **이슈 등록**: GitHub Issues
3. **로그 확인**: `ai-review -v` (verbose 모드)

---

**Happy Reviewing! 🚀**

"""Phase 1: 독립적 초기 리뷰 모듈 (MCP 기반)

각 AI가 MCP 도구를 활용하여 독립적으로 코드를 분석하는 Phase 1을 담당합니다.
파일 내용을 프롬프트에 포함하지 않고, AI가 직접 MCP로 읽도록 위임합니다.
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

# ai_cli_tools 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_cli_tools import AIClient, AIModel
from src.mcp import MCPManager


class Phase1Reviewer:
    """Phase 1 독립적 초기 리뷰 실행기 (MCP 기반)"""

    def __init__(self, ai_client: AIClient, use_mcp: bool = True, verbose: bool = False):
        """초기화

        Args:
            ai_client: AI 클라이언트
            use_mcp: MCP 사용 여부 (현재는 항상 True)
            verbose: 상세 출력 여부
        """
        self.ai_client = ai_client
        self.use_mcp = use_mcp
        self.verbose = verbose
        self.mcp_manager = MCPManager() if use_mcp else None

    def execute(
        self,
        files: List[str],
        available_ais: Dict[str, AIModel],
        base_branch: Optional[str] = None,
        review_mode: str = "file"
    ) -> Dict[str, str]:
        """Phase 1 실행 (병렬)

        Args:
            files: 리뷰할 파일 목록 (경로만)
            available_ais: 사용 가능한 AI 모델들
            base_branch: 기준 브랜치 (branch/commits 모드용)
            review_mode: 리뷰 모드 (file, directory, staged, commits, branch)

        Returns:
            {ai_name: review_response} 형태의 딕셔너리
        """
        print("\n" + "=" * 70)
        print("Phase 1: 독립적 초기 리뷰 (MCP 기반)")
        print("=" * 70)
        print(f"참여 AI: {len(available_ais)}개")
        print(f"리뷰 파일: {len(files)}개")

        if self.use_mcp:
            print(f"MCP 모드: 활성화 - AI가 직접 파일 읽기")
        print()

        # Git 컨텍스트 수집 (MCP 사용 시)
        git_context = None
        if self.use_mcp and base_branch:
            try:
                git_context = self.mcp_manager.get_context_for_review(base_branch)
                if git_context.get("diff_stats"):
                    stats = git_context["diff_stats"]
                    print(f"📊 Git 통계: {stats['files_changed']}개 파일, "
                          f"+{stats['insertions']}/-{stats['deletions']} 줄")
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Git 컨텍스트 수집 실패: {e}")

        # MCP 도구 설명 생성
        mcp_tools_doc = ""
        if self.use_mcp and self.mcp_manager:
            mcp_tools_doc = self.mcp_manager.generate_tool_description()

        # 프롬프트 생성 (파일 내용 없이)
        prompt = self._generate_mcp_delegated_prompt(
            files,
            review_mode,
            base_branch,
            git_context,
            mcp_tools_doc
        )

        if self.verbose:
            print(f"\n프롬프트 크기: {len(prompt):,} 문자")
            print(f"프롬프트 줄 수: {prompt.count(chr(10)):,} 줄\n")

        # 병렬 실행
        reviews = {}
        with ThreadPoolExecutor(max_workers=len(available_ais)) as executor:
            futures = {}

            for ai_name, ai_model in available_ais.items():
                print(f"[{ai_name}] 리뷰 시작...")

                # Agent 지정
                agents = ["Explore", "Observe", "Orient", "Security", "Performance"]

                # 비동기 실행
                future = executor.submit(
                    self.ai_client.call_ai_with_retry,
                    prompt,
                    ai_model,
                    agents,
                )
                futures[future] = ai_name

            # 결과 수집
            for future in as_completed(futures):
                ai_name = futures[future]
                try:
                    response = future.result(timeout=600)
                    reviews[ai_name] = response
                    print(f"[{ai_name}] ✓ 리뷰 완료 ({len(response)} 자)")
                except Exception as e:
                    print(f"[{ai_name}] ✗ 리뷰 실패: {e}")
                    reviews[ai_name] = ""

        print(f"\nPhase 1 완료: {len([r for r in reviews.values() if r])}개 AI 성공\n")
        return reviews

    def _generate_mcp_delegated_prompt(
        self,
        files: List[str],
        review_mode: str,
        base_branch: Optional[str],
        git_context: Optional[Dict],
        mcp_tools_doc: str
    ) -> str:
        """MCP 위임 방식의 프롬프트 생성

        파일 내용을 포함하지 않고, AI가 MCP 도구로 직접 읽도록 지시합니다.

        Args:
            files: 파일 경로 리스트
            review_mode: 리뷰 모드
            base_branch: 기준 브랜치
            git_context: Git 컨텍스트 정보
            mcp_tools_doc: MCP 도구 설명

        Returns:
            프롬프트 문자열
        """
        # 기본 정보
        prompt = f"""# Code Review Task (Phase 1: Independent Review)

## Your Role
You are a professional code reviewer with access to powerful MCP tools.
Your task is to conduct a thorough, independent code review.

## Review Context
- **Review Mode**: {review_mode}
- **Total Files**: {len(files)}
"""

        # Git 컨텍스트 추가
        if git_context:
            if "current_branch" in git_context:
                prompt += f"- **Current Branch**: {git_context['current_branch']}\n"
            if base_branch:
                prompt += f"- **Base Branch**: {base_branch}\n"
            if "diff_stats" in git_context:
                stats = git_context["diff_stats"]
                prompt += f"- **Changes**: {stats['files_changed']} files, +{stats['insertions']}/-{stats['deletions']} lines\n"

        prompt += "\n"

        # 파일 목록
        prompt += "## Files to Review\n\n"
        for i, file_path in enumerate(files, 1):
            prompt += f"{i}. `{file_path}`\n"

        prompt += "\n"

        # MCP 도구 설명
        prompt += mcp_tools_doc
        prompt += "\n"

        # 리뷰 프로세스 지침
        prompt += """## Review Process

### Step 1: Understand the Changes (REQUIRED)

**For branch/commits/staged mode:**
```
1. Use git.get_diff() to see what actually changed
2. Use git.get_changed_files() to get the file list
3. Use git.get_diff_stats() to understand the scope
```

**For file/directory mode:**
```
1. Use filesystem.get_file_info() to check file sizes
2. Prioritize larger or more complex files
```

### Step 2: Read Files Selectively (SMART APPROACH)

**Don't read everything at once!** Be strategic:

```
1. Start with git diff to see changed lines
2. Read only files with significant changes
3. Skip files with minor formatting changes
4. Read related files if you suspect issues
```

**Example workflow:**
```python
# 1. Check what changed
diff = git.get_diff("main", "HEAD")  # See the actual changes

# 2. Get changed files
changed = git.get_changed_files("main", "HEAD")

# 3. For each significant change, read the file
for file in changed:
    if significant_change_detected(file):
        content = filesystem.read_file(file)
        # Analyze the content
```

### Step 3: Analyze Context (OPTIONAL)

When you find potential issues:
```
- git.get_blame(file, line_start, line_end) - Who wrote this code?
- git.get_commit_info(hash) - What was the original intention?
- filesystem.read_file(related_file) - Check related code
```

### Step 4: Write Your Review (REQUIRED)

For each issue found, use this format:

---
### [SEVERITY] Issue Title
**Location**: `file:line` or `file:start-end`
**Description**: Clear explanation of the problem
**Current Code**:
```
The problematic code snippet
```
**Suggested Fix**:
```
The improved code
```
**Rationale**: Why this is a problem and how the fix helps
---

## Review Focus Areas

Analyze code from these perspectives:

### 1. Security (CRITICAL)
- SQL Injection, XSS, CSRF vulnerabilities
- Authentication/Authorization flaws
- Sensitive data exposure
- Insecure cryptography
- Input validation issues

### 2. Performance (MAJOR)
- Inefficient algorithms
- Unnecessary repeated operations
- Memory leaks
- Database query optimization
- Resource management

### 3. Code Quality (MAJOR/MINOR)
- Readability and maintainability
- Code duplication (DRY principle)
- Cyclomatic complexity
- Naming conventions
- Comments and documentation

### 4. Architecture (MAJOR)
- SOLID principles violations
- Dependency management
- Modularity and separation of concerns
- Design patterns misuse

### 5. Bugs and Error Handling (CRITICAL/MAJOR)
- Logic errors
- Missing exception handling
- Edge case handling
- Race conditions

## Severity Levels

- **CRITICAL**: Security vulnerabilities, data loss risks, critical bugs
- **MAJOR**: Performance issues, design flaws, important bugs
- **MINOR**: Code quality, readability, minor optimizations
- **SUGGESTION**: Nice-to-have improvements, alternative approaches

## Best Practices

✅ **DO:**
- Start with git diff to see changes
- Read files selectively based on changes
- Focus deeply on changed code
- Provide specific line numbers
- Show concrete code examples
- Explain the reasoning behind each finding

❌ **DON'T:**
- Don't read all files upfront
- Don't review unchanged code
- Don't make vague suggestions
- Don't miss security issues
- Don't overlook error handling

## Example Workflow

```
1. git.get_diff("main", "feature-branch")
   → Observe: src/auth.py changed lines 45-67, added new function

2. filesystem.read_file("src/auth.py")
   → Review the authentication logic changes

3. FOUND ISSUE: Potential SQL injection at line 52

4. git.get_blame("src/auth.py", 52)
   → Context: who wrote this, when

5. filesystem.read_file("src/db_utils.py")
   → Check if there's a safe query function available

6. Write detailed review with the security issue
```

## Output Format

Start your review with a summary, then list all issues:

```
# Code Review Summary
- Files reviewed: X
- Issues found: Y (Z critical, W major, V minor, U suggestions)
- Focus areas: [List main concerns]

# Detailed Findings

[Issue 1]
[Issue 2]
...
```

## Ready to Start?

You have all the tools you need. Begin by:
1. Checking git diff (if applicable)
2. Reading files strategically
3. Analyzing thoroughly
4. Documenting your findings

Use MCP tools wisely. Good luck! 🚀
"""

        return prompt

    # Legacy methods removed:
    # - _read_files() - NO LONGER NEEDED
    # - File embedding in prompts - DELETED

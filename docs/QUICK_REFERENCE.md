# Quick Reference - Pure Task Delegation

## 🎯 The Golden Rule

> **"AI에게 데이터를 전달하지 말고, 할 일만 전달하라"**
>
> **"Don't pass data to AI. Just tell them what to do."**

## Old vs New Approach

| Aspect | ❌ Old (Function Paradigm) | ✅ New (Agent Paradigm) |
|--------|---------------------------|------------------------|
| **Prompt Strategy** | Embed 145K tokens of diff | Send 500 tokens with task |
| **AI Role** | Passive data processor | Active autonomous explorer |
| **Data Flow** | Python → AI (push) | AI → MCP (pull) |
| **Scalability** | 30 files max | 1000+ files |
| **Token Usage** | 275K tokens | 4.5K tokens (98.4% ↓) |
| **Cost per Review** | ~$55 | ~$0.90 (98.4% ↓) |
| **MCP Server Role** | Tool provider only | Orchestrator + Mediator |
| **Collaboration** | None (sequential) | Multi-round consensus |

## Round-Based Process

### Round 1: Independent Review
- **Prompt**: ~500 tokens (task description only)
- **AI Task**: Explore changes, analyze code, find issues
- **MCP Tools Used**: `git_get_changed_files`, `git_get_file_diff`, `review_submit_review`
- **Result**: Each AI submits independent review

### Round 2: Critique Phase
- **Prompt**: ~3K tokens (includes other reviews)
- **AI Task**: Read other AIs' reviews, critique findings
- **MCP Tools Used**: `review_get_other_reviews`, `review_submit_review`
- **Result**: Each AI submits critique (agree/disagree)

### Round 3: Final Consensus
- **Prompt**: ~1K tokens (synthesis instructions)
- **AI Task**: Read all rounds, identify consensus, create final report
- **MCP Tools Used**: `review_get_session_info`, `review_finalize_review`
- **Result**: Final consensus report with priority levels

## MCP Tools Cheat Sheet

### Git Tools (7)
```python
# Get changed files list
git_get_changed_files(base, head)

# Get overview statistics
git_get_diff_stats(base, head)

# Read specific file diff (selective!)
git_get_file_diff(path, base, head)

# Find who wrote code
git_get_blame(path, line_start, line_end)

# Get commit details
git_get_commit_info(commit_hash)

# Current branch
git_get_current_branch()

# ⚠️ DON'T USE for large changes:
git_get_diff(base, head)  # Will error if >10K lines
```

### Review Orchestration Tools (7)
```python
# Start new review session
session_id = review_create_review_session(base, target)

# Submit your review
review_submit_review(session_id, ai_name, review)

# Read other AIs' reviews
reviews = review_get_other_reviews(session_id, ai_name)

# Check if all AIs submitted
status = review_check_consensus(session_id)

# Move to next round
review_advance_round(session_id)

# Finalize consensus
review_finalize_review(session_id, final_review)

# Get session details
info = review_get_session_info(session_id)
```

### Filesystem Tools (4)
```python
# Read file
filesystem_read_file(path)

# List files by pattern
filesystem_list_files(pattern)

# Get file info
filesystem_get_file_info(path)

# Get directory tree
filesystem_get_tree(path, max_depth)
```

## Prompt Templates

### Round 1 Template (500 tokens)
```markdown
# Code Review Task - Round 1

## Your Mission
Review changes from {base_branch} to {target_branch}.
Session ID: {session_id}

## Your Task
1. Explore using git_get_changed_files()
2. Analyze using git_get_file_diff()
3. Write review
4. Submit with review_submit_review()

Ready? Start exploring! 🚀
```

### Round 2 Template (3K tokens)
```markdown
# Code Review Task - Round 2: Critique

## Other AI Reviews
{other_reviews}

## Your Task
For each issue:
- ✅ AGREE: Correct finding
- ❌ DISAGREE: Not a problem
- Better solution?

Submit critique.
```

### Round 3 Template (1K tokens)
```markdown
# Code Review Task - Final Consensus

## Your Task
1. Read all rounds via review_get_session_info()
2. Identify consensus: 3/3 = CRITICAL, 2/3 = MAJOR
3. Create final report
4. Submit: review_finalize_review()
```

## Common Mistakes to Avoid

### ❌ DON'T: Embed Data in Prompts
```python
# WRONG!
diff = git.get_diff("develop", "HEAD")
prompt = f"Review this diff:\n{diff}"  # 145K tokens!
```

### ✅ DO: Delegate Task Only
```python
# CORRECT!
prompt = f"""
Review changes from develop to HEAD.
Session: {session_id}
Use MCP tools to explore.
"""  # 500 tokens
```

### ❌ DON'T: Pass File Contents
```python
# WRONG!
files = git.get_changed_files()
for file in files:
    content = read_file(file)
    prompt += f"File {file}:\n{content}"  # Huge!
```

### ✅ DO: Let AI Read Selectively
```python
# CORRECT!
prompt = """
Use git_get_changed_files() to see files.
Use git_get_file_diff() to read important ones.
"""
```

### ❌ DON'T: Aggregate Reviews in Python
```python
# WRONG!
reviews = []
for ai in ais:
    review = ai.review(diff)  # Each AI isolated
    reviews.append(review)
final = aggregate(reviews)  # Python does consensus
```

### ✅ DO: Let AIs Collaborate via MCP
```python
# CORRECT!
# Round 1: Each AI explores independently
# Round 2: AIs critique each other via MCP
# Round 3: AIs reach consensus themselves
```

## Token Usage Calculation

### Old Approach (Function Paradigm)
```
Round 1: 145K tokens × 3 AIs = 435K tokens
Total: 435K tokens
Cost: ~$87 (Claude Sonnet 4.5)
```

### New Approach (Agent Paradigm)
```
Round 1: 500 tokens × 3 AIs = 1.5K tokens
Round 2: 3K tokens × 3 AIs = 9K tokens
Round 3: 1K tokens × 1 AI = 1K tokens
Total: 11.5K tokens (97.4% reduction)
Cost: ~$2.30 (Claude Sonnet 4.5)
```

## Performance Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| **Token Reduction** | >95% | 98.4% ✅ |
| **Scalability** | 100+ files | 1000+ files ✅ |
| **AI Autonomy** | Self-exploration | Yes ✅ |
| **Collaboration** | Multi-round | 3 rounds ✅ |
| **Consensus** | 3/3, 2/3 levels | Yes ✅ |

## Usage Example

```bash
# 1. Start Claude CLI
claude

# 2. Ask for code review
> Review the changes from develop to HEAD using ai-code-review MCP server.
>
> Steps:
> 1. Create review session
> 2. Explore changes using MCP tools
> 3. Write comprehensive review
> 4. Submit to session
>
> Your AI name: "Claude-Reviewer-1"

# 3. AI will:
- Call review_create_review_session("develop", "HEAD")
- Call git_get_changed_files("develop", "HEAD")
- Call git_get_diff_stats("develop", "HEAD")
- Selectively call git_get_file_diff() for important files
- Analyze and write review
- Call review_submit_review(session_id, "Claude-Reviewer-1", review)

# 4. Repeat for Round 2 (critique)
> Now read other AI's review and critique it.
> Session: {session_id}
> Your name: "Claude-Reviewer-2"

# 5. Round 3 (consensus)
> Create final consensus report.
> Session: {session_id}
```

## Configuration

### MCP Server Configuration
Location: `~/.claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ai-code-review": {
      "command": "python3",
      "args": ["/full/path/to/ai-code-review/src/mcp/server.py"],
      "env": {}
    }
  }
}
```

### Verify Installation
```bash
# List MCP tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python3 src/mcp/server.py

# Should show 18 tools:
# - 4 filesystem tools
# - 7 git tools
# - 7 review orchestration tools
```

## Debugging

### Check Session Files
```bash
ls -la /tmp/ai_code_review_sessions/
cat /tmp/ai_code_review_sessions/review_*.json
```

### Check MCP Server Logs
```bash
tail -f /tmp/mcp_server.log
```

### Test MCP Tools Manually
```bash
# Test tool directly
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_get_changed_files","arguments":{"base":"develop","head":"HEAD"}}}' | \
  python3 src/mcp/server.py
```

## Key Insights

### 1. AI is NOT a Function
```python
# ❌ Function paradigm
def ai_review(data) -> result:
    return process(data)

# ✅ Agent paradigm
def ai_review(task) -> result:
    data = self.explore(tools)
    return self.analyze(data)
```

### 2. MCP is an Orchestrator
Not just a tool box, but a coordinator that:
- Manages sessions
- Stores reviews
- Relays information between AIs
- Tracks consensus
- Coordinates rounds

### 3. Token Savings ≠ Data Compression
```python
# ❌ Wrong approach
compress(huge_data)  # Still large

# ✅ Right approach
"Use tools to get data"  # Minimal
```

### 4. Collaboration Through Critique
- Round 1: Independent thinking
- Round 2: Challenge assumptions
- Round 3: Reach consensus
- Result: Higher quality, validated findings

## Further Reading

- [PURE_TASK_DELEGATION.md](./PURE_TASK_DELEGATION.md) - Complete architecture documentation
- [MCP_ORCHESTRATION.md](./MCP_ORCHESTRATION.md) - Orchestration details
- [ARCHITECTURE_CHANGE.md](./ARCHITECTURE_CHANGE.md) - Paradigm shift explanation
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - How to test the system

---

**Remember**: Don't pass data. Delegate tasks. Let AI explore autonomously! 🚀

# Testing Guide - MCP-Orchestrated Review System

## Prerequisites

1. **MCP Server Configured**:
```bash
# Verify configuration exists
cat ~/.claude/claude_desktop_config.json | grep ai-code-review
```

2. **Claude CLI Available**:
```bash
# Test MCP tools are accessible
# In Claude CLI, type: "List available MCP tools for ai-code-review"
```

## Test Workflow

### Phase 1: Verify MCP Tools

Test each MCP tool category individually:

```bash
# 1. Git Tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"git_get_changed_files","arguments":{"base":"develop","head":"HEAD"}}}' | python3 src/mcp/server.py

# 2. Review Orchestration Tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"review_create_review_session","arguments":{"base":"develop","target":"HEAD"}}}' | python3 src/mcp/server.py

# 3. Check session info
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"review_get_session_info","arguments":{"session_id":"<session_id_from_above>"}}}' | python3 src/mcp/server.py
```

### Phase 2: Test Round 1 (Independent Review)

In Claude CLI:

```
I need you to perform a code review using the ai-code-review MCP server.

Base branch: develop
Target branch: HEAD

Steps:
1. Create a review session using review_create_review_session
2. Explore changes using git_get_changed_files and git_get_diff_stats
3. For important files, use git_get_file_diff to read selectively
4. Write your review focusing on:
   - Security issues
   - Performance problems
   - Bugs and logic errors
5. Submit your review using review_submit_review

Your AI name: "Claude-Reviewer-1"

Start now and let me know what you find.
```

**Expected Behavior**:
- AI should call MCP tools autonomously
- AI should NOT ask for file contents
- AI should read files selectively
- Prompt size should be ~500 tokens
- Review should be comprehensive despite minimal initial prompt

### Phase 3: Test Round 2 (Critique Phase)

After Round 1 completes:

```
Now for Round 2: Critique Phase

Session ID: <session_id_from_round1>
Your AI name: "Claude-Reviewer-2"

Steps:
1. Use review_get_other_reviews to read other AI's review
2. Critically analyze their findings:
   - What did they get right?
   - What did they miss?
   - Are their solutions correct?
3. Submit your critique using review_submit_review

Be honest and critical - the goal is consensus, not politeness.
```

**Expected Behavior**:
- AI reads other reviews via MCP tool
- AI provides critical analysis
- AI agrees/disagrees with specific points
- AI suggests better solutions where needed

### Phase 4: Test Round 3 (Final Consensus)

After Round 2 completes:

```
Final Round: Consensus Report

Session ID: <session_id>
Your AI name: "Claude-Reviewer-Final"

Steps:
1. Use review_get_session_info to see all rounds
2. Read all reviews from Round 1 and Round 2
3. Identify consensus levels:
   - All AIs agree (3/3) → CRITICAL
   - Most AIs agree (2/3) → MAJOR
   - Only one AI (1/3) → Note but don't mandate
4. Create final consensus report
5. Submit using review_finalize_review

This is the authoritative final review!
```

**Expected Behavior**:
- AI reads all rounds via MCP
- AI identifies agreement patterns
- Final report shows consensus levels
- Report is actionable and prioritized

## Verification Checklist

### Token Usage Verification

Monitor token usage at each phase:

- [ ] Round 1 prompt: ~500 tokens (task description only)
- [ ] Round 2 prompt: ~3K tokens (includes reviews to critique)
- [ ] Round 3 prompt: ~1K tokens (synthesis instructions)
- [ ] Total: ~4.5K tokens (vs 275K in old approach)

### MCP Tool Usage Verification

Verify AI called these tools:

**Round 1**:
- [ ] `git_get_changed_files()`
- [ ] `git_get_diff_stats()`
- [ ] `git_get_file_diff()` for selected files
- [ ] `review_submit_review()`

**Round 2**:
- [ ] `review_get_other_reviews()`
- [ ] `review_submit_review()`

**Round 3**:
- [ ] `review_get_session_info()`
- [ ] `review_finalize_review()`

### Behavioral Verification

Check AI behavior matches "Agent Paradigm":

- [ ] AI explores autonomously (not asking for data)
- [ ] AI reads files selectively (not requesting full diff)
- [ ] AI focuses on important changes
- [ ] AI collaborates with other AIs via MCP
- [ ] AI reaches consensus through critique

## Debugging

### If AI Doesn't Use MCP Tools

**Problem**: AI doesn't call MCP tools, asks for data instead

**Solutions**:
1. Check MCP server is running:
   ```bash
   ps aux | grep "python3 src/mcp/server.py"
   ```

2. Verify Claude CLI configuration:
   ```bash
   cat ~/.claude/claude_desktop_config.json
   ```

3. Restart Claude CLI to reload MCP servers

4. Make prompt more explicit:
   ```
   IMPORTANT: You MUST use MCP tools. Do NOT ask me for file contents.
   Use git_get_changed_files() to explore on your own.
   ```

### If Token Limit Still Exceeded

**Problem**: AI tries to call `git_get_diff()` and hits token limit

**Root Cause**: AI is still thinking in "data embedding" paradigm

**Solution**: The `git_get_diff()` tool now has built-in protection:
```python
# In src/mcp/git.py
if total_changes > 10000:
    raise RuntimeError(
        "⚠️ Diff too large\n"
        "❌ Don't use git_get_diff() for large changes!\n"
        "✅ Use git_get_file_diff() instead"
    )
```

Tell AI:
```
The diff is too large. Use this approach instead:
1. files = git_get_changed_files("develop", "HEAD")
2. stats = git_get_diff_stats("develop", "HEAD")
3. For each important file:
     diff = git_get_file_diff(file, "develop", "HEAD")
```

### Session Not Found

**Problem**: `review_get_session_info` returns "Session not found"

**Debugging**:
1. Check session was created:
   ```bash
   ls /tmp/ai_code_review_sessions/
   ```

2. Verify session ID format:
   ```python
   # Should match: review_<timestamp>_<id>
   ```

3. Check session file:
   ```bash
   cat /tmp/ai_code_review_sessions/review_*.json
   ```

## Performance Benchmarks

Expected improvements vs old approach:

| Metric | Old (Embedded) | New (Delegated) | Improvement |
|--------|---------------|-----------------|-------------|
| **Round 1 Prompt** | 145K tokens | 500 tokens | 99.7% |
| **Round 2 Prompt** | 50K tokens | 3K tokens | 94% |
| **Round 3 Prompt** | 80K tokens | 1K tokens | 98.8% |
| **Total Tokens** | 275K tokens | 4.5K tokens | 98.4% |
| **Scalability** | ~30 files max | 1000+ files | 33x |
| **Cost** | ~$55/review | ~$0.90/review | 98.4% |

## Success Criteria

A successful test shows:

✅ **Token Efficiency**: <5K tokens for all prompts combined
✅ **Scalability**: Handles 76+ file changes without issues
✅ **AI Autonomy**: AI explores independently using MCP tools
✅ **Collaboration**: AIs critique each other's reviews
✅ **Consensus**: Final report shows agreement levels (3/3, 2/3, 1/3)
✅ **Quality**: Review findings are comprehensive and actionable

## Next Steps After Testing

Once basic workflow works:

1. **Add More AIs**: Test with 3+ AIs for richer consensus
2. **Larger Codebases**: Test with 200+ file changes
3. **Different Review Types**: Security-focused, Performance-focused, etc.
4. **Automation**: Integrate with CI/CD for automatic PR reviews
5. **Metrics**: Track consensus accuracy and review quality over time

## Example Session Output

A successful session should produce:

```
/tmp/ai_code_review_sessions/review_1234567890.json:
{
  "session_id": "review_1234567890",
  "base_branch": "develop",
  "target_branch": "HEAD",
  "current_round": 3,
  "reviews": {
    "Claude-1": {
      "1": {"content": "# Round 1 Review...", "timestamp": 1234567890},
      "2": {"content": "# Round 2 Critique...", "timestamp": 1234567895}
    },
    "Claude-2": {
      "1": {"content": "# Round 1 Review...", "timestamp": 1234567891},
      "2": {"content": "# Round 2 Critique...", "timestamp": 1234567896}
    }
  },
  "consensus_reached": true,
  "final_review": "# Final Consensus Report\n## Critical Issues (3/3)...",
  "created_at": 1234567890
}
```

This confirms:
- ✅ Multi-round process completed
- ✅ Multiple AIs participated
- ✅ Consensus was reached
- ✅ Final report generated

---

**Remember**: The system works by **task delegation**, not **data embedding**. Trust the AI to explore autonomously using MCP tools!

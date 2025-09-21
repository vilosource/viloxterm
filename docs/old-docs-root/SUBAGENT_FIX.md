# Subagent Configuration Fix

## Problem
The subagents (code-monkey, code-quality-auditor, etc.) were failing with error:
```
API Error: 404 {"type":"error","error":{"type":"not_found_error","message":"model: sonnet"}}
```

## Root Cause
The environment variable `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` was set, causing the Task tool to request a model called "sonnet" which doesn't exist.

## Solutions Applied

### 1. Removed Invalid Model Parameters
- Removed `model: sonnet` from `.claude/agents/code-quality-auditor.md`
- Ensured `code-monkey.md` has no model parameter

### 2. Correct Agent Configuration
According to Claude Code documentation, valid YAML frontmatter parameters are:
- `name` (required) - kebab-case identifier
- `description` (required) - when to invoke the agent
- `tools` (optional) - comma-separated list of tools

The `model` parameter is NOT supported.

### 3. Updated Code-Monkey Agent
Simplified and focused the agent to ~190 lines with:
- Clear implementation protocol
- Step-by-step instructions for FIX_IMPLEMENTATION_PLAN.md
- 10-line rule enforcement
- Architecture compliance checks
- Testing requirements

## To Fix Environment Variable

### Option 1: Unset for Current Session
```bash
unset CLAUDE_CODE_SUBAGENT_MODEL
```

### Option 2: Find and Remove Source
Check where it's being set:
```bash
# Check current shell
echo $CLAUDE_CODE_SUBAGENT_MODEL

# Search config files
grep -r "CLAUDE_CODE_SUBAGENT_MODEL" ~/

# Check if Claude Code sets it
ps aux | grep claude
```

### Option 3: Override in Shell Config
Add to `~/.bashrc` or `~/.zshrc`:
```bash
# Fix Claude Code subagent model issue
unset CLAUDE_CODE_SUBAGENT_MODEL
```

## Available Subagent Types
Based on system documentation, these are the available agents:
- `general-purpose` - General research and multi-step tasks
- `statusline-setup` - Configure status line settings
- `output-style-setup` - Create output styles
- `agent-creator` - Create and configure agents

Custom agents in `.claude/agents/`:
- `code-monkey` - Incremental implementation
- `code-quality-auditor` - Code quality analysis
- `agent-creator` - Agent configuration expert

## Testing Agents
Once environment variable is fixed, test with:
```bash
# In Claude Code, use:
/code-monkey
/code-quality-auditor
```

Or invoke programmatically:
```python
# Using Task tool
Task(
    description="Implementation task",
    prompt="Implement Phase 1 from FIX_IMPLEMENTATION_PLAN.md",
    subagent_type="code-monkey"
)
```

## Status
- ✅ Agent configurations fixed (no invalid model parameters)
- ✅ Code-monkey agent updated and simplified
- ⚠️ Environment variable needs to be unset to enable subagents
- ✅ Implementation plan fixes completed (Phase 1)
# ⚠️ CRITICAL: Agent File Locations - READ THIS FIRST ⚠️

## THE GOLDEN RULE
**`.claude/agents/` = REAL AGENTS** (Claude Code executes these)  
**`docs/agents/` = DOCUMENTATION** (Just docs, NOT executable)

## Before You Touch ANY Agent File, Ask Yourself:

### 1. "Am I editing the ACTUAL agent or just documentation?"
- If the path starts with `.claude/agents/` → IT'S A REAL AGENT
- If the path starts with `docs/` → IT'S JUST DOCUMENTATION

### 2. Check the Format Requirements

#### REAL AGENTS (`.claude/agents/*.md`) MUST HAVE:
```markdown
---
name: agent-name
description: "Brief description of what the agent does"
tools: Read, Write, Edit, Bash, Grep  # List of tools
model: sonnet  # Optional, defaults to sonnet
---

# Agent Name

System prompt content here...
```

#### DOCUMENTATION (`docs/agents/*`) CAN BE:
- Any format
- Design documents
- Proposals
- Usage logs
- Examples
- NO YAML frontmatter required

## Common Mistakes to AVOID:

### ❌ WRONG: Editing docs thinking it will change agent behavior
```bash
# This does NOTHING for Claude Code:
edit docs/agents/code-monkey.md  # Just documentation!
```

### ✅ CORRECT: Editing the actual agent file
```bash
# This ACTUALLY changes the agent:
edit .claude/agents/code-monkey.md  # Real agent file!
```

## Quick Reference Table

| Purpose | Location | Format | Effect |
|---------|----------|---------|---------|
| **Change agent behavior** | `.claude/agents/agent-name.md` | YAML frontmatter + markdown | Claude Code uses this |
| **Document agent design** | `docs/agents/agent-name.md` | Any markdown | For human reference only |
| **Log agent usage** | `docs/agents/AGENT_USAGE_LOG.md` | Any markdown | Historical record |
| **Explain how agents work** | `docs/agents/how-to-write-an-agent.md` | Any markdown | Instructions for humans |

## File Validation Checklist

Before saving any agent-related file:

1. **Path Check**: Does it start with `.claude/agents/`?
   - YES → Must have YAML frontmatter
   - NO → It's just documentation

2. **Format Check**: If it's a real agent, does it have:
   - [ ] YAML frontmatter with `name` and `description`
   - [ ] Optional `tools` list
   - [ ] System prompt in markdown body

3. **Purpose Check**: 
   - Am I trying to change agent behavior? → Edit `.claude/agents/`
   - Am I documenting something? → Edit `docs/agents/`

## Memory Aid for Future Sessions

**Think of it like this:**
- `.claude/` = Claude's brain (executable)
- `docs/` = Documentation shelf (reference only)

**When someone says "update the agent":**
→ They mean `.claude/agents/agent-name.md`

**When someone says "document our learnings":**
→ They mean `docs/agents/` files

---

## Current Agent Inventory

### Real Agents (in `.claude/agents/`)
- `code-monkey.md` - Safe implementation agent
- `design-compliance.md` - Design verification agent

### Documentation (in `docs/agents/`)
- Various design docs, proposals, usage logs
- These are NOT agents, just documentation

---

Remember: **Only `.claude/agents/*.md` files are actual agents that Claude Code can execute!**
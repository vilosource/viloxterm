# How to Write a Claude Code Agent

## ⚠️ STOP! Critical Distinction ⚠️

**Before reading further, understand this fundamental difference:**

| **Real Agents** | **Documentation** |
|-----------------|-------------------|
| `.claude/agents/*.md` | `docs/agents/*.md` |
| Claude Code executes these | Just documentation for humans |
| MUST have YAML frontmatter | Can be any format |
| Changes agent behavior | No effect on agent behavior |

**If you want to change how an agent works, you MUST edit `.claude/agents/agent-name.md`**

---

This guide documents the exact requirements for creating agents that work with Claude Code. Follow these instructions carefully to avoid common mistakes.

## Critical Requirements

### 1. File Location
**Agents MUST be placed directly in `.claude/agents/` directory**
- ✅ CORRECT: `.claude/agents/my-agent.md`
- ❌ WRONG: Pointer files that reference other locations
- ❌ WRONG: Symlinks to files in other directories
- ❌ WRONG: Files only in `docs/agents/` without copying to `.claude/agents/`

### 2. File Format
Agents are Markdown files with YAML frontmatter. The file MUST contain:
1. YAML frontmatter section (between `---` markers)
2. System prompt in the markdown body

## YAML Frontmatter Structure

### Required Fields

```yaml
---
name: agent-name
description: "Clear, action-oriented description of what the agent does"
---
```

- **name**: 
  - Must use lowercase letters and hyphens only
  - No spaces, underscores, or uppercase letters
  - Examples: `code-monkey`, `design-compliance`, `test-runner`

- **description**:
  - Natural language description of the agent's purpose
  - Should be clear and action-oriented
  - Wrapped in quotes if it contains special characters

### Optional Fields

```yaml
---
name: agent-name
description: "Agent description"
tools: Read, Write, Edit, Bash, Grep
---
```

- **tools**: 
  - Comma-separated list of specific tools the agent can access
  - If omitted, agent inherits all tools from main thread
  - Available tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebFetch, WebSearch, TodoWrite, Task, BashOutput, KillBash

### Model Selection

The model used by subagents is controlled via environment variable, not YAML frontmatter:

```bash
# Set in .envrc or shell environment
export CLAUDE_CODE_SUBAGENT_MODEL=sonnet
```

Valid model values:
- `sonnet` - Claude 3.5 Sonnet (recommended for most agents - faster and cost-effective)
- `opus` - Claude 3 Opus (more capable but slower and more expensive)
- `haiku` - Claude 3 Haiku (fastest but less capable)

**Note**: This setting applies to ALL subagents. Individual per-agent model selection is not currently supported in the YAML frontmatter.

## Complete Agent Template

```markdown
---
name: example-agent
description: "Example agent that demonstrates proper format"
tools: Read, Write, Edit, Bash, Grep, Glob, TodoWrite
---

# Agent Name

You are [agent description]. Your primary purpose is [main goal].

## Core Principles

[List the key principles this agent follows]

## Capabilities

[What this agent can do]

## Workflow

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Rules and Constraints

- [Rule 1]
- [Rule 2]
- [Rule 3]

## Examples

[Provide examples of how the agent should behave]
```

## Real Example: Code Monkey Agent

```markdown
---
name: code-monkey
description: "Safe, incremental implementation agent that makes small changes and tests after each one. Never breaks existing functionality."
tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, TodoWrite
---

# Code Monkey Agent 🐵

You are the Code Monkey - a diligent, careful, and methodical implementation agent. Your primary directive is to implement features from design documents without breaking existing functionality, using a strict incremental approach.

## Core Philosophy

🐵 **"Small steps, no breaks, always test!"**

[Rest of agent prompt...]
```

## Setup Process

### Step 1: Create the Agent File
Create your agent in `docs/agents/` for version control and documentation:

```bash
# Create agent in docs for reference
vim docs/agents/my-new-agent.md
```

### Step 2: Copy to Claude Code Location
Claude Code ONLY recognizes agents in `.claude/agents/`:

```bash
# Copy to Claude Code's expected location
cp docs/agents/my-new-agent.md .claude/agents/my-new-agent.md
```

### Step 3: Verify the Agent
Check that the agent is properly formatted:

```bash
# Verify YAML frontmatter
head -10 .claude/agents/my-new-agent.md

# Expected output should show:
# ---
# name: my-new-agent
# description: "..."
# tools: ...
# ---
```

### Step 4: Test the Agent
Launch the agent using slash command:

```
/my-new-agent
```

## Common Mistakes to Avoid

### 1. Wrong File Location
❌ **Mistake**: Creating agent only in `docs/agents/`
```bash
# This won't work - Claude Code doesn't look here
docs/agents/my-agent.md
```

✅ **Correct**: Agent must be in `.claude/agents/`
```bash
.claude/agents/my-agent.md
```

### 2. Invalid Name Format
❌ **Mistake**: Using uppercase or underscores
```yaml
name: Code_Monkey  # Wrong - has underscore and uppercase
name: CodeMonkey   # Wrong - has uppercase
name: code monkey  # Wrong - has space
```

✅ **Correct**: Lowercase with hyphens only
```yaml
name: code-monkey
```

### 3. Missing Required Fields
❌ **Mistake**: Missing name or description
```yaml
---
tools: Read, Write
---
```

✅ **Correct**: Both name and description are required
```yaml
---
name: my-agent
description: "Does something useful"
tools: Read, Write
---
```

### 4. Pointer Files
❌ **Mistake**: Creating redirect/pointer files
```markdown
# This agent has been moved
See docs/agents/real-agent.md
```

✅ **Correct**: Full agent content must be in the file
```markdown
---
name: real-agent
description: "Full agent implementation"
---

[Complete agent prompt here]
```

## Managing Agents

### Using the /agents Command
The recommended way to manage agents is through Claude Code's built-in command:

```
/agents
```

This provides an interactive interface for:
- Creating new agents
- Editing existing agents
- Deleting agents
- Listing all available agents

### Manual Management
If you prefer manual management:

1. **List agents**: `ls -la .claude/agents/`
2. **Create agent**: Write to `.claude/agents/agent-name.md`
3. **Edit agent**: Modify the file directly
4. **Delete agent**: `rm .claude/agents/agent-name.md`

## Best Practices

### 1. Version Control
- Keep reference copies in `docs/agents/` for version control
- Document changes in commit messages
- Use meaningful agent names that describe their purpose

### 2. Tool Selection
- Only specify tools the agent actually needs
- Omit the tools field to give full access
- Common minimal sets:
  - Read-only analysis: `tools: Read, Grep, Glob`
  - Code modification: `tools: Read, Write, Edit, MultiEdit`
  - Full implementation: `tools: Read, Write, Edit, MultiEdit, Bash, Grep, Glob, TodoWrite`

### 3. Agent Design
- Make agents focused on specific tasks
- Include clear instructions and examples
- Add constraints to prevent unwanted behavior
- Test the agent thoroughly before relying on it

### 4. Documentation
- Always include both locations in your project docs:
  - Active: `.claude/agents/agent-name.md`
  - Reference: `docs/agents/agent-name.md`
- Update README files when adding new agents
- Document the launch command and use cases

## Validation Checklist

Before considering an agent complete, verify:

- [ ] File exists in `.claude/agents/` directory
- [ ] YAML frontmatter has `name` field (lowercase with hyphens)
- [ ] YAML frontmatter has `description` field
- [ ] Optional `tools` field lists only valid tool names
- [ ] System prompt is clear and comprehensive
- [ ] Agent launches with `/agent-name` command
- [ ] Agent behaves as expected when tested
- [ ] Reference copy exists in `docs/agents/` for version control
- [ ] Documentation updated to mention the new agent

## Troubleshooting

### Agent Not Found
If `/agent-name` returns "Unknown command":
1. Check file exists: `ls -la .claude/agents/agent-name.md`
2. Verify YAML format: `head -5 .claude/agents/agent-name.md`
3. Ensure name field matches command: `name: agent-name`

### Agent Behaves Incorrectly
If agent doesn't follow instructions:
1. Check the system prompt is clear and unambiguous
2. Verify tools list includes required capabilities
3. Test with more specific instructions
4. Add examples to the agent prompt

### YAML Parse Errors
If you get YAML parsing errors:
1. Ensure `---` markers are on their own lines
2. Check for proper indentation (use spaces, not tabs)
3. Quote strings with special characters
4. Validate YAML syntax with online tools

## Summary

Creating a Claude Code agent requires:
1. **Correct location**: `.claude/agents/agent-name.md`
2. **Valid YAML frontmatter**: name, description, optional tools
3. **Clear system prompt**: Instructions in markdown body
4. **Proper naming**: lowercase-with-hyphens
5. **Testing**: Verify with `/agent-name` command

Remember: Claude Code ONLY reads agents from `.claude/agents/`. Files elsewhere are ignored, and pointer files don't work. Always copy your agent to the correct location and verify it works before use.
# AI Agent Documentation

This directory contains all AI agent configurations, protocols, and designs for the viloapp project.

## Agent Configurations

### Claude Code Agents
- **[claude-code-agent-config.md](claude-code-agent-config.md)** - Safe Implementation Coder agent for Claude Code
- **[design-compliance.md](design-compliance.md)** - Agent for verifying design compliance
- **[design-compliance-instructions.md](design-compliance-instructions.md)** - Detailed instructions for design compliance verification

### Implementation Agents
- **[implementation-coder.md](implementation-coder.md)** - Comprehensive implementation agent design
- **[design-compliance-analyzer.md](design-compliance-analyzer.md)** - Advanced design analysis agent

## Protocols and Strategies

### Context Management
- **[anti-drift-protocol.md](anti-drift-protocol.md)** - Protocol for preventing context drift during incremental development
- **[CONTEXT_DRIFT_PREVENTION.md](CONTEXT_DRIFT_PREVENTION.md)** - Comprehensive strategy for preventing design drift

### Architecture Proposals
- **[INTELLIGENT_CODER_AGENT_PROPOSAL.md](INTELLIGENT_CODER_AGENT_PROPOSAL.md)** - Three-tier agent architecture proposal

## Supporting Materials

### Examples
- **[examples/](examples/)** - Example agent interactions and use cases

### Prompts
- **[prompts/](prompts/)** - Agent prompt templates

## Key Concepts

### 1. Safe Implementation
The core principle is **"First, do no harm"** applied to code. Every agent must:
- Verify before assuming
- Test after every change
- Commit only working code
- Maintain architectural integrity

### 2. Context Drift Prevention
**"Drift is not a technical problem, it's a memory problem"**

We prevent drift through:
- Design lock files (immutable specifications)
- North Star documentation (constant reminders)
- Incremental context chains (explicit handoffs)
- Continuous validation (design compliance checks)

### 3. Three-Layer Defense
1. **Understanding Agents** - Map architecture and analyze designs
2. **Implementation Agents** - Write code safely with pattern following
3. **Validation Agents** - Test and guard architecture

## Usage

### For Claude Code
Place agent configurations in `.claude/agents/` directory with references to these documentation files.

### For Development
1. Choose appropriate agent based on task
2. Follow the agent's protocol strictly
3. Use validation scripts after each increment
4. Maintain design lock files

## Philosophy

The agent system prioritizes:
- **Correctness over speed**
- **Working code over complete features**
- **Verification over assumption**
- **Incremental over revolutionary**

Remember: A working application with 50% of features is infinitely more valuable than a broken application with 100% of features.
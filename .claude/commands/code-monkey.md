# /code-monkey Command

**Description:** Launch the Code Monkey agent for safe, incremental implementation
**Model:** Claude 3.5 Sonnet (Latest)
**Agent:** docs/agents/code-monkey.md

## Usage

```
/code-monkey
```

## What It Does

Launches the Code Monkey agent which will:
1. Read any existing design lock files (.design-lock.yml)
2. Check implementation context (.implementation-context.md)
3. Survey the codebase for patterns
4. Implement features incrementally (max 10 lines at a time)
5. Test after every single change
6. Revert if anything breaks

## When to Use

- Implementing new features
- Making changes that could break existing code
- Following a design document
- Refactoring existing functionality
- Working on complex multi-file changes

## Example

```
User: /code-monkey
Assistant: 🐵 Code Monkey activated! 

I'll implement features using:
- Maximum 10 lines per change
- Testing after every change
- Following existing patterns
- Never breaking what works

What feature would you like me to implement?
```

## Configuration

The Code Monkey will automatically:
- Use Claude 3.5 Sonnet model
- Follow the protocol in docs/agents/code-monkey.md
- Read context files if they exist
- Create incremental plans
- Update progress as it works

## Remember

The Code Monkey motto: **"Small steps, no breaks, always test!"** 🐵
# Anti-Drift Protocol for Incremental Implementation

## The Problem
During incremental development, each small "reasonable" change compounds into significant deviation from the original design. Like a game of telephone, the final implementation barely resembles the original intent.

## The Solution: Three-Layer Defense

### Layer 1: North Star Reminder (At Every Step)

```python
# ALWAYS start each increment with:
"""
NORTH STAR REMINDER:
Original Goal: [What we're building]
Current Step: [X of Y]
Must Maintain: [Core invariants]
Success Looks Like: [Final state]
"""
```

### Layer 2: Design Contract Validation

Before EVERY increment, the agent must answer:

```yaml
validation_questions:
  1. "What was the ORIGINAL requirement for this part?"
  2. "Am I still building what was originally designed?"
  3. "Have I introduced any NEW patterns not in the design?"
  4. "Would someone reading only the design recognize this code?"
```

If ANY answer is concerning, STOP and realign.

### Layer 3: Incremental Context Chain

Each increment passes explicit context to the next:

```python
increment_context = {
    "increment_number": 3,
    "original_design": "Commands use function handlers",
    "what_i_just_did": "Created handler function",
    "what_comes_next": "Register with registry",
    "must_not_change": ["Handler pattern", "Return type"],
    "design_reference": "DESIGN.md#section-2.3"
}
```

## Practical Implementation

### Step 1: Create Design Lock File

```yaml
# .design-lock.yml
# This file is IMMUTABLE during implementation
feature: Command System
locked_at: 2025-09-11T10:00:00

requirements:
  REQ001:
    description: "Commands are function handlers"
    test: "No class-based commands"
    
  REQ002:
    description: "Registry separate from executor"
    test: "Registry only stores, executor only runs"
    
  REQ003:
    description: "All commands have keyboard shortcuts"
    test: "Every command in keymaps.py"

invariants:
  - "Command is a @dataclass"
  - "ServiceLocator in services/ not core/services/"
  - "No inheritance from Command"

success_criteria:
  - "User can execute commands via Ctrl+Shift+P"
  - "All commands discoverable"
  - "Keyboard shortcuts work"
```

### Step 2: Validation Script

```python
# scripts/validate_against_design.py
def validate_implementation():
    """Run after EVERY increment."""
    
    design_lock = load_yaml(".design-lock.yml")
    
    # Check each requirement
    for req_id, req in design_lock["requirements"].items():
        if not test_requirement(req["test"]):
            print(f"❌ DRIFT DETECTED: {req['description']}")
            print(f"   Requirement {req_id} no longer met!")
            return False
    
    # Check invariants
    for invariant in design_lock["invariants"]:
        if not check_invariant(invariant):
            print(f"❌ INVARIANT VIOLATED: {invariant}")
            return False
    
    print("✅ Still aligned with design")
    return True
```

### Step 3: Context Preservation Template

```markdown
# CONTEXT FOR INCREMENT {N}

## Where We Started
- **Original Design:** [Link to design doc]
- **Original Goal:** [One sentence summary]

## Where We Are
- **Completed Steps:** 
  1. ✅ [Step 1 - what was built]
  2. ✅ [Step 2 - what was built]
  3. 🔄 [Current step]

## Where We're Going  
- **Next Step:** [What to build next]
- **End Goal:** [What success looks like]

## Critical Constraints
- **MUST NOT:** Change these patterns: [list]
- **MUST:** Follow these patterns: [list]
- **RED FLAGS:** Stop if you see: [list]

## Quick Validation
Run this to ensure we're still on track:
```bash
python scripts/validate_against_design.py
python main.py  # App still works?
```
```

## Agent Instructions Enhancement

### For Claude Code Agents

```markdown
You are implementing a feature incrementally. To prevent context drift:

1. **Before EACH increment**, read:
   - The original design document
   - The .design-lock.yml file
   - The previous increment's context

2. **During EACH increment**:
   - Maximum 10 lines of code
   - Test immediately
   - Run validation script
   - If validation fails, STOP and report

3. **After EACH increment**, create:
   - Updated context for next increment
   - Note any decisions made
   - Flag any concerns about drift

4. **NEVER**:
   - Introduce patterns not in original design
   - "Improve" on the design during implementation
   - Skip validation "just this once"

5. **ALWAYS**:
   - Keep original design visible
   - Question if changes match intent
   - Choose fidelity over optimization
```

## Drift Detection Patterns

### Early Warning Signs

```python
drift_indicators = [
    "Maybe we should just...",  # Rationalization
    "It would be simpler if...",  # Pattern change
    "Actually, instead of...",    # Requirement change
    "This is basically the same as...",  # Equivalence fallacy
    "For now, let's just...",     # Temporary becomes permanent
]
```

### Code Smell Detection

```python
def detect_drift_smells(code_change):
    smells = []
    
    # New patterns introduced?
    if "class.*Command\(" in code_change:
        smells.append("New class-based command pattern")
    
    # Import path drift?
    if "from core.services" in code_change:
        smells.append("Wrong import path pattern")
    
    # Return type drift?
    if "return True" in code_change and "CommandResult" in context:
        smells.append("Return type changed from CommandResult")
    
    return smells
```

## Recovery Protocol

When drift is detected:

1. **STOP immediately**
2. **Document what drifted and why**
3. **Review original design**
4. **Choose one:**
   - Revert to last valid increment
   - Justify drift and update design
   - Find way to meet original intent

Never continue with drift hoping to "fix it later".

## Success Metrics

Implementation is successful if:
- ✅ Final code matches original design intent
- ✅ All design requirements met
- ✅ No new patterns introduced
- ✅ Original problem actually solved
- ✅ Someone reading only the design would recognize the code

## Example: Preventing Our Previous Failure

**Original Design:** Commands use function handlers  
**What Went Wrong:** Assumed inheritance, created class-based commands  
**How This Protocol Would Have Prevented It:**

1. **Design Lock:** Would have explicitly stated "no inheritance"
2. **Validation Script:** Would have caught class-based pattern
3. **Context Chain:** Would have reminded "use function handlers"
4. **North Star:** Would have kept original pattern visible

## The Key Insight

**Drift is not a technical problem, it's a memory problem.**

By creating external memory (design locks, context chains, validation scripts) that persists across increments, we prevent the gradual forgetting that leads to drift.

Think of it like this:
- **Without protocol:** Like navigating by dead reckoning, errors compound
- **With protocol:** Like navigating with GPS, constant course correction

## Summary

Prevent drift through:
1. **Immutable design reference** (design lock file)
2. **Continuous validation** (after every increment)
3. **Explicit context passing** (context chain)
4. **Early detection** (drift indicators)
5. **Hard stops** (validation failures)

The goal: Make it impossible to drift without knowing it.

---

*"A journey of a thousand miles begins with a single step... in the right direction."*
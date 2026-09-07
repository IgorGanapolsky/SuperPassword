# Skill: Fresh Start

Archive current session learnings and begin a clean context window. Use when previous context becomes irrelevant or cluttered.

## Trigger

- User invokes `/fresh-start`
- Context has accumulated too many unrelated topics
- Starting a distinctly new task after completing previous work

## Workflow

### 1. Archive Current Session

Save key learnings from the current session:

```bash
# Create session archive
ARCHIVE_DIR=".claude/memory/sessions"
SESSION_ID=$(date +%Y%m%d-%H%M%S)
mkdir -p "$ARCHIVE_DIR"
```

Document in archive file:

- Key decisions made
- Patterns discovered
- Errors encountered and solutions
- Files modified

### 2. Consolidate Feedback

Invoke ROSE-lite autowire (agents only — never hand this to the CEO):

- Prefer the SessionStart hook / `scripts/agent_rose_lite/autowire.py --mode session-start` which already runs ingest + maintain + hybrid recall.
- Confirm `.claude/memory/rose_lite_session.json` or hook `additionalContext` is present before continuing.
### 3. Reset Working Context

Clear transient state while preserving:

- Memory cells (.claude/memory/memory_cells.jsonl)
- CLAUDE.md documentation
- Feedback logs (for future learning)

### 4. Prepare Fresh Context

Load only essential context for the new task:

- Project structure overview
- Recent git history (last 5 commits)
- Active TODO items
- Critical lessons from semantic memory

### 5. Confirm Fresh Start

Output a clean session header:

```
============================================
FRESH SESSION - Random Timer
============================================
Previous session archived: {SESSION_ID}
Learnings consolidated: {count} entries

Ready for new task.
============================================
```

## When to Use

**Good candidates for fresh start:**

- Completed a major feature, starting something unrelated
- Debugging session is polluting context with failed attempts
- Conversation has gone in circles
- Starting a new day's work

**NOT recommended when:**

- Mid-way through a multi-step task
- Context is still relevant to current work
- Debugging an issue (history might help)

## Session Archive Format

`.claude/memory/sessions/{SESSION_ID}.md`:

```markdown
# Session: {SESSION_ID}

## Summary

Brief description of what was accomplished

## Decisions Made

- Decision 1: rationale
- Decision 2: rationale

## Patterns Discovered

- Pattern: description

## Errors & Solutions

- Error: solution

## Files Modified

- path/to/file.ts: description of changes
```

## Success Criteria

- Previous learnings are archived, not lost
- Semantic memory is up-to-date
- Context window is clean and focused
- Ready to begin new work efficiently

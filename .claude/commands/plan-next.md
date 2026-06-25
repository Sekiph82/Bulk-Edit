# /plan-next — Plan the Next Sprint or Task

## Instructions for Claude

1. Read TASKS.md — find next sprint marked `[ ] TODO`
2. Read ARCHITECTURE.md — understand dependencies
3. Read DECISIONS.md — understand prior constraints
4. Read PROJECT_STATUS.md — check for blockers

Then produce:

## Plan Format

```
NEXT SPRINT PLAN: Sprint N — [Name]

Active skills:
- [skill-id] [skill-name] (primary)
- [skill-id] [skill-name] (supporting)

Files to inspect first:
- [file path] — reason

Tasks (in order):
1. [task description]
   - Files changed: [list]
   - Tests: [list]
2. [task description]
   ...

Dependencies / blockers:
- [any credential, API key, or prior task required]

Estimated sessions: [N]

Ready to start? Say 'go' or 'başla'.
```

Do not begin implementation until user confirms.

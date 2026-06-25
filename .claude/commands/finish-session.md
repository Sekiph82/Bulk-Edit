# /finish-session — End of Session Protocol

## Instructions for Claude

Full session end. Execute in order:

1. Complete the current atomic task if < 10 minutes of work remains. Otherwise stop mid-task.
2. Run tests:
   ```bash
   cd apps/backend && pytest --tb=short -q 2>/dev/null || echo "No backend tests yet"
   cd apps/frontend && npm test -- --passWithNoTests 2>/dev/null || echo "No frontend tests yet"
   ```
3. Update TASKS.md — mark all status accurately
4. Update PROJECT_STATUS.md
5. Update HANDOFF.md:
   - Exact file and line stopped at
   - Exact next task
   - Exact copy-paste prompt for next session
   - All known issues
6. Update CHANGELOG_AI.md with session summary
7. Update DECISIONS.md if decisions were made
8. Commit and push:
   ```bash
   git add .
   git status
   git commit -m "chore: end of session — sprint N — <description>"
   git push origin main
   ```
9. Print session summary to user

## Session Summary Format

```
SESSION COMPLETE
Date: [date]
Sprint: [N]
Tasks completed: [list]
Tasks remaining: [list]
Blockers: [list or none]
Next session starts with: [exact prompt from HANDOFF.md]
Push: [success / failed]
```

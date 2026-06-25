# /checkpoint — Save State and Stop

## Instructions for Claude

Execute immediately when triggered:

1. **Stop** — do not start any new work
2. **Run tests** if currently in a coding sprint:
   ```bash
   cd apps/backend && pytest --tb=short -q 2>/dev/null || echo "No tests yet"
   cd apps/frontend && npm test -- --passWithNoTests 2>/dev/null || echo "No tests yet"
   ```
3. **Update TASKS.md** — mark completed `[x]`, in-progress `[~]`, blocked `[!]`
4. **Update PROJECT_STATUS.md** — current sprint, blockers, metrics
5. **Update HANDOFF.md** — exact file, function, line being worked on; exact next prompt
6. **Update CHANGELOG_AI.md** — append session summary
7. **Update DECISIONS.md** — if any decision was made this session
8. **Commit and push**:
   ```bash
   git add .
   git status
   git commit -m "chore: checkpoint — <brief description>"
   git push origin main
   ```
9. If push fails — document exact error in HANDOFF.md

## Output Format

After checkpoint:
```
CHECKPOINT COMPLETE
Sprint: [N]
Last completed: [task]
Next task: [exact description]
Push: [success / failed — error]
```

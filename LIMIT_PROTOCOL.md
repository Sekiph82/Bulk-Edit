# LIMIT_PROTOCOL.md — Context Limit and Checkpoint Protocol

## Trigger Words

When the user says any of these words or phrases, immediately execute the checkpoint protocol:

- `checkpoint`
- `limit`
- `dur`
- `finish session`
- `oturumu bitir`

Also execute when:
- Approaching context window limit (estimated)
- About to start a task that may not complete in one session
- User ends the conversation unexpectedly

---

## Checkpoint Protocol (Execute in Order)

### Step 1 — Stop New Work
Do not start any new file, function, or task. Finish the current atomic unit only.

### Step 2 — Run Tests (if possible)
Run any tests relevant to the current sprint. Document results.

```bash
# backend tests
cd apps/backend && pytest --tb=short -q

# frontend tests
cd apps/frontend && npm test -- --passWithNoTests
```

### Step 3 — Update TASKS.md
- Mark completed tasks as `[x]`
- Mark in-progress tasks as `[~]`
- Add any newly discovered tasks

### Step 4 — Update PROJECT_STATUS.md
- Update current sprint
- Update blockers
- Update metrics

### Step 5 — Update HANDOFF.md
Write:
- Exact file being worked on when stopped
- Exact function or section being written
- Exact next action
- Exact next prompt for next session
- Any known issues

### Step 6 — Update CHANGELOG_AI.md
Append a session summary entry.

### Step 7 — Commit and Push

```bash
git add .
git status
git commit -m "chore: checkpoint — <brief description>"
git push origin main
```

If push fails, document exact error in HANDOFF.md.

---

## Resume Protocol

At start of next session, read in order:

1. `CLAUDE.md`
2. `TASKS.md`
3. `SKILLS.md`
4. `PROJECT_STATUS.md`
5. `HANDOFF.md` — find exact resume point
6. `DECISIONS.md`
7. `LIMIT_PROTOCOL.md`

Then execute the exact next action from HANDOFF.md.

---

## What Never Gets Skipped

Even in emergency limit situations:
- HANDOFF.md must be updated with exact resume point
- CHANGELOG_AI.md must get a summary entry
- TASKS.md must reflect current state
- Code must be committed (even if incomplete — with a `WIP:` prefix)

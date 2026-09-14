# /audit

Perform an independent truth audit of the active work and the H!veAI tracker state.

1. Read `CLAUDE.md`, root `TASKS.md`, and relevant source/tests/evidence.
2. Verify the implementation claim independently. Builder/agent self-report is not acceptance evidence.
3. Verify root `TASKS.md` remains the only current-state ledger.
4. Verify Project Status labels are plain text and parser-compatible:
   - `Current Milestone:`
   - `Current Sprint:`
   - `Current Task:`
   - `Current Task Status:`
   - `Next Task/Action:`
   - `Required Actor:`
   - `Workflow State:` when used
5. Verify canonical task rows use only `- [x]`, `- [~]`, `- [!]`, or `- [ ]` plus a stable task ID, `—`, and title.
6. Flag checkbox evidence/notes as tracker defects because H!veAI will count them as tasks.
7. Verify current metadata agrees with the canonical row owning the active work.
8. Verify blockers, required actor, owner-only live actions, and acceptance gates are truthful.
9. Record findings without silently promoting tasks to `[x]`.
10. A read-only audit must not edit, commit, push, open a PR, run migrations, or mutate production state.

Historical archived tracker files are provenance only and should not be rewritten to look current.

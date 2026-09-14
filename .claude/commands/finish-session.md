# /finish-session

Close the session without creating tracker drift.

1. Finish the current safe atomic unit and run relevant tests when feasible.
2. Update root `TASKS.md` when current task/status/next action/actor/workflow/blockers or a canonical task marker changed.
3. Keep H!veAI parser fields plain and task rows parser-safe.
4. Append meaningful engineering history to `CHANGELOG_AI.md`.
5. Append durable decisions to `DECISIONS.md` when needed.
6. Review Git status/diff and confirm no secrets or unrelated files are staged.
7. Commit/push only when appropriate to the task and branch policy.
8. Report the canonical current task and next action from root `TASKS.md`.

Do not write duplicated live state into `PROJECT_STATUS.md` or `HANDOFF.md`; both are compatibility pointers only.

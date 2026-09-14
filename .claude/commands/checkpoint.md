# /checkpoint

Create a safe H!veAI-compatible checkpoint without creating a second tracker.

1. Read root `TASKS.md` and `LIMIT_PROTOCOL.md`.
2. Finish only the current safe atomic unit.
3. Run relevant tests when feasible.
4. Update root `TASKS.md` only if project truth changed:
   - Project Status fields
   - matching canonical task row
   - Blockers/Waits
5. Keep Project Status labels plain text, never Markdown-bolded.
6. Use only parser-safe task rows: `- [x]`, `- [~]`, `- [!]`, `- [ ]` followed by stable task ID + `—` + title.
7. Keep evidence as ordinary bullets so H!veAI does not count evidence as tasks.
8. Append engineering history to `CHANGELOG_AI.md` and durable decisions to `DECISIONS.md` when warranted.
9. Commit/push only when appropriate to branch and production-deploy policy.

Do not update `PROJECT_STATUS.md` or `HANDOFF.md` with duplicated live state. They are compatibility pointers only.

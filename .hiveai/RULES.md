# H!veAI Project Control Rules v1

All H!veAI tracked repositories use this same control-plane contract.

## Mandatory read order
1. `.hiveai/PROJECT.json`
2. `.hiveai/RULES.md`
3. `.hiveai/STATE.json`
4. `.hiveai/HANDOFF.md`
5. canonical task source declared in PROJECT.json
6. task-specific project documents

## Truth
- Canonical task ledger: `TASKS.md`.
- STATE.json = current materialized state.
- HANDOFF.md = resume pointer.
- EVENTS.jsonl = append-only lifecycle history.
- Builder logs = CLAIM_ONLY.
- Audits = independent evidence.
- Never create a second task ledger.

## Mandatory post-action sync
After any meaningful task, workflow, audit, remediation, agent-session, blocker, owner-acceptance, or release change:
1. update canonical task source if task truth changed;
2. update STATE.json;
3. update HANDOFF.md;
4. append one EVENTS.jsonl row;
5. write new prompt/log/audit artifacts under standard .hiveai directories when applicable.

Workflow states: IDLE, READY, IN_PROGRESS, AWAITING_AUDIT, CHANGES_REQUIRED, BLOCKED, WAITING_OWNER, COMPLETE.

Event schema: `{"schema":"hiveai-event/v1","eventId":"<id>","projectKey":"bulk-edit","type":"<type>","at":"<UTC>","actor":"CODEX|CLAUDE|CHATGPT|OWNER|SYSTEM","taskId":"<id|null>","workflowState":"<state>","summary":"<fact>","commit":"<sha|null>","auditId":"<id|null>","sessionId":"<id|null>"}`

## Refresh contract
H!veAI watches canonical task source, PROJECT/STATE/HANDOFF/EVENTS, Git HEAD/index/refs, and standard artifact directories. Filesystem changes trigger immediate debounced refresh. A 60-second reconciliation is fallback only.

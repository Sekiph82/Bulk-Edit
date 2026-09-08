hiveaiDashboardSchema: hiveai-project-dashboard/v1
projectKey: bulk-edit
repository: Sekiph82/Bulk-Edit
branchPolicy: main
dashboardMode: source-map
trackingMode: canonical-control-plane-v1
refreshPolicy: watcher-first-500ms-plus-60s-reconcile

## Source authorities

Canonical task source: `TASKS.md`
Handoff source: `.hiveai/HANDOFF.md`
Roadmap source: `TASKS.md`
Progress/history source: `.hiveai/EVENTS.jsonl`
Architecture source: `.hiveai/PROJECT.json`
Decision/governance source: `.hiveai/RULES.md`
Agent instruction source: `.hiveai/RULES.md`
Build/test metadata: `.hiveai/STATE.json`

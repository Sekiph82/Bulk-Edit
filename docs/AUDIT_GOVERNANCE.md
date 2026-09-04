# Bulk Edit Strict Audit Governance

Source lineage: adapted from the H!veAI strict audit governance standard in `Sekiph82/AI-Commerce-HQ` (`H!veAI/AGENTS.md`, branch `H!veAI`). This file is the canonical Bulk Edit audit contract for every future log/PR review.

## Core rule

A Claude/Codex completion log, final report, or checklist is a claim, not proof. The independent audit must recover the actual contract, inspect repository truth, verify changed code and docs, and explicitly separate proven work from partial, missing, risky, or unverifiable work.

## Mandatory audit sections

Every audit must include these sections:

1. `VERDICT` — exactly one of `PASS`, `CONDITIONAL`, or `FAIL`.
2. `CONTRACT RECOVERY` — what the prompt, TASKS, docs, prior audits, and acceptance criteria actually required.
3. `BRANCH / HEAD / DIFF SCOPE` — audited branch, PR number, merge commit, changed files, and final HEAD.
4. `ACCEPTANCE CRITERIA MATRIX` — every criterion marked `PASS`, `PARTIAL`, `FAIL`, or `UNVERIFIED`.
5. `BUILDER CLAIMS VS REPOSITORY TRUTH` — compare log/final-report claims against real implementation.
6. `FILE / SYMBOL EVIDENCE` — inspect real implementation files, endpoints, symbols, migrations, config, UI components, and runtime boundaries.
7. `FOCUSED TEST EVIDENCE` — verify tests that directly exercise changed behavior.
8. `REGRESSION EVIDENCE` — verify relevant previously completed behavior still works.
9. `SECURITY / SAFETY REVIEW` — Etsy writes, billing, secrets, env, PII, permissions, destructive actions, and unsafe fallbacks.
10. `ARCHITECTURE CONSISTENCY` — check implementation against Bulk Edit architecture and cross-milestone contracts.
11. `TRACKER / LOG / DOCUMENTATION TRUTHFULNESS` — TASKS, HANDOFF, PROJECT_STATUS, CHANGELOG_AI, DECISIONS, H!veAI dashboard, local log, and LOG_INDEX must match repository reality.
12. `FINAL REPOSITORY STATE` — verify PR merge state, remote visibility, CI, deploy status, and historical-log preservation.
13. `OPEN CROSS-MILESTONE FINDINGS` — carry forward known gaps; do not silently forget them.
14. `DEFECTS BY SEVERITY` — classify as `BLOCKER`, `MAJOR`, `MINOR`, or `NOTE`.
15. `TECHNICAL DEBT / UPGRADE OPPORTUNITIES` — production hardening or maintainability work that is not blocking.
16. `UNVERIFIED ITEMS` — anything lacking evidence remains explicitly unverified.
17. `REGRESSION RISK` — `LOW`, `MEDIUM`, or `HIGH`, with rationale.
18. `AUDIT CONFIDENCE` — `LOW`, `MEDIUM`, or `HIGH`, with rationale.
19. `FINAL VERDICT` — concise closure statement.
20. `REQUIRED REMEDIATION` — exact fixes required before progression when verdict is not unconditional `PASS`.

## Evidence rules

- Treat logs, final reports, and PR bodies as claims to verify.
- Prefer source code, migrations, tests, CI, deploy evidence, Git history, runtime-safe route checks, and owner-provided screenshots over summaries.
- A passing test suite does not override a direct specification violation.
- A feature that exists only in a test/mock path but not production code is not complete.
- If a manual acceptance step is required and was not performed, mark it `UNVERIFIED` or `PENDING MANUAL ACCEPTANCE`.
- If environment limitations prevent verification, record the limitation explicitly.
- Cross-milestone regressions or previously missed defects may reopen earlier milestone findings.
- Historical logs are immutable; corrections belong in new audit/remediation files.
- Do not approve solely because implementation compiles, tests pass, or Claude/Codex says `COMPLETE`.
- Do not mark TASKS.md `[x]` unless the implementation, tests/route evidence, and manual evidence where required all support it.
- When TASKS.md remains stale or overstates completion, the audit must flag it as a documentation/tracker defect.

## Verdict semantics

- `PASS`: all blocking requirements are satisfied with sufficient evidence; only clearly non-blocking notes remain.
- `CONDITIONAL`: core implementation is substantially correct, but bounded required follow-ups remain before the next quality gate or release boundary.
- `FAIL`: any blocker, specification violation, unsafe behavior, missing required evidence, or materially incomplete acceptance criterion exists.

## Remediation prompt rule

When an audit finds required fixes, create a bounded remediation prompt. For each finding, include:

- originating milestone/finding
- severity
- exact file/symbol or subsystem where known
- current incorrect behavior
- required target behavior
- required code/config/documentation changes
- focused tests to add or update
- regression tests that must remain green
- security/safety constraints
- acceptance criteria for closure
- prohibited shortcuts or scope expansion

## Bulk Edit audit minimum evidence checklist

For every future uploaded log, the auditor must inspect or verify:

- Uploaded local execution log and `LOG_INDEX.md` row.
- GitHub PR metadata, merge commit, changed files, diff, and review threads.
- CI/check status for the merge/head commit.
- TASKS.md exact changed sections and whether they match real evidence.
- HANDOFF.md, PROJECT_STATUS.md, CHANGELOG_AI.md, DECISIONS.md, and `.hiveai/PROJECT_DASHBOARD.md` when touched.
- Any schema/migration impact and whether deploy/migration succeeded.
- Any Etsy/write/revert/sync/media/video/billing/env/DNS/secret safety boundary.
- Owner-provided screenshots only as manual evidence, never as code proof.

## Audit response format

Use this compact status vocabulary inside the acceptance matrix:

- `KANITLANDI / PASS`
- `KISMEN KANITLANDI / PARTIAL`
- `KANITLANMADI / FAIL`
- `KANIT YOK / UNVERIFIED`
- `RISK`

The final answer must state clearly what was audited, what was not audited, and what must happen next.
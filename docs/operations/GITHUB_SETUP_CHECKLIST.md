# GitHub Setup Checklist (manual — repo owner)

These are dashboard settings that code cannot set. Do them once. They enforce the
workflow in `GIT_WORKFLOW.md`.

> **STATUS: COMPLETED 2026-07-02.** Verified from the public rulesets API:
> - `main` ruleset active — PR required, 1 approval, 5 required checks (Backend Tests,
>   Frontend Lint & Build, Docker Compose Validate, Analyze python, Analyze js-ts),
>   no force-push, no deletion.
> - `staging` ruleset active — same rules.
> Owner-confirmed (not API-visible): Secret scanning + Push protection enabled,
> Dependabot alerts + security updates enabled, Actions workflow permissions
> read-only, Actions cannot create/approve PRs. CI + CodeQL green on staging `faf5dae`.

## 1. Branches

- [ ] Confirm `staging` branch exists (pushed).
- [ ] Set default PR base to `staging` (Settings → General → Pull Requests, optional).

## 2. Branch protection — `main` (Settings → Branches → Add rule)

- [ ] Require a pull request before merging; **require 1 approval**.
- [ ] Dismiss stale approvals on new commits.
- [ ] Require status checks to pass:
  - [ ] `Backend Tests` (ci.yml)
  - [ ] `Frontend Lint & Build` (ci.yml)
  - [ ] `Docker Compose Validate` (ci.yml)
  - [ ] `Analyze (python)` + `Analyze (javascript-typescript)` (codeql.yml)
- [ ] Require branches to be up to date before merging.
- [ ] **Block force pushes.**
- [ ] **Include administrators** (no bypass).
- [ ] Restrict who can push to matching branches: none (PR-only).

## 3. Branch protection — `staging`

- [ ] Require a pull request before merging (approval optional — testers iterate).
- [ ] Require CI + CodeQL status checks to pass.
- [ ] Block force pushes.

## 4. Code security (Settings → Code security and analysis)

- [ ] Enable **Secret scanning**.
- [ ] Enable **Push protection** (blocks committing secrets).
- [ ] Enable **Dependabot alerts**.
- [ ] Enable **Dependabot security updates**.
- [ ] Confirm `dependabot.yml` version-update PRs appear (target `staging`).
- [ ] CodeQL: either the committed `codeql.yml` (advanced) OR "Default setup" — not both.

## 5. Actions (Settings → Actions → General)

- [ ] Workflow permissions: **Read repository contents** by default.
- [ ] Do not allow Actions to push to `main`.

## 6. Access

- [ ] Confirm collaborators/teams and least-privilege roles.
- [ ] Enable 2FA requirement for the org/repo if available.

## Verification

- [ ] Attempt a direct push to `main` from a clone → must be **rejected**.
- [ ] Open a test PR with a fake secret → push protection should block it.
- [ ] Confirm CI + CodeQL run on PRs into `staging` and `main`.

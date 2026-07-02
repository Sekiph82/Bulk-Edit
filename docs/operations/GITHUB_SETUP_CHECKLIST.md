# GitHub Setup Checklist (manual — repo owner)

These are dashboard settings that code cannot set. Do them once. They enforce the
workflow in `GIT_WORKFLOW.md`.

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

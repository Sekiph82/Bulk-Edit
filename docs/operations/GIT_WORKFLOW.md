# Git Workflow

Branch model that keeps AI/dev changes off production until reviewed.

## Branches

| Branch | Role | Deploys to |
|---|---|---|
| `main` | Production. Protected. No direct pushes. | Production DO app (later phase) |
| `staging` | Integration/test. Protected (lighter). | Staging DO app |
| `feature/*` | Active development (AI + human). | Ephemeral / preview |

## Flow

```
feature/*  --PR-->  staging  --(tester approval)-->  main
   dev              staging deploy + QA              production deploy
```

1. Branch from `staging`: `git checkout staging && git pull && git checkout -b feature/<slug>`.
2. Commit work on the feature branch. Never commit to `main` or `staging` directly.
3. Open a PR into **`staging`**. CI + CodeQL must pass.
4. Merge to `staging` → staging auto-deploys → tester verifies on `staging.bulkeditapp.com`.
5. Only after staging approval, open a PR **`staging` → `main`** with ≥1 human approval.
6. Merge to `main` → production deploys (later phase).

## Hard rules

- **No one pushes to `main` directly** — not humans, not AI tools, not Actions.
- Every change reaches production only via `feature/* → staging → main`.
- Hotfix path: `feature/hotfix-*` → PR into `staging` → fast-track review → `main`. Only use a
  temporary admin override for true emergencies, then re-enable protection immediately.
- Dependabot PRs target `staging` (see `.github/dependabot.yml`).
- App rollback (revert deploy) is **not** DB rollback. See `BACKUP_AND_ROLLBACK.md`.

## Commit hygiene

- Conventional-style subjects (`feat:`, `fix:`, `chore:`, `docs:`, `security:`).
- Never commit secrets or `.env*` (only `.env.example` / `deploy-secrets.local.env.example`).
- Update `CHANGELOG.md` for user-visible changes.

The GitHub-side settings that enforce this are in `GITHUB_SETUP_CHECKLIST.md`.

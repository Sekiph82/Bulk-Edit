# Release Checklist

## Pre-Release (Every Sprint)

- [ ] All sprint tasks marked complete in TASKS.md
- [ ] All tests pass (backend pytest, frontend Vitest)
- [ ] No critical security findings in SECURITY.md
- [ ] HANDOFF.md updated with next sprint entry
- [ ] CHANGELOG_AI.md updated
- [ ] Code committed and pushed to main

## v1.0 Release Checklist

### Code Quality
- [ ] Backend test coverage > 80%
- [ ] Frontend test coverage > 70%
- [ ] All E2E tests pass
- [ ] No TypeScript errors (`npm run build`)
- [ ] No Python type errors (`mypy app/`)
- [ ] Linters pass (`ruff`, `eslint`)

### Security
- [ ] OWASP ZAP scan complete — no critical findings
- [ ] `pip audit` — no known vulnerabilities
- [ ] `npm audit` — no known vulnerabilities
- [ ] All secrets in env vars (no hardcoded values in git)
- [ ] Rate limiting tested and working
- [ ] Stripe webhook signature verification tested
- [ ] JWT expiry and rotation tested
- [ ] Etsy token encryption verified

### Etsy Safety
- [ ] Bulk write safety protocol tested end-to-end
- [ ] Preview flow working correctly
- [ ] Snapshot backup verified before every write
- [ ] Magic Revert tested and working
- [ ] Audit log verified for all write operations
- [ ] Subscription gate tested on all Pro features

### Infrastructure
- [ ] Production Docker Compose / cloud configs ready
- [ ] Production environment variables set
- [ ] SSL configured
- [ ] Database backed up
- [ ] Redis persistence configured
- [ ] S3 bucket configured with correct permissions
- [ ] Health endpoints returning 200 in production

### Stripe (Live Mode)
- [ ] Stripe products and prices created in live mode
- [ ] Live price IDs set in production env
- [ ] Stripe webhook endpoint registered in live mode
- [ ] Test checkout completed in live mode
- [ ] Customer portal working in live mode

### Monitoring
- [ ] Sentry configured and receiving errors
- [ ] Celery worker monitoring configured
- [ ] Database connection monitoring active

### Communication
- [ ] README updated with live setup instructions
- [ ] Support email configured

## Post-Release

- [ ] Monitor error rate for 24 hours
- [ ] Monitor Celery queue depth
- [ ] Monitor Stripe webhook delivery
- [ ] Tag release: `git tag v1.0.0 && git push origin v1.0.0`

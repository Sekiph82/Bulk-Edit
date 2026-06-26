# SECURITY.md — Security Rules and Findings

## Non-Negotiable Security Rules

1. Never hardcode secrets in any file committed to the repository.
2. All secrets must be in environment variables loaded at runtime.
3. HTTPS only in production. HTTP strictly for local development.
4. All Etsy tokens must be encrypted at rest in the database.
5. JWT access tokens expire in 15 minutes. Refresh tokens expire in 7 days.
6. Refresh tokens are rotated on every use.
7. Token blacklist maintained in Redis for logout and revocation.
8. Stripe webhook signatures must always be verified.
9. All admin routes must verify `role=admin` on every request.
10. No PII or credentials may appear in logs.
11. All user inputs must be validated with Pydantic schemas.
12. SQL queries must use ORM parameterization — no raw string interpolation.
13. File uploads must validate type and size before accepting.
14. CORS must be configured to allow only known frontend origins.
15. Rate limiting must be applied to all public endpoints.
16. All external write operations must be logged in the audit log.

---

## OWASP Top 10 Mitigation Plan

| Risk | Mitigation |
|---|---|
| A01 Broken Access Control | RBAC on all routes, organization-scoped queries |
| A02 Cryptographic Failures | Bcrypt passwords, encrypted Etsy tokens, HTTPS |
| A03 Injection | SQLAlchemy ORM, Pydantic validation |
| A04 Insecure Design | Preview-before-write, safe external write protocol |
| A05 Security Misconfiguration | Env vars only, no debug mode in prod |
| A06 Vulnerable Components | Dependabot alerts, regular dependency updates |
| A07 Auth Failures | JWT rotation, short expiry, Redis blacklist |
| A08 Software/Data Integrity | Webhook signature verification |
| A09 Logging Failures | Structured logging, no PII in logs, audit trail |
| A10 SSRF | Whitelist allowed external URLs, no user-controlled URLs |

---

## Local Superuser Seed Security Rules

1. Real credentials for local demo users go in `apps/backend/.local-superusers.env` only.
2. That file is gitignored (`*.env` pattern + explicit paths) and must never be committed.
3. The example file `apps/backend/.local-superusers.env.example` contains fake placeholder values only.
4. The seed script never prints passwords and never logs secrets.
5. No Stripe calls are made — subscription records are created directly in DB (local dev only).
6. Seeded users are marked `is_superuser=True` for local dev access only.
7. Do not use the same credentials in any other environment.

---

## Security Findings Log

| Date | Severity | Finding | Status |
|---|---|---|---|
| — | — | No findings yet | — |

---

## Planned Security Hardening (Sprint 18)

- [ ] Run automated OWASP ZAP scan
- [ ] Run dependency vulnerability audit (`pip audit`, `npm audit`)
- [ ] Review all JWT handling
- [ ] Review all Stripe webhook handling
- [ ] Review CORS and CSP headers
- [ ] Review rate limiting coverage
- [ ] Review file upload validation
- [ ] Review admin route protection
- [ ] Review audit log completeness
- [ ] Penetration test checklist

# /audit — Security and Consistency Audit

## Instructions for Claude

Run all checks. Report findings. Do not fix without user confirmation.

### 1. Secret Audit
Search for hardcoded secrets:
```bash
grep -rn "sk_" apps/ --include="*.py" --include="*.ts" --include="*.tsx"
grep -rn "password\s*=" apps/ --include="*.py" --include="*.ts"
grep -rn "secret\s*=" apps/ --include="*.py" --include="*.ts"
```

### 2. Auth Audit
- All routes have auth middleware?
- Admin routes check `role=admin`?
- JWT expiry configured correctly?

### 3. External Write Audit
Search for Etsy PUT/POST/PATCH calls:
```bash
grep -rn "etsy" apps/backend --include="*.py" | grep -i "put\|post\|patch\|delete"
```
Verify each call goes through `safe-external-write` skill path.

### 4. Feature Gate Audit
Search for paid feature endpoints and verify gate middleware is applied.

### 5. AI Output Audit
Verify no AI output is applied directly — all go through preview flow.

### 6. Documentation Consistency
- TASKS.md matches actual code state?
- DECISIONS.md up to date?
- DATABASE_SCHEMA.md matches current models?
- API_SPEC.md matches current endpoints?

## Report Format

```
AUDIT REPORT — [date]

CRITICAL: [list or none]
HIGH: [list or none]
MEDIUM: [list or none]
LOW: [list or none]

Recommendation: [fix order]
```

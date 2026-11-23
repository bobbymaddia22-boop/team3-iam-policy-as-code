# Decision Records

Each file records one design or scope decision: what we decided, why, and what evidence or finding supports it.

Naming: `NNNN-short-title.md`. Number them in order. Do not rewrite an old record. If a decision changes, add a new record that supersedes it.

## Template

```
# NNNN: Title

**Date:** YYYY-MM-DD
**Status:** Proposed / Accepted / Superseded by NNNN
**Decided by:** names

## Context
What problem or question led to this?

## Finding
The specific finding that informs this, with a citation (author, year, and what exactly it says).

## Decision
What we are doing.

## Consequences
What this means for the tests, evidence, and what we can claim.
```

## Index

| No. | Title | Status |
|-----|-------|--------|
| 0001 | Scope the control to registered MFA devices | Accepted |
| 0002 | Separate data collection from policy evaluation | Accepted |
| 0003 | Treat a never-used password as in scope (no grace period) | Proposed |

# 0002: Separate data collection from policy evaluation

**Date:** 2026-11-22
**Status:** Accepted
**Decided by:** Team 3

## Context
The automated check (`automation/mfa_checker/`) has two parts: `collect_iam_state.py` gathers IAM data, and `policy/mfa.rego` evaluates it with OPA.

## Finding
Keeping the two parts apart made both testable in this project. The Rego rule is tested against hand-written snapshots without AWS (`policy/mfa_test.rego`, 8 tests), and the collector is tested end to end against simulated IAM (`tests/test_pipeline.py`, 8 tests). The collector needs only three read actions (`scanner-iam-policy.json`), and every run keeps its snapshot as the input that produced its report.

## Decision
The collector only reads and records data. The Rego policy only evaluates a saved snapshot. Neither part does the other's job.

## Consequences
- The policy can be tested without AWS (`policy/mfa_test.rego`).
- The collector can be limited to read-only permissions.
- The snapshot is the traceable input for each run, and it is not committed because it contains an unmasked account ID.

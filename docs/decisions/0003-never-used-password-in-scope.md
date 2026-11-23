# 0003: Treat a never-used password as in scope (no grace period)

**Date:** 2026-11-22
**Status:** Proposed
**Decided by:** Proposed by Bobby Maddia; the team confirms it in the team channel, then this changes to Accepted

## Context
Test user t7 has a console password that must be reset at next sign-in, has never been used, and has no MFA device. The question is whether a new user gets a grace period before the control applies.

## Finding
The control applies to "IAM users that have a console password" (CIS AWS Foundations Benchmark). It has no exception for a password that has not been used yet. A password that exists can be used to sign in whether or not it has been used before. In Run 02, the checker classified t7 as NON_COMPLIANT.

## Decision
There is no grace period. A user with a console password and no MFA device is NON_COMPLIANT, even if the user has never signed in.

## Consequences
- t7 is labeled NON_COMPLIANT in the answer key and in the test cases.
- If the team later adds a grace period, a new record supersedes this one, and the check and its tests change with it.
- Both populations that include a t7-like user (Run 02 and the sandbox set) must use the same label.

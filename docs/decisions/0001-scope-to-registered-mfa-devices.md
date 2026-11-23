# 0001: Scope the control to registered MFA devices

**Date:** 2026-11-22
**Status:** Accepted
**Decided by:** Team 3

## Context
Progress Report 1 used the phrase "MFA enforcement" for a check that reads IAM configuration. Reviewer feedback pointed out that reading registered devices shows whether MFA is configured, not whether AWS blocks a sign-in or API call that lacks MFA.

## Finding
The CIS AWS Foundations Benchmark control "Ensure multi-factor authentication (MFA) is enabled for all IAM users that have a console password" is a configuration requirement: it asks whether each such user has MFA enabled, not whether AWS denies a request that lacks it. Its control number differs between benchmark versions (see `tests/traceability-matrix.md`). The tests in this project read the registered devices, which is the same thing the control asks about.

## Decision
- The control under test is: every IAM user with a console password has at least one MFA device registered.
- The check classifies each user as COMPLIANT, NON_COMPLIANT, or NOT_APPLICABLE. NON_COMPLIANT is the positive class for scoring.
- "MFA enforcement" is used only for tests that show AWS actually denying access without MFA. Those are later work.
- Root MFA is reported separately and is not part of the user-control score.

## Consequences
- The test plan, test cases, and README use "MFA configuration check" wording.
- The policy-simulator cases (MFA-03, MFA-04, MFA-08) are labeled later work.
- Results from this project support claims about configuration detection on the labeled users, not about enforcement.

# Traceability Matrix: MFA Configuration Check

Shows that every requirement is covered by at least one test and has evidence, and shows
how much of that evidence exists today.

## Status key

- **Verified:** the evidence file is in the repository and a reader can check it.
- **Reported:** the team reports the result, but the raw files are not yet in the repository.
- **Designed:** the file or procedure exists but has not been run in the sandbox.
- **Planned:** nothing exists yet.

## Requirements

| Requirement | Source | Test case(s) | Evidence file(s) | Status | Last run |
|-------------|--------|--------------|------------------|--------|----------|
| R1: Root user has MFA | CIS AWS Foundations Benchmark, root-user MFA control (its number differs by benchmark version) | SAF-05 | Unit tests; `evidence/support/scanner-identity-and-negative-tests/` (screenshot 23: root MFA reported separately) | Reported | 2026-11-08 |
| R2: Every console user has an MFA device | CIS AWS Foundations Benchmark, "Ensure multi-factor authentication (MFA) is enabled for all IAM users that have a console password" (control 1.10 in v1.3.0 to v4.0.1, 1.9 in v5.0.0, 2.9 in v6.0.0, 2.10 in v7.0.0); NIST SP 800-53 Rev. 5 IA-2(1), IA-2(2) | T1 to T5, T6 to T8, blind set t10 to t39, CR-01 | Run 01: `evidence/run-01/` (findings, `labeled-population.csv`, `manual-audit.csv`, screenshots). T1 to T5 rebuilt: `evidence/support/practice-account-run/`. T6 to T8: `evidence/run-02/edge-cases-t6-t8/`. Blind test: `evidence/run-03/blind-30-user-test/`. Credential report cross-check: `evidence/support/credential-report-cross-check/` | Run 01: Reported (raw automated files not saved). T1 to T5: Verified. T6 to T8: Verified (t7 rule still open). Blind test: Verified (30 of 30, partly blind). CR-01: Verified (12 of 12 agree). | 2026-11-12 |
| Fair comparison of automated and manual methods | Team requirement | C1, C2 | `tests/manual-audit-procedure.md`; `evidence/run-03/blind-30-user-test/` | Verified for Run 03 (shuffled labels, key hash recorded at build and checked before scoring, one tester) | 2026-11-12 |
| R3: MFA enforced for sensitive actions | NIST SP 800-63B-4 (background) | LW-01, LW-02 | None | Planned (later work) | |

## Safety requirements

| Requirement | How it is checked | Test case(s) | Evidence file(s) | Status |
|-------------|-------------------|--------------|------------------|--------|
| SR2: Checks are read-only | `scanner-iam-policy.json`; test that the collector issues only read-only calls | SAF-01 | `automation/mfa_checker/scanner-iam-policy.json`, `automation/mfa_checker/tests/test_pipeline.py`, `evidence/support/scanner-identity-and-negative-tests/` | Verified. Run 01 used the root user. |
| SR3: Wrong account is refused | `--approved-account-id` checked before any IAM call | SAF-02 | `automation/mfa_checker/tests/test_pipeline.py`, `tests/test_check_mfa_status.py`, `tests/test_credential_report_check.py`, `evidence/support/scanner-identity-and-negative-tests/` | Verified at unit level. Live: Verified for the automated check (exit 2). |
| SR4: Results are traceable | Timestamp, masked account ID, tool versions, hashes | SAF-03 | Tool versions in each run's findings file. SHA-256 hash lists: `evidence/run-03/blind-30-user-test/SHA256SUMS.txt` and `evidence/support/credential-report-cross-check/SHA256SUMS.txt` | Verified for Run 03 and the cross-check. Hash lists are not recorded for Runs 01 and 02. |
| Fail closed: no result from unusable input | AWS errors and malformed reports stop the run | SAF-04 | `automation/mfa_checker/tests/test_pipeline.py`, `tests/test_credential_report_check.py`, `evidence/support/scanner-identity-and-negative-tests/` | Verified at unit level. Live: Verified (automated check exit 3, validation script exit 2). |

## How to maintain this file

1. After each run, update **Status**, **Evidence file(s)**, and **Last run**.
2. Move a row to **Verified** only when its evidence file is committed and a reader can
   check it.
3. If a requirement has no test case, add one in `test-cases.md` and link it here.
4. If a test case has no requirement, either link it to one or question why the test exists.

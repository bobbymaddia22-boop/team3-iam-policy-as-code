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
| R1: Root user has MFA | [CIS control ID, version] | SAF-05 | Unit tests only | Designed (live run not made) | |
| R2: Every console user has an MFA device | [CIS control ID, version] | T1 to T5, CR-01 | `evidence/run-01/findings.md`, `labeled-population.csv`, `manual-audit.csv`, redacted screenshots | Reported (raw automated files pending) | 2026-10-05 |
| Fair comparison of automated and manual methods | Team requirement | C1, C2 | `tests/manual-audit-procedure.md`; run 01 was not blind | Designed | |
| R3: MFA enforced for sensitive actions | NIST SP 800-63B-4 (background) | LW-01, LW-02 | None | Planned (later work) | |

## Safety requirements

| Requirement | How it is checked | Test case(s) | Evidence file(s) | Status |
|-------------|-------------------|--------------|------------------|--------|
| SR2: Checks are read-only | `scanner-iam-policy.json`; test that the collector issues only read-only calls | SAF-01 | `automation/mfa_checker/scanner-iam-policy.json`, `automation/mfa_checker/tests/test_pipeline.py` | Designed. Run 01 used the root user, so the scanner identity is untested. |
| SR3: Wrong account is refused | `--approved-account-id` checked before any IAM call | SAF-02 | `automation/mfa_checker/tests/test_pipeline.py`, `tests/test_check_mfa_status.py`, `tests/test_credential_report_check.py` | Verified at unit level. Live: Planned. |
| SR4: Results are traceable | Timestamp, masked account ID, tool versions, hashes | SAF-03 | `evidence/run-01/findings.md` (tool versions); hashes not yet recorded | Reported (hashes pending) |
| Fail closed: no result from unusable input | AWS errors and malformed reports stop the run | SAF-04 | `automation/mfa_checker/tests/test_pipeline.py`, `tests/test_credential_report_check.py` | Verified at unit level. Live: Planned. |
| SR1, SR5, SR6 | [copy each requirement from the report] | [fill in] | [fill in] | [fill in] |

## How to maintain this file

1. After each run, update **Status**, **Evidence file(s)**, and **Last run**.
2. Move a row to **Verified** only when its evidence file is committed and a reader can
   check it.
3. If a requirement has no test case, add one in `test-cases.md` and link it here.
4. If a test case has no requirement, either link it to one or question why the test exists.

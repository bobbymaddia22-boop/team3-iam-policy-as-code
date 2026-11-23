# Test Cases: MFA Configuration Check (AWS IAM)

Control under test: every IAM user with a console password has at least one MFA device
registered. These cases test whether the check **detects that configuration correctly**.
They do not test whether AWS blocks a sign-in or API call that lacks MFA. That work is
listed under "Later work" at the end of this file.

All identities, account IDs, and ARNs are placeholders. Keep real values out of this
public repo. The method for each run is set out in `test-plan.md` and
`manual-audit-procedure.md`.

Status values: Not run / Pass / Pass (evidence incomplete) / Fail / Blocked.
"Pass (evidence incomplete)" means the team reports the result but the raw output files
are not yet in `evidence/`.

## Summary

### A. Labeled population (both methods run on the same five users)

| ID | User | Configuration | Expected status | Requirement | Status |
|----|------|---------------|-----------------|-------------|--------|
| T1 | t1 | Console password and one MFA device | COMPLIANT | R2 | Pass  |
| T2 | t2 | Console password and no MFA device | NON_COMPLIANT | R2 | Pass |
| T3 | t3 | No console password (access key only) | NOT_APPLICABLE | R2 | Pass  |
| T4 | t4 | Console password; MFA device added then removed | NON_COMPLIANT | R2 | Pass  |
| T5 | t5 | Console password and two MFA devices | COMPLIANT | R2 | Pass  |
| T6 | t6 | MFA device and console password set, then the password removed | NOT_APPLICABLE | R2 | Pass |
| T7 | t7 | Console password, must reset at next sign-in, never used, no MFA | NON_COMPLIANT | R2 | Pass |
| T8 | t8.test+mfa,Case=A@team3 | Special characters in the username, console password, no MFA | NON_COMPLIANT | R2 | Pass |

### B. Method comparison

| ID | Title | Status |
|----|-------|--------|
| C1 | Blind manual audit on the labeled population | Not run |
| C2 | Repeated timing runs for both methods | Not run |
| CR-01 | Credential report cross-check on the labeled population | Not run (unit-tested only) |

### C. Safety and behavior

| ID | Title | Safety requirement | Unit or simulated test | Live sandbox |
|----|-------|--------------------|------------------------|--------------|
| SAF-01 | Checks are read-only | SR2 | Pass | Pass under the scanner identity |
| SAF-02 | Wrong account is refused | SR3 | Pass | Pass for the automated check |
| SAF-03 | Results are traceable to a run | SR4 | Pass | Hashes not yet recorded |
| SAF-04 | An unusable result is never a pass | Fail closed | Pass | Pass (exit 3 for the automated check, exit 2 for the validation script) |
| SAF-05 | Root MFA is reported separately | R1 | Pass | In Progress |

---

## A. Labeled population

Run each case once with the automated check and once with the manual audit. Record both
results against the answer key in `evidence/run-NN/labeled-population.csv`.

### T1 to T5

- **Requirement:** R2
- **Preconditions:** The five users exist in the sandbox account exactly as in the table
  above, built and labeled by the person who holds the answer key.
- **Steps:**
  1. Automated: run the check as described in `automation/mfa_checker/README.md` and save
     `report.csv` and `report.json`.
  2. Manual: follow `manual-audit-procedure.md` and save the results file.
  3. Score both against the answer key:
     `py scripts\score_results.py --truth ... --automated ... --manual ...`
- **Expected result:** each user receives the status in the summary table. NON_COMPLIANT is
  the positive class.
- **Boundary cases:**
  - T3 checks that a user with no console password is excluded, not flagged.
  - T4 checks that a user whose MFA device was removed is flagged, even though the user
    once had a device.
  - T5 checks that more than one device is handled.
- **Run 01 (2026-10-05):** the team reports that both methods matched the answer key for
  all five users, with no disagreements. The automated run was made in AWS CloudShell
  under the root user, not the read-only scanner identity. The raw `report.json` and
  `report.csv` are not yet in `evidence/run-01/automated/`. A CloudShell screenshot shows
  the per-user statuses and a total time of 0.5619 s.
- **Evidence:** `evidence/run-01/findings.md`, `labeled-population.csv`,
  `manual-audit.csv`, and the redacted screenshots


### T6 to T8: edge cases 

- **Requirement:** R2
- **Steps:** run the automated check under the read-only scanner identity, then score it
  against the combined answer key (t1 to t8) with `scripts\score_results.py`.
- **Expected result:** t6 NOT_APPLICABLE, t7 NON_COMPLIANT, t8 NON_COMPLIANT.
- **Boundary cases:**
  - T6 checks that the rule depends on the console password, not on whether an MFA device
    exists.
  - T7 checks that a user who has never signed in is still flagged. This assumes no grace
    period for new users. See `docs/decisions/0003-never-used-password-in-scope.md`.
  - T8 checks that special characters (+ @ , and mixed case) in a username do not break the
    output or cause the user to be skipped. The comma must stay inside one quoted CSV column.
- **Run 2026-11-08:** 8 of 8 exact matches (TP 4, FP 0, FN 0, TN 4).
- **Evidence:** `evidence/verification/2026-11-08-edge-cases-t6-t8/`

## B. Method comparison

### C1: Blind manual audit

- **Requirement:** fair comparison (`test-plan.md`, section 6)
- **Preconditions:** the auditor did not build or label the population and has not seen
  the answer key.
- **Steps:** follow `manual-audit-procedure.md`. Save the results file and record its
  SHA-256 hash before the answer key is opened.


### CR-01: Credential report cross-check

- **Requirement:** R2
- **Steps:** run `scripts\credential_report_check.py` against the sandbox with
  `--max-report-age-minutes` set, so the report is recent. Compare its user statuses with
  the labeled population.
- **Expected result:** the same status for each of the five users. The report generation
  time is recorded in the output.
- **Note:** AWS can reuse a report generated in the last four hours. Record the generation
  time with the result.
- **Status:** The logic is covered by unit tests in
  `tests/test_credential_report_check.py`.

## C. Safety and behavior

Each case has a simulated or unit-level test and a live sandbox test.

### SAF-01: Checks are read-only (SR2)

- **Unit or simulated:** `scanner-iam-policy.json` allows only list and get calls, and
  `test_collector_issues_only_read_only_calls` in `automation/mfa_checker/tests/test_pipeline.py`
  fails if the collector makes any other call.
- **Live:** the automated check ran under the scanner identity (5 of 5 matches),
  and the validation script ran under its own read-only identity (t2 and t4 FAIL). The
  validation script failed with AccessDenied under the scanner identity, as expected, because
  that identity lacks `iam:GetAccountSummary`. Not yet run in the sandbox.
- **Live:** run each check under a read-only identity, not root. The automated check uses
  the scanner policy. The validation scripts also read the account summary and the credential
  report, so they need `iam-config/validation-scripts-readonly-policy.json`. Confirm that
  each check completes and that the identity has no write permissions.
- **Note:** `GenerateCredentialReport` does not change a user, password, or MFA device, but it
  asks IAM to create a report. Say so when describing the scripts as read-only.
- **Expected result:** each check completes under its read-only identity.

### SAF-02: Wrong account is refused (SR3)

- **Unit or simulated:** `test_wrong_account_is_refused_before_any_iam_call` and
  `test_cli_exit_code_for_wrong_account` (automated check), and `AccountGuardTests` and
  `GuardAndInputTests` (validation scripts).
- **Live:** run each check with a deliberately wrong `--approved-account-id`.
- **Expected result:** exit code 2, an error that identifies the account problem, and no IAM
  call made. The collector's message names no account digits. The validation scripts' message shows only the last four digits of each account ID.
- **Live result:** the automated check refused to scan with exit code 2 and
  made no IAM call. The validation scripts were not run live with a wrong ID.

### SAF-03: Results are traceable to a run (SR4)

- **Unit or simulated:** `test_report_records_timestamp_account_and_timing` and
  `test_masked_report_hides_account_id_but_snapshot_keeps_it`.
- **Live:** each run folder holds the raw outputs, the SHA-256 hash of each file, the
  timings, the tool versions, and the identity used.
- **Expected result:** a reader can match every number in `findings.md` to a hashed file.

### SAF-04: An unusable result is never a pass

- **Unit or simulated:** `test_missing_permission_fails_closed` (automated check), and the
  empty, cut-off, and malformed credential report tests in
  `tests/test_credential_report_check.py` (validation scripts).
- **Live:** run a check under an identity that lacks one required permission.
- **Expected result:** exit with an error and no report. A clean-looking report is a failure.
- **Live result:** the automated check under an identity with no IAM
  permissions stopped with AccessDenied on `iam:ListUsers`, wrote no report, and exited 3. The
  validation script under the scanner identity stopped with AccessDenied and exited 2.
- **Finding:** `--mask-account-id` masks the report files only. AWS's own error text prints the
  full account ID, so it must be masked before it is published.

### SAF-05: Root MFA is reported separately (R1)

- **Unit or simulated:** `RootSeparationTests` in `tests/test_credential_report_check.py`
  and `EmptyAndRootTests` in `tests/test_check_mfa_status.py`.
- **Live:** record the root user's MFA status in the run and keep it out of the user-control
  score.
- **Expected result:** the user-control result is the same whether root MFA is on or off.
- **Live result:** the validation script reported root MFA PASS separately
  from the user-control result (FAIL, 2 failing of 4 console users). The comparison with root
  MFA off was not run.

---

## Later work (not part of the current claim)

These cases test whether AWS actually enforces MFA. They are not covered by the
configuration check and are not in the results above.

| ID | Title | Replaces |
|----|-------|----------|
| LW-01 | Console sign-in with and without MFA | MFA-01, MFA-02 |
| LW-02 | API or CLI action denied without MFA, allowed with an MFA session (policy simulator or live) | MFA-03, MFA-04 |
| LW-03 | Comparison with the AWS Config managed rules `iam-user-mfa-enabled` and `mfa-enabled-for-iam-console-access`, starting with t3 | |
| LW-04 | Passkey or security-key (FIDO) devices | |
| LW-05 | A larger population of users | |
|  | (Partly started, A 30-user blind set is planned.) | |
| LW-06 | A user changed after the collector has run | |

MFA-05 (MFA device removed) is covered by T4. MFA-06 (root MFA) is covered by SAF-05. MFA-07
(credential report) is covered by CR-01.

# MFA Configuration Check: Tests

Testing and validation materials for the IAM console-user MFA check.
This folder belongs to Team 3 (Cloud Identity and Policy-as-Code Assurance).

## Purpose

Show, with repeatable evidence, whether the check correctly detects this
configuration: every IAM user with a console password has at least one MFA device
registered. The tests compare an automated check with a manual audit on five labeled
users (t1 to t5). Three edge-case users (t6 to t8) have also been run.

These tests do not show that AWS blocks a sign-in or API call that lacks MFA. That is
enforcement testing, and it is listed as later work in `test-plan.md`.

## Contents

| File | What it is |
|------|------------|
| `test-plan.md` | Control, scope, the five labeled users, how the comparison is kept fair, metrics, and pass/fail criteria |
| `manual-audit-procedure.md` | Step-by-step procedure for the manual audit, including the rules and timing boundaries |
| `test-cases.md` | The individual test cases (steps, expected results) |
| `results-template.md` | Blank record to copy for each test run |
| `traceability-matrix.md` | Links each requirement to its test and evidence |
| `test_check_mfa_status.py` | Unit tests for `scripts/check_mfa_status.py` and `scripts/mfa_common.py` |
| `test_credential_report_check.py` | Unit tests for `scripts/credential_report_check.py` |
| `test_score_results.py` | Unit tests for `scripts/score_results.py` |

## Two kinds of testing

- **Unit tests** (`test_*.py`) check the scripts' logic with fake AWS clients. They do
  not need an AWS account and cannot show how the check behaves in a real account.
- **Labeled-population runs** use the five test users in the sandbox account. Their
  results are recorded in `evidence/run-NN/`.


The automated OPA/Rego check has its own tests in `automation/mfa_checker/tests/`.


## Run the unit tests

From the repository root:

```
py -m pip install -r scripts\requirements.txt
py -m unittest discover -s tests -v
```

A passing run ends with `OK`.

## Run a labeled-population test

1. Read `test-plan.md` and confirm the prerequisites are met.
2. Create the next run folder, for example `evidence/run-02/`, and copy in the
   labeled population file.
3. Run the automated check and the manual audit following `test-plan.md`, section 6.
   The manual auditor must not see the answer key until the results are saved.
4. Record the SHA-256 hash of each results file and the timings in the run's
   `findings.md`.
5. Score the run:
   ```
   py scripts\score_results.py --truth evidence\run-02\labeled-population.csv --automated evidence\run-02\automated\report.csv --manual evidence\run-02\manual-audit.csv --out-dir evidence\run-02
   ```
6. Update `traceability-matrix.md` with the final status.

## Rules for this public repository

- Never commit access keys, secret keys, session tokens, or passwords.
- Replace real account IDs, ARNs, and user names with placeholders such as
  `111122223333` and `example-user`.
- Redact the AWS console header, account alias, access key IDs, and email addresses
  in screenshots. Check the image at full size before committing it.
- Never commit `snapshot.json` or anything in `output-private/`.
- MFA device ARNs and serial numbers contain the account ID. AWS error text can print the
  full account ID even when the report files are masked. Check both before committing.
- Use only controlled lab data. No real user or organizational data.

## Owner

Testing and Validation Lead: Bobby Maddia

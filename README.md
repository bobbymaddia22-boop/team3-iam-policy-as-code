# team3-iam-policy-as-code

Capstone 2026 project: Team 3, Cloud Identity and Policy-as-Code Assurance.

## What this project does

The team compares an automated policy-as-code check with a manual audit for one AWS IAM
control: **every IAM user with a console password has at least one MFA device registered**.
The check reads registered-device configuration. It does not test whether AWS blocks a
sign-in or API call that lacks MFA. That is enforcement testing and is listed as later work.

Three methods are compared on labeled synthetic users with known answers (t1 to t5, then t1 to t8, then a blind set of 30):

1. **Automated policy-as-code check** (`automation/mfa_checker/`): a read-only collector
   gathers IAM facts and an Open Policy Agent (OPA) rule decides compliance.
2. **Independent validation scripts** (`scripts/`): Python checks of user MFA status and the
   IAM credential report, plus a script that scores results against the answer key. They
   cross-check the automated result. They are a validation tool, not a second implementation
   of the control.
3. **Manual audit** (`tests/manual-audit-procedure.md`): a person checks each test user
   by hand, which gives an accuracy and timing baseline.

## Status

As of 2026-11-22. Details are in `tests/traceability-matrix.md`.

| Item | State |
|------|-------|
| OPA rule, collector, and report (`automation/mfa_checker/`) | **Done.** 8 Rego tests and 8 end-to-end tests on simulated IAM. |
| Validation scripts and scoring script (`scripts/`) | **Done.** 105 unit tests with fake AWS clients. They need no AWS account. |
| Run 01 (5 users, team sandbox, 2026-10-05) | **Done.** Both methods matched the answer key. The run used the root user. The manual time (about 15 minutes) is an estimate. The raw output files were not saved. |
| Run 02 (8 users, edge cases t6 to t8) | **Done.** 8 of 8 matches under the read-only scanner identity. Not blind. |
| Run 03 (blind test, 30 users) | **Done.** Both methods scored 30 of 30. The automated check took 4.4 s and the manual audit 16 min. The test is only partly blind: the tester built the users and did the only audit. |
| Credential report cross-check | **Done.** The automated check and the AWS credential report agreed on all 12 users. |
| Negative tests | **Done.** The wrong account is refused (exit 2). A run without permission stops with no report written (exit 3). |
| Independent audit of a set built by another team member | **In progress.** |
| Comparison with the AWS Config managed rules | **Planned.** |


## Repository map

| Folder | What is in it |
|--------|---------------|
| `automation/mfa_checker/` | Automated check: collector, OPA rule, tests, and its own README |
| `scripts/` | Validation scripts: user MFA status, credential report check, and scoring |
| `tests/` | Test plan, manual audit procedure, test cases, results template, traceability matrix, and unit tests |
| `policies/` | Baseline requirements and pointers to machine-readable policies |
| `iam-config/` | IAM policy documents used in the lab |
| `docs/` | Working agreement, schedule, fallback plan, decision records, and standards |
| `evidence/` | Redacted outputs and screenshots from test runs |

Each folder has its own README with details. The repository is licensed under `LICENSE`.
Third-party tools and their licenses are in `THIRD_PARTY.md`.

## Quick start

Commands are for Windows Command Prompt or PowerShell. Replace `<SANDBOX_ID>` with the
sandbox account ID when you run a command, and never type the real ID into a file you commit.
In AWS CloudShell, use `python3` instead of `py`.

**Run the unit tests (no AWS account needed):**

```
py -m pip install -r scripts\requirements.txt
py -m unittest discover -s tests -v
```

**Run the automated check (sandbox account only).** It needs the `opa` program on your path,
or pass its location with `--opa`. See `automation/mfa_checker/README.md`.

```
cd automation\mfa_checker
py run_check.py --approved-account-id <SANDBOX_ID> --outdir ..\..\evidence\run-02\automated --mask-account-id
```

**Run the validation scripts (sandbox account only).** They refuse to run in any other account.

```
cd scripts
py check_mfa_status.py --approved-account-id <SANDBOX_ID> --profile lab-readonly
py credential_report_check.py --approved-account-id <SANDBOX_ID> --profile lab-readonly
```

**Score a run against the answer key:**

```
py scripts\score_results.py --truth evidence\run-02\edge-cases-t6-t8\labeled-population.csv --automated evidence\run-02\edge-cases-t6-t8\report.csv --out-dir evidence\run-02\edge-cases-t6-t8
```
The blind test in `evidence/run-03/` was scored with `scripts/TestScripts/score_blind.py`. See that folder's README.

## Working in this repository

- Work on a branch and open a pull request. Do not commit directly to `main`.
- Never commit access keys, secret keys, session tokens, or passwords.
- Replace real account IDs, access key IDs, ARNs, and user names with placeholders before committing.
- Do not commit raw `snapshot.json` files, `output-private/`, or the OPA executable.
- Check every screenshot at full size before committing it.
- Use only controlled lab data.
- This repository is intended to be public, so assume anyone can read every file and its
  full history.

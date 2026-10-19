# team3-iam-policy-as-code

Capstone 2026 project: Team 3, Cloud Identity and Policy-as-Code Assurance.

## What this project does

The team builds an identity and control-assurance pipeline for AWS IAM. It compares a
baseline security requirement with machine-checkable evidence collected from a controlled
sandbox account. The first control under test is **MFA enforcement**: every IAM user who
can sign in to the AWS console must have multi-factor authentication.

Three methods are compared against labeled test users (t1 to t5) with known answers:

1. **Automated policy-as-code check:** a read-only collector gathers IAM facts and an
   Open Policy Agent (OPA) rule decides compliance.
2. **Independent read-only scripts:** Python checks of user MFA status and the IAM
   credential report, used to cross-check the automated result.
3. **Manual audit:** a person checks each test user in the console, which provides a
   timing and accuracy baseline.

## Repository map

| Folder | What is in it |
|--------|---------------|
| `automation/mfa_checker/` | Automated check: collector, OPA rule, tests, and its own README |
| `tests/` | Test plan, test cases, results template, traceability matrix, and unit tests |
| `policies/` | Baseline requirements and pointers to machine-readable policies |
| `iam-config/` | IAM policy documents used in the lab |
| `docs/` | Standards, plans, and project notes |
| `evidence/` | Redacted outputs and screenshots from test runs |

Each folder has its own README with details and run instructions.

## Quick start

```
# Automated check (sandbox account only; see automation/mfa_checker/README.md)
python run_check.py --approved-account-id <SANDBOX_ID> --outdir evidence/run1 --mask-account-id



## Working in this repository

- Work on a branch and open a pull request. Do not commit directly to `main`.
- Never commit access keys, secret keys, session tokens, or passwords.
- Replace real account IDs, ARNs, and usernames with placeholders before committing.
- Do not commit raw `snapshot.json` files or the OPA executable.
- Use only controlled lab data.
- This repository is intended to be public, so assume anyone can read every file and
  its full history.

## Status

Work in progress. Test results and evidence are added to `evidence/` as runs are
completed, and each requirement is tracked in `tests/traceability-matrix.md`.

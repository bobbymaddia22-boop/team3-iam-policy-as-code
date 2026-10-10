# MFA Enforcement Tests

Testing and validation materials for the **MFA enforcement** control on AWS IAM.
This folder belongs to Team 3 (Cloud Identity and Policy-as-Code Assurance).

## Purpose

Verify, with repeatable and machine-checkable evidence, that multi-factor
authentication (MFA) is enforced for IAM identities in the controlled lab environment.

## Contents

| File | What it is |
|------|------------|
| `test-plan.md` | Control objective, scope, environment, and pass/fail criteria |
| `test-cases.md` | The individual test cases (steps, expected results) |
| `results-template.md` | Blank record to copy for each test run |
| `traceability-matrix.md` | Links each baseline requirement to its test and evidence |

## How to run the tests

1. Read `test-plan.md` and confirm the environment prerequisites are met.
2. Work through the cases in `test-cases.md` in order.
3. For each run, copy `results-template.md` to a new file named
   `results-YYYY-MM-DD-<tester-initials>.md` and fill it in.
4. Save screenshots and raw outputs in the repo's `/evidence` folder
   (sanitized first) and reference them by filename in your results.
5. Update `traceability-matrix.md` with the final status.

## Rules for this public repository

- Never commit access keys, secret keys, session tokens, or passwords.
- Replace real account IDs, ARNs, and usernames with placeholders such as
  `111122223333` and `example-user`.
- Redact the AWS console header, account alias, and email addresses in screenshots.
- Use only controlled lab data. No real user or organizational data.

## Owner

Testing and Validation Lead: Bobby Maddia


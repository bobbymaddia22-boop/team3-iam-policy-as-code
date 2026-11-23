# IAM Identity Policy Standards

## Purpose

Define the security requirements for the IAM identity policies kept in this repository and
for the IAM control this project tests: every IAM user with a console password has at least
one MFA device registered.

Each standard says how the project checks it today, so the document does not claim more than
the team has done.

## Standards

### IAM-001: Valid policy syntax
All policy files must contain valid JSON and follow the AWS IAM policy grammar.

*Checked by:* review. No automated validator runs yet.

### IAM-002: Least privilege
Grant only the actions and resources required by the intended user, role, or workload.

*Checked by:* review. The two policies in this repository grant read-only IAM actions only
(see IAM-008).

### IAM-003: Wildcard actions
`Action: "*"` is prohibited by default. Exceptions require documented justification and
review.

*Checked by:* review. Neither policy in this repository uses a wildcard action.

### IAM-004: Resource scoping
Use specific resource ARNs where supported. `Resource: "*"` must be reviewed for necessity.

*Checked by:* review. Both policies use `Resource: "*"` for read-only list and report
actions. This was reviewed and accepted for the lab. Narrowing it is a possible improvement.

### IAM-005: Review and traceability
Changes are made on a branch and merged through a pull request that a teammate reviews.

*Checked by:* the pull request history.

### IAM-006: Automated validation
Policy and code changes should pass the project's tests before they are merged.

*Checked by:* reviewers run the tests by hand (`tests/README.md`). The repository does not
yet run them automatically on each pull request.

### IAM-007: MFA for console users
Every IAM user with a console password has at least one MFA device registered. Users
without a console password are outside this rule (status `NOT_APPLICABLE`).

*Source:* the CIS AWS Foundations Benchmark control "Ensure multi-factor authentication
(MFA) is enabled for all IAM users that have a console password". Its control number differs
between benchmark versions, so see `tests/traceability-matrix.md` for the version used.

*Checked by:* the automated check in `automation/mfa_checker/` (OPA rule on collected IAM
state), the validation scripts in `scripts/`, and a manual audit. Results for each run are in
`evidence/`.

### IAM-008: Read-only checks
The identities that run the checks have read-only permissions.

- The automated check uses `automation/mfa_checker/scanner-iam-policy.json`:
  `iam:ListUsers`, `iam:ListMFADevices`, `iam:GetLoginProfile`.
- The validation scripts use `iam-config/validation-scripts-readonly-policy.json`, which adds
  `iam:GetAccountSummary`, `iam:GenerateCredentialReport`, and `iam:GetCredentialReport`.
  `GenerateCredentialReport` asks IAM to create a report but does not change any user,
  password, or MFA device.

*Checked by:* the policy files, the unit tests, and a run under the read-only scanner
identity (`evidence/support/scanner-identity-and-negative-tests/`).

### IAM-009: Wrong account is refused
Each script takes an approved account ID and stops before making any IAM call if the
credentials belong to another account.

*Checked by:* the unit tests and a live wrong-account run
(`evidence/support/scanner-identity-and-negative-tests/`).

## Scope

These standards cover IAM identity policies and the MFA registration control above.
Resource policies and Service Control Policies are outside the scanning scope.

## Limitations

- The check reads which MFA devices are registered. It does not test whether AWS blocks a
  sign-in or API call that lacks MFA. That is enforcement testing and is later work.
- Results describe the account at the moment of the run.
- Test populations are small and synthetic. Treat accuracy figures as descriptive, not as
  an estimate of real-world performance.
- Passing automated checks does not guarantee that a policy is secure or implements least
  privilege.

# IAM configuration

IAM policy documents used in the lab.

| File | What it is |
|------|------------|
| `validation-scripts-readonly-policy.json` | Permissions the validation scripts in `scripts/` need: `ListUsers`, `ListMFADevices`, `GetLoginProfile`, `GetAccountSummary`, `GenerateCredentialReport`, and `GetCredentialReport`. Attach it to the read-only identity used for a run. |

The automated check's read-only scanner permissions are kept next to the tool in
`automation/mfa_checker/scanner-iam-policy.json`. They are narrower than the file above:
the automated check does not read the account summary or the credential report, so an
identity that has only the scanner policy cannot run the validation scripts.

`GenerateCredentialReport` does not change any user, password, or MFA device, but it does
ask IAM to create a report. Say so when describing the scripts as read-only.

Policies for enforcement tests, such as a policy that denies actions without MFA, are
later work. Add them here when the team creates them, and replace real account IDs with
placeholders.

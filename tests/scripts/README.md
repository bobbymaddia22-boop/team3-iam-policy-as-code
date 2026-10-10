# MFA Check Scripts

Read-only Python scripts that check MFA coverage in the AWS IAM lab account.
They never create, change, or delete anything in AWS.

## Files

| File | Purpose | Test cases |
|------|---------|------------|
| `check_mfa_status.py` | Lists IAM users, console access, MFA devices, and root MFA status | MFA-01, MFA-02, MFA-06 |
| `credential_report_check.py` | Checks the IAM credential report for console users without MFA | MFA-06, MFA-07 |
| `mfa_common.py` | Shared helpers (AWS connection, redaction, saving results) |  |
| `requirements.txt` | Python dependencies |  |

## Setup

1. Install Python 3 and the AWS CLI.
2. Install dependencies: `pip install -r requirements.txt`
3. Create a read-only lab profile: `aws configure --profile lab-readonly`

Required IAM permissions: `iam:ListUsers`, `iam:GetLoginProfile`,
`iam:ListMFADevices`, `iam:GetAccountSummary`,
`iam:GenerateCredentialReport`, `iam:GetCredentialReport`.

## Usage

```
python check_mfa_status.py --profile lab-readonly
python credential_report_check.py --profile lab-readonly --format both
```

Results print to the screen and are saved to `sample-output/`
with user names redacted (user-001, user-002, ...).

Exit codes: 0 = pass, 1 = at least one failure, 2 = could not run.

## Safety rules (public repository)

- Never put access keys or secrets in these scripts or commit them.
- Do not commit anything in `output-private/`. It is created by the
  `--show-names` option and contains real user names.
- Review output files for account IDs, ARNs, and names before committing.
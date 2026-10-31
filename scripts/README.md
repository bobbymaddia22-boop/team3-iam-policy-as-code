# MFA Check Scripts

Read-only Python scripts that check MFA coverage in the AWS IAM lab account.
They never create, change, or delete anything in AWS.

## Files

| File | Purpose | Test cases |
|------|---------|------------|
| `check_mfa_status.py` | Lists IAM users, console access, MFA devices, and root MFA status | MFA-01, MFA-02, MFA-06 |
| `credential_report_check.py` | Checks the IAM credential report for console users without MFA | MFA-06, MFA-07 |
| `mfa_common.py` | Shared helpers (AWS connection, redaction, saving results) |  |
| `score_results.py` | Scores the automated and manual results against the labeled population. Reads files only and never calls AWS | T1 to T5 comparison |
| `requirements.txt` | Python dependencies |  |

## Setup

1. Install Python 3 and the AWS CLI.
2. Install dependencies: `pip install -r requirements.txt`
3. Create a read-only lab profile: `aws configure --profile lab-readonly`

Required IAM permissions: `iam:ListUsers`, `iam:GetLoginProfile`,
`iam:ListMFADevices`, `iam:GetAccountSummary`,
`iam:GenerateCredentialReport`, `iam:GetCredentialReport`.
The account check uses `sts:GetCallerIdentity`, which needs no IAM permission.

## Usage

Both checks require `--approved-account-id`, the 12-digit ID of the sandbox account.
Before any IAM call, the script asks AWS which account the credentials belong to and
refuses to run if it is a different account (exit code 2).

```
py check_mfa_status.py --approved-account-id <SANDBOX_ID> --profile lab-readonly
py credential_report_check.py --approved-account-id <SANDBOX_ID> --profile lab-readonly --format both
```

Results print to the screen and are saved to `sample-output/` with user names
redacted (user-001, user-002, ...). Only the last four digits of the account ID are
written (for example `********3333`).

Do not type the real account ID into any file you commit. Put it in the command only.

## What the output reports

- **User control:** console users without an MFA device are failures. This is the
  result used to score the labeled population.
- **Root MFA:** reported separately in the summary (`root_mfa`). It is not counted
  in the user-control result.
- **Report generation time:** `credential_report_check.py` records
  `report_generated_utc` and `report_age_minutes`. AWS reuses a report generated
  in the last four hours, so the report can be that old. Use
  `--max-report-age-minutes 30` to refuse an older report.

## When the scripts refuse to give a result (exit code 2)

- The credentials belong to a different account than `--approved-account-id`, or the
  account cannot be confirmed (for example, an expired session).
- AWS denies a call.
- No users are returned.
- The credential report is empty, cut off, has no root row, or contains values other
  than true or false. An unusable report is never scored as a pass.
- The credential report is older than `--max-report-age-minutes`.

Exit codes: 0 = user control and root MFA both pass, 1 = at least one failure,
2 = could not run.

## Safety rules (public repository)

- Never put access keys or secrets in these scripts or commit them.
- Do not commit anything in `output-private/`. It is created by the
  `--show-names` option and contains real user names.
- Review output files for account IDs, ARNs, and names before committing.

## Scoring a run

`score_results.py` compares each method's results with the answer key in
`evidence/run-NN/labeled-population.csv`. It prints the confusion matrix,
precision, recall, false-positive rate, and the users where the two methods
disagree. It stops with exit code 2 if a user is missing, duplicated, or has an
unknown status, so a broken file is never scored as a success.

```
py score_results.py --truth ..\evidence\run-02\labeled-population.csv --automated ..\evidence\run-02\automated\report.csv --manual ..\evidence\run-02\manual-audit.csv --out-dir ..\evidence\run-02
```

The script writes `scoring-results.md` and `scoring-results.json` to `--out-dir`.
Unit tests: run `py -m unittest discover -s tests -v` from the repository root.

# Screenshots (add files here)

Use the original image files, not copies pasted out of a report. Name them `NN-short-description.png`.
The same screenshot may appear in more than one team member's section, so keep one copy of each.

## Screenshots from the sandbox run

1. `01-iam-users-list.png`: the IAM users list for t1 to t5, with the MFA and console access
   (or password age) columns visible
2. `02-iam-users-list-account.png`: the IAM users list in the Team 3 Capstone Project account
3. `03-script-run-report-csv.png`: the script run and the `report.csv` output
4. `04-cloudshell-tool-versions-run.png`: the CloudShell session showing the tool versions and the run
5. `05-cloudshell-summary-per-user.png`: the CloudShell output showing the summary line and the
   status for each user

## Still to capture

- `06-manual-audit-evidence.png`: the page or report the manual auditor used to check the users, so
  the evidence source is on record
- `07-t4-no-mfa-device.png` and `08-t5-two-mfa-devices.png`: the security credentials pages for the
  two users that test the boundary cases

## Redact before committing

- The AWS account ID and alias in the console header
- **Access key IDs** (for example t3's, which was already hidden in the report screenshots)
- Your email address and any other user names or ARNs
- Device serial numbers, if they contain the account ID

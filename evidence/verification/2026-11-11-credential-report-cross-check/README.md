# Credential report cross-check (2026-11-11)

Compares the automated MFA check with the AWS IAM credential report for the same account.

- Credential report generated (UTC): 2026-11-12T01:24:48+00:00
- Credential report downloaded (UTC): 2026-11-12T01:27:27.4677283Z
- Checker run (UTC): 2026-11-12T01:31:43.4441967Z
- Checker identity: scanner-ro (read-only). Report identity: validation-ro (read-only).
- No users or MFA devices were changed between the report and the checker run.

Result: 12 users compared, 12 matches, 0 mismatches, 0 users missing from the checker.

Method: the credential report was reduced to three columns (user, password_enabled, mfa_active) and mapped to a status (password and MFA = COMPLIANT, password without MFA = NON_COMPLIANT, no password = NOT_APPLICABLE). The raw report contains ARNs with the account ID and is not committed. The root account row was removed because the checker scans IAM users only.

Limits: both sources read the same IAM data, so agreement shows consistency, not that the answer key is correct. Not a blind test.
